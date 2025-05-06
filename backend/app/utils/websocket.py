import asyncio
import time
from typing import Any, Dict, List, Set

from fastapi import WebSocket

from lib.utils.logger import get_logger

# Initialize logger
logger = get_logger("websocket_manager")


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    This class handles:
    - Connection management for pipeline status and queue data streams
    - Broadcasting messages to connected clients
    - Connection lifecycle events
    """

    def __init__(self) -> None:
        # Pipeline status connections
        self.pipeline_connections: Dict[str, Set[WebSocket]] = {}

        # Queue streaming connections
        self.queue_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}

        # Background tasks
        self.tasks: List[asyncio.Task] = []

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
            {"type": "connection_status", "connected": True, "pipeline": pipeline_name, "timestamp": time.time()},
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

    def start_background_tasks(self) -> None:
        """Start background tasks for data streaming."""
        # Will be implemented when connecting to Redis
        pass

    def cleanup(self) -> None:
        """Cleanup all resources."""
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Clear all connections
        self.pipeline_connections.clear()
        self.queue_connections.clear()


# Global connection manager instance
manager = ConnectionManager()
