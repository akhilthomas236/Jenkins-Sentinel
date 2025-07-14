from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class BuildInfo(BaseModel):
    """Information about a Jenkins build.
    
    Attributes:
        job_name: Name of the Jenkins job
        build_number: Build number
        result: Build result state. One of:
            - SUCCESS: Build completed successfully
            - FAILURE: Build failed
            - UNSTABLE: Build completed but with test failures
            - ABORTED: Build was manually aborted
            - IN_PROGRESS: Build is still running
            - UNKNOWN: Build state cannot be determined
        timestamp: When the build started
        duration: Build duration in milliseconds
        parameters: Build parameters
        url: URL to the build in Jenkins UI
        console_log: Build console output
    """
    job_name: str
    build_number: int
    result: str
    timestamp: datetime
    duration: int
    parameters: Dict[str, Any]
    url: str
    console_log: Optional[str] = None


class BuildAnalysis(BaseModel):
    build_info: BuildInfo
    last_success: Optional[BuildInfo]
    error_patterns: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    recommendations: List[str]
    severity: str
    confidence: float
    timestamp: datetime


class BuildComparison(BaseModel):
    failed_build: BuildInfo
    successful_build: BuildInfo
    parameter_diff: Dict[str, Any]
    environment_diff: Dict[str, Any]
    log_diff: Dict[str, Any]
    timestamp: datetime
