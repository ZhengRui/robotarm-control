import base64
import json
import os
import socket
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Union

import cv2

from .data_factory import DataFactory, decode
from .logger import get_logger

logger = get_logger("data_stream")


class DataStreamClient(ABC):
    """Abstract base class for data stream clients."""

    @abstractmethod
    def send_frame(self, msg: bytes, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
        """Send a frame to the server.

        Args:
            msg: Encoded frame message
            metadata: Additional metadata

        Returns:
            Tuple containing (result, success_status)
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the client connection."""
        pass


class ImageZMQDataStreamClient(DataStreamClient):
    """Client for sending frames using ImageZMQ."""

    def __init__(self, server_config: Dict[str, Any]):
        """Initialize ImageZMQ client.

        Args:
            server_config: Server configuration
        """
        try:
            import imagezmq

            addr = server_config.get("addr", "127.0.0.1")
            port = server_config.get("port", 5555)

            self.client = imagezmq.ImageSender(connect_to=f"tcp://{addr}:{port}")
            self.rpi_name = socket.gethostname()
            logger.info(f"ImageZMQ client connected to {addr}:{port}")
        except ImportError:
            logger.error("ImageZMQ not available. Please ensure imagezmq is installed.")
            raise

    def send_frame(self, msg: bytes, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
        """Send a frame using ImageZMQ.

        Args:
            msg: Encoded frame message
            metadata: Additional metadata (not used in ImageZMQ)

        Returns:
            Tuple containing (response_data, success_status)
        """
        try:
            reply = self.client.send_jpg(self.rpi_name, msg)
            response = json.loads(reply)
            return response, True
        except Exception as err:
            logger.warning(f"ImageZMQ send error: {err}")
            return None, False

    def close(self) -> None:
        """Close the ImageZMQ connection."""
        # ImageZMQ doesn't have an explicit close method
        self.client = None


class RedisDataStreamClient(DataStreamClient):
    """Client for sending frames using Redis."""

    def __init__(self, server_config: Dict[str, Any]):
        """Initialize Redis client.

        Args:
            server_config: Server configuration
        """
        try:
            import redis
            from redis import Redis

            self.host = server_config.get("addr", "127.0.0.1")
            self.port = server_config.get("port", 6379)
            self.queue = server_config.get("queue", "camera_frames")
            self.max_frames = server_config.get("max_frames", None)
            self.time_window = server_config.get("time_window", None)  # Time window in seconds
            self.rpi_name = socket.gethostname()

            self.redis: Optional[Redis] = redis.Redis(
                host=self.host,
                port=self.port,
                db=server_config.get("db", 0),
                password=server_config.get("password", None),
            )

            # Test connection
            self.redis.ping()
            logger.info(f"Redis client connected to {self.host}:{self.port}")

        except ImportError:
            logger.error("Redis client not available. Please ensure redis-py is installed.")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {self.host}:{self.port}: {e}")
            raise

    def send_frame(self, msg: bytes, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Any, bool]:
        """Send a frame using Redis.

        Args:
            msg: Encoded frame message
            metadata: Additional metadata

        Returns:
            Tuple containing (queue_length, success_status)
        """
        try:
            # Convert binary data to Base64 for JSON compatibility
            msg_base64_encoded = base64.b64encode(msg).decode("ascii")

            # Prepare message payload
            payload = {
                "timestamp": time.time(),
                "frame": msg_base64_encoded,
            }

            # Add metadata if provided
            if metadata:
                payload["metadata"] = metadata

            # Send to Redis
            if self.redis:
                queue_length = self.redis.lpush(self.queue, json.dumps(payload))

                # If max_frames is set, trim the list to keep only the latest frames
                if self.max_frames and queue_length > self.max_frames:
                    self.redis.ltrim(self.queue, 0, self.max_frames - 1)

                # If time_window is set, remove frames outside the time window
                if self.time_window:
                    current_time = time.time()
                    cutoff_time = current_time - self.time_window

                    # Get the oldest frame (rightmost in the list)
                    while True:
                        oldest_frame = self.redis.lindex(self.queue, -1)
                        if not oldest_frame:
                            break

                        # Handle different types that might be returned by lindex
                        if isinstance(oldest_frame, bytes):
                            oldest_frame_str = oldest_frame.decode("utf-8")
                        else:
                            oldest_frame_str = str(oldest_frame)

                        oldest_frame_data = json.loads(oldest_frame_str)
                        if oldest_frame_data.get("timestamp", 0) < cutoff_time:
                            # Remove this outdated frame
                            self.redis.rpop(self.queue)
                        else:
                            # Found a frame within the time window, stop checking
                            break

                return queue_length, True
            return None, False

        except Exception as e:
            logger.warning(f"Redis send error: {e}")
            return None, False

    def close(self) -> None:
        """Close the Redis connection."""
        if hasattr(self, "redis") and self.redis:
            self.redis.close()
            self.redis = None


class DataStream:
    """Stream data from a source to a server using either imagezmq or redis backend.

    This class provides a flexible streaming interface that can use either
    ImageZMQ or Redis as a backend for transmitting image/video data.
    """

    def __init__(
        self,
        backend: str = "imagezmq",
        server_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the data stream with backend configuration.

        Args:
            backend: The backend to use ('imagezmq' or 'redis')
            server_config: Server connection parameters
                For imagezmq: {'addr': '127.0.0.1', 'port': 5555}
                For redis: {'addr': '127.0.0.1', 'port': 6379, 'queue': 'camera_frames',
                           'max_frames': 100, 'time_window': 5.0}
        """
        self.backend = backend.lower()

        # Set default server config if not provided
        if server_config is None:
            if self.backend == "imagezmq":
                server_config = {"addr": "127.0.0.1", "port": 5555}
            else:  # redis
                server_config = {
                    "addr": "127.0.0.1",
                    "port": 6379,
                    "queue": "camera_frames",
                    "max_frames": 100,
                    "time_window": 5.0,  # Default 5 seconds
                }

        self.server_config = server_config

        # Initialize appropriate client based on backend
        self.client: Union[ImageZMQDataStreamClient, RedisDataStreamClient]
        if self.backend == "imagezmq":
            self.client = ImageZMQDataStreamClient(server_config)
        elif self.backend == "redis":
            self.client = RedisDataStreamClient(server_config)
        else:
            raise ValueError(f"Unsupported backend: {backend}. Use 'imagezmq' or 'redis'.")

        self.rpi_name = self.client.rpi_name

        self._wnd_resized = False

        logger.info(f"DataStream initialized with {self.backend} backend")

    def run(
        self,
        source: str,
        max_size: int = 800,
        keep_size: bool = False,
        lossy: bool = True,
        jpg_quality: int = 50,
        visualization: bool = False,
        write_to: Optional[str] = None,
        display_file_name: bool = False,
        autoplay: bool = False,
        enable_freeze: bool = False,
    ) -> None:
        """Stream data from the source to the server.

        Args:
            source: Source path (file, directory, webcam id)
            max_size: Maximum size of the longer dimension
            keep_size: Whether to keep original frame size
            lossy: Whether to use lossy compression
            jpg_quality: JPEG quality for compression
            visualization: Whether to show visualization window
            write_to: Directory to write frames to
            display_file_name: Whether to display file name on frames
            autoplay: Whether to autoplay image sources
            enable_freeze: Whether to enable freezing with spacebar
        """
        # Initialize data factory
        factory = DataFactory(source)

        # Setup visualization if enabled
        fps, i_frame, d_frame = 0.0, 0, 10
        t0 = time.time()

        if visualization:
            t_wait = 0 if (factory.type == "image" and not autoplay) else 10
            cv2.namedWindow("DataStream", cv2.WINDOW_GUI_NORMAL)
            self._wnd_resized = False
            is_paused = False

        # Process frames
        for msg in factory.pipeline(keep_size=keep_size, max_size=max_size, lossy=lossy, jpg_quality=jpg_quality):
            try:
                # Send frame with metadata
                metadata = {"i_frame": i_frame, "source": source, "rpi_name": self.rpi_name}
                result, success = self.client.send_frame(msg, metadata)

                if not success:
                    logger.warning("Failed to send frame")
                elif i_frame % 100 == 0:  # Log every 100 frames
                    logger.debug(f"{i_frame} Frame sent, fps: {fps:3.1f}")

            except Exception as err:
                logger.warning(f"Communication Error: {err}")

            i_frame += 1
            if not i_frame % d_frame:
                t1 = time.time()
                fps = d_frame / (t1 - t0)
                t0 = t1

            # Handle visualization if enabled
            if visualization:
                self._handle_visualization(
                    msg, factory, i_frame, fps, source, display_file_name, write_to, autoplay, enable_freeze, is_paused
                )

                # Check for exit
                key = cv2.waitKey(0 if enable_freeze and is_paused else t_wait) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord(" ") and enable_freeze:
                    is_paused = not is_paused
                    logger.info("Stream " + ("paused" if is_paused else "resumed"))

        # Cleanup
        if visualization:
            cv2.destroyAllWindows()

    def _handle_visualization(
        self,
        msg: bytes,
        factory: DataFactory,
        i_frame: int,
        fps: float,
        source: str,
        display_file_name: bool,
        write_to: Optional[str],
        autoplay: bool,
        enable_freeze: bool,
        is_paused: bool,
    ) -> None:
        """Handle visualization of frames.

        Args:
            msg: Encoded message
            factory: DataFactory instance
            i_frame: Current frame index
            fps: Current FPS
            source: Source path
            display_file_name: Whether to display file name
            write_to: Directory to write frames to
            autoplay: Whether to autoplay
            enable_freeze: Whether to enable freezing
            is_paused: Current pause state
        """
        _, im_readonly = decode(msg)
        im = im_readonly.copy()
        h, w = im.shape[:2]

        # Add text overlay
        label = self.rpi_name
        if display_file_name and isinstance(factory.source, list):
            source_path = factory.source[i_frame - 1]
            file_name = source_path.split(source)
            label = file_name[1]

        cv2.putText(
            im,
            f"{fps:3.1f}fps {h}x{w} {label}",
            (10, 25),
            cv2.FONT_HERSHEY_DUPLEX,
            0.4,
            (0, 255, 255),
            1,
        )

        # Write frame to file if specified
        if write_to:
            if factory.type == "image" and isinstance(factory.source, list):
                savename = os.path.basename(factory.source[i_frame - 1])
            else:
                savename = f"{i_frame - 1:04d}.jpg"

            cv2.imwrite(
                os.path.join(write_to, savename),
                im,
                [int(cv2.IMWRITE_JPEG_QUALITY), 100],
            )

        # Display frame
        cv2.imshow("DataStream", im)

        # Resize window if needed
        if factory.type == "image" or not self._wnd_resized:
            cv2.resizeWindow("DataStream", (w, h))
            self._wnd_resized = True

    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, "client"):
            self.client.close()
