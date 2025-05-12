import { useEffect, useRef, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createPipelineWebSocket } from "@/lib/pipeline";
import isEqual from "lodash/isEqual";
import pick from "lodash/pick";

// Configuration for reconnection logic
const BASE_RETRY_MS = 1000;
const MAX_RETRY_MS = 30000;
const MAX_RETRIES = 10;
const CONNECT_DEBOUNCE_MS = 300; // Debounce time for connection attempts

export function usePipelineWebSocket(pipelineName: string | null) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const lastDataRef = useRef<Record<string, any>>({});
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastPipelineNameRef = useRef<string | null>(null);
  const retryCountRef = useRef(0);
  const [connectionStatus, setConnectionStatus] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("disconnected");
  const isConnectingRef = useRef(false);

  // Function to connect or reconnect to WebSocket
  const connectToWebSocket = useCallback(() => {
    if (!pipelineName) return;

    // Prevent duplicate connection attempts
    if (isConnectingRef.current) {
      console.log(
        `Already attempting to connect to pipeline ${pipelineName}, skipping duplicate request`
      );
      return;
    }

    isConnectingRef.current = true;

    // Clean up existing connection if any
    if (wsRef.current) {
      const currentWs = wsRef.current;
      // Store the old reference but don't null out wsRef.current yet
      // This prevents race conditions during cleanup

      console.log(
        `Closing existing connection to pipeline ${lastPipelineNameRef.current}`
      );

      // Remove event listeners to prevent duplicate handlers
      currentWs.onopen = null;
      currentWs.onmessage = null;
      currentWs.onerror = null;
      currentWs.onclose = null;

      // Close the connection
      currentWs.close();
      wsRef.current = null;
    }

    setConnectionStatus("connecting");
    console.log(
      `Creating new WebSocket connection to pipeline ${pipelineName}`
    );

    // Update the last pipeline name reference
    lastPipelineNameRef.current = pipelineName;

    const ws = createPipelineWebSocket(pipelineName);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected: pipeline ${pipelineName}`);
      setConnectionStatus("connected");
      retryCountRef.current = 0; // Reset retry count on successful connection
      isConnectingRef.current = false;
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
      setConnectionStatus("error");
      isConnectingRef.current = false;
    };

    ws.onclose = (event) => {
      console.log(
        `WebSocket closed: pipeline ${pipelineName}`,
        event.code,
        event.reason
      );

      // Only change status and schedule reconnect if this is still the current connection
      // This prevents issues when rapidly switching between pipelines
      if (lastPipelineNameRef.current === pipelineName) {
        setConnectionStatus("disconnected");
        isConnectingRef.current = false;
        // Only schedule reconnect if this wasn't an intentional close
        if (event.code !== 1000) {
          scheduleReconnect();
        }
      }
    };
  }, [pipelineName, queryClient]);

  // Schedule reconnection with exponential backoff
  const scheduleReconnect = useCallback(() => {
    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Don't reconnect if there's no pipeline name or if we've gone over retry limit
    if (!lastPipelineNameRef.current || retryCountRef.current >= MAX_RETRIES) {
      if (retryCountRef.current >= MAX_RETRIES) {
        console.log(
          `Exceeded maximum retry attempts (${MAX_RETRIES}) for pipeline ${lastPipelineNameRef.current}`
        );
      }
      return;
    }

    // Calculate delay with exponential backoff + jitter
    const delay = Math.min(
      MAX_RETRY_MS,
      BASE_RETRY_MS *
        Math.pow(2, retryCountRef.current) *
        (0.9 + Math.random() * 0.2)
    );

    console.log(
      `Scheduling reconnect attempt ${retryCountRef.current + 1} in ${Math.round(delay)}ms for pipeline ${lastPipelineNameRef.current}`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      retryCountRef.current += 1;
      connectToWebSocket();
    }, delay);
  }, [connectToWebSocket]);

  // Manual reconnect function that resets the retry counter
  const reconnect = useCallback(() => {
    console.log(`Manual reconnect requested for pipeline ${pipelineName}`);

    // Clear any existing timers
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
    }

    retryCountRef.current = 0;
    isConnectingRef.current = false; // Reset connecting flag for manual reconnects

    // Debounce connection attempts to prevent rapid reconnects
    connectTimeoutRef.current = setTimeout(() => {
      connectToWebSocket();
    }, CONNECT_DEBOUNCE_MS);
  }, [connectToWebSocket, pipelineName]);

  // Initial connection and cleanup on unmount or pipeline change
  useEffect(() => {
    // Clear any existing connect timer to prevent race conditions
    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
    }

    // Only connect if we have a pipeline name
    if (pipelineName) {
      // Debounce connection to prevent rapid reconnects during navigation
      connectTimeoutRef.current = setTimeout(() => {
        connectToWebSocket();
      }, CONNECT_DEBOUNCE_MS);
    } else {
      // Reset state when no pipeline is selected
      setConnectionStatus("disconnected");
      lastPipelineNameRef.current = null;
    }

    return () => {
      // Clean up all timers and connections when component unmounts or pipeline changes
      if (wsRef.current) {
        const currentWs = wsRef.current;
        // Remove all event handlers to prevent duplicate events
        currentWs.onopen = null;
        currentWs.onmessage = null;
        currentWs.onerror = null;
        currentWs.onclose = null;

        // Close the connection and clear the reference
        console.log(
          `Cleaning up connection to pipeline ${lastPipelineNameRef.current}`
        );
        currentWs.close();
        wsRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (connectTimeoutRef.current) {
        clearTimeout(connectTimeoutRef.current);
        connectTimeoutRef.current = null;
      }

      // Reset connecting flag during cleanup
      isConnectingRef.current = false;
    };
  }, [pipelineName, connectToWebSocket]);

  // Return methods to interact with the WebSocket
  return {
    sendMessage: (message: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(message);
        return true;
      }
      return false;
    },
    isConnected: () => wsRef.current?.readyState === WebSocket.OPEN,
    connectionStatus,
    reconnect,
  };
}
