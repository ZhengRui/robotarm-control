import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createPipelineWebSocket } from "@/lib/pipeline";
import isEqual from "lodash/isEqual";
import pick from "lodash/pick";

export function usePipelineWebSocket(pipelineName: string | null) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const lastDataRef = useRef<Record<string, any>>({});

  useEffect(() => {
    if (!pipelineName) return;

    const ws = createPipelineWebSocket(pipelineName);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected: pipeline ${pipelineName}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Update the pipeline in the query cache
        if (data) {
          // Check if data has actually changed
          // Extract the keys we care about for comparison (running, state, etc.)
          const relevantKeys = ["running", "state"];
          const currentData = pick(data, relevantKeys);
          const previousData = pick(lastDataRef.current, relevantKeys);

          // Compare using lodash's deep equality check
          if (!isEqual(currentData, previousData)) {
            // Store current data for future comparisons
            lastDataRef.current = { ...data };

            // Update React Query cache to trigger UI updates
            queryClient.invalidateQueries({
              queryKey: ["pipeline", pipelineName],
            });

            queryClient.invalidateQueries({
              queryKey: ["pipelines"],
            });
          }
        }
      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = (event) => {
      console.log(
        `WebSocket closed: pipeline ${pipelineName}`,
        event.code,
        event.reason
      );
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [pipelineName, queryClient]);

  // Return methods to interact with the WebSocket if needed
  return {
    sendMessage: (message: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(message);
        return true;
      }
      return false;
    },
    isConnected: () => wsRef.current?.readyState === WebSocket.OPEN,
  };
}
