import asyncio
import json
import time
from typing import Any, Dict, List, Set

from fastapi import WebSocket

from lib.utils.logger import get_logger

from ..config import config

# Initialize logger
logger = get_logger("websocket_manager")


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    This class handles:
    - Connection management for pipeline status and queue data streams
    - Broadcasting messages to connected clients
    - Connection lifecycle events
    - Redis subscriptions for pipeline data queues
    """

    def __init__(self) -> None:
        # Pipeline status connections
        self.pipeline_connections: Dict[str, Set[WebSocket]] = {}

        # Queue streaming connections
        self.queue_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}

        # Background tasks
        self.tasks: List[asyncio.Task] = []

        # Redis client
        self.redis: Dict[str, Any] = {}

    async def connect_pipeline(self, websocket: WebSocket, pipeline_name: str) -> None:
        """Connect a client to a pipeline's status updates.

        Args:
            websocket: The WebSocket connection
            pipeline_name: Name of the pipeline to monitor
        """
        await websocket.accept()

        # Initialize the set if it doesn't exist
        if pipeline_name not in self.pipeline_connections:
            self.pipeline_connections[pipeline_name] = set()

        # Add the connection
        self.pipeline_connections[pipeline_name].add(websocket)

        # Send connection confirmation
        await self.send_message(
            websocket,
            {
                "type": "connection_status",
                "connected": True,
                "pipeline": pipeline_name,
                "timestamp": time.time(),
            },
        )

        logger.info(f"Client connected to pipeline '{pipeline_name}' status feed")

    async def connect_queue(self, websocket: WebSocket, pipeline_name: str, queue_name: str) -> None:
        """Connect a client to a pipeline's queue data stream.

        Args:
            websocket: The WebSocket connection
            pipeline_name: Name of the pipeline
            queue_name: Name of the queue to stream
        """
        await websocket.accept()

        # Initialize pipeline dict if it doesn't exist
        if pipeline_name not in self.queue_connections:
            self.queue_connections[pipeline_name] = {}

        # Initialize queue set if it doesn't exist
        if queue_name not in self.queue_connections[pipeline_name]:
            self.queue_connections[pipeline_name][queue_name] = set()

            # Start Redis subscription for this queue if it's the first connection
            if len(self.queue_connections[pipeline_name][queue_name]) == 0:
                await self._ensure_redis_subscription(pipeline_name, queue_name)

        # Add the connection
        self.queue_connections[pipeline_name][queue_name].add(websocket)

        # Send connection confirmation
        await self.send_message(
            websocket,
            {
                "type": "connection_status",
                "connected": True,
                "pipeline": pipeline_name,
                "queue": queue_name,
                "timestamp": time.time(),
            },
        )

        logger.info(f"Client connected to pipeline '{pipeline_name}' queue '{queue_name}' data feed")

    async def disconnect_pipeline(self, websocket: WebSocket, pipeline_name: str) -> None:
        """Disconnect a client from a pipeline's status updates.

        Args:
            websocket: The WebSocket connection
            pipeline_name: Name of the pipeline
        """
        # Remove the connection
        if pipeline_name in self.pipeline_connections:
            try:
                self.pipeline_connections[pipeline_name].remove(websocket)
                logger.info(f"Client disconnected from pipeline '{pipeline_name}' status feed")

                # Clean up if no connections left
                if not self.pipeline_connections[pipeline_name]:
                    del self.pipeline_connections[pipeline_name]
            except KeyError:
                pass

    async def disconnect_queue(self, websocket: WebSocket, pipeline_name: str, queue_name: str) -> None:
        """Disconnect a client from a pipeline's queue data stream.

        Args:
            websocket: The WebSocket connection
            pipeline_name: Name of the pipeline
            queue_name: Name of the queue
        """
        # Remove the connection
        try:
            if pipeline_name in self.queue_connections:
                if queue_name in self.queue_connections[pipeline_name]:
                    self.queue_connections[pipeline_name][queue_name].remove(websocket)
                    logger.info(f"Client disconnected from pipeline '{pipeline_name}' queue '{queue_name}' data feed")

                    # Clean up if no connections left for this queue
                    if not self.queue_connections[pipeline_name][queue_name]:
                        del self.queue_connections[pipeline_name][queue_name]

                    # Clean up if no queues left for this pipeline
                    if not self.queue_connections[pipeline_name]:
                        del self.queue_connections[pipeline_name]
        except KeyError:
            pass

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send a message to a specific WebSocket client.

        Args:
            websocket: The WebSocket connection
            message: The message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

    async def broadcast_pipeline_update(self, pipeline_name: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all clients connected to a pipeline's status feed.

        Args:
            pipeline_name: Name of the pipeline
            message: The message to broadcast
        """
        if pipeline_name in self.pipeline_connections:
            disconnected = set()

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = time.time()

            # Send to all connected clients
            for connection in self.pipeline_connections[pipeline_name]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client, will disconnect: {e}")
                    disconnected.add(connection)

            # Remove disconnected clients
            for connection in disconnected:
                await self.disconnect_pipeline(connection, pipeline_name)

    async def broadcast_queue_update(self, pipeline_name: str, queue_name: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all clients connected to a pipeline's queue data feed.

        Args:
            pipeline_name: Name of the pipeline
            queue_name: Name of the queue
            message: The message to broadcast
        """
        if pipeline_name in self.queue_connections and queue_name in self.queue_connections[pipeline_name]:
            disconnected = set()

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = time.time()

            # Send to all connected clients
            for connection in self.queue_connections[pipeline_name][queue_name]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client, will disconnect: {e}")
                    disconnected.add(connection)

            # Remove disconnected clients
            for connection in disconnected:
                await self.disconnect_queue(connection, pipeline_name, queue_name)

    async def _ensure_redis_client(self, redis_config: Dict[str, Any]) -> Any:
        """Ensure Redis client is initialized with configuration from config.py.

        Args:
            redis_config: Redis configuration from config.py

        Returns:
            Redis client instance
        """
        try:
            import aioredis

            # Extract config values with defaults
            host = redis_config.get("host", "localhost")
            port = redis_config.get("port", 6379)
            db = redis_config.get("db", 0)
            password = redis_config.get("password", None)

            # Build connection URL
            redis_url = "redis://"
            if password:
                redis_url += f":{password}@"
            redis_url += f"{host}:{port}/{db}"

            # Connect to Redis
            redis_client = await aioredis.from_url(redis_url)
            logger.info(f"Connected to Redis at {host}:{port}/{db}")

            return redis_client
        except ImportError:
            logger.error("aioredis package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _ensure_redis_subscription(self, pipeline_name: str, queue_name: str) -> None:
        """Ensure there is a Redis subscription for the given pipeline queue.

        Args:
            pipeline_name: Name of the pipeline
            queue_name: Name of the queue
        """
        redis_config = config.get(pipeline_name, {}).get("redis", {})

        # Ensure Redis client is initialized
        if pipeline_name not in self.redis:
            self.redis[pipeline_name] = await self._ensure_redis_client(redis_config)

        redis_client = self.redis[pipeline_name]

        # Start background task for pub/sub subscription
        channel = f"pipeline:{pipeline_name}:queue:{queue_name}"

        # Create a task for pub/sub subscription
        pubsub_task = asyncio.create_task(
            self._subscribe_to_redis_channel(pipeline_name, queue_name, channel, redis_client)
        )
        self.tasks.append(pubsub_task)

    async def _subscribe_to_redis_channel(
        self,
        pipeline_name: str,
        queue_name: str,
        channel: str,
        redis_client: Any,
    ) -> None:
        """Subscribe to a Redis pub/sub channel and forward messages to WebSocket clients.

        Args:
            pipeline_name: Name of the pipeline
            queue_name: Name of the queue
            channel: Redis channel name
            redis_client: Redis client to use for this subscription
        """
        try:
            # New API for pubsub in aioredis 2.0+
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel)

            logger.info(f"Subscribed to Redis channel: {channel}")

            # Process messages
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None and message["type"] == "message":
                    try:
                        msg = message["data"].decode("utf-8")
                        data = json.loads(msg)

                        # Ensure type field is present
                        if "type" not in data:
                            data["type"] = "pubsub_message"

                        # Add pipeline and queue info if not present
                        if "pipeline" not in data:
                            data["pipeline"] = pipeline_name
                        if "queue" not in data:
                            data["queue"] = queue_name

                        # Broadcast to connected clients
                        await self.broadcast_queue_update(pipeline_name, queue_name, data)
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from Redis channel {channel}")
                    except Exception as e:
                        logger.error(f"Error processing message from Redis: {e}")

                # Small sleep to avoid busy waiting
                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            # Handle task cancellation
            logger.info(f"Redis subscription task for {channel} cancelled")
            await pubsub.unsubscribe(channel)
            raise
        except Exception as e:
            logger.error(f"Error in Redis subscription: {e}")
            # Try to reconnect after a delay
            await asyncio.sleep(5)
            pubsub_task = asyncio.create_task(
                self._subscribe_to_redis_channel(pipeline_name, queue_name, channel, redis_client)
            )
            self.tasks.append(pubsub_task)

    async def start_background_tasks(self) -> None:
        """Start background tasks for data streaming.

        This method is called during API startup to initialize
        background tasks for Redis subscription.
        """
        # This method is called from the API startup event
        # Any existing connections will have their subscription tasks started on connect
        logger.info("WebSocket manager background tasks started")

    async def close_pipeline_connections(self, pipeline_name: str) -> None:
        """Close all WebSocket connections for a specific pipeline.

        This should be called when a pipeline is stopped to ensure all clients
        are notified and disconnected.

        Args:
            pipeline_name: Name of the pipeline that was stopped
        """
        logger.info(f"Closing all connections for stopped pipeline '{pipeline_name}'")

        # Close pipeline status connections
        if pipeline_name in self.pipeline_connections:
            disconnected_clients = set()

            # Notify all clients
            for websocket in self.pipeline_connections[pipeline_name]:
                try:
                    # Send pipeline stopped notification
                    await self.send_message(
                        websocket,
                        {
                            "type": "pipeline_stopped",
                            "pipeline": pipeline_name,
                            "message": "Pipeline has been stopped",
                            "timestamp": time.time(),
                        },
                    )
                    # Close the connection
                    await websocket.close(code=1000, reason="Pipeline stopped")
                    disconnected_clients.add(websocket)
                except Exception as e:
                    logger.error(f"Error closing connection for pipeline '{pipeline_name}': {e}")
                    disconnected_clients.add(websocket)

            # Remove all disconnected clients
            for websocket in disconnected_clients:
                await self.disconnect_pipeline(websocket, pipeline_name)

        # Close queue data connections
        if pipeline_name in self.queue_connections:
            for queue_name in list(self.queue_connections[pipeline_name].keys()):
                connections = self.queue_connections[pipeline_name][queue_name]
                disconnected_clients = set()

                # Notify all clients
                for websocket in connections:
                    try:
                        # Send pipeline stopped notification
                        await self.send_message(
                            websocket,
                            {
                                "type": "pipeline_stopped",
                                "pipeline": pipeline_name,
                                "queue": queue_name,
                                "message": "Pipeline has been stopped",
                                "timestamp": time.time(),
                            },
                        )
                        # Close the connection
                        await websocket.close(code=1000, reason="Pipeline stopped")
                        disconnected_clients.add(websocket)
                    except Exception as e:
                        logger.error(
                            f"Error closing connection for pipeline '{pipeline_name}' queue '{queue_name}': {e}"
                        )
                        disconnected_clients.add(websocket)

                # Remove all disconnected clients
                for websocket in disconnected_clients:
                    await self.disconnect_queue(websocket, pipeline_name, queue_name)

        # Close Redis connection if exists
        if pipeline_name in self.redis:
            try:
                await self.redis[pipeline_name].close()
                del self.redis[pipeline_name]
                logger.info(f"Closed Redis connection for stopped pipeline '{pipeline_name}'")
            except Exception as e:
                logger.error(f"Error closing Redis connection for pipeline '{pipeline_name}': {e}")

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        # Cancel all background tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Close all Redis connections
        for pipeline_name, redis_client in self.redis.items():
            try:
                await redis_client.close()
                logger.info(f"Closed Redis connection for pipeline '{pipeline_name}'")
            except Exception as e:
                logger.error(f"Error closing Redis connection for pipeline '{pipeline_name}': {e}")

        # Clear all connections
        self.pipeline_connections.clear()
        self.queue_connections.clear()
        self.redis.clear()

        logger.info("WebSocket manager resources cleaned up")


# Global connection manager instance
manager = ConnectionManager()
