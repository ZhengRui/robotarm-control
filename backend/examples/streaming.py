import argparse
import os

from lib.utils.data_stream import DataStream
from lib.utils.logger import get_logger

logger = get_logger("streaming")


def stream(args: argparse.Namespace) -> None:
    """Stream images/videos using DataStream with Redis backend."""
    # Check if write_to directory exists
    if args.write_to:
        assert os.path.exists(args.write_to), f"Write directory {args.write_to} does not exist"

    # Configure Redis connection
    server_config = {
        "addr": args.server,
        "port": args.redis_port,
        "queue": args.redis_queue,
        "max_frames": args.max_frames,
        "time_window": args.time_window,
    }

    # Create DataStream with Redis backend
    stream = DataStream(backend="redis", server_config=server_config)
    logger.info(f"Initialized Redis DataStream to {args.server}:{args.redis_port}")

    try:
        # Run the stream
        stream.run(
            source=args.source,
            max_size=args.max_size,
            keep_size=args.keep_size,
            lossy=args.lossy,
            jpg_quality=args.jpg_quality,
            visualization=args.visualization,
            write_to=args.write_to,
            display_file_name=args.display_file_name,
            autoplay=args.autoplay,
            enable_freeze=args.enable_freeze,
        )
    except KeyboardInterrupt:
        logger.info("Streaming interrupted by user")
    finally:
        # Clean up resources
        stream.close()
        logger.info("Streaming terminated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Streaming Client with Redis")

    # Server configuration
    parser.add_argument("--server", type=str, default="127.0.0.1", help="Redis server address")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis server port")
    parser.add_argument("--redis-queue", type=str, default="camera_frames", help="Redis queue name for frames")
    parser.add_argument(
        "--max-frames", dest="max_frames", type=int, default=100, help="Maximum number of frames to keep in Redis"
    )
    parser.add_argument(
        "--time-window", dest="time_window", type=float, default=5.0, help="Time window in seconds to keep frames"
    )

    # Source configuration
    parser.add_argument("--source", type=str, required=True, help="Image path, video path, or webcam (webcam:0)")

    # Frame processing options
    parser.add_argument("--max_size", type=int, default=800, help="Maximum size of the longer side")
    parser.add_argument("--keep_size", dest="keep_size", action="store_true", help="Keep frames original size")
    parser.add_argument("--jpg_quality", type=int, default=50, help="JPG Quality (1-100), higher is better quality")
    parser.add_argument("--lossless", dest="lossy", action="store_false", help="Send raw frames to server")

    # Visualization options
    parser.add_argument("--visualization", action="store_true", help="Enable visualization window")
    parser.add_argument("--autoplay", action="store_true", help="Auto-advance when source is image directory")
    parser.add_argument("--enable_freeze", action="store_true", help="Allow pausing with spacebar")
    parser.add_argument("--display_file_name", action="store_true", help="Display filename in visualization")

    # Output options
    parser.add_argument("--write_to", type=str, default=None, help="Directory to save visualization frames")

    args = parser.parse_args()
    stream(args)
