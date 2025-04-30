import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import yaml
from deepmerge import Merger

from ..handlers import HandlerFactory
from ..utils.logger import get_logger

# Create module-level logger
logger = get_logger("pipeline")

# Create custom merger configuration
cfg_merger = Merger([(list, ["override"]), (dict, ["merge"])], ["override"], ["override"])


class BasePipeline(ABC):
    """Base class for all pipelines.

    This class provides a framework for pipeline implementation with the following features:
    - Configuration loading and handler initialization
    - Core pipeline logic defined by step() and handle_signal()
    - State information access methods

    Subclasses must implement:
    - handle_signal(): Process user signals/commands
    - step(): Process a single step in the current pipeline state
    """

    def __init__(self, pipeline_name: str, config_override: Optional[Dict[str, Any]] = None, debug: bool = False):
        """Initialize pipeline with configuration.

        Args:
            pipeline_name: Name of the pipeline (used to load configuration)
            config_override: Optional configuration dictionary to override defaults
            debug: Whether to enable debug mode for visualization and logging

        Raises:
            RuntimeError: If pipeline fails to initialize
        """
        self.pipeline_name = pipeline_name
        self.debug = debug

        logger.info(f"Initializing pipeline: {pipeline_name} (debug={debug})")

        # Load default configuration
        self.config = self._load_config()

        # Extract this pipeline's configuration
        self.config = self.config.get(self.pipeline_name, {})
        if not self.config:
            logger.warning(f"No configuration found for pipeline: {pipeline_name}")

        # Merge with override config if provided
        if config_override:
            self._merge_config(config_override)

        # Initialize handlers
        self.handlers = self._initialize_handlers()
        logger.info(f"Pipeline '{pipeline_name}' initialized handlers: {', '.join(self.handlers.keys())}")

    @property
    def available_signals(self) -> List[str]:
        """Return the available signals for this pipeline.

        Returns:
            List of signal strings that can be sent to this pipeline
        """
        return []  # Base implementation returns empty list

    @property
    def available_states(self) -> List[str]:
        """Return the available states for this pipeline.

        Returns:
            List of possible state strings for this pipeline
        """
        return []  # Base implementation returns empty list

    @property
    def current_state(self) -> Optional[str]:
        """Return the current state of the pipeline.

        Returns:
            Current state as a string, or None if not applicable
        """
        return None  # Base implementation returns None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from default.yaml.

        Returns:
            Dictionary with all pipeline configurations

        Raises:
            RuntimeError: If configuration file cannot be loaded
        """
        config_path = os.path.join(os.path.dirname(__file__), "default.yaml")

        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, IOError) as e:
            error_msg = f"Failed to load configuration from {config_path}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Merge user configuration with default configuration.

        The merger is configured to:
        - Override lists completely rather than merging them
        - Merge dictionaries recursively
        - Override other types

        Args:
            user_config: User configuration to merge with defaults
        """
        # Use custom merger to merge configurations
        self.config = cfg_merger.merge(self.config, user_config)

    def _initialize_handlers(self) -> Dict[str, Any]:
        """Initialize handlers based on configuration keys.

        Each key in the configuration that corresponds to a valid handler type
        will be used to initialize that handler. The 'init' section of the
        handler configuration will be passed to the handler constructor.

        Returns:
            Dictionary of handler instances keyed by handler type

        Raises:
            RuntimeError: If a handler fails to initialize
        """
        handlers = {}

        # Initialize handlers based on config keys
        for handler_type, handler_config in self.config.items():
            # Skip non-handler configuration sections
            if not isinstance(handler_config, dict):
                continue

            try:
                # Extract initialization parameters from the 'init' section if it exists
                init_params = handler_config.get("init", {})

                # Create the handler with initialization parameters
                handlers[handler_type] = HandlerFactory.create_handler(handler_type=handler_type, config=init_params)
            except ValueError:
                # Skip keys that don't correspond to handler types
                continue
            except Exception as e:
                error_msg = f"Failed to initialize {handler_type} handler for pipeline '{self.pipeline_name}': {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        return handlers

    @abstractmethod
    def handle_signal(self, signal: str) -> None:
        """Handle a signal from the user.

        This method should be implemented by subclasses to define how
        the pipeline responds to user signals (e.g., state transitions).

        Args:
            signal: The signal to handle
        """
        pass

    @abstractmethod
    def step(self) -> None:
        """Process a single step in the current pipeline state.

        This method should be implemented by subclasses to define the
        pipeline's processing logic based on its current state.
        """
        pass
