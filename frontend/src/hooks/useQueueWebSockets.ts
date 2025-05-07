import { useEffect, useRef } from "react";
import { createQueueWebSocket } from "@/lib/pipeline";

type QueueData = {
  frame?: string;
  timestamp?: number;
  metadata?: any;
  error?: string;
};

export function useQueueWebSockets(
  pipelineName: string | null,
  queueNames: string[],
  isRunning: boolean,
  onData: (queueName: string, data: QueueData) => void
) {
  // Create a ref to hold websocket connections, keyed by queue name
  const webSocketsRef = useRef<Record<string, WebSocket>>({});
  // Track the current queue names
  const queueNamesRef = useRef<string[]>([]);

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

  // Check if queue names have changed by comparing strings
  const queueNamesString = queueNames.join(",");

  useEffect(() => {
    // Update the queue names ref
    queueNamesRef.current = queueNames;

    // Skip if not running or no pipeline selected
    if (!isRunningRef.current || !pipelineNameRef.current) {
      // Clean up all existing connections
      Object.entries(webSocketsRef.current).forEach(([queueName, ws]) => {
        console.log(
          `Closing connection for queue ${queueName} (pipeline inactive)`
        );
        ws.close();
        delete webSocketsRef.current[queueName];
      });
      return;
    }

    // Track queues to add and remove
    const currentQueues = Object.keys(webSocketsRef.current);
    const queuesToAdd = queueNames.filter((q) => !currentQueues.includes(q));
    const queuesToRemove = currentQueues.filter((q) => !queueNames.includes(q));

    // Close connections for removed queues
    queuesToRemove.forEach((queueName) => {
      if (webSocketsRef.current[queueName]) {
        console.log(
          `Closing connection for queue ${queueName} (queue deselected)`
        );
        webSocketsRef.current[queueName].close();
        delete webSocketsRef.current[queueName];
      }
    });

    // Create connections for new queues
    queuesToAdd.forEach((queueName) => {
      if (pipelineNameRef.current) {
        // Create new WebSocket connection
        console.log(`Creating new connection for queue ${queueName}`);
        const ws = createQueueWebSocket(pipelineNameRef.current, queueName);
        webSocketsRef.current[queueName] = ws;

        // Setup event handlers
        ws.onopen = () => {
          console.log(
            `Queue WebSocket connected: pipeline ${pipelineNameRef.current}, queue ${queueName}`
          );
        };

        ws.onmessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            // Use the ref to the callback to avoid closure issues
            onDataRef.current(queueName, data);
          } catch (err) {
            console.error(`Error parsing message for queue ${queueName}:`, err);
            onDataRef.current(queueName, { error: "Failed to parse data" });
          }
        };

        ws.onerror = (error: Event) => {
          console.error(`WebSocket error for queue ${queueName}:`, error);
          onDataRef.current(queueName, { error: "Connection error" });
        };

        ws.onclose = (event: CloseEvent) => {
          console.log(
            `Queue WebSocket closed: pipeline ${pipelineNameRef.current}, queue ${queueName}`,
            event.code,
            event.reason
          );

          // Remove from our tracking
          if (webSocketsRef.current[queueName] === ws) {
            delete webSocketsRef.current[queueName];
          }
        };
      }
    });

    // Removed cleanup function here
  }, [queueNamesString]);

  // Cleanup all connections on unmount
  useEffect(() => {
    return () => {
      Object.entries(webSocketsRef.current).forEach(([queueName, ws]) => {
        console.log(`Closing connection for queue ${queueName} (cleanup)`);
        ws.close();
      });
      webSocketsRef.current = {};
    };
  }, []);
}
