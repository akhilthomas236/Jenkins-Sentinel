"""Utility functions for log processing and analysis."""
from typing import List, Dict, Any
import re

def extract_error_patterns(log: str) -> List[Dict[str, Any]]:
    """Extract error patterns and their context from a build log."""
    error_patterns = []
    lines = log.splitlines()
    
    # Common error patterns to look for
    patterns = [
        r'(?i)error:.*',
        r'(?i)exception:.*',
        r'(?i)failure:.*',
        r'(?i)failed.*',
        r'BUILD FAILED',
        r'\[ERROR\].*',
    ]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line):
                # Get context (5 lines before and after)
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                context = lines[start:end]
                
                error_patterns.append({
                    'pattern': line,
                    'context': '\n'.join(context),
                    'line_number': i + 1
                })
                break
                
    return error_patterns

def analyze_test_failures(log: str) -> Dict[str, Any]:
    """Analyze test failures from build log."""
    test_results = {
        'failed_tests': [],
        'error_count': 0,
        'failure_count': 0,
        'skipped_count': 0
    }
    
    # Look for common test failure patterns
    failed_test_patterns = [
        r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)',  # JUnit pattern
        r'FAIL: ([\w\.]+)',  # Simple test failure pattern
        r'Failed tests:(\n\s+[\w\.]+)*'  # Maven test failure pattern
    ]
    
    for pattern in failed_test_patterns:
        matches = re.finditer(pattern, log)
        for match in matches:
            if len(match.groups()) == 4:  # JUnit style result
                test_results['failure_count'] += int(match.group(2))
                test_results['error_count'] += int(match.group(3))
                test_results['skipped_count'] += int(match.group(4))
            else:  # Individual test failure
                test_results['failed_tests'].append(match.group(1))
                
    return test_results

def analyze_build_time(log: str) -> Dict[str, Any]:
    """Analyze build timing information."""
    timing_info = {
        'total_time': None,
        'slow_phases': [],
        'phase_times': {}
    }
    
    # Look for build timing patterns
    time_patterns = [
        r'Total time: ([\d\.]+) s',  # Maven pattern
        r'Finished: (\w+) \(at (.*)\) \[([\d\.]+) s\]',  # Jenkins pattern
        r'BUILD (\w+) in ([\d\.]+)s'  # Gradle pattern
    ]
    
    for pattern in time_patterns:
        matches = re.finditer(pattern, log)
        for match in matches:
            if match.groups():
                time = float(match.groups()[-1])
                if not timing_info['total_time'] or time > timing_info['total_time']:
                    timing_info['total_time'] = time
                    
    # Analyze individual phase times
    phase_pattern = r'\[(\w+)\] (.*?) \[([\d\.]+)s\]'
    for match in re.finditer(phase_pattern, log):
        phase = match.group(2)
        time = float(match.group(3))
        timing_info['phase_times'][phase] = time
        
        # Mark phases taking more than 60 seconds as slow
        if time > 60:
            timing_info['slow_phases'].append({
                'phase': phase,
                'time': time
            })
            
    return timing_info

def analyze_dependency_issues(log: str) -> List[Dict[str, Any]]:
    """Analyze dependency-related issues in the build."""
    dependency_issues = []
    
    # Common dependency issue patterns
    patterns = [
        r'Could not resolve dependencies for project (.*?): Failed to collect dependencies for \[(.*?)\]',
        r'Could not find artifact (.*?) in (.*)',
        r'Failed to resolve: (.*?)\n',
        r'Unable to find version (.*?) for package (.*)'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, log)
        for match in matches:
            dependency_issues.append({
                'type': 'dependency_error',
                'message': match.group(0),
                'artifact': match.group(1) if match.groups() else None
            })
            
    return dependency_issues

def analyze_compilation_issues(log: str) -> List[Dict[str, Any]]:
    """Analyze compilation-related issues in the build."""
    compilation_issues = []
    
    # Common compilation issue patterns
    patterns = [
        r'(?m)^.*?\.(?:java|groovy|kt):\[(\d+),(\d+)\] error: (.*?)$',  # Java/Groovy/Kotlin
        r'(?m)^.*?\.(?:py):\d+: (.*?)$',  # Python
        r'(?m)^.*?\.(?:ts|js):\d+:\d+: error (TS\d+): (.*?)$'  # TypeScript/JavaScript
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, log)
        for match in matches:
            compilation_issues.append({
                'type': 'compilation_error',
                'message': match.group(0),
                'line': int(match.group(1)) if len(match.groups()) > 1 else None,
                'column': int(match.group(2)) if len(match.groups()) > 2 else None,
                'error': match.group(3) if len(match.groups()) > 2 else match.group(1)
            })
            
    return compilation_issues
