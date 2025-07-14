"""Autonomous agent manager for build analysis and monitoring."""
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from app.services.jenkins_client import JenkinsClient
from app.services.bedrock_client import BedrockClient
from app.services.build_analyzer import BuildAnalyzer
from app.services.database import DatabaseService
from app.models.build import BuildInfo, BuildAnalysis
from app.utils.log_analyzer import (
    analyze_test_failures,
    analyze_build_time,
    analyze_dependency_issues,
    analyze_compilation_issues
)

class AgentManager:
    def __init__(
        self,
        jenkins_client: JenkinsClient,
        bedrock_client: BedrockClient,
        build_analyzer: BuildAnalyzer,
        db_service: DatabaseService
    ):
        self.jenkins = jenkins_client
        self.bedrock = bedrock_client
        self.analyzer = build_analyzer
        self.db = db_service
        
        # Initialize monitoring and caching attributes
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.analysis_cache: Dict[str, BuildAnalysis] = {}
        self.pattern_database: Dict[str, List[Dict[str, Any]]] = {}
        self.action_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize flags
        self.learning_enabled = True
        self.monitoring_enabled = True
        
        # Initialize database
        asyncio.create_task(self.db.init_db())
        
        # Load patterns from database
        asyncio.create_task(self.load_patterns())
        
    async def load_patterns(self):
        """Load patterns from the database."""
        try:
            logger.info("Loading patterns from database")
            patterns = await self.db.get_patterns()
            self.pattern_database = patterns
            logger.info(f"Loaded {sum(len(p) for p in patterns.values())} patterns from database")
        except Exception as e:
            logger.error(f"Error loading patterns from database: {e}")
            # Initialize with empty pattern database
            self.pattern_database = {}
        
    async def start(self):
        """Start the agent manager and its monitoring tasks."""
        logger.info("Starting agent monitoring tasks")
        try:
            await asyncio.gather(
                self.monitor_builds(),
                self.update_pattern_database(),
                self.cleanup_cache()
            )
        except Exception as e:
            logger.error(f"Failed to start monitoring tasks: {e}")
            raise
        
    async def monitor_builds(self):
        """Continuously monitor Jenkins builds."""
        logger.info("Starting build monitoring loop")
        while True:
            try:
                logger.debug("Fetching Jenkins jobs")
                jobs = self._get_all_jobs()
                for job in jobs:
                    job_name = job['fullname'] if 'fullname' in job else job['name']
                    if job_name not in self.active_monitors:
                        logger.info(f"Starting monitor for job: {job_name}")
                        self.active_monitors[job_name] = asyncio.create_task(
                            self.monitor_job(job_name)
                        )
                        
                # Clean up completed monitors
                completed = [name for name, task in self.active_monitors.items() 
                           if task.done()]
                for name in completed:
                    del self.active_monitors[name]
                    
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in build monitor: {e}")
                await asyncio.sleep(300)  # Back off on error
                
    async def monitor_job(self, job_name: str):
        """Monitor a specific Jenkins job."""
        last_build = None
        logger.info(f"Started monitoring job: {job_name}")
        while True:
            try:
                logger.debug(f"Checking for new builds in {job_name}")
                job_info = self.jenkins.server.get_job_info(job_name)
                latest_build = job_info.get('lastBuild', {}).get('number')
                
                if latest_build and latest_build != last_build:
                    await self.analyze_and_act(job_name, latest_build)
                    last_build = latest_build
                    
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error monitoring job {job_name}: {e}")
                await asyncio.sleep(300)
                
    async def analyze_and_act(self, job_name: str, build_number: int):
        """Analyze a build and take appropriate actions."""
        try:
            logger.info(f"Starting analysis for build {job_name}#{build_number}")
            # Get build analysis
            analysis = await self.analyzer.analyze_build(job_name, build_number)
            
            # Cache the analysis
            cache_key = f"{job_name}#{build_number}"
            self.analysis_cache[cache_key] = analysis
            logger.debug(f"Cached analysis for {cache_key}")
            
            # If build failed, take action
            if analysis.build_info.result != 'SUCCESS':
                await self.handle_failure(analysis)
                
            # Learn from the build
            if self.learning_enabled:
                await self.learn_from_build(analysis)
                
        except Exception as e:
            logger.error(f"Error analyzing build {job_name}#{build_number}: {e}")
            
    async def handle_failure(self, analysis: BuildAnalysis):
        """Handle build failures intelligently."""
        actions_taken = []
        build_key = f"{analysis.build_info.job_name}#{analysis.build_info.build_number}"
        
        # Check for known patterns
        matches = self.match_known_patterns(analysis)
        if matches:
            for match in matches:
                action = await self.apply_known_solution(match, analysis)
                actions_taken.append(action)
                self._record_action(build_key, {
                    "type": "pattern_match",
                    "pattern": match["pattern"],
                    "action": action
                })
        
        # Analyze specific issues
        test_results = analyze_test_failures(analysis.build_info.console_log)
        timing_info = analyze_build_time(analysis.build_info.console_log)
        dependency_issues = analyze_dependency_issues(analysis.build_info.console_log)
        compilation_issues = analyze_compilation_issues(analysis.build_info.console_log)
        
        # Take specific actions based on issue type
        if test_results['failed_tests']:
            action = await self.handle_test_failures(analysis, test_results)
            self._record_action(build_key, {
                "type": "test_failure",
                "details": test_results,
                "action": action
            })
            actions_taken.append(action)
            
        if dependency_issues:
            action = await self.handle_dependency_issues(analysis, dependency_issues)
            self._record_action(build_key, {
                "type": "dependency_issue",
                "details": dependency_issues,
                "action": action
            })
            actions_taken.append(action)
            
        if compilation_issues:
            action = await self.handle_compilation_issues(analysis, compilation_issues)
            self._record_action(build_key, {
                "type": "compilation_issue",
                "details": compilation_issues,
                "action": action
            })
            actions_taken.append(action)
            
        # Update build description with actions taken
        description = (
            f"Build Analysis Report:\n"
            f"- Severity: {analysis.severity}\n"
            f"- Confidence: {analysis.confidence}\n"
            f"- Actions Taken: {', '.join(actions_taken)}\n"
            f"- Recommendations: {', '.join(analysis.recommendations)}"
        )
        
        # Update build description using the proper method
        try:
            self.jenkins.update_build_description(
                analysis.build_info.job_name,
                analysis.build_info.build_number,
                description
            )
            logger.debug(f"Updated build description for {analysis.build_info.job_name}#{analysis.build_info.build_number}")
        except Exception as e:
            logger.error(f"Failed to update build description: {e}")
        
    async def learn_from_build(self, analysis: BuildAnalysis):
        """Learn from build outcomes to improve future analysis."""
        build_key = f"{analysis.build_info.job_name}#{analysis.build_info.build_number}"
        if analysis.build_info.result == 'SUCCESS':
            # Learn from successful builds
            logger.info(f"Learning from successful build: {build_key}")
            self.update_success_patterns(analysis)
        else:
            # Learn from failures and their resolutions
            logger.info(f"Learning from failed build: {build_key}")
            self.update_failure_patterns(analysis)
            
    def match_known_patterns(self, analysis: BuildAnalysis) -> List[Dict[str, Any]]:
        """Match build issues against known patterns."""
        matches = []
        for pattern in self.pattern_database.get(analysis.build_info.job_name, []):
            if self.pattern_matches(pattern, analysis):
                matches.append(pattern)
        return matches
    
    def _record_action(self, build_key: str, action: Dict[str, Any]):
        """Record an action taken by the agent."""
        if build_key not in self.action_history:
            self.action_history[build_key] = []
        action["timestamp"] = datetime.now().isoformat()
        self.action_history[build_key].append(action)

    async def apply_known_solution(self, pattern: Dict[str, Any], analysis: BuildAnalysis) -> str:
        """Apply a known solution and record the action."""
        build_key = f"{analysis.build_info.job_name}#{analysis.build_info.build_number}"
        solution = pattern.get('solution')
        if not solution:
            return "No known solution"
            
        try:
            result = None
            if solution.get('type') == 'retry':
                result = await self.retry_build(analysis)
            elif solution.get('type') == 'parameter_adjust':
                result = await self.adjust_build_parameters(analysis, solution.get('parameters', {}))
            elif solution.get('type') == 'notification':
                result = await self.notify_team(analysis, solution.get('message'))
            
            # Record the action
            self._record_action(build_key, {
                "type": solution.get('type'),
                "pattern": pattern['pattern'],
                "result": result
            })
            
            return result or f"Unknown solution type: {solution.get('type')}"
        except Exception as e:
            logger.error(f"Error applying solution: {e}")
            return f"Solution failed: {str(e)}"
            
    async def retry_build(self, analysis: BuildAnalysis) -> str:
        """Retry a failed build with potential adjustments."""
        try:
            self.jenkins.server.build_job(
                analysis.build_info.job_name,
                analysis.build_info.parameters
            )
            return "Build retried"
        except Exception as e:
            logger.error(f"Error retrying build: {e}")
            return f"Retry failed: {str(e)}"
            
    async def adjust_build_parameters(self, analysis: BuildAnalysis, adjustments: Dict[str, Any]) -> str:
        """Adjust build parameters based on analysis."""
        try:
            new_params = analysis.build_info.parameters.copy()
            new_params.update(adjustments)
            self.jenkins.server.build_job(
                analysis.build_info.job_name,
                new_params
            )
            return f"Build retried with adjusted parameters: {adjustments}"
        except Exception as e:
            logger.error(f"Error adjusting parameters: {e}")
            return f"Parameter adjustment failed: {str(e)}"
            
    async def notify_team(self, analysis: BuildAnalysis, message: str) -> str:
        """Notify team about build issues."""
        # Implementation would depend on your notification system
        # This is a placeholder
        logger.info(f"Team notification for {analysis.build_info.job_name}: {message}")
        return "Team notified"
            
    async def update_pattern_database(self):
        """Periodically update the pattern database based on learned patterns."""
        while True:
            try:
                # Analyze recent builds to identify patterns
                for job_name in self.pattern_database.keys():
                    recent_analyses = [
                        analysis for key, analysis in self.analysis_cache.items()
                        if key.startswith(f"{job_name}#")
                    ]
                    
                    if recent_analyses:
                        new_patterns = self.extract_patterns(recent_analyses)
                        self.pattern_database[job_name].extend(new_patterns)
                        
                # Clean up old patterns
                self.cleanup_patterns()
                
                await asyncio.sleep(3600)  # Update every hour
            except Exception as e:
                logger.error(f"Error updating pattern database: {e}")
                await asyncio.sleep(3600)
                
    def extract_patterns(self, analyses: List[BuildAnalysis]) -> List[Dict[str, Any]]:
        """Extract common patterns from build analyses."""
        patterns = []
        # Implementation would use clustering or pattern matching algorithms
        # This is a simplified version
        error_counts: Dict[str, int] = {}
        
        for analysis in analyses:
            for error in analysis.error_patterns:
                key = error['pattern']
                error_counts[key] = error_counts.get(key, 0) + 1
                
        # Convert frequent patterns to pattern database entries
        for pattern, count in error_counts.items():
            if count >= 3:  # Pattern appears in at least 3 builds
                patterns.append({
                    'pattern': pattern,
                    'frequency': count,
                    'last_seen': datetime.now(),
                    'solution': self.derive_solution(pattern, analyses)
                })
                
        return patterns
    
    def derive_solution(self, pattern: str, analyses: List[BuildAnalysis]) -> Optional[Dict[str, Any]]:
        """Derive a solution for a pattern based on historical data."""
        # Implementation would analyze successful resolutions
        # This is a placeholder
        return None
        
    def cleanup_patterns(self):
        """Clean up old or invalid patterns."""
        now = datetime.now()
        for job_name in self.pattern_database.keys():
            self.pattern_database[job_name] = [
                pattern for pattern in self.pattern_database[job_name]
                if now - pattern['last_seen'] < timedelta(days=30)
            ]
            
    async def cleanup_cache(self):
        """Periodically clean up the analysis cache."""
        while True:
            try:
                now = datetime.now()
                expired = []
                
                for key, analysis in self.analysis_cache.items():
                    if now - analysis.timestamp > timedelta(days=7):
                        expired.append(key)
                        
                for key in expired:
                    del self.analysis_cache[key]
                    
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error cleaning up cache: {e}")
                await asyncio.sleep(3600)
                
    def pattern_matches(self, pattern: Dict[str, Any], analysis: BuildAnalysis) -> bool:
        """Check if a pattern matches the current build analysis."""
        pattern_str = pattern['pattern']
        return any(
            error['pattern'] == pattern_str
            for error in analysis.error_patterns
        )
    
    async def handle_test_failures(self, analysis: BuildAnalysis, test_results: Dict[str, Any]) -> str:
        """Handle test failures by analyzing patterns and suggesting fixes."""
        failed_tests = test_results.get('failed_tests', [])
        if not failed_tests:
            return "No test failures to handle"
            
        # Group failures by type/package
        failure_groups = {}
        for test in failed_tests:
            group = test.get('package', 'unknown')
            if group not in failure_groups:
                failure_groups[group] = []
            failure_groups[group].append(test)
            
        actions = []
        for group, tests in failure_groups.items():
            if len(tests) > 3:
                # Multiple failures in same package - might be environmental
                actions.append(f"Multiple failures in {group} - checking environment")
                await self.check_test_environment(analysis, group)
            else:
                # Individual test failures - analyze each
                for test in tests:
                    actions.append(f"Analyzing failure in {test.get('name')}")
                    await self.analyze_test_failure(analysis, test)
                    
        return "; ".join(actions)
        
    async def handle_dependency_issues(self, analysis: BuildAnalysis, issues: List[Dict[str, Any]]) -> str:
        """Handle dependency-related build failures."""
        actions = []
        for issue in issues:
            if issue.get('type') == 'missing':
                # Handle missing dependencies
                actions.append(f"Missing dependency: {issue.get('name')}")
                if issue.get('version'):
                    actions.append(f"Attempting to install version {issue.get('version')}")
                    # Would integrate with package manager here
            elif issue.get('type') == 'version_conflict':
                # Handle version conflicts
                actions.append(f"Version conflict in {issue.get('name')}")
                if issue.get('resolution'):
                    actions.append(f"Suggested resolution: {issue.get('resolution')}")
                    
        if actions:
            return "; ".join(actions)
        return "No dependency issues to handle"
        
    async def handle_compilation_issues(self, analysis: BuildAnalysis, issues: List[Dict[str, Any]]) -> str:
        """Handle compilation failures."""
        actions = []
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type == 'syntax_error':
                actions.append(f"Syntax error in {issue.get('file')}: {issue.get('message')}")
            elif issue_type == 'type_error':
                actions.append(f"Type error: {issue.get('message')}")
            elif issue_type == 'import_error':
                actions.append(f"Import error: {issue.get('message')}")
                # Could add logic to fix import paths or suggest missing imports
                
        if actions:
            return "; ".join(actions)
        return "No compilation issues to handle"
        
    async def check_test_environment(self, analysis: BuildAnalysis, package: str):
        """Check the test environment for issues affecting multiple tests."""
        # This would integrate with your test infrastructure
        logger.info(f"Checking test environment for package {package}")
        # Implementation would depend on your testing setup
        
    async def analyze_test_failure(self, analysis: BuildAnalysis, test: Dict[str, Any]):
        """Analyze an individual test failure."""
        # This would integrate with your test runner and source control
        logger.info(f"Analyzing test failure: {test.get('name')}")
        # Implementation would depend on your testing setup
        
    def update_success_patterns(self, analysis: BuildAnalysis):
        """Update patterns based on successful builds."""
        job_name = analysis.build_info.job_name
        
        # Initialize job patterns if not exists
        if job_name not in self.pattern_database:
            self.pattern_database[job_name] = []
            
        # Extract success patterns from the build
        success_indicators = self._extract_success_indicators(analysis)
        
        for indicator in success_indicators:
            # Check if this success pattern already exists
            existing_pattern = None
            for pattern in self.pattern_database[job_name]:
                if (pattern.get('type') == 'success' and 
                    pattern.get('indicator') == indicator['pattern']):
                    existing_pattern = pattern
                    break
                    
            if existing_pattern:
                # Update existing pattern
                existing_pattern['frequency'] += 1
                existing_pattern['last_seen'] = datetime.now()
                existing_pattern['success_rate'] = min(1.0, existing_pattern.get('success_rate', 0.8) + 0.1)
            else:
                # Create new success pattern
                self.pattern_database[job_name].append({
                    'type': 'success',
                    'pattern': indicator['pattern'],
                    'indicator': indicator['pattern'],
                    'frequency': 1,
                    'last_seen': datetime.now(),
                    'success_rate': 0.9,
                    'build_params': analysis.build_info.parameters.copy(),
                    'environment': indicator.get('environment', {}),
                    'duration_range': {
                        'min': analysis.build_info.duration,
                        'max': analysis.build_info.duration
                    }
                })
                
        logger.debug(f"Updated success patterns for {job_name}: {len(success_indicators)} indicators")
        
    def update_failure_patterns(self, analysis: BuildAnalysis):
        """Update patterns based on failed builds."""
        job_name = analysis.build_info.job_name
        
        # Initialize job patterns if not exists
        if job_name not in self.pattern_database:
            self.pattern_database[job_name] = []
            
        # Extract failure patterns from the analysis
        for error_pattern in analysis.error_patterns:
            pattern_key = error_pattern.get('pattern', '')
            
            # Check if this failure pattern already exists
            existing_pattern = None
            for pattern in self.pattern_database[job_name]:
                if (pattern.get('type') == 'failure' and 
                    pattern.get('pattern') == pattern_key):
                    existing_pattern = pattern
                    break
                    
            if existing_pattern:
                # Update existing pattern
                existing_pattern['frequency'] += 1
                existing_pattern['last_seen'] = datetime.now()
                existing_pattern['severity'] = max(
                    existing_pattern.get('severity', 'medium'),
                    analysis.severity
                )
                
                # Update failure contexts
                if 'contexts' not in existing_pattern:
                    existing_pattern['contexts'] = []
                existing_pattern['contexts'].append({
                    'build_number': analysis.build_info.build_number,
                    'timestamp': analysis.timestamp,
                    'parameters': analysis.build_info.parameters.copy(),
                    'duration': analysis.build_info.duration
                })
                
                # Keep only last 10 contexts to prevent memory bloat
                existing_pattern['contexts'] = existing_pattern['contexts'][-10:]
                
            else:
                # Create new failure pattern
                new_pattern = {
                    'type': 'failure',
                    'pattern': pattern_key,
                    'frequency': 1,
                    'last_seen': datetime.now(),
                    'severity': analysis.severity,
                    'confidence': analysis.confidence,
                    'error_type': error_pattern.get('type', 'unknown'),
                    'contexts': [{
                        'build_number': analysis.build_info.build_number,
                        'timestamp': analysis.timestamp,
                        'parameters': analysis.build_info.parameters.copy(),
                        'duration': analysis.build_info.duration
                    }],
                    'solution': None  # Will be derived later
                }
                
                # Try to derive an initial solution based on error type
                initial_solution = self._derive_initial_solution(error_pattern)
                if initial_solution:
                    new_pattern['solution'] = initial_solution
                    
                self.pattern_database[job_name].append(new_pattern)
                
        # Check if we can correlate this failure with previous successful builds
        self._correlate_failure_with_success(analysis)
        
        logger.debug(f"Updated failure patterns for {job_name}: {len(analysis.error_patterns)} patterns")
        
    def _extract_success_indicators(self, analysis: BuildAnalysis) -> List[Dict[str, Any]]:
        """Extract indicators that contributed to build success."""
        indicators = []
        
        # Check build parameters that often correlate with success
        stable_params = ['branch', 'environment', 'version']
        param_indicators = {}
        for param in stable_params:
            if param in analysis.build_info.parameters:
                param_indicators[param] = analysis.build_info.parameters[param]
                
        if param_indicators:
            indicators.append({
                'pattern': f"stable_params_{hash(str(sorted(param_indicators.items())))}",
                'type': 'parameters',
                'environment': param_indicators
            })
            
        # Check build timing - successful builds often have consistent timing
        if analysis.build_info.duration:
            duration_category = 'fast' if analysis.build_info.duration < 300 else 'normal'
            indicators.append({
                'pattern': f"timing_{duration_category}",
                'type': 'timing',
                'duration': analysis.build_info.duration
            })
            
        # Check for absence of common failure indicators in logs
        if hasattr(analysis.build_info, 'console_log') and analysis.build_info.console_log:
            log_indicators = self._extract_log_success_indicators(analysis.build_info.console_log)
            indicators.extend(log_indicators)
            
        return indicators
        
    def _extract_log_success_indicators(self, console_log: str) -> List[Dict[str, Any]]:
        """Extract success indicators from build logs."""
        indicators = []
        
        # Look for positive indicators
        success_patterns = [
            'BUILD SUCCESSFUL',
            'Tests run: .* Failures: 0',
            'All tests passed',
            'Compilation successful',
            'No errors found'
        ]
        
        for pattern in success_patterns:
            if pattern.lower() in console_log.lower():
                indicators.append({
                    'pattern': f"log_success_{pattern.replace(' ', '_').lower()}",
                    'type': 'log_indicator',
                    'matched_text': pattern
                })
                
        return indicators
        
    def _derive_initial_solution(self, error_pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Derive an initial solution based on error pattern type."""
        error_type = error_pattern.get('type', 'unknown')
        pattern = error_pattern.get('pattern', '')
        
        # Common solutions based on error types
        if error_type == 'test_failure':
            return {
                'type': 'retry',
                'reason': 'Test failures often resolve on retry',
                'max_retries': 2
            }
        elif error_type == 'dependency_issue':
            return {
                'type': 'parameter_adjust',
                'parameters': {'clean_dependencies': 'true'},
                'reason': 'Clean dependency cache and retry'
            }
        elif error_type == 'compilation_error':
            return {
                'type': 'notification',
                'message': f'Compilation error detected: {pattern}',
                'reason': 'Code changes needed, notify development team'
            }
        elif 'timeout' in pattern.lower():
            return {
                'type': 'parameter_adjust',
                'parameters': {'timeout': '1800'},
                'reason': 'Increase timeout for long-running builds'
            }
        elif 'out of memory' in pattern.lower() or 'oom' in pattern.lower():
            return {
                'type': 'parameter_adjust',
                'parameters': {'memory': '4g'},
                'reason': 'Increase memory allocation'
            }
            
        return None
        
    def _correlate_failure_with_success(self, analysis: BuildAnalysis):
        """Correlate current failure with previous successful builds to identify differences."""
        job_name = analysis.build_info.job_name
        
        # Find recent successful builds from cache
        successful_analyses = []
        for key, cached_analysis in self.analysis_cache.items():
            if (key.startswith(f"{job_name}#") and 
                cached_analysis.build_info.result == 'SUCCESS' and
                cached_analysis.build_info.build_number < analysis.build_info.build_number):
                successful_analyses.append(cached_analysis)
                
        if not successful_analyses:
            return
            
        # Get the most recent successful build
        latest_success = max(successful_analyses, 
                           key=lambda x: x.build_info.build_number)
        
        # Compare parameters
        param_diff = self._compare_build_parameters(
            analysis.build_info.parameters,
            latest_success.build_info.parameters
        )
        
        if param_diff:
            # Add correlation pattern
            correlation_pattern = {
                'type': 'correlation',
                'pattern': f"param_change_{hash(str(sorted(param_diff.items())))}",
                'frequency': 1,
                'last_seen': datetime.now(),
                'parameter_changes': param_diff,
                'success_build': latest_success.build_info.build_number,
                'failure_build': analysis.build_info.build_number,
                'solution': {
                    'type': 'parameter_adjust',
                    'parameters': {k: v['old'] for k, v in param_diff.items() 
                                 if v['type'] == 'changed'},
                    'reason': 'Revert parameter changes that may have caused failure'
                }
            }
            
            if job_name not in self.pattern_database:
                self.pattern_database[job_name] = []
            self.pattern_database[job_name].append(correlation_pattern)
            
            logger.info(f"Found parameter correlation for {job_name}: {param_diff}")
            
    def _compare_build_parameters(self, current_params: Dict[str, Any], 
                                success_params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare build parameters between current and successful builds."""
        diff = {}
        all_keys = set(current_params.keys()) | set(success_params.keys())
        
        for key in all_keys:
            if key not in current_params:
                diff[key] = {'type': 'removed', 'old': success_params[key], 'new': None}
            elif key not in success_params:
                diff[key] = {'type': 'added', 'old': None, 'new': current_params[key]}
            elif current_params[key] != success_params[key]:
                diff[key] = {'type': 'changed', 'old': success_params[key], 'new': current_params[key]}
                
        return diff

    def _get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all Jenkins jobs including multibranch pipeline jobs."""
        all_jobs = []
        
        def collect_jobs(jobs, prefix=""):
            for job in jobs:
                if job.get('_class') == 'org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject':
                    # This is a multibranch pipeline, get its sub-jobs
                    try:
                        multibranch_jobs = self.jenkins.server.get_jobs(folder_depth=1, )
                        for sub_job in multibranch_jobs:
                            sub_job['fullname'] = f"{prefix}{job['name']}/{sub_job['name']}"
                            all_jobs.append(sub_job)
                    except Exception as e:
                        logger.warning(f"Failed to get multibranch jobs for {job['name']}: {e}")
                elif job.get('_class') == 'com.cloudbees.hudson.plugins.folder.Folder':
                    # This is a folder, get its sub-jobs
                    try:
                        folder_jobs = self.jenkins.server.get_jobs(folder_depth=1, )
                        collect_jobs(folder_jobs, f"{prefix}{job['name']}/")
                    except Exception as e:
                        logger.warning(f"Failed to get folder jobs for {job['name']}: {e}")
                else:
                    # Regular job
                    job['fullname'] = f"{prefix}{job['name']}"
                    all_jobs.append(job)
        
        try:
            top_level_jobs = self.jenkins.server.get_jobs()
            collect_jobs(top_level_jobs)
        except Exception as e:
            logger.error(f"Failed to get Jenkins jobs: {e}")
            return []
            
        logger.debug(f"Found {len(all_jobs)} total jobs (including multibranch pipelines)")
        return all_jobs
