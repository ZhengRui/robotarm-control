import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lib.pipelines import PipelineFactory, SignalPriority
from lib.utils.logger import get_logger

from ..config import config
from ..utils.websocket import manager
from .ws_routes import router as websocket_router

# Initialize logger
logger = get_logger("api")

# Create FastAPI app
app = FastAPI(title="Robot Arm Control API", description="API for controlling the robot arm pipeline")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include WebSocket routes
app.include_router(websocket_router)

# Get initial pipeline settings from environment variables
initial_pipeline = os.environ.get("PIPELINE")


class SignalRequest(BaseModel):
    """Signal request model."""

    signal: str
    priority: SignalPriority = SignalPriority.NORMAL


@app.get("/pipelines")
async def get_pipelines(with_meta: bool = False):
    """Get information about all available pipelines."""

    # Format response based on requested detail level
    pipelines = []

    for pipeline_name, pipeline_config in config.items():
        pipeline_status = PipelineFactory.get_status(pipeline_name)
        if with_meta and isinstance(pipeline_status, dict):
            pipeline_type = pipeline_config.get("pipeline", pipeline_name)
            meta = PipelineFactory.get_meta(pipeline_type)

            # Instance metadata takes precedence over class metadata
            for key in ["available_states", "available_signals", "available_queues"]:
                if key not in pipeline_status:
                    # Only use class metadata if instance metadata is not available
                    pipeline_status[key] = meta.get(key, [])

            # Add other metadata (config_schema, etc.)
            for key, value in meta.items():
                if key not in ["available_states", "available_signals", "available_queues"]:
                    pipeline_status[key] = value

        pipelines.append(pipeline_status)

    return {"pipelines": pipelines}


@app.get("/pipeline")
async def get_pipeline(pipeline_name: str, with_meta: bool = False):
    """Get detailed information about a specific pipeline.

    Args:
        pipeline_name: Name of the pipeline
    """

    # Check if pipeline exists in config
    if pipeline_name not in config:
        raise HTTPException(status_code=404, detail=f"Pipeline configuration '{pipeline_name}' not found")

    try:
        pipeline_status = PipelineFactory.get_status(pipeline_name)
        if with_meta and isinstance(pipeline_status, dict):
            pipeline_type = config[pipeline_name].get("pipeline", pipeline_name)
            meta = PipelineFactory.get_meta(pipeline_type)

            # Instance metadata takes precedence over class metadata
            for key in ["available_states", "available_signals", "available_queues"]:
                if key not in pipeline_status:
                    # Only use class metadata if instance metadata is not available
                    pipeline_status[key] = meta.get(key, [])

            # Add other metadata (config_schema, etc.)
            for key, value in meta.items():
                if key not in ["available_states", "available_signals", "available_queues"]:
                    pipeline_status[key] = value

        return pipeline_status
    except ValueError as e:
        # Handle case where pipeline is not registered
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get pipeline info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline info: {e!s}")


@app.post("/pipeline/start")
async def start_pipeline(pipeline_name: str):
    """Start a specific pipeline.

    Args:
        pipeline_name: Name of the pipeline to start
    """

    # Check if pipeline exists in config
    if pipeline_name not in config:
        raise HTTPException(status_code=404, detail=f"Pipeline configuration '{pipeline_name}' not found")

    try:
        success = PipelineFactory.create_pipeline(pipeline_name, config_override=config.get(pipeline_name, {}))

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to start pipeline '{pipeline_name}'")

        return {
            "status": "success",
            "pipeline": pipeline_name,
            "message": f"Pipeline '{pipeline_name}' started successfully",
        }
    except ValueError as e:
        # Handle case where pipeline is not registered
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e!s}")


@app.post("/pipeline/stop")
async def stop_pipeline(pipeline_name: str):
    """Stop a running pipeline.

    Args:
        pipeline_name: Name of the pipeline to stop
    """
    pipeline_status = await get_pipeline(pipeline_name)
    running = pipeline_status.get("running", False)

    if not running:
        return {"status": "success", "pipeline": pipeline_name, "message": f"Pipeline '{pipeline_name}' is not running"}

    # Stop the pipeline
    success = PipelineFactory.stop_pipeline(pipeline_name)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline '{pipeline_name}'")

    # Close all connections for the pipeline
    # await manager.close_pipeline_connections(pipeline_name)

    return {
        "status": "success",
        "pipeline": pipeline_name,
        "message": f"Pipeline '{pipeline_name}' stopped successfully",
    }


@app.post("/pipeline/signal")
async def send_signal(pipeline_name: str, signal_name: str, priority: SignalPriority = SignalPriority.NORMAL):
    """Send a signal to a running pipeline.

    Args:
        pipeline_name: Name of the target pipeline
        signal_name: Name of the signal to send
        priority: Signal priority (HIGH or NORMAL)
    """
    pipeline_status = await get_pipeline(pipeline_name)
    running = pipeline_status.get("running", False)

    if not running:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' is not running")

    # Convert SignalPriority enum to integer priority value
    # HIGH is 1, NORMAL is 2 (lower number = higher priority)
    priority_value = 1 if priority == SignalPriority.HIGH else 2

    # Send the signal
    success = PipelineFactory.send_signal(pipeline_name, signal_name, priority_value)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to send signal to pipeline '{pipeline_name}'")

    logger.info(f"Signal '{signal_name}' sent to pipeline '{pipeline_name}' with priority {priority.name}")
    return {
        "status": "success",
        "pipeline": pipeline_name,
        "signal": signal_name,
        "message": "Signal sent successfully",
    }


@app.post("/pipeline/config")
async def update_config(pipeline_name: str, config_update: Dict[str, Any]):
    """Update pipeline configuration.

    Args:
        pipeline_name: Name of the pipeline to configure
        config_update: Configuration updates
    """
    # This endpoint would require enhancing the PipelineFactory/Manager to support
    # updating configuration of a running pipeline

    # For now, return a not implemented response
    raise HTTPException(status_code=501, detail="Configuration updates for running pipelines not yet implemented")


# No automatic pipeline startup on application start
@app.on_event("startup")
async def startup_event():
    """Initialize API service."""
    logger.info("API server starting")

    # Start WebSocket manager background tasks
    await manager.start_background_tasks()

    # Start initial pipeline if specified in environment variables
    if initial_pipeline:
        try:
            logger.info(f"Starting initial pipeline '{initial_pipeline}'")
            success = PipelineFactory.create_pipeline(
                initial_pipeline, config_override=config.get(initial_pipeline, {})
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

    # Clean up WebSocket connections
    await manager.cleanup()

    # Clean up pipeline resources
    PipelineFactory.cleanup()
