import json
import time
from typing import Any, Dict

import imagezmq
import numpy as np

from ..utils.factory import decode
from ..utils.logger import get_logger

logger = get_logger("dataloader")


class DataLoaderHandler:
    """Handler for loading image data from various sources.

    This handler connects to an imagezmq server and receives frames.
    It handles connection issues gracefully and provides the received frames
    to the pipeline for further processing.

    The handler is typically the first in a pipeline, providing input data
    for subsequent handlers to process.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the data loader handler.

        Creates a connection to the imagezmq hub for receiving frames.

        Args:
            **kwargs: Additional configuration parameters (not currently used)
        """
        self.hub = imagezmq.ImageHub()
        logger.info("DataLoaderHandler initialized with imagezmq hub")

    def process(self, retry_delay: float = 1.0, log_interval: int = 100, **kwargs: Any) -> Dict[str, np.ndarray]:
        """Process a single data loading step.

        Receives a frame from the imagezmq hub and returns it.
        If there's a communication error, it will retry until successful.

        Args:
            retry_delay: Time in seconds to wait between retries on errors (default: 1.0)
            log_interval: Number of frames between logging messages (default: 100)
            **kwargs: Additional process parameters (not currently used)

        Returns:
            dict: Dictionary containing the loaded frame with key 'frame'

        Note:
            This method blocks until a valid frame is received
        """
        frame_received = False
        rpi_name = None
        i_frame = 0
        frame = None

        while not frame_received:
            try:
                rpi_name, msg = self.hub.recv_jpg()
                i_frame, frame = decode(msg.bytes)
                assert frame.size
                frame_received = True
            except Exception as err:
                logger.warning(f"Communication Error {err}!", exc_info=True)
                time.sleep(retry_delay)
                continue

        assert frame is not None

        if i_frame % log_interval == 0:
            logger.info(f"{rpi_name} {i_frame}th frame: {frame.shape}")

        # Send reply to acknowledge receipt
        self.hub.send_reply(json.dumps({"status": "OK"}).encode("utf-8"))

        return {"frame": frame}
