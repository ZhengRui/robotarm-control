import { useEffect, useRef, useCallback } from "react";
import { createQueueWebSocket } from "@/lib/pipeline";

type QueueData = {
  frame?: string;
  timestamp?: number;
  metadata?: any;
  error?: string;
};

// Add debounce time to prevent rapid connection/disconnection cycles
const CONNECTION_DEBOUNCE_MS = 250;

export function useQueueWebSockets(
  pipelineName: string | null,
  queueNames: string[],
  isRunning: boolean,
  onData: (queueName: string, data: QueueData) => void
) {
  // Create a ref to hold websocket connections, keyed by queue name
  const webSocketsRef = useRef<Record<string, WebSocket>>({});
  // Track connection attempts to prevent duplicate connections
  const connectionAttemptsRef = useRef<Record<string, boolean>>({});
  // Track the current queue names
  const queueNamesRef = useRef<string[]>([]);
  // Track the last pipeline name to detect changes
  const lastPipelineRef = useRef<string | null>(null);
  // Timer for debounced connection management
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Store references to the dependencies to avoid issues with the dependency array
  const pipelineNameRef = useRef<string | null>(pipelineName);
  const isRunningRef = useRef<boolean>(isRunning);

  // Store memoized onData callback to avoid reconnections
  const onDataRef = useRef(onData);

  // Update refs when dependencies change
  useEffect(() => {
    pipelineNameRef.current = pipelineName;
    isRunningRef.current = isRunning;
    onDataRef.current = onData;
  }, [pipelineName, isRunning, onData]);

  // Safely close a specific websocket connection
  const closeConnection = useCallback(
    (queueName: string, reason: string = "cleanup") => {
      const ws = webSocketsRef.current[queueName];
      if (ws) {
        console.log(`Closing connection for queue ${queueName} (${reason})`);

        // First remove all event handlers to prevent any callbacks
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;

        try {
          // Then close the connection with a normal closure code
          ws.close(1000, reason);
        } catch (e) {
          console.error(`Error closing WebSocket for queue ${queueName}:`, e);
        }

        // Finally remove from our tracking
        delete webSocketsRef.current[queueName];
        delete connectionAttemptsRef.current[queueName];
      }
    },
    []
  );

  // Function to close all existing connections
  const closeAllConnections = useCallback(
    (reason: string = "cleanup") => {
      console.log(`Closing all queue connections (${reason})`);

      // Get a stable copy of the queue names to avoid issues during iteration
      const queues = Object.keys(webSocketsRef.current);

      // Close each connection individually
      queues.forEach((queueName) => {
        closeConnection(queueName, reason);
      });

      // Reset connection attempts tracking
      connectionAttemptsRef.current = {};
    },
    [closeConnection]
  );

  // Clear any pending debounce timer
  const clearDebounceTimer = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
  }, []);

  // Debounced function to update connections
  const debouncedUpdateConnections = useCallback(() => {
    clearDebounceTimer();

    debounceTimerRef.current = setTimeout(() => {
      // Skip if not running or no pipeline selected
      if (!isRunningRef.current || !pipelineNameRef.current) {
        console.log(
          `Skipping queue connections: running=${isRunningRef.current}, pipeline=${pipelineNameRef.current}`
        );
        closeAllConnections("pipeline inactive");
        return;
      }

      const currentPipeline = pipelineNameRef.current;
      const currentQueues = queueNamesRef.current;

      // Track queues to add and remove
      const existingQueues = Object.keys(webSocketsRef.current);
      const queuesToAdd = currentQueues.filter(
        (q) => !existingQueues.includes(q)
      );
      const queuesToRemove = existingQueues.filter(
        (q) => !currentQueues.includes(q)
      );

      // Close connections for removed queues
      queuesToRemove.forEach((queueName) => {
        closeConnection(queueName, "queue deselected");
      });

      // Create connections for new queues
      queuesToAdd.forEach((queueName) => {
        // Skip if we're already attempting to connect this queue
        if (connectionAttemptsRef.current[queueName]) {
          return;
        }

        // Mark as attempting connection
        connectionAttemptsRef.current[queueName] = true;

        try {
          // Create new WebSocket connection
          console.log(
            `Creating new connection for queue ${queueName} in pipeline ${currentPipeline}`
          );
          const ws = createQueueWebSocket(currentPipeline, queueName);
          webSocketsRef.current[queueName] = ws;

          // Setup event handlers
          ws.onopen = () => {
            console.log(
              `Queue WebSocket connected: pipeline ${currentPipeline}, queue ${queueName}`
            );
            // Connection successful, update tracking
            connectionAttemptsRef.current[queueName] = false;
          };

          ws.onmessage = (event: MessageEvent) => {
            try {
              const data = JSON.parse(event.data);
              // Use the ref to the callback to avoid closure issues
              onDataRef.current(queueName, data);
            } catch (err) {
              console.error(
                `Error parsing message for queue ${queueName}:`,
                err
              );
              onDataRef.current(queueName, { error: "Failed to parse data" });
            }
          };

          ws.onerror = (error: Event) => {
            console.error(`WebSocket error for queue ${queueName}:`, error);
            onDataRef.current(queueName, { error: "Connection error" });
            // Reset connection attempt tracking on error
            connectionAttemptsRef.current[queueName] = false;
          };

          ws.onclose = (event: CloseEvent) => {
            console.log(
              `Queue WebSocket closed: pipeline ${currentPipeline}, queue ${queueName}`,
              event.code,
              event.reason
            );

            // Remove from our tracking
            if (webSocketsRef.current[queueName] === ws) {
              delete webSocketsRef.current[queueName];
            }

            // Reset connection attempt tracking on close
            connectionAttemptsRef.current[queueName] = false;
          };
        } catch (error) {
          console.error(
            `Failed to create WebSocket for queue ${queueName}:`,
            error
          );
          // Reset connection attempt tracking on error
          connectionAttemptsRef.current[queueName] = false;
        }
      });
    }, CONNECTION_DEBOUNCE_MS);
  }, [closeAllConnections, closeConnection, clearDebounceTimer]);

  // Handle pipeline changes - close all connections when pipeline changes
  useEffect(() => {
    if (pipelineName !== lastPipelineRef.current) {
      console.log(
        `Pipeline changed from ${lastPipelineRef.current} to ${pipelineName}, resetting all queue connections`
      );

      // Clear any pending connection updates
      clearDebounceTimer();

      // Close all existing connections
      closeAllConnections("pipeline changed");

      // Update the ref
      lastPipelineRef.current = pipelineName;
    }
  }, [pipelineName, closeAllConnections, clearDebounceTimer]);

  // Check if queue names have changed by comparing strings
  const queueNamesString = queueNames.join(",");

  // Main effect to manage websocket connections - triggers on queue changes or running state changes
  useEffect(() => {
    // Update the queue names ref
    queueNamesRef.current = queueNames;

    // Debounce connection updates to prevent rapid connect/disconnect cycles
    debouncedUpdateConnections();

    // Cleanup function
    return () => {
      clearDebounceTimer();
    };
  }, [
    queueNamesString,
    isRunning,
    debouncedUpdateConnections,
    clearDebounceTimer,
  ]);

  // Cleanup all connections on unmount
  useEffect(() => {
    return () => {
      clearDebounceTimer();
      console.log(`Component unmounting, cleaning up all queue connections`);
      closeAllConnections("component unmounted");
    };
  }, [closeAllConnections, clearDebounceTimer]);
}
