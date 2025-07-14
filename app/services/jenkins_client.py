"""Jenkins API client service for interacting with Jenkins server."""
from typing import Optional, Dict, Any, List
import jenkins
import requests
from app.core.config import Settings
from app.models.build import BuildInfo
from datetime import datetime

class JenkinsClient:
    def __init__(self, settings: Settings):
        self.server = jenkins.Jenkins(
            settings.jenkins_url,
            username=settings.jenkins_user,
            password=settings.jenkins_token
        )
        
    async def get_build_info(self, job_name: str, build_number: int) -> BuildInfo:
        """Get detailed information about a specific build."""
        build = self.server.get_build_info(job_name, build_number)
        
        # Handle None result - build might be in progress or unknown state
        result = build['result']
        if result is None:
            if build.get('building', False):
                result = 'IN_PROGRESS'
            else:
                result = 'UNKNOWN'
        
        return BuildInfo(
            job_name=job_name,
            build_number=build_number,
            result=result,
            timestamp=datetime.fromtimestamp(build['timestamp'] / 1000),
            duration=build['duration'] or 0,  # Handle None duration
            parameters=self._extract_parameters(build),
            url=build['url'],
            console_log=self.server.get_build_console_output(job_name, build_number)
        )
    
    async def get_last_successful_build(self, job_name: str, current_build: int) -> Optional[BuildInfo]:
        """Get the last successful build before the specified build number."""
        job_info = self.server.get_job_info(job_name)
        for build in job_info['builds']:
            if build['number'] >= current_build:
                continue
            build_info = self.server.get_build_info(job_name, build['number'])
            if build_info['result'] == 'SUCCESS':
                return await self.get_build_info(job_name, build['number'])
        return None
    
    def update_build_description(self, job_name: str, build_number: int, description: str) -> None:
        """Update the description of a build."""
        # try:
        #     self.server.set_build_description(job_name, build_number, description)
        # except jenkins.JenkinsException as e:
        #     # Fall back to updating via direct API if set_build_description is not available
        job_info = self.server.get_job_info(job_name)
        if 'url' in job_info:
            build_url = f"{job_info['url']}{build_number}/submitDescription"
            self.server.jenkins_open(
                requests.Request(
                    'POST',
                    build_url,
                    data={'description': description}
                )
            )
                
    def _extract_parameters(self, build: Dict[str, Any]) -> Dict[str, Any]:
        """Extract build parameters from the build info."""
        params = {}
        if 'actions' in build:
            for action in build['actions']:
                if 'parameters' in action:
                    for param in action['parameters']:
                        params[param['name']] = param['value']
        return params
