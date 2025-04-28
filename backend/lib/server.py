import argparse
import threading
from typing import Optional

from .pipelines import PipelineFactory
from .utils.logger import get_logger

logger = get_logger("server")


def serve_pipeline(pipeline_name: str, debug: bool = False) -> None:
    """Serve the pipeline and monitor its execution.

    This function initializes the requested pipeline, sets up a callback
    for when the pipeline exits, and waits for the pipeline to complete.

    Args:
        pipeline_name: Name of the pipeline to initialize and serve
        debug: Whether to run in debug mode with visualizations

    Raises:
        ValueError: If the requested pipeline is not supported
    """
    # Initialize the pipeline using the factory
    logger.info(f"Initializing pipeline: {pipeline_name}")
    pipeline = PipelineFactory.create_pipeline(pipeline_name, debug=debug)

    # Create a stop event for graceful shutdown
    stop_event = threading.Event()

    # Define the callback function that will be called when the pipeline exits
    def on_pipeline_exit(success: bool, error_message: Optional[str]) -> None:
        if success:
            logger.info("Pipeline exited successfully")
        else:
            # Log the error with full traceback in the main thread
            logger.error(f"Pipeline exited with error: {error_message}")
        # Signal the main thread to exit
        stop_event.set()

    # Set the callback on the pipeline
    pipeline.set_exit_callback(on_pipeline_exit)

    try:
        logger.info(f"Server started with {pipeline.pipeline_name} pipeline (debug={debug})")

        # Wait for the pipeline to exit or for a keyboard interrupt
        stop_event.wait()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down server")
        pipeline.signal("stop")  # Signal pipeline to stop
        # Wait briefly for the pipeline to process the stop signal
        stop_event.wait(timeout=2.0)
    finally:
        # Ensure pipeline is stopped even if the callback wasn't triggered
        pipeline.stop()
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robot Arm Control Server")
    parser.add_argument(
        "--pipeline",
        type=str,
        default="yahboom_pick_and_place",
        help="Pipeline to use (default: yahboom_pick_and_place)",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Enable debug mode with visualizations",
    )
    args = parser.parse_args()

    try:
        serve_pipeline(args.pipeline, debug=args.debug)
    except ValueError as e:
        logger.error(f"Pipeline error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
