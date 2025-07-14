"""Build analysis service that coordinates the analysis process."""
from typing import List, Optional
from app.services.jenkins_client import JenkinsClient
from app.services.bedrock_client import BedrockClient
from app.models.build import BuildInfo, BuildAnalysis, BuildComparison
from datetime import datetime

class BuildAnalyzer:
    def __init__(self, jenkins_client: JenkinsClient, bedrock_client: BedrockClient):
        self.jenkins = jenkins_client
        self.bedrock = bedrock_client
        
    async def analyze_build(self, job_name: str, build_number: int) -> BuildAnalysis:
        """Analyze a build and generate insights."""
        # Get build information
        build_info = await self.jenkins.get_build_info(job_name, build_number)
        
        # If build failed or is in progress, get last successful build for comparison
        last_success = None
        if build_info.result not in ['SUCCESS', 'IN_PROGRESS']:
            last_success = await self.jenkins.get_last_successful_build(job_name, build_number)
        elif build_info.result == 'IN_PROGRESS':
            # For in-progress builds, we'll analyze what we have so far
            build_info.result = 'UNKNOWN'  # Set a valid result state for analysis
            
        # Perform LLM analysis
        analysis = await self.bedrock.analyze_build(build_info, last_success)
        
        if last_success:
            # Create build comparison for more detailed insights
            comparison = await self.compare_builds(build_info, last_success)
            
            # Add any additional insights from comparison to the analysis
            analysis.differences.extend([
                {"type": "parameters", "description": str(comparison.parameter_diff)},
                {"type": "environment", "description": str(comparison.environment_diff)}
            ])
            
        return analysis
    
    async def compare_builds(self, failed_build: BuildInfo, successful_build: BuildInfo) -> BuildComparison:
        """Compare a failed build with a successful build to identify differences."""
        # Compare build parameters
        param_diff = self._compare_dicts(
            failed_build.parameters,
            successful_build.parameters
        )
        
        # Compare environment variables (extracted from build logs)
        env_vars_failed = self._extract_env_vars(failed_build.console_log)
        env_vars_success = self._extract_env_vars(successful_build.console_log)
        env_diff = self._compare_dicts(env_vars_failed, env_vars_success)
        
        # Compare logs (focusing on error sections)
        log_diff = self._compare_logs(failed_build.console_log, successful_build.console_log)
        
        return BuildComparison(
            failed_build=failed_build,
            successful_build=successful_build,
            parameter_diff=param_diff,
            environment_diff=env_diff,
            log_diff=log_diff,
            timestamp=datetime.now()
        )
    
    def _compare_dicts(self, dict1: dict, dict2: dict) -> dict:
        """Compare two dictionaries and return differences."""
        diff = {}
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in all_keys:
            if key not in dict1:
                diff[key] = {'type': 'removed', 'old': dict2[key], 'new': None}
            elif key not in dict2:
                diff[key] = {'type': 'added', 'old': None, 'new': dict1[key]}
            elif dict1[key] != dict2[key]:
                diff[key] = {'type': 'changed', 'old': dict2[key], 'new': dict1[key]}
                
        return diff
    
    def _extract_env_vars(self, log: str) -> dict:
        """Extract environment variables from build log."""
        env_vars = {}
        # Look for common environment variable patterns in log
        # This is a simple implementation - could be enhanced with regex patterns
        for line in log.splitlines():
            if '=' in line and not line.strip().startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    if key.isupper():  # Most env vars are uppercase
                        env_vars[key] = parts[1].strip()
        return env_vars
    
    def _compare_logs(self, failed_log: str, success_log: str) -> dict:
        """Compare build logs to identify key differences."""
        from difflib import unified_diff
        
        # Split logs into lines
        failed_lines = failed_log.splitlines()
        success_lines = success_log.splitlines()
        
        # Generate unified diff
        diff_lines = list(unified_diff(success_lines, failed_lines))
        
        # Analyze the diff to find significant changes
        changes = {
            'added_lines': [],
            'removed_lines': [],
            'error_contexts': []
        }
        
        current_context = []
        for line in diff_lines:
            if line.startswith('+') and 'error' in line.lower():
                changes['added_lines'].append(line[1:])
                changes['error_contexts'].append(current_context[-5:])  # Last 5 lines of context
            elif line.startswith('-') and 'error' in line.lower():
                changes['removed_lines'].append(line[1:])
            current_context.append(line)
            
        return changes
