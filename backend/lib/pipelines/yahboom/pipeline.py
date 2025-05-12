import base64
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from ...utils.logger import get_logger
from ..base import BasePipeline

# Create module-level logger
logger = get_logger("yahboom_pipeline")


class PipelineState(Enum):
    """Enum representing the different states of the pipeline."""

    IDLE = "idle"
    CALIBRATING = "calibrating"
    DETECTING = "detecting"
    PICKING_PLACING = "picking_placing"
    PICKING_STACKING = "picking_stacking"
    STOPPED = "stopped"


class PipelineSignal(Enum):
    """Enum representing signals that can be sent to the pipeline."""

    RESET_ARM = "reset_arm"
    RE_CALIBRATE = "re_calibrate"
    CALIBRATION_CONFIRMED = "calibration_confirmed"
    PICK_PLACE = "pick_place"
    PICK_STACK = "pick_stack"
    STOP = "stop"


class PipelineQueue(Enum):
    """Enum representing the different visualization purposed queues of the pipeline."""

    INPUT_FRAMES = "input_frames"
    CALIBRATION_FRAMES = "calibration_frames"
    PT_FRAMES = "pt_frames"
    DETECTION_FRAMES = "detection_frames"


class Pipeline(BasePipeline):
    """Pipeline for pick and place operations with the Yahboom robot arm.

    This pipeline follows these states:
    1. CALIBRATING: Calibrates the camera-to-robot coordinate system
    2. DETECTING: Detects colored objects in the frame
    3. PICKING_PLACING: Picks and places detected objects

    User signals:
    - "reset_arm": Reset the robot arm
    - "re_calibrate": Re-calibrate the robot arm
    - "calibration_confirmed": Transition from CALIBRATING to DETECTING
    - "pick_place": Transition from DETECTING to PICKING_PLACING
    - "pick_stack": Transition from DETECTING to PICKING_STACKING
    - "stop": Stop the pipeline
    """

    def __init__(
        self,
        pipeline_name: str = "yahboom_pick_and_place",
        config_override: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the yahboom pick and place pipeline.

        Args:
            pipeline_name: Name of the pipeline
            config_override: Optional configuration overrides
        """
        # Initialize state before parent constructor to ensure it's set before the thread starts
        self.state = PipelineState.IDLE

        # Store detected objects
        self.detected_objects: List[Dict[str, Any]] = []

        # A buffer for the latest frame
        self.current_frame: Optional[np.ndarray] = None

        # Store the perspective transformed frame
        self.current_pt_frame: Optional[np.ndarray] = None

        # Store the perspective transformation matrix
        self.pt_matrix: Optional[np.ndarray] = None

        # Call parent constructor - this will start the pipeline thread
        super().__init__(pipeline_name=pipeline_name, config_override=config_override)

        self.dataloader_handler = self.handlers.get("data_loader", None)
        self.calibrate_handler = self.handlers.get("calibrate", None)
        self.detect_handler = self.handlers.get("detect", None)
        self.arm_control_handler = self.handlers.get("arm_control", None)
        self.config_handlers = self.config.get("handlers", {})

    @classmethod
    def get_available_signals(cls) -> List[str]:
        """Return the available signals for this pipeline class.

        Returns:
            List of signal strings that can be sent to this pipeline
        """
        return [signal.value for signal in PipelineSignal]

    @classmethod
    def get_available_states(cls) -> List[str]:
        """Return the available states for this pipeline class.

        Returns:
            List of possible state strings for this pipeline
        """
        return [state.value for state in PipelineState]

    @classmethod
    def get_available_queues(cls) -> List[str]:
        """Return the available data queues for this pipeline class.

        Returns:
            List of queue names that this pipeline uses
        """
        return [queue.value for queue in PipelineQueue]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return the configuration schema for this pipeline class.

        Returns:
            Dictionary containing the configuration schema for this pipeline
        """
        return {}

    @property
    def current_state(self) -> str:
        """Return the current state of the pipeline.

        Returns:
            Current state as a string
        """
        return self.state.value

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame as base64 JPEG for transmission."""
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return ""
        return base64.b64encode(buffer.tobytes()).decode("utf-8")

    def handle_signal(self, signal: str) -> None:
        """Handle user signals for state transitions.

        Args:
            signal: The signal to handle
        """
        logger.info(f"Handling signal: {signal} in state: {self.state.value}")

        if signal == PipelineSignal.RESET_ARM.value:
            logger.info("Resetting arm")
            self.arm_control_handler._reset()

        if signal == PipelineSignal.RE_CALIBRATE.value:
            logger.info("Re-calibrating")
            self.arm_control_handler._reset()
            self.state = PipelineState.CALIBRATING

        if signal == PipelineSignal.CALIBRATION_CONFIRMED.value and self.state == PipelineState.CALIBRATING:
            logger.info("Calibration confirmed, transitioning to detection state")
            self.state = PipelineState.DETECTING

        elif signal == PipelineSignal.PICK_PLACE.value and self.state == PipelineState.DETECTING:
            logger.info("Starting pick and place operation")
            self.state = PipelineState.PICKING_PLACING

        elif signal == PipelineSignal.PICK_STACK.value and self.state == PipelineState.DETECTING:
            logger.info("Starting pick and stack operation")
            self.state = PipelineState.PICKING_STACKING

        elif signal == PipelineSignal.STOP.value:
            logger.info("Stopping pipeline due to stop signal")
            self.state = PipelineState.STOPPED

    def step(self) -> None:
        """Process a single step based on the current state.

        This method handles the state-specific processing, using the dataloader
        to receive frames and passing them to the appropriate handlers.
        """
        # Skip processing if in IDLE or STOPPED state
        if self.state == PipelineState.IDLE:
            # Initialize the robot arm
            self.arm_control_handler._reset()

            # Initialize to calibration state on first step
            self.state = PipelineState.CALIBRATING
            logger.info("Pipeline initialized to calibration state")
            return

        elif self.state == PipelineState.STOPPED:
            # Nothing to do in stopped state
            return

        # Get the latest frame from the dataloader
        self._get_latest_frame()

        if self.current_frame is None:
            # No frame available, sleep a bit to avoid busy waiting
            time.sleep(0.01)
            return

        # Process the frame based on current state
        if self.state == PipelineState.CALIBRATING:
            self._process_calibration()

        elif self.state == PipelineState.DETECTING:
            self._process_detection()

        elif self.state == PipelineState.PICKING_PLACING:
            self._process_pick_and_place()

        elif self.state == PipelineState.PICKING_STACKING:
            self._process_pick_and_stack()

    def _get_latest_frame(self) -> None:
        """Get the latest frame from the dataloader handler.

        Uses the dataloader handler to receive a new frame and
        updates self.current_frame with the result.
        """
        if self.dataloader_handler is None:
            logger.warning("DataLoader handler not available")
            return

        try:
            # Get process parameters for dataloader
            process_params = self.config_handlers.get("data_loader", {}).get("process", {})

            # Process frame with dataloader handler
            result = self.dataloader_handler.process(**process_params)

            if result and "frame" in result:
                self.current_frame = result["frame"]

                if self.current_frame is None:
                    return

                self.publish_to_queue(
                    PipelineQueue.INPUT_FRAMES.value, {"frame": self._encode_frame(self.current_frame)}
                )

                # Update perspective transformed frame if we have a transformation matrix
                if self.pt_matrix is not None:
                    h, w = self.current_frame.shape[:2]
                    self.current_pt_frame = cv2.warpPerspective(self.current_frame, self.pt_matrix, (w, h))

                    self.publish_to_queue(
                        PipelineQueue.PT_FRAMES.value,
                        {"frame": self._encode_frame(self.current_pt_frame)},
                    )
            else:
                logger.warning("DataLoader did not return a valid frame")
        except Exception as e:
            logger.error(f"Error in data loading: {e}")
            self.current_frame = None

    def _process_calibration(self) -> None:
        """Process the current frame with the calibration handler."""
        if self.calibrate_handler is None:
            logger.warning("Calibration handler not available")
            return

        try:
            # Get process parameters for calibration
            process_params = self.config_handlers.get("calibrate", {}).get("process", {})

            # Process frame with calibration handler
            result = self.calibrate_handler.process(self.current_frame, **process_params)

            # Store the perspective transformation matrix
            if result and "pt_matrix" in result:
                self.pt_matrix = result["pt_matrix"]

                self.publish_to_queue(
                    PipelineQueue.CALIBRATION_FRAMES.value, {"frame": self._encode_frame(result["processed_frame"])}
                )
            else:
                logger.warning("Failed to get perspective transformation matrix")

        except Exception as e:
            logger.error(f"Error in calibration processing: {e}")

    def _process_detection(self) -> None:
        """Process the current frame with the detection handler."""
        if self.detect_handler is None:
            logger.warning("Detection handler not available")
            return

        try:
            # Get process parameters for detection
            process_params = self.config_handlers.get("detect", {}).get("process", {})

            # Use the perspective transformed frame if available
            frame_to_process = self.current_pt_frame if self.current_pt_frame is not None else self.current_frame

            # Process frame with detection handler - returns a list of detections directly
            result = self.detect_handler.process(frame_to_process, **process_params)

            if result and "detections" in result:
                self.detected_objects = result["detections"]

                # if self.detected_objects:
                #     logger.info(f"Detected {len(self.detected_objects)} objects")

                self.publish_to_queue(
                    PipelineQueue.DETECTION_FRAMES.value,
                    {"frame": self._encode_frame(result["processed_frame"])},
                )

        except Exception as e:
            logger.error(f"Error in detection processing: {e}")
            self.detected_objects = []

    def _process_pick_and_place(self) -> None:
        """Process pick and place operation with the arm control handler."""
        if self.arm_control_handler is None:
            logger.warning("Arm control handler not available")
            return

        if not self.detected_objects:
            logger.warning("No objects detected for pick and place operation")
            self.state = PipelineState.DETECTING
            return

        try:
            # Get process parameters for arm control
            process_params = self.config_handlers.get("arm_control", {}).get("process", {})

            # Process objects with arm control handler
            result = self.arm_control_handler.process(self.detected_objects, **process_params)
            failed = result.get("failed", [])

            if failed:
                logger.info(
                    f"Failed to pick and place {len(failed)} objects: {','.join([obj['label'] for obj in failed])}"
                )

            logger.info("Pick and place tried, back to detection state")
            self.state = PipelineState.DETECTING

        except Exception as e:
            logger.error(f"Error in pick and place operation: {e}")

    def _process_pick_and_stack(self) -> None:
        """Process pick and stack operation with the arm control handler."""
        if self.arm_control_handler is None:
            logger.warning("Arm control handler not available")
            return

        if not self.detected_objects:
            logger.warning("No objects detected for pick and stack operation")
            self.state = PipelineState.DETECTING
            return

        try:
            # Get process parameters for arm control
            process_params = self.config_handlers.get("arm_control", {}).get("process", {})

            # Ensure task is set to pick_and_stack
            process_params["task"] = "pick_and_stack"

            # Process objects with arm control handler
            result = self.arm_control_handler.process(self.detected_objects, **process_params)
            failed = result.get("failed", [])

            if failed:
                logger.info(
                    f"Failed to pick and stack {len(failed)} objects: {','.join([obj['label'] for obj in failed])}"
                )

            logger.info("Pick and stack tried, back to detection state")
            self.state = PipelineState.DETECTING

        except Exception as e:
            logger.error(f"Error in pick and stack operation: {e}")

    def get_instance_meta(self) -> Dict[str, Any]:
        """Return instance-specific metadata based on current configuration.

        This allows for dynamic signals and states based on the task type.
        """
        task = self.config_handlers.get("arm_control", {}).get("init", {}).get("task", "pick_and_place")

        # Base states and signals that are always available
        base_states = [
            PipelineState.IDLE.value,
            PipelineState.CALIBRATING.value,
            PipelineState.DETECTING.value,
            PipelineState.STOPPED.value,
        ]

        base_signals = [
            PipelineSignal.RESET_ARM.value,
            PipelineSignal.RE_CALIBRATE.value,
            PipelineSignal.CALIBRATION_CONFIRMED.value,
            PipelineSignal.STOP.value,
        ]

        # Task-specific states and signals
        if task == "pick_and_stack":
            meta = {
                "available_states": [*base_states, PipelineState.PICKING_STACKING.value],
                "available_signals": [*base_signals, PipelineSignal.PICK_STACK.value],
                "available_queues": [queue.value for queue in PipelineQueue],
            }
        else:  # Default to pick_and_place
            meta = {
                "available_states": [*base_states, PipelineState.PICKING_PLACING.value],
                "available_signals": [*base_signals, PipelineSignal.PICK_PLACE.value],
                "available_queues": [queue.value for queue in PipelineQueue],
            }

        return meta
