import os
import queue
import threading
import time
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml
from deepmerge import Merger

from ..handlers import HandlerFactory
from ..utils.logger import get_logger

# Create module-level logger
logger = get_logger("pipeline")

# Create custom merger configuration
cfg_merger = Merger([(list, ["override"]), (dict, ["merge"])], ["override"], ["override"])


class SignalPriority(Enum):
    """Priority levels for pipeline signals."""

    HIGH = auto()  # Must be processed immediately
    NORMAL = auto()  # Can be processed in next cycle


class BasePipeline(ABC):
    """Base class for all pipelines.

    This class provides a framework for pipeline execution with the following features:
    - Configuration loading and handler initialization
    - Two separate threads: one for signal handling, one for step execution
    - Priority-based signal queue for user interaction
    - Callback mechanism for pipeline state changes
    """

    def __init__(self, pipeline_name: str, config_override: Optional[Dict[str, Any]] = None, debug: bool = False):
        """Initialize pipeline with configuration and start execution.

        Args:
            pipeline_name: Name of the pipeline (used to load configuration)
            config_override: Optional configuration dictionary to override defaults
            debug: Whether to enable debug mode for visualization and logging

        Raises:
            RuntimeError: If pipeline fails to initialize or start
        """
        self.pipeline_name = pipeline_name
        self.debug = debug

        logger.info(f"Initializing pipeline: {pipeline_name} (debug={debug})")

        # Load default configuration
        self.config = self._load_config()

        # Extract this pipeline's configuration
        self.config = self.config.get(pipeline_name, {})
        if not self.config:
            logger.warning(f"No configuration found for pipeline: {pipeline_name}")

        # Merge with override config if provided
        if config_override:
            self._merge_config(config_override)

        # Initialize handlers
        self.handlers = self._initialize_handlers()
        logger.info(f"Pipeline '{pipeline_name}' initialized handlers: {', '.join(self.handlers.keys())}")

        self.running = False
        self.on_exit_callback: Optional[Callable[[bool, Optional[str]], None]] = None

        # Create priority queue for signals
        self.signal_queue: queue.PriorityQueue[Tuple[int, str]] = queue.PriorityQueue()

        # Thread management
        self._signal_thread: Optional[threading.Thread] = None
        self._step_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        try:
            self.start()
        except Exception as e:
            logger.error(f"Failed to start pipeline '{pipeline_name}': {e}")
            raise RuntimeError(f"Failed to start pipeline '{pipeline_name}': {e}")

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

                # If no 'init' section, use the whole config except 'process' section
                if not init_params:
                    init_params = {k: v for k, v in handler_config.items() if k != "process"}

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

    def signal(self, signal: str, priority: SignalPriority = SignalPriority.NORMAL) -> None:
        """Send a signal to the pipeline with specified priority.

        Args:
            signal: The signal to send
            priority: Priority level of the signal (default: NORMAL)
        """
        logger.info(f"Pipeline '{self.pipeline_name}' received signal: {signal} (priority: {priority.name})")
        # Use priority value as the first element of the tuple for queue ordering
        self.signal_queue.put((priority.value, signal))

    def _get_pending_signal(self) -> Optional[str]:
        """Check for pending signals without blocking.

        Returns:
            Signal if available, None otherwise
        """
        try:
            # Get the signal from the priority queue
            _, signal = self.signal_queue.get_nowait()
            return signal
        except queue.Empty:
            return None

    def set_exit_callback(self, callback: Callable[[bool, Optional[str]], None]) -> None:
        """Set a callback function that will be called when the pipeline exits.

        The callback will be called with two arguments:
        - success: a boolean indicating whether the pipeline exited normally
        - error_message: an optional string with error details (None if success is True)

        Args:
            callback: The callback function to call when pipeline exits
        """
        self.on_exit_callback = callback
        logger.debug(f"Pipeline '{self.pipeline_name}' exit callback set")

    def start(self) -> None:
        """Start the pipeline with two separate threads for signal handling and step execution."""
        if self._signal_thread is not None and self._signal_thread.is_alive():
            logger.warning(f"Pipeline '{self.pipeline_name}' already running")
            return

        self.running = True
        self._stop_event.clear()

        # Start signal handling thread
        self._signal_thread = threading.Thread(target=self._signal_loop)
        self._signal_thread.daemon = True
        self._signal_thread.start()

        # Start step execution thread
        self._step_thread = threading.Thread(target=self._step_loop)
        self._step_thread.daemon = True
        self._step_thread.start()

        logger.info(f"Pipeline '{self.pipeline_name}' started with separate signal and step threads")

    def _signal_loop(self) -> None:
        """Run the signal handling loop.

        This method continuously checks for signals and processes them
        until the pipeline is stopped.
        """
        success = False
        error_message = None

        try:
            while self.running and not self._stop_event.is_set():
                # Check for signals
                signal = self._get_pending_signal()
                if signal is not None:
                    self.handle_signal(signal)

                # Small sleep to prevent busy waiting
                time.sleep(0.1)

            # If we reached here, the signal thread exited normally
            success = True
        except Exception as e:
            # Capture any exceptions that occurred during signal handling
            error_message = f"Pipeline '{self.pipeline_name}' signal thread encountered an error: {e!s}"
            logger.error(error_message, exc_info=True)
            self.running = False
            self._stop_event.set()
        finally:
            # Notify that the pipeline has exited if this is the last thread to exit
            if not self._step_thread or not self._step_thread.is_alive():
                self._notify_exit(success, error_message)

            logger.info(f"Pipeline '{self.pipeline_name}' signal thread exiting")

    def _step_loop(self) -> None:
        """Run the step execution loop.

        This method continuously executes pipeline steps until the pipeline is stopped,
        handling any exceptions that occur during step execution.
        """
        success = False
        error_message = None

        try:
            while self.running and not self._stop_event.is_set():
                try:
                    self.step()
                except Exception as e:
                    logger.error(f"Error in pipeline step: {e}", exc_info=True)
                    # Continue running despite errors

                # Small sleep to prevent busy waiting
                time.sleep(0.01)

            # If we reached here, the step thread exited normally
            success = True
        except Exception as e:
            # Capture any exceptions that occurred during step execution
            error_message = f"Pipeline '{self.pipeline_name}' step thread encountered an error: {e!s}"
            logger.error(error_message, exc_info=True)
            self.running = False
            self._stop_event.set()
        finally:
            # Notify that the pipeline has exited if this is the last thread to exit
            if not self._signal_thread or not self._signal_thread.is_alive():
                self._notify_exit(success, error_message)

            logger.info(f"Pipeline '{self.pipeline_name}' step thread exiting")

    def _notify_exit(self, success: bool, error_message: Optional[str]) -> None:
        """Notify the exit callback that the pipeline has exited.

        Args:
            success: Whether the pipeline exited successfully
            error_message: Error message if the pipeline exited with an error
        """
        if self.on_exit_callback:
            try:
                self.on_exit_callback(success, error_message)
            except Exception as callback_error:
                # Don't let callback errors propagate
                logger.error(f"Error in pipeline exit callback: {callback_error}", exc_info=True)

    def stop(self) -> None:
        """Stop the pipeline and wait for threads to exit."""
        self.running = False
        self._stop_event.set()

        # Wait for threads to exit
        if self._signal_thread:
            self._signal_thread.join(timeout=1.0)

        if self._step_thread:
            self._step_thread.join(timeout=1.0)

        logger.info(f"Pipeline '{self.pipeline_name}' stopped")

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
