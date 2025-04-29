import multiprocessing
import queue
import threading
import time
from enum import Enum
from typing import Any, Dict, Optional, Type

from ..utils.logger import get_logger
from .base import BasePipeline

# Initialize logger
logger = get_logger("pipeline_process")


class SignalPriority(str, Enum):
    """Priority levels for pipeline signals."""

    HIGH = "HIGH"
    NORMAL = "NORMAL"


class PipelineProcess:
    """Manages a pipeline instance running in a separate process.

    This class encapsulates all multiprocessing logic, providing a clean
    interface for starting, stopping, and communicating with pipeline instances.

    It handles:
    - Process lifecycle management
    - Inter-process communication through queues
    - Signal routing
    - Status reporting
    """

    def __init__(
        self,
        pipeline_class: Type[BasePipeline],
        pipeline_name: str,
        config_override: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize a pipeline process manager.

        Args:
            pipeline_class: The BasePipeline subclass to instantiate
            pipeline_name: Name of the pipeline
            config_override: Optional configuration overrides
            debug: Whether to enable debug mode
        """
        self.pipeline_class = pipeline_class
        self.pipeline_name = pipeline_name
        self.config_override = config_override or {}
        self.debug = debug

        # IPC queues
        self.signal_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.status_queue: multiprocessing.Queue = multiprocessing.Queue()

        # Process instance
        self.process: Optional[multiprocessing.Process] = None
        self._last_status = {"state": None, "running": False}
        self._status_lock = threading.Lock()

    def start(self) -> None:
        """Start the pipeline in a separate process."""
        if self.process and self.process.is_alive():
            logger.warning(f"Pipeline '{self.pipeline_name}' already running")
            return

        logger.info(f"Starting pipeline '{self.pipeline_name}' in separate process (debug={self.debug})")

        # Create and start the process
        self.process = multiprocessing.Process(
            target=self._run_pipeline,
            args=(
                self.pipeline_class,
                self.pipeline_name,
                self.config_override,
                self.debug,
                self.signal_queue,
                self.status_queue,
            ),
            daemon=True,
        )
        self.process.start()

        # Wait for initial status update
        try:
            status = self.status_queue.get(timeout=5.0)
            with self._status_lock:
                self._last_status = status
        except queue.Empty:
            logger.warning(f"No initial status received from pipeline '{self.pipeline_name}'")

    def stop(self, timeout: float = 5.0) -> bool:
        """Stop the pipeline process.

        Args:
            timeout: Seconds to wait for process to terminate

        Returns:
            True if process terminated normally, False if forced
        """
        if not self.process or not self.process.is_alive():
            logger.info(f"Pipeline '{self.pipeline_name}' not running")
            return True

        logger.info(f"Stopping pipeline '{self.pipeline_name}'")

        # Send stop signal
        self.signal_queue.put({"type": "stop"})

        # Wait for process to terminate
        self.process.join(timeout=timeout)

        # Force termination if still running
        if self.process.is_alive():
            logger.warning(f"Pipeline '{self.pipeline_name}' did not terminate, forcing...")
            self.process.terminate()
            self.process.join(timeout=1.0)
            return False

        logger.info(f"Pipeline '{self.pipeline_name}' stopped")
        return True

    def send_signal(self, signal: str, priority: int = 1) -> None:
        """Send a signal to the pipeline.

        Args:
            signal: The signal string to send
            priority: Signal priority (lower is higher priority)
        """
        if not self.process or not self.process.is_alive():
            logger.warning(f"Cannot send signal '{signal}' - pipeline not running")
            return

        logger.debug(f"Sending signal '{signal}' to pipeline '{self.pipeline_name}'")
        self.signal_queue.put({"type": "signal", "signal": signal, "priority": priority})

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the pipeline.

        This checks for new status updates from the queue without blocking,
        and returns the most recent status information.

        Returns:
            Dictionary with current pipeline status
        """
        # Check for status updates (non-blocking)
        try:
            while not self.status_queue.empty():
                status = self.status_queue.get(block=False)
                with self._status_lock:
                    self._last_status = status
        except (queue.Empty, EOFError):
            pass

        # Return the most recent status
        with self._status_lock:
            return self._last_status.copy()

    def is_running(self) -> bool:
        """Check if the pipeline process is running.

        Returns:
            True if the process is alive, False otherwise
        """
        return self.process is not None and self.process.is_alive()

    @staticmethod
    def _run_pipeline(
        pipeline_class: Type[BasePipeline],
        pipeline_name: str,
        config_override: Dict[str, Any],
        debug: bool,
        signal_queue: multiprocessing.Queue,
        status_queue: multiprocessing.Queue,
    ):
        """Pipeline process entry point.

        This runs in a separate process and manages the pipeline instance.

        Args:
            pipeline_class: The BasePipeline subclass to instantiate
            pipeline_name: Name of the pipeline
            config_override: Configuration overrides
            debug: Debug flag
            signal_queue: Queue for receiving signals
            status_queue: Queue for sending status updates
        """
        # Configure process-specific logger
        logger = get_logger(f"pipeline_process_{pipeline_name}")
        logger.info(f"Pipeline process started for '{pipeline_name}'")

        # Signal handling flags
        stop_event = threading.Event()

        try:
            # Create pipeline instance with pipeline_name
            pipeline = pipeline_class(pipeline_name=pipeline_name, config_override=config_override, debug=debug)

            # Initial status update
            _send_status(pipeline, status_queue, stop_event)

            # Start signal handling thread
            signal_thread = threading.Thread(
                target=_process_signals, args=(pipeline, signal_queue, status_queue, stop_event)
            )
            signal_thread.daemon = True
            signal_thread.start()

            # Main step loop (in main thread of process)
            while not stop_event.is_set():
                try:
                    # Run one pipeline step
                    pipeline.step()

                    # Periodically update status (every ~1 second)
                    if int(time.time()) % 1 == 0:
                        _send_status(pipeline, status_queue, stop_event)

                    # Small sleep to prevent CPU spinning
                    time.sleep(0.01)

                except Exception as e:
                    logger.error(f"Error in pipeline step: {e}", exc_info=True)

            # Final status update
            _send_status(pipeline, status_queue, stop_event)
            logger.info(f"Pipeline '{pipeline_name}' terminated")

        except Exception as e:
            logger.error(f"Error in pipeline process: {e}", exc_info=True)

            # Send error status
            status_queue.put({"state": "error", "running": False, "error": str(e), "timestamp": time.time()})

        finally:
            # Cleanup
            logger.info("Performing final cleanup")
            # Note: OpenCV windows should be closed by pipeline implementation


def _process_signals(
    pipeline: BasePipeline,
    signal_queue: multiprocessing.Queue,
    status_queue: multiprocessing.Queue,
    stop_event: threading.Event,
):
    """Process signals from the main process.

    Args:
        pipeline: The pipeline instance
        signal_queue: Queue for receiving signals
        status_queue: Queue for sending status updates
        stop_event: Event to signal process termination
    """
    logger = get_logger("signal_thread")

    while not stop_event.is_set():
        try:
            # Collect all available signals (non-blocking)
            signals = []
            max_signals = 10  # Maximum number of signals to collect per batch

            # First, try to get at least one signal (with timeout to check stop_event)
            try:
                signal_data = signal_queue.get(timeout=0.1)
                signals.append((signal_data.get("priority", 2), signal_data))
            except queue.Empty:
                # No signals available, continue to next iteration
                continue

            # Try to collect more signals if available (non-blocking)
            for _ in range(max_signals - 1):
                try:
                    signal_data = signal_queue.get(block=False)
                    signals.append((signal_data.get("priority", 2), signal_data))
                except queue.Empty:
                    break

            # Process stop signals first
            stop_signals = [s for _, s in signals if s["type"] == "stop"]
            if stop_signals:
                logger.info("Received stop signal")
                stop_event.set()
                continue

            # Sort remaining signals by priority (lower number = higher priority)
            other_signals = [(p, s) for p, s in signals if s["type"] != "stop"]
            other_signals.sort(key=lambda x: x[0])  # Sort by priority

            # Process at least the highest priority signal
            if other_signals:
                _, signal_data = other_signals[0]
                logger.debug(f"Handling signal: {signal_data['signal']}")
                pipeline.handle_signal(signal_data["signal"])
                _send_status(pipeline, status_queue, stop_event)

                # If we have more signals, put the remaining ones back
                # Putting signals back in priority order
                for _, signal_data in other_signals[1:]:
                    signal_queue.put(signal_data)

        except Exception as e:
            logger.error(f"Error processing signal: {e}", exc_info=True)


def _send_status(pipeline: BasePipeline, status_queue: multiprocessing.Queue, stop_event: threading.Event):
    """Send pipeline status to the main process.

    Args:
        pipeline: The pipeline instance
        status_queue: Queue for sending status updates
        stop_event: Process termination event
    """
    try:
        # Get basic status information
        status: Dict[str, Any] = {
            "state": pipeline.current_state,
            "running": not stop_event.is_set(),
            "timestamp": time.time(),
        }

        # Add available signals and states
        status["available_signals"] = pipeline.available_signals
        status["available_states"] = pipeline.available_states

        # Send to main process
        status_queue.put(status)
    except Exception as e:
        logger.error(f"Error sending status: {e}")
