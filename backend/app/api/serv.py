import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import Body, FastAPI, HTTPException
from lib.pipelines import PipelineFactory
from lib.pipelines.base import SignalPriority
from lib.utils.logger import get_logger
from pydantic import BaseModel

# Initialize logger
logger = get_logger("api")

# Create FastAPI app
app = FastAPI(title="Robot Arm Control API", description="API for controlling the robot arm pipeline")

# Store the pipeline instance
pipeline_instance = None

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
        logger.error(f"Failed to load pipeline configuration: {e}")
        return []


@app.post("/signal", status_code=200)
async def send_signal(request: SignalRequest):
    """Send a signal to the running pipeline."""
    if pipeline_instance is None:
        raise HTTPException(status_code=500, detail="No pipeline is running")

    try:
        pipeline_instance.signal(request.signal, priority=request.priority)
        logger.info(f"Signal '{request.signal}' sent to pipeline with priority {request.priority.name}")
        return {"status": "success", "message": f"Signal '{request.signal}' sent successfully"}
    except Exception as e:
        logger.error(f"Error sending signal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send signal: {str(e)}")


@app.get("/status", status_code=200)
async def get_status():
    """Get current pipeline status."""
    if pipeline_instance is None:
        return {"status": "no_pipeline"}

    # Get basic status information
    status = {
        "pipeline": pipeline_instance.pipeline_name,
        "running": pipeline_instance.running,
        "state": pipeline_instance.current_state
    }

    return status


@app.get("/info", status_code=200)
async def get_info():
    """Get information about available signals and states for the current pipeline."""
    if pipeline_instance is None:
        raise HTTPException(status_code=500, detail="No pipeline is running")

    return {
        "pipeline": pipeline_instance.pipeline_name,
        "signals": pipeline_instance.available_signals,
        "states": pipeline_instance.available_states,
        "current_state": pipeline_instance.current_state
    }


@app.get("/pipelines", status_code=200)
async def list_pipelines():
    """List all available pipelines."""
    pipelines = get_available_pipelines()

    return {
        "available_pipelines": pipelines,
        "current_pipeline": pipeline_instance.pipeline_name if pipeline_instance else None
    }


def _create_and_start_pipeline(pipeline_name: str, debug: bool = False) -> None:
    """Helper function to create and start a pipeline.

    Args:
        pipeline_name: Name of the pipeline to start
        debug: Whether to run in debug mode

    Raises:
        Exception: If pipeline creation fails
    """
    global pipeline_instance

    logger.info(f"Initializing pipeline: {pipeline_name} (debug={debug})")
    pipeline_instance = PipelineFactory.create_pipeline(
        pipeline_name, debug=debug
    )

    def on_pipeline_exit(success: bool, error_message: Optional[str] = None):
        if success:
            logger.info("Pipeline exited successfully")
        else:
            logger.error(f"Pipeline exited with error: {error_message}")

    pipeline_instance.set_exit_callback(on_pipeline_exit)
    logger.info(f"Pipeline '{pipeline_name}' started successfully")


@app.post("/pipelines/start", status_code=200)
async def start_pipeline(request: PipelineRequest):
    """Start a specific pipeline."""
    global pipeline_instance

    # Stop existing pipeline if one is running
    if pipeline_instance is not None:
        await stop_pipeline()

    try:
        _create_and_start_pipeline(request.pipeline_name, request.debug)
        return {
            "status": "success",
            "pipeline": request.pipeline_name,
            "message": f"Pipeline '{request.pipeline_name}' started successfully"
        }
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline '{request.pipeline_name}': {str(e)}"
        )


def _stop_running_pipeline() -> None:
    """Helper function to stop the currently running pipeline.

    This is a no-op if no pipeline is running.
    """
    global pipeline_instance

    if not pipeline_instance:
        return

    logger.info("Stopping pipeline")
    pipeline_instance.signal("stop", priority=SignalPriority.HIGH)
    pipeline_instance.stop()
    pipeline_instance = None
    logger.info("Pipeline stopped, time to clear stop event")


@app.post("/pipelines/stop", status_code=200)
async def stop_pipeline():
    """Stop the current pipeline."""
    if pipeline_instance is None:
        return {"status": "success", "message": "No pipeline is running"}

    try:
        pipeline_name = pipeline_instance.pipeline_name
        _stop_running_pipeline()
        return {
            "status": "success",
            "message": f"Pipeline '{pipeline_name}' stopped successfully"
        }
    except Exception as e:
        logger.error(f"Error stopping pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline: {str(e)}")


# No automatic pipeline startup on application start
@app.on_event("startup")
async def startup_event():
    """Initialize API service."""
    logger.info("API server started")

    if initial_pipeline:
        try:
            _create_and_start_pipeline(initial_pipeline, initial_debug)
        except Exception as e:
            logger.error(f"Failed to start pipeline on startup: {e}")


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the pipeline when the API shuts down."""
    _stop_running_pipeline()
