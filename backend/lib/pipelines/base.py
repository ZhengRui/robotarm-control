import json
import os
import time
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

        # Initialize Redis client for queue publishing
        self.redis = self._initialize_redis_client()

        # Initialize handlers
        self.handlers = self._initialize_handlers()
        logger.info(f"Pipeline '{pipeline_name}' initialized handlers: {', '.join(self.handlers.keys())}")

    @property
    def current_state(self) -> Optional[str]:
        """Return the current state of the pipeline.

        Returns:
            Current state as a string, or None if not applicable
        """
        return None  # Base implementation returns None

    @classmethod
    def get_available_signals(cls) -> List[str]:
        """Return the available signals for this pipeline class.

        This class method allows getting pipeline signals without instantiation.

        Returns:
            List of signal strings that can be sent to this pipeline
        """
        return []  # Base implementation returns empty list

    @classmethod
    def get_available_states(cls) -> List[str]:
        """Return the available states for this pipeline class.

        This class method allows getting pipeline states without instantiation.

        Returns:
            List of possible state strings for this pipeline
        """
        return []  # Base implementation returns empty list

    @classmethod
    def get_available_queues(cls) -> List[str]:
        """Return the available data queues for this pipeline class.

        This class method allows getting queue information without instantiation.

        Returns:
            List of queue names that this pipeline uses
        """
        return []  # Base implementation returns empty list

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return the configuration schema for this pipeline class.

        This class method allows getting configuration schema without instantiation.

        Returns:
            Dictionary containing the configuration schema for this pipeline
        """
        return {}  # Base implementation returns empty dict

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
            if not isinstance(handler_config, dict) or handler_type == "redis":
                continue

            try:
                # Extract initialization parameters from the 'init' section if it exists
                init_params = handler_config.get("init", {}).copy()

                if handler_type == "dataloader":
                    redis_config = self.config.get("redis", {})
                    if redis_config:
                        init_params.update(redis_config)

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

    def _initialize_redis_client(self) -> Optional[Any]:
        """Initialize Redis client for queue publishing.

        Returns:
            Redis client instance or None if initialization fails
        """
        redis_config = self.config.get("redis", {})
        if not redis_config:
            logger.info(f"No Redis configuration found for pipeline '{self.pipeline_name}', queue publishing disabled")
            return None

        try:
            import redis

            client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password", None),
                decode_responses=redis_config.get("decode_responses", False),
            )
            # Test connection
            client.ping()
            logger.info(f"Redis connection established for pipeline '{self.pipeline_name}'")
            return client
        except ImportError:
            logger.warning("Redis package not installed, queue publishing disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            return None

    def publish_to_queue(self, queue_name: str, data: Dict[str, Any]) -> bool:
        """Publish data to a named queue via Redis.

        Args:
            queue_name: Name of the queue
            data: Data to publish

        Returns:
            True if published successfully, False otherwise
        """
        if not self.redis:
            return False

        try:
            channel = f"pipeline:{self.pipeline_name}:queue:{queue_name}"

            # Add a timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = time.time()

            # JSON encode the data and publish
            self.redis.publish(channel, json.dumps(data))

            return True
        except Exception as e:
            logger.error(f"Failed to publish to queue '{queue_name}': {e}")
            return False

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
