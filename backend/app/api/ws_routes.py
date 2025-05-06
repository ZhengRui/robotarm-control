from fastapi import (
    APIRouter,
    Path,
    WebSocket,
    WebSocketDisconnect,
)

from lib.pipelines import PipelineFactory
from lib.utils.logger import get_logger

from ..utils.websocket import manager

# Initialize logger
logger = get_logger("websocket_routes")

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/pipeline/{pipeline_name}")
async def pipeline_websocket(
    websocket: WebSocket,
    pipeline_name: str = Path(..., description="Name of the pipeline to monitor"),
):
    """WebSocket endpoint for real-time pipeline status updates.

    This endpoint streams real-time state changes and events for a specific pipeline.

    Args:
        websocket: WebSocket connection
        pipeline_name: Name of the pipeline to monitor
    """
    # Check if pipeline exists in configuration
    try:
        # Use PipelineFactory to check if pipeline exists
        available_pipelines = PipelineFactory.get_available_pipelines()
        if pipeline_name not in available_pipelines:
            await websocket.close(code=4004, reason=f"Pipeline '{pipeline_name}' not found")
            return

        # Connect to pipeline status feed
        await manager.connect_pipeline(websocket, pipeline_name)

        try:
            # Main connection loop - keep connection alive
            while True:
                # Wait for client messages (ping/pong handled automatically)
                _ = await websocket.receive_text()

                # Process any client commands if needed
                # Currently, we don't expect client commands as this is a one-way stream
                pass

        except WebSocketDisconnect:
            logger.info(f"Client disconnected from pipeline '{pipeline_name}' status feed")
        finally:
            await manager.disconnect_pipeline(websocket, pipeline_name)

    except Exception as e:
        logger.error(f"Error in pipeline websocket: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Server error")
        except RuntimeError:
            # WebSocket might already be closed
            pass


@router.websocket("/pipeline/{pipeline_name}/queue/{queue_name}")
async def queue_websocket(
    websocket: WebSocket,
    pipeline_name: str = Path(..., description="Name of the pipeline"),
    queue_name: str = Path(..., description="Name of the queue to stream"),
):
    """WebSocket endpoint for streaming queue data.

    This endpoint streams real-time frame data and processing results from a specific queue.

    Args:
        websocket: WebSocket connection
        pipeline_name: Name of the pipeline
        queue_name: Name of the queue to stream
    """
    # Check if pipeline exists in configuration
    try:
        # Use PipelineFactory to check if pipeline exists
        available_pipelines = PipelineFactory.get_available_pipelines()
        if pipeline_name not in available_pipelines:
            await websocket.close(code=4004, reason=f"Pipeline '{pipeline_name}' not found")
            return

        # Connect to queue data feed
        await manager.connect_queue(websocket, pipeline_name, queue_name)

        try:
            # Main connection loop - keep connection alive
            while True:
                # Wait for client messages (ping/pong handled automatically)
                _ = await websocket.receive_text()

                # Process any client commands if needed
                # Currently, we don't expect client commands as this is a one-way stream
                pass

        except WebSocketDisconnect:
            logger.info(f"Client disconnected from pipeline '{pipeline_name}' queue '{queue_name}' data feed")
        finally:
            await manager.disconnect_queue(websocket, pipeline_name, queue_name)

    except Exception as e:
        logger.error(f"Error in queue websocket: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Server error")
        except RuntimeError:
            # WebSocket might already be closed
            pass
