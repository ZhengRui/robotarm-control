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
    - Threading infrastructure for non-blocking execution
    - Priority-based signal queue for user interaction
    - Main execution loop with frame processing
    - Callback mechanism for pipeline state changes

    Subclasses must implement:
    - handle_signal(): Process user signals/commands
    - step(): Process a single step in the current pipeline state
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
        self.thread: Optional[threading.Thread] = None
        self.on_exit_callback: Optional[Callable[[bool, Optional[str]], None]] = None

        # Create priority queue for signals
        self.signal_queue: queue.PriorityQueue[Tuple[int, str]] = queue.PriorityQueue()

        # Thread management for step execution
        self._step_thread: Optional[threading.Thread] = None
        self._step_complete = threading.Event()
        self._step_complete.set()
        self._step_error: Optional[Exception] = None

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
        """Start the pipeline in a separate thread."""
        if self.thread is not None and self.thread.is_alive():
            logger.warning(f"Pipeline '{self.pipeline_name}' already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self.serve)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Pipeline '{self.pipeline_name}' started in background thread")

    def serve(self) -> Any:
        """Serve the pipeline workflow.

        This method runs in a separate thread and forms the main execution
        loop of the pipeline, checking for signals and processing frames.
        If an exit callback is set, it will be called when the pipeline exits,
        either normally or due to an exception.

        Returns:
            Pipeline result (implementation-dependent)
        """
        success = False
        error_message = None

        try:
            while self.running:
                # Check for signals
                signal = self._get_pending_signal()
                if signal is not None:
                    self.handle_signal(signal)

                # Check if current step is complete
                if self._step_complete.is_set():
                    # Handle step completion
                    if self._step_error:
                        error_message = f"Step failed: {self._step_error}"
                        logger.error(error_message)

                        # keep running the pipeline
                        # self.running = False
                        # break

                    # Clean up and start next step
                    self._step_thread = None
                    self._step_error = None
                    self._step_complete.clear()

                    # Start next step
                    self._step_thread = threading.Thread(target=self._run_step)
                    self._step_thread.start()

                # Small sleep to prevent busy waiting
                time.sleep(0.1)

            # If we reached here, the pipeline exited normally
            success = True
        except Exception as e:
            # Capture any exceptions that occurred during pipeline execution
            error_message = f"Pipeline '{self.pipeline_name}' encountered an error: {e!s}"
            # Log the error only if no callback is set (to avoid redundant logging)
            if not self.on_exit_callback:
                logger.error(error_message, exc_info=True)
            self.running = False
        finally:
            # Notify that the pipeline has exited, whether normally or due to an error
            if self.on_exit_callback:
                try:
                    self.on_exit_callback(success, error_message)
                except Exception as callback_error:
                    # Don't let callback errors propagate
                    logger.error(f"Error in pipeline exit callback: {callback_error}", exc_info=True)

            logger.info(f"Pipeline '{self.pipeline_name}' thread exiting")

    def _run_step(self) -> None:
        """Run a single step in a separate thread.

        This method wraps the step() method to handle exceptions and
        signal step completion.
        """
        try:
            self.step()
        except Exception as e:
            self._step_error = e
        finally:
            self._step_complete.set()

    def stop(self) -> None:
        """Stop the pipeline."""
        self.running = False
        if self._step_thread:
            self._step_thread.join(timeout=1.0)
        if self.thread:
            self.thread.join(timeout=1.0)
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
