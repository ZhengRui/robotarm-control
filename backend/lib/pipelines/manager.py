import time
from typing import Any, Dict, List, Optional, Type, Union

from ..utils.logger import get_logger
from .base import BasePipeline
from .process import PipelineProcess

# Initialize logger
logger = get_logger("pipeline_manager")


class PipelineManager:
    """Manages multiple pipeline processes.

    This class serves as a central manager for all pipeline processes,
    providing a unified interface for the API server to interact with pipelines.

    It handles:
    - Creating and tracking pipeline processes
    - Routing signals to appropriate pipelines
    - Aggregating status information
    - Coordinating pipeline lifecycle
    """

    def __init__(self) -> None:
        """Initialize the pipeline manager."""
        self.pipelines: Dict[str, PipelineProcess] = {}

    def create_pipeline(
        self,
        pipeline_class: Type[BasePipeline],
        pipeline_name: str,
        config_override: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ) -> bool:
        """Create and start a new pipeline process.

        Args:
            pipeline_class: The BasePipeline subclass to instantiate
            pipeline_name: Name for the pipeline instance
            config_override: Optional configuration overrides
            debug: Whether to enable debug mode

        Returns:
            True if pipeline created successfully, False otherwise
        """
        # Stop existing pipeline with the same name if any
        if pipeline_name in self.pipelines:
            logger.info(f"Stopping existing pipeline '{pipeline_name}'")
            self.stop_pipeline(pipeline_name)

        try:
            # Create and start new pipeline process
            logger.info(f"Creating pipeline '{pipeline_name}'")
            process = PipelineProcess(
                pipeline_class=pipeline_class, pipeline_name=pipeline_name, config_override=config_override, debug=debug
            )
            process.start()

            # Store in registry
            self.pipelines[pipeline_name] = process

            return True
        except Exception as e:
            logger.error(f"Failed to create pipeline '{pipeline_name}': {e}", exc_info=True)
            return False

    def stop_pipeline(self, pipeline_name: str) -> bool:
        """Stop a specific pipeline process.

        Args:
            pipeline_name: Name of the pipeline to stop

        Returns:
            True if pipeline stopped successfully, False otherwise
        """
        if pipeline_name not in self.pipelines:
            logger.warning(f"Pipeline '{pipeline_name}' not found")
            return False

        try:
            # Stop the pipeline process
            success = self.pipelines[pipeline_name].stop()

            # Remove from registry
            del self.pipelines[pipeline_name]

            return success
        except Exception as e:
            logger.error(f"Error stopping pipeline '{pipeline_name}': {e}", exc_info=True)
            return False

    def stop_all(self) -> None:
        """Stop all running pipeline processes."""
        pipelines = list(self.pipelines.keys())
        for pipeline_name in pipelines:
            self.stop_pipeline(pipeline_name)

    def send_signal(self, pipeline_name: str, signal: str, priority: int = 1) -> bool:
        """Send a signal to a specific pipeline.

        Args:
            pipeline_name: Name of the target pipeline
            signal: The signal to send
            priority: Signal priority (lower is higher priority)

        Returns:
            True if signal sent successfully, False otherwise
        """
        if pipeline_name not in self.pipelines:
            logger.warning(f"Cannot send signal - pipeline '{pipeline_name}' not found")
            return False

        try:
            self.pipelines[pipeline_name].send_signal(signal, priority)
            return True
        except Exception as e:
            logger.error(f"Error sending signal to '{pipeline_name}': {e}", exc_info=True)
            return False

    def get_status(self, pipeline_name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get status of a specific pipeline or all pipelines.

        Args:
            pipeline_name: Name of the pipeline, or None for all pipelines

        Returns:
            Dictionary with status information for a specific pipeline,
            or list of dictionaries for all pipelines
        """
        status: Dict[str, Any]

        if pipeline_name is not None:
            # Get status of specific pipeline
            if pipeline_name not in self.pipelines:
                return {
                    "name": pipeline_name,
                    "running": False,
                    "state": None,
                    "timestamp": time.time(),
                    "config": {},
                    "queues": [],
                }

            # Create a base status dictionary
            status = {
                "name": pipeline_name,
                "config": {},
                "queues": [],
            }

            # Get the pipeline's status and merge with base status
            pipeline_status = self.pipelines[pipeline_name].get_status()
            status.update(pipeline_status)

            return status
        else:
            # Get status of all pipelines
            status_list: List[Dict[str, Any]] = []

            for name, pipeline in self.pipelines.items():
                # Create a base status dictionary
                status = {
                    "name": name,
                    "config": {},
                    "queues": [],
                }

                # Get the pipeline's status and merge with base status
                pipeline_status = pipeline.get_status()
                status.update(pipeline_status)

                status_list.append(status)

            return status_list

    def get_running_pipelines(self) -> List[str]:
        """Get list of currently running pipelines.

        Returns:
            List of pipeline names of currently running pipelines
        """
        return list(self.pipelines.keys())

    def cleanup(self) -> None:
        """Clean up all resources before shutdown."""
        logger.info("Cleaning up pipeline manager")
        self.stop_all()
