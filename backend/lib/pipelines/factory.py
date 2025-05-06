from typing import Any, ClassVar, Dict, List, Optional, Type, TypedDict, Union

from ..utils.logger import get_logger
from .base import BasePipeline
from .manager import PipelineManager

# Initialize logger
logger = get_logger("pipeline_factory")


class PipelineMeta(TypedDict):
    """Type for pipeline metadata."""

    available_states: List[str]
    available_signals: List[str]
    available_queues: List[str]
    config_schema: Dict[str, Any]


class PipelineRegistryEntry(TypedDict):
    """Type for pipeline registry entries."""

    class_: Type[BasePipeline]
    meta: PipelineMeta


class PipelineFactory:
    """Factory class for creating pipeline instances.

    This class provides static methods to create and manage pipeline instances,
    using the appropriate concrete implementation based on the pipeline name.
    """

    # Registry of available pipeline classes
    _pipeline_registry: ClassVar[Dict[str, PipelineRegistryEntry]] = {}

    # Singleton pipeline manager instance
    _manager: Optional[PipelineManager] = None

    @classmethod
    def register_pipeline(cls, name: str, pipeline_class: Type[BasePipeline]) -> None:
        """Register a pipeline class with a name.

        Args:
            name: Name to register the pipeline class under
            pipeline_class: The pipeline class to register
        """
        cls._pipeline_registry[name] = {
            "class_": pipeline_class,
            "meta": {
                "available_states": pipeline_class.get_available_states(),
                "available_signals": pipeline_class.get_available_signals(),
                "available_queues": pipeline_class.get_available_queues(),
                "config_schema": pipeline_class.get_config_schema(),
            },
        }
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
    def get_available_pipelines(cls) -> List[str]:
        """Get list of available (registered) pipelines.

        Returns:
            List of pipeline names that are registered
        """
        return list(cls._pipeline_registry.keys())

    @classmethod
    def get_running_pipelines(cls) -> List[str]:
        """Get list of currently running pipelines.

        Returns:
            List of pipeline names that are currently running
        """
        manager = cls.get_pipeline_manager()
        return manager.get_running_pipelines()

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
        # Check if pipeline is registered
        if pipeline_name not in cls._pipeline_registry:
            error_msg = f"Unknown pipeline: {pipeline_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get the pipeline class
        pipeline_class = cls._pipeline_registry[pipeline_name]["class_"]

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
        if pipeline_name is not None and pipeline_name not in cls._pipeline_registry:
            error_msg = f"Unknown pipeline: {pipeline_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        manager = cls.get_pipeline_manager()
        return manager.get_status(pipeline_name)

    @classmethod
    def get_meta(cls, pipeline_name: str) -> PipelineMeta:
        """Get meta information for a pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            Dictionary with meta information for a specific pipeline
        """
        if pipeline_name not in cls._pipeline_registry:
            error_msg = f"Unknown pipeline: {pipeline_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        return cls._pipeline_registry[pipeline_name]["meta"]

    @classmethod
    def cleanup(cls) -> None:
        """Clean up all pipeline resources.

        This should be called before application shutdown.
        """
        if cls._manager:
            cls._manager.cleanup()
            cls._manager = None

        cls._pipeline_registry = {}
