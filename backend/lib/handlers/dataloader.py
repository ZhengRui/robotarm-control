import base64
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, TypedDict, Union

import numpy as np

from ..utils.data_factory import decode
from ..utils.logger import get_logger

logger = get_logger("dataloader")


# Define custom type for frame result that allows None and boolean values
class FrameResult(TypedDict, total=False):
    frame: Optional[np.ndarray]
    available: bool
    error: str


class BaseDataLoaderHandler(ABC):
    """Abstract base class for data loader handlers.

    Defines the interface that all data loader handlers must implement.
    """

    @abstractmethod
    def process(self, **kwargs: Any) -> FrameResult:
        """Process a single data loading step.

        Args:
            **kwargs: Additional parameters for specific implementations

        Returns:
            Dictionary containing the loaded frame
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close resources used by the handler."""
        pass


class ImageZMQDataLoaderHandler(BaseDataLoaderHandler):
    """Handler for loading image data from ImageZMQ source.

    This handler connects to an imagezmq server and receives frames.
    It handles connection issues gracefully and provides the received frames
    to the pipeline for further processing.

    WARNING: The process method in this handler is BLOCKING and will wait
    indefinitely until a frame is received. This can cause issues with pipeline
    shutdown if no frames are being sent. Consider using RedisDataLoaderHandler
    for non-blocking operation.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555, **kwargs: Any) -> None:
        """Initialize the ImageZMQ data loader handler.

        Creates a connection to the imagezmq hub for receiving frames.

        Args:
            host: ImageZMQ host address
            port: ImageZMQ port
            **kwargs: Additional configuration parameters (not currently used)
        """
        try:
            import imagezmq

            self.hub = imagezmq.ImageHub(connect_to=f"tcp://{host}:{port}")
            logger.info(f"ImageZMQDataLoaderHandler initialized with hub at {host}:{port}")
        except ImportError:
            logger.error("ImageZMQ not available. Please ensure imagezmq is installed.")
            raise

    def process(self, retry_delay: float = 1.0, log_interval: int = 100, **kwargs: Any) -> FrameResult:
        """Process a single data loading step.

        Receives a frame from the imagezmq hub and returns it.
        If there's a communication error, it will retry until successful.

        Args:
            retry_delay: Time in seconds to wait between retries on errors (default: 1.0)
            log_interval: Number of frames between logging messages (default: 100)
            **kwargs: Additional process parameters (not currently used)

        Returns:
            FrameResult containing the loaded frame with key 'frame'

        Note:
            This method BLOCKS until a valid frame is received, which may cause
            pipeline shutdown issues if no frames are available
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

        # Return properly typed result
        result: FrameResult = {"frame": frame, "available": True}
        return result

    def close(self) -> None:
        """Close the ImageZMQ connection."""
        # ImageZMQ doesn't have a formal close method
        self.hub = None


class RedisDataLoaderHandler(BaseDataLoaderHandler):
    """Handler for loading image data from Redis queue.

    This handler connects to a Redis server and receives frames from a queue.
    It provides a non-blocking alternative to ImageZMQ, allowing for better
    pipeline shutdown handling and more flexible integration with other systems.
    """

    def __init__(
        self, host: str = "127.0.0.1", port: int = 6379, db: int = 0, password: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize the Redis data loader handler.

        Args:
            host: Redis host address
            port: Redis port
            db: Redis database number
            password: Redis password
            **kwargs: Additional configuration parameters
        """
        try:
            import redis
            from redis import Redis

            self.redis: Redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
            )

            # Test connection
            self.redis.ping()

            self.last_frame_id = 0

            logger.info(f"RedisDataLoaderHandler initialized with redis at {host}:{port}")
        except ImportError:
            logger.error("Redis not available. Please ensure redis-py is installed.")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {host}:{port}: {e}")
            raise

    def process(self, wait: bool = False, queue: str = "camera_frames", timeout: int = 1, **kwargs: Any) -> FrameResult:
        """Process a single data loading step.

        Receives a frame from the Redis queue and returns it.

        Args:
            wait: Whether to wait for a frame if none is available
            queue: Redis queue name for image frames
            timeout: Timeout in seconds for blocking operations
            **kwargs: Additional process parameters

        Returns:
            FrameResult containing the loaded frame with key 'frame'
            and 'available' flag indicating if a frame was received
        """
        # Prepare the empty result for cases when no frame is available
        no_frame_result: FrameResult = {"frame": None, "available": False}

        try:
            # Try to get the next frame from the queue
            if wait:
                # Use blocking operation with timeout - brpop expects a list of keys
                brpop_result = self.redis.brpop([queue], timeout=timeout)
                if brpop_result is None:
                    # No frame available within timeout
                    return no_frame_result

                # brpop returns a tuple of (queue_name, data)
                queue_name, msg_data = brpop_result  # type: ignore
            else:
                # Use non-blocking operation
                msg_data = self.redis.rpop(queue)
                if msg_data is None:
                    # No frame available
                    return no_frame_result

            # Parse the message
            try:
                payload = json.loads(msg_data)
                frame_data = payload.get("frame", None)
                metadata = payload.get("metadata", {})
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON message from Redis")
                return no_frame_result

            if not frame_data:
                # No frame data in the message
                return no_frame_result

            try:
                # Decode the frame data from Base64
                binary_data = base64.b64decode(frame_data)

                # Decode the binary data to get the frame
                i_frame, frame = decode(binary_data)
                self.last_frame_id = i_frame

                # Create frame result with the image data
                frame_result: FrameResult = {"frame": frame, "available": True}

                # Add metadata to the result
                if metadata:
                    for key, value in metadata.items():
                        frame_result[key] = value  # type: ignore

                return frame_result

            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to decode frame data: {e}")
                return no_frame_result

        except Exception as e:
            logger.warning(f"Redis receive error: {e}")
            error_result: FrameResult = {"frame": None, "available": False, "error": str(e)}
            return error_result

    def close(self) -> None:
        """Close the Redis connection."""
        if hasattr(self, "redis") and self.redis:
            self.redis.close()
            self.redis = None  # type: ignore


class DataLoaderHandler:
    """Handler for loading image data from various sources.

    This handler provides a unified interface for receiving frames from
    different backends (ImageZMQ or Redis). It automatically selects the
    appropriate backend handler based on configuration.

    The handler is typically the first in a pipeline, providing input data
    for subsequent handlers to process.
    """

    def __init__(self, name: str = "imagezmq", **kwargs: Any) -> None:
        """Initialize the data loader handler.

        Creates a connection to the specified backend for receiving frames.

        Args:
            name: Backend to use ('imagezmq' or 'redis')
            **kwargs: Additional configuration parameters for the backend
        """
        self.name = name.lower()

        # Initialize appropriate handler based on backend
        self.handler: Union[ImageZMQDataLoaderHandler, RedisDataLoaderHandler]
        if self.name == "imagezmq":
            self.handler = ImageZMQDataLoaderHandler(**kwargs)
            logger.info("DataLoaderHandler initialized with ImageZMQ backend")
        elif self.name == "redis":
            self.handler = RedisDataLoaderHandler(**kwargs)
            logger.info("DataLoaderHandler initialized with Redis backend")
        else:
            raise ValueError(f"Unsupported backend: {name}. Use 'imagezmq' or 'redis'.")

    def process(self, **kwargs: Any) -> FrameResult:
        """Process a single data loading step.

        Delegates to the appropriate backend handler to receive a frame.

        Args:
            **kwargs: Additional process parameters passed to the backend handler

        Returns:
            FrameResult containing the loaded frame with key 'frame'
        """
        return self.handler.process(**kwargs)

    def close(self) -> None:
        """Close resources used by the handler."""
        if hasattr(self, "handler"):
            self.handler.close()
