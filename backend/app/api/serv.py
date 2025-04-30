import os
from pathlib import Path
from typing import List

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lib.pipelines import PipelineFactory, SignalPriority
from lib.utils.logger import get_logger

from ..config import config

# Initialize logger
logger = get_logger("api")

# Create FastAPI app
app = FastAPI(title="Robot Arm Control API", description="API for controlling the robot arm pipeline")

# Get initial pipeline settings from environment variables
initial_pipeline = os.environ.get("PIPELINE")
initial_debug = os.environ.get("DEBUG", "").lower() == "true"


# Define request models
class SignalRequest(BaseModel):
    signal: str
    priority: SignalPriority = SignalPriority.NORMAL


class PipelineRequest(BaseModel):
    pipeline_name: str
    debug: bool = False


def get_available_pipelines() -> List[str]:
    """Get list of available pipelines from default.yaml.

    Returns:
        List of pipeline names
    """
    # Use Path for better path handling
    config_path = Path(__file__).parent.parent.parent / "lib" / "pipelines" / "default.yaml"
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
            return list(config.keys())
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Failed to load pipeline configuration: {e}", exc_info=True)
        return []


@app.post("/signal", status_code=200)
async def send_signal(request: SignalRequest, pipeline_name: str):
    """Send a signal to a running pipeline.

    Args:
        request: The signal request containing signal and priority
        pipeline_name: Target pipeline name
    """
    # Check if pipeline is running by getting its specific status
    pipeline_status = PipelineFactory.get_status(pipeline_name)

    if "error" in pipeline_status:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' is not running")

    # Convert SignalPriority enum to integer priority value
    # HIGH is 1, NORMAL is 2 (lower number = higher priority)
    priority_value = 1 if request.priority == SignalPriority.HIGH else 2

    # Send the signal
    success = PipelineFactory.send_signal(pipeline_name, request.signal, priority_value)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to send signal to pipeline '{pipeline_name}'")

    logger.info(f"Signal '{request.signal}' sent to pipeline '{pipeline_name}' with priority {request.priority.name}")
    return {"status": "success", "message": f"Signal '{request.signal}' sent successfully"}


@app.get("/info", status_code=200)
@app.get("/status", status_code=200)
async def get_status(pipeline_name: str):
    """Get information about available signals and states for a pipeline.

    Args:
        pipeline_name: Pipeline name to get info for
    """
    # Get detailed status for the pipeline
    pipeline_status = PipelineFactory.get_status(pipeline_name)

    # Since we're requesting status for a specific pipeline, we should get a dictionary
    # However, let's check and handle appropriately to satisfy the type checker
    if isinstance(pipeline_status, dict) and "error" in pipeline_status:
        raise HTTPException(status_code=404, detail=pipeline_status["error"])

    return pipeline_status


@app.get("/pipelines", status_code=200)
async def list_pipelines():
    """List all available pipelines and running pipelines."""
    # Get all registered pipelines from config
    available_pipelines = get_available_pipelines()

    # Get status to get running pipelines
    status_list = PipelineFactory.get_status()
    running_pipelines = []

    # Handle the list of dictionaries properly
    if isinstance(status_list, list):
        running_pipelines = [each["pipeline"] for each in status_list]

    return {"available_pipelines": available_pipelines, "running_pipelines": running_pipelines}


@app.post("/pipelines/start", status_code=200)
async def start_pipeline(request: PipelineRequest):
    """Start a specific pipeline.

    Args:
        request: The pipeline request containing pipeline_name and debug flag
    """
    try:
        # Create and start the pipeline
        success = PipelineFactory.create_pipeline(
            request.pipeline_name, config_override=config.get(request.pipeline_name, {}), debug=request.debug
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to start pipeline '{request.pipeline_name}'")

        return {
            "status": "success",
            "pipeline": request.pipeline_name,
            "message": f"Pipeline '{request.pipeline_name}' started successfully",
        }
    except ValueError as e:
        # Handle case where pipeline is not registered
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e!s}")


@app.post("/pipelines/stop", status_code=200)
async def stop_pipeline(pipeline_name: str):
    """Stop a running pipeline.

    Args:
        pipeline_name: Pipeline name to stop
    """
    # Check if pipeline is running by getting its specific status
    pipeline_status = PipelineFactory.get_status(pipeline_name)

    # Check for error in the pipeline status
    if isinstance(pipeline_status, dict) and "error" in pipeline_status:
        return {"status": "success", "message": f"Pipeline '{pipeline_name}' is not running"}

    # Stop the pipeline
    success = PipelineFactory.stop_pipeline(pipeline_name)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline '{pipeline_name}'")

    return {"status": "success", "message": f"Pipeline '{pipeline_name}' stopped successfully"}


# No automatic pipeline startup on application start
@app.on_event("startup")
async def startup_event():
    """Initialize API service."""
    logger.info("API server starting")

    # Start initial pipeline if specified in environment variables
    if initial_pipeline:
        try:
            logger.info(f"Starting initial pipeline '{initial_pipeline}' (debug={initial_debug})")
            success = PipelineFactory.create_pipeline(
                initial_pipeline, config_override=config.get(initial_pipeline, {}), debug=initial_debug
            )
            if not success:
                logger.error(f"Failed to start initial pipeline '{initial_pipeline}'")
        except Exception as e:
            logger.error(f"Error starting initial pipeline: {e}", exc_info=True)

    logger.info("API server started")


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the API shuts down."""
    logger.info("API server shutting down, cleaning up resources")
    PipelineFactory.cleanup()
