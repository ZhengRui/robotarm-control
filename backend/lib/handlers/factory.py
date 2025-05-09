from typing import Any, ClassVar, Dict, List, Type

from .base import BaseHandler

HandlerType = Type[BaseHandler]


class HandlerFactory:
    """Factory for registering and creating handlers."""

    _registry: ClassVar[Dict[Type, Dict[str, HandlerType]]] = {}
    _common_registry: ClassVar[Dict[str, HandlerType]] = {}

    @classmethod
    def register_for_pipeline(cls, pipeline_class: Type, handler_type: str, handler_class: HandlerType) -> None:
        """Register a handler for a specific pipeline class.

        Args:
            pipeline_class: The pipeline class this handler belongs to
            handler_type: Type identifier for the handler
            handler_class: The handler class to register
        """
        if pipeline_class not in cls._registry:
            cls._registry[pipeline_class] = {}
        cls._registry[pipeline_class][handler_type] = handler_class

    @classmethod
    def register_for_pipelines(
        cls, pipeline_classes: List[Type], handler_type: str, handler_class: HandlerType
    ) -> None:
        """Register a handler for multiple pipeline classes.

        Args:
            pipeline_classes: List or tuple of pipeline classes to register this handler for
            handler_type: Type identifier for the handler
            handler_class: The handler class to register
        """
        for pipeline_class in pipeline_classes:
            cls.register_for_pipeline(pipeline_class, handler_type, handler_class)

    @classmethod
    def register_common(cls, handler_type: str, handler_class: HandlerType) -> None:
        """Register a common handler available to all pipelines.

        Args:
            handler_type: Type identifier for the handler
            handler_class: The handler class to register
        """
        cls._common_registry[handler_type] = handler_class

    @classmethod
    def get_handler_class(cls, pipeline_class: Type, handler_type: str) -> HandlerType:
        """Get handler class for the given pipeline class and handler type.

        First checks for pipeline-specific handler, then falls back to common handler.

        Args:
            pipeline_class: The pipeline class to check for handlers
            handler_type: Type identifier for the handler

        Returns:
            Handler class if found

        Raises:
            ValueError: If no handler class found for the given type
        """
        # Try pipeline-specific handler first
        if pipeline_class in cls._registry and handler_type in cls._registry[pipeline_class]:
            return cls._registry[pipeline_class][handler_type]

        # Fall back to common handler
        if handler_type in cls._common_registry:
            return cls._common_registry[handler_type]

        # Generate a more specific error message based on what was missing
        pipeline_class_name = pipeline_class.__name__
        if pipeline_class in cls._registry:
            available_handlers = ", ".join(cls._registry[pipeline_class].keys())
            error_msg = (
                f"No handler found for type '{handler_type}' in handler factory. "
                f"Available handlers for pipeline class '{pipeline_class_name}': {available_handlers or 'none'}"
            )
        else:
            error_msg = f"No handlers registered for pipeline class '{pipeline_class_name}'"

        # Add information about available common handlers
        if cls._common_registry:
            common_handlers = ", ".join(cls._common_registry.keys())
            error_msg += f". Available common handlers: {common_handlers}"
        else:
            error_msg += ". No common handlers registered"

        raise ValueError(error_msg)

    @classmethod
    def create_handler(cls, pipeline_class: Type, handler_type: str, config: Dict[str, Any]) -> BaseHandler:
        """Create a handler instance.

        Args:
            pipeline_class: The pipeline class to check for handlers
            handler_type: Type identifier for the handler
            config: Configuration for the handler

        Returns:
            Handler instance

        Raises:
            ValueError: If no handler class found for the given type
        """
        handler_class = cls.get_handler_class(pipeline_class, handler_type)
        return handler_class(**config)
