from typing import Any, ClassVar, Dict, List, Optional, Type, Union

from ..utils.logger import get_logger
from .base import BasePipeline
from .manager import PipelineManager

# Initialize logger
logger = get_logger("pipeline_factory")


class PipelineFactory:
    """Factory class for creating pipeline instances.

    This class provides static methods to create and manage pipeline instances,
    using the appropriate concrete implementation based on the pipeline name.
    """

    # Registry of available pipeline classes
    _pipeline_registry: ClassVar[Dict[str, Type[BasePipeline]]] = {}

    # Singleton pipeline manager instance
    _manager: Optional[PipelineManager] = None

    @classmethod
    def register_pipeline(cls, name: str, pipeline_class: Type[BasePipeline]) -> None:
        """Register a pipeline class with a name.

        Args:
            name: Name to register the pipeline class under
            pipeline_class: The pipeline class to register
        """
        cls._pipeline_registry[name] = pipeline_class
        logger.debug(f"Registered pipeline class: {name}")

    @classmethod
    def get_pipeline_manager(cls) -> PipelineManager:
        """Get or create the pipeline manager instance.

        Returns:
            PipelineManager instance
        """
        if cls._manager is None:
            cls._manager = PipelineManager()
            logger.debug("Created new PipelineManager instance")
        return cls._manager

    @classmethod
    def create_pipeline(
        cls, pipeline_name: str, config_override: Optional[Dict[str, Any]] = None, debug: bool = False
    ) -> bool:
        """Create a pipeline instance based on name.

        This method looks up the pipeline class in the registry and creates
        an instance through the pipeline manager.

        Args:
            pipeline_name: Name of the pipeline to create
            config_override: Optional configuration dictionary to override defaults
            debug: Whether to enable debug mode

        Returns:
            True if pipeline created successfully, False otherwise

        Raises:
            ValueError: If pipeline_name is not registered
        """
        # Ensure pipeline class is registered
        if pipeline_name not in cls._pipeline_registry:
            error_msg = f"Unknown pipeline type: {pipeline_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get the pipeline class
        pipeline_class = cls._pipeline_registry[pipeline_name]

        # Create the pipeline through the manager
        manager = cls.get_pipeline_manager()
        return manager.create_pipeline(
            pipeline_class=pipeline_class, pipeline_name=pipeline_name, config_override=config_override, debug=debug
        )

    @classmethod
    def stop_pipeline(cls, pipeline_name: str) -> bool:
        """Stop a running pipeline.

        Args:
            pipeline_name: Name of the pipeline to stop

        Returns:
            True if pipeline stopped successfully, False otherwise
        """
        manager = cls.get_pipeline_manager()
        return manager.stop_pipeline(pipeline_name)

    @classmethod
    def send_signal(cls, pipeline_name: str, signal: str, priority: int = 1) -> bool:
        """Send a signal to a pipeline.

        Args:
            pipeline_name: Name of the target pipeline
            signal: The signal to send
            priority: Signal priority (lower is higher priority)

        Returns:
            True if signal sent successfully, False otherwise
        """
        manager = cls.get_pipeline_manager()
        return manager.send_signal(pipeline_name, signal, priority)

    @classmethod
    def get_status(cls, pipeline_name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get status of a pipeline or all pipelines.

        Args:
            pipeline_name: Name of the pipeline, or None for all pipelines

        Returns:
            Dictionary with status information for a specific pipeline,
            or list of dictionaries for all pipelines
        """
        manager = cls.get_pipeline_manager()
        return manager.get_status(pipeline_name)

    @classmethod
    def cleanup(cls) -> None:
        """Clean up all pipeline resources.

        This should be called before application shutdown.
        """
        if cls._manager:
            cls._manager.cleanup()
            cls._manager = None
