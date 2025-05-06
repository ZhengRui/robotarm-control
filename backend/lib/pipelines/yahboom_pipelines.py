import time
from enum import Enum
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from ..utils.logger import get_logger
from .base import BasePipeline

# Create module-level logger
logger = get_logger("yahboom_pipeline")


class PipelineState(Enum):
    """Enum representing the different states of the pipeline."""

    IDLE = "idle"
    CALIBRATING = "calibrating"
    DETECTING = "detecting"
    PICKING_PLACING = "picking_placing"
    STOPPED = "stopped"


class PipelineSignal(Enum):
    """Enum representing signals that can be sent to the pipeline."""

    CALIBRATION_CONFIRMED = "calibration_confirmed"
    START_PICK_PLACE = "start_pick_place"
    STOP = "stop"


class YahboomPickAndPlacePipeline(BasePipeline):
    """Pipeline for pick and place operations with the Yahboom robot arm.

    This pipeline follows these states:
    1. CALIBRATING: Calibrates the camera-to-robot coordinate system
    2. DETECTING: Detects colored objects in the frame
    3. PICKING_PLACING: Picks and places detected objects

    User signals:
    - "calibration_confirmed": Transition from CALIBRATING to DETECTING
    - "start_pick_place": Transition from DETECTING to PICKING_PLACING
    - "stop": Stop the pipeline
    """

    def __init__(
        self,
        pipeline_name: str = "yahboom_pick_and_place",
        config_override: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize the yahboom pick and place pipeline.

        Args:
            pipeline_name: Name of the pipeline (used to load configuration)
            config_override: Optional configuration overrides
            debug: Whether to enable debug mode for visualization
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
        super().__init__(pipeline_name=pipeline_name, config_override=config_override, debug=debug)

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
        return ["camera_frames", "detection_results"]

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

    def handle_signal(self, signal: str) -> None:
        """Handle user signals for state transitions.

        Args:
            signal: The signal to handle
        """
        logger.info(f"Handling signal: {signal} in state: {self.state.value}")

        if signal == PipelineSignal.CALIBRATION_CONFIRMED.value and self.state == PipelineState.CALIBRATING:
            logger.info("Calibration confirmed, transitioning to detection state")
            self.state = PipelineState.DETECTING

        elif signal == PipelineSignal.START_PICK_PLACE.value and self.state == PipelineState.DETECTING:
            logger.info("Starting pick and place operation")
            self.state = PipelineState.PICKING_PLACING

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
            time.sleep(1)
            return

        # Process the frame based on current state
        if self.state == PipelineState.CALIBRATING:
            self._process_calibration()

        elif self.state == PipelineState.DETECTING:
            self._process_detection()

        # elif self.state == PipelineState.PICKING_PLACING:
        #     self._process_pick_and_place()

    def _get_latest_frame(self) -> None:
        """Get the latest frame from the dataloader handler.

        Uses the dataloader handler to receive a new frame and
        updates self.current_frame with the result.
        """
        if "dataloader" not in self.handlers:
            logger.warning("DataLoader handler not available")
            return

        try:
            # Get process parameters for dataloader
            process_params = self.config.get("dataloader", {}).get("process", {})

            # Process frame with dataloader handler
            result = self.handlers["dataloader"].process(**process_params)

            if result and "frame" in result:
                self.current_frame = result["frame"]

                # Update perspective transformed frame if we have a transformation matrix
                if self.pt_matrix is not None and self.current_frame is not None:
                    h, w = self.current_frame.shape[:2]
                    self.current_pt_frame = cv2.warpPerspective(self.current_frame, self.pt_matrix, (w, h))
            else:
                logger.warning("DataLoader did not return a valid frame")
        except Exception as e:
            logger.error(f"Error in data loading: {e}")
            self.current_frame = None

    def _process_calibration(self) -> None:
        """Process the current frame with the calibration handler."""
        if "calibrate" not in self.handlers:
            logger.warning("Calibration handler not available")
            return

        try:
            # Get process parameters for calibration
            process_params = self.config.get("calibrate", {}).get("process", {})

            # Process frame with calibration handler
            result = self.handlers["calibrate"].process(self.current_frame, debug=self.debug, **process_params)

            # Store the perspective transformation matrix
            if result and "pt_matrix" in result:
                self.pt_matrix = result["pt_matrix"]
                if self.pt_matrix is not None and self.current_frame is not None:
                    h, w = self.current_frame.shape[:2]
                    self.current_pt_frame = cv2.warpPerspective(self.current_frame, self.pt_matrix, (w, h))
                    logger.info("Perspective transformation matrix applied successfully")
                else:
                    logger.warning("Failed to apply perspective transformation matrix")
        except Exception as e:
            logger.error(f"Error in calibration processing: {e}")

    def _process_detection(self) -> None:
        """Process the current frame with the detection handler."""
        if "detect" not in self.handlers:
            logger.warning("Detection handler not available")
            return

        try:
            # Get process parameters for detection
            process_params = self.config.get("detect", {}).get("process", {})

            # Use the perspective transformed frame if available
            frame_to_process = self.current_pt_frame if self.current_pt_frame is not None else self.current_frame

            # Process frame with detection handler - returns a list of detections directly
            self.detected_objects = self.handlers["detect"].process(
                frame_to_process, debug=self.debug, **process_params
            )

            if self.detected_objects:
                logger.info(f"Detected {len(self.detected_objects)} objects")
        except Exception as e:
            logger.error(f"Error in detection processing: {e}")
            self.detected_objects = []

    def _process_pick_and_place(self) -> None:
        """Process pick and place operation with the arm control handler."""
        if "armcontrol" not in self.handlers:
            logger.warning("Arm control handler not available")
            return

        if not self.detected_objects:
            logger.warning("No objects detected for pick and place operation")
            self.state = PipelineState.DETECTING
            return

        try:
            # Get process parameters for arm control
            process_params = self.config.get("armcontrol", {}).get("process", {})

            # Process objects with arm control handler
            self.handlers["armcontrol"].process(self.detected_objects, debug=self.debug, **process_params)
        except Exception as e:
            logger.error(f"Error in pick and place operation: {e}")
