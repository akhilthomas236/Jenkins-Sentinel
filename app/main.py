"""FastAPI endpoints for the build analyzer service."""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
from loguru import logger
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.jenkins_client import JenkinsClient
from app.services.bedrock_client import BedrockClient
from app.services.build_analyzer import BuildAnalyzer
from app.services.database import DatabaseService
from app.services.agent_manager import AgentManager
from app.models.build import BuildInfo, BuildAnalysis

app = FastAPI(title="Jenkins Build Analyzer")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
settings = Settings()

# Configure logging
configure_logging(settings)

# Initialize base services
logger.info("Initializing services")
jenkins_client = JenkinsClient(settings)
bedrock_client = BedrockClient(settings)
build_analyzer = BuildAnalyzer(jenkins_client, bedrock_client)
db_service = DatabaseService(settings)

# Initialize and start services that require async setup
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize database
        logger.info("Initializing database")
        await db_service.init_db()
        
        # Initialize agent manager
        logger.info("Initializing agent manager")
        global agent_manager
        agent_manager = AgentManager(jenkins_client, bedrock_client, build_analyzer, db_service)
        
        # Start agent manager
        logger.info("Starting agent manager")
        asyncio.create_task(agent_manager.start())
        logger.info("Agent manager started successfully")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        # Re-raise the error so FastAPI can handle it
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check Jenkins connection
        logger.debug("Checking Jenkins connection")
        jenkins_client.server.get_whoami()

        # Check AWS credentials
        logger.debug("Checking AWS credentials")
        bedrock_client.client.list_foundation_models()
        
        logger.debug("Readiness check passed")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/analyze")
async def analyze_build(
    job_name: str,
    build_number: int,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Analyze a Jenkins build."""
    try:
        # Start analysis in background
        background_tasks.add_task(build_analyzer.analyze_build, job_name, build_number)
        logger.info(f"Started background analysis for {job_name} #{build_number}")
        
        return {
            "status": "accepted",
            "message": f"Analysis started for {job_name} #{build_number}",
            "job": job_name,
            "build": build_number,
        }
    except Exception as e:
        logger.error(f"Failed to start analysis for {job_name} #{build_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze/failure")
async def analyze_failure(
    job_name: str,
    build_number: int,
    last_success: Optional[int] = None,
) -> BuildAnalysis:
    """Analyze a failed build with detailed comparison."""
    try:
        logger.info(f"Starting failure analysis for {job_name} #{build_number}")
        result = await build_analyzer.analyze_build(job_name, build_number)
        logger.info(f"Completed failure analysis for {job_name} #{build_number}")
        return result
    except Exception as e:
        logger.error(f"Failed to analyze failed build {job_name} #{build_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/patterns")
async def get_patterns() -> Dict[str, List[Dict[str, Any]]]:
    """Get the current pattern database showing what the agent has learned."""
    try:
        return {
            "patterns": agent_manager.pattern_database,
            "total_patterns": sum(len(patterns) for patterns in agent_manager.pattern_database.values()),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/actions")
async def get_actions(
    job_name: str = Query(..., description="Name of the Jenkins job"),
    build_number: int = Query(..., description="Build number")
) -> Dict[str, Any]:
    """Get actions taken by the agent for a specific build."""
    cache_key = f"{job_name}#{build_number}"
    if cache_key not in agent_manager.analysis_cache:
        raise HTTPException(status_code=404, detail="Build analysis not found")
    
    analysis = agent_manager.analysis_cache[cache_key]
    return {
        "build_info": analysis.build_info,
        "actions_taken": agent_manager.action_history.get(cache_key, []),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/learning/status")
async def get_learning_status() -> Dict[str, Any]:
    """Get the current learning status of the agent."""
    return {
        "learning_enabled": agent_manager.learning_enabled,
        "total_builds_analyzed": len(agent_manager.analysis_cache),
        "pattern_database_size": sum(len(patterns) for patterns in agent_manager.pattern_database.values()),
        "active_monitors": len(agent_manager.active_monitors),
        "last_learning_update": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
