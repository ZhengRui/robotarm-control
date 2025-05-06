import { useEffect, useRef } from "react";
import { createQueueWebSocket } from "@/lib/pipeline";

export function useQueueWebSocket(
  pipelineName: string | null,
  queueName: string | null,
  isRunning: boolean,
  onData?: (data: any) => void
) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!pipelineName || !queueName || !isRunning) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const ws = createQueueWebSocket(pipelineName, queueName);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(
        `Queue WebSocket connected: pipeline ${pipelineName}, queue ${queueName}`
      );
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Call the callback with the data
        if (onData) {
          onData(data);
        }
      } catch (err) {
        console.error("Error parsing Queue WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("Queue WebSocket error:", error);
    };

    ws.onclose = (event) => {
      console.log(
        `Queue WebSocket closed: pipeline ${pipelineName}, queue ${queueName}`,
        event.code,
        event.reason
      );

      // Reconnect logic
      if (isRunning && event.code !== 1000 && event.code !== 1005) {
        setTimeout(() => {
          if (isRunning && pipelineName && queueName) {
            // Reconnect
            wsRef.current = createQueueWebSocket(pipelineName, queueName);
          }
        }, 3000);
      }
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [pipelineName, queueName, isRunning, onData]);

  return {
    isConnected: () => wsRef.current?.readyState === WebSocket.OPEN,
  };
}
