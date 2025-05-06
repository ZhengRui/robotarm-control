import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { createPipelineWebSocket } from "@/lib/pipeline";
import { pipelinesAtom } from "@/atoms";
import { Pipeline } from "@/interfaces";

export function usePipelineWebSocket(
  pipelineName: string | null,
  isRunning: boolean
) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const [, setPipelines] = useAtom(pipelinesAtom);

  useEffect(() => {
    if (!pipelineName || !isRunning) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

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
          // Update in react-query cache
          queryClient.setQueryData<Pipeline>(
            ["pipeline", pipelineName],
            (oldData) => {
              if (!oldData) return data;
              return { ...oldData, ...data };
            }
          );

          // Update in pipelines atom
          setPipelines((currentPipelines) =>
            currentPipelines.map((p) =>
              p.name === pipelineName ? { ...p, ...data } : p
            )
          );
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

      // Reconnect logic
      if (isRunning && event.code !== 1000 && event.code !== 1005) {
        setTimeout(() => {
          if (isRunning && pipelineName) {
            // Reconnect
            wsRef.current = createPipelineWebSocket(pipelineName);
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
  }, [pipelineName, isRunning, queryClient, setPipelines]);

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
