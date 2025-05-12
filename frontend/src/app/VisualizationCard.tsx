"use client";

import { useState, useEffect, useRef } from "react";
import { useAtom } from "jotai";
import { Card, CardContent } from "@/components/ui/card";
import {
  RefreshCw,
  Settings,
  List,
  Download,
  MoreHorizontal,
} from "lucide-react";
import { selectedPipelineNameAtom } from "@/atoms";
import { MultiSelect, Tag, TagsContainer } from "@/components/ui/custom-select";
import { useGetPipeline, useQueueWebSockets } from "@/hooks";

type QueueData = {
  frame?: string; // Base64 encoded image
  timestamp?: number;
  metadata?: any;
  error?: string;
};

const VisualizationCard = () => {
  const [selectedPipelineName] = useAtom(selectedPipelineNameAtom);
  const { data: pipelineData } = useGetPipeline(selectedPipelineName, true);
  const prevPipelineNameRef = useRef<string | null>(null);

  // Track selected queues for each pipeline
  // This maintains which queues were selected for each pipeline
  // so when switching between pipelines, the previously selected queues are remembered
  const [pipelineQueueSelections, setPipelineQueueSelections] = useState<
    Record<string, string[]>
  >({});

  // Active queues for the current pipeline
  const [activeQueues, setActiveQueues] = useState<string[]>([]);

  // Store queue data received from websockets
  const [queueDataMap, setQueueDataMap] = useState<Record<string, QueueData>>(
    {}
  );

  // Derived values directly from pipelineData
  const pipelineRunning = pipelineData?.running || false;
  const pipelineQueues = pipelineData?.available_queues || [];

  // Effect to update active queues when the pipeline changes
  useEffect(() => {
    // Only run this effect when the pipeline name actually changes
    if (selectedPipelineName !== prevPipelineNameRef.current) {
      console.log(
        `Pipeline changed from ${prevPipelineNameRef.current} to ${selectedPipelineName}`
      );

      // First save the current queues for the previous pipeline (if any)
      const previousPipeline = prevPipelineNameRef.current;
      if (previousPipeline) {
        // Create a stable local copy of current activeQueues to prevent race conditions
        const currentQueues = [...activeQueues];
        if (currentQueues.length > 0) {
          setPipelineQueueSelections((prev) => {
            // Create a new object to avoid mutation
            const updated = { ...prev };
            updated[previousPipeline] = currentQueues;
            return updated;
          });
        }
      }

      // Clear queue data immediately when switching pipelines
      setQueueDataMap({});

      // Then set the new active queues based on the new pipeline
      if (selectedPipelineName) {
        // Get the saved queues for the new pipeline (if any)
        const savedQueues = pipelineQueueSelections[selectedPipelineName] || [];
        // Update active queues with the saved queues
        setActiveQueues(savedQueues);
      } else {
        setActiveQueues([]);
      }

      // Finally update the reference to the current pipeline
      prevPipelineNameRef.current = selectedPipelineName;
    }
  }, [selectedPipelineName, pipelineQueueSelections]);

  // Separate effect to handle updating queue selections when active queues change
  // This prevents race conditions when switching pipelines
  useEffect(() => {
    // Only save if we have a current pipeline and there was no pipeline change
    if (
      selectedPipelineName &&
      selectedPipelineName === prevPipelineNameRef.current
    ) {
      // Update the saved selections for current pipeline when queues change
      setPipelineQueueSelections((prev) => ({
        ...prev,
        [selectedPipelineName]: [...activeQueues],
      }));
    }
  }, [selectedPipelineName, activeQueues]);

  // Handle queue selection (now supports multi-select)
  const handleQueueSelection = (newSelection: string[]) => {
    setActiveQueues(newSelection);

    // Also update the saved selections for current pipeline
    if (selectedPipelineName) {
      setPipelineQueueSelections((prev) => ({
        ...prev,
        [selectedPipelineName]: newSelection,
      }));
    }
  };

  // Create a callback for handling queue data
  const handleQueueData = (queueName: string, data: QueueData) => {
    setQueueDataMap((prev) => ({
      ...prev,
      [queueName]: data,
    }));
  };

  // Use our imported hook to manage queue connections
  useQueueWebSockets(
    selectedPipelineName,
    activeQueues,
    pipelineRunning,
    handleQueueData
  );

  return (
    <Card className="h-full shadow-sm rounded-md overflow-auto border-0 bg-gray-200 p-0 gap-0">
      <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
        <div className="flex justify-between items-center w-full">
          <h3 className="text-sm font-semibold">Visualization</h3>
          <div className="flex items-center gap-2">
            {/* Icon buttons group */}
            <button
              className="size-6 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              title="Refresh"
            >
              <RefreshCw className="size-4" />
            </button>
            <button
              className="size-6 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              title="Settings"
            >
              <Settings className="size-4" />
            </button>
            <button
              className="size-6 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              title="Download"
            >
              <Download className="size-4" />
            </button>
            <button
              className="size-6 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              title="Logs"
            >
              <List className="size-4" />
            </button>
            <button
              className="size-6 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              title="More options"
            >
              <MoreHorizontal className="size-4" />
            </button>
          </div>
        </div>
      </div>
      <CardContent className="px-5 py-3 flex flex-col h-[calc(100%-3rem)] overflow-y-auto">
        {/* Stream queues section */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-semibold">Stream Queues</h3>
            <MultiSelect
              label="Stream Queues"
              selectedValues={activeQueues}
              options={selectedPipelineName ? pipelineQueues : []}
              onChange={handleQueueSelection}
              disabled={!selectedPipelineName || !pipelineRunning}
              placeholder="Select queues"
            />
          </div>

          {/* Selected queue tags display */}
          {activeQueues.length > 0 && (
            <TagsContainer>
              {activeQueues.map((queue) => (
                <Tag
                  key={queue}
                  label={queue}
                  onRemove={() => {
                    const newQueues = activeQueues.filter((q) => q !== queue);
                    setActiveQueues(newQueues);

                    // Also update saved selections
                    if (selectedPipelineName) {
                      setPipelineQueueSelections((prev) => ({
                        ...prev,
                        [selectedPipelineName]: newQueues,
                      }));
                    }
                  }}
                />
              ))}
            </TagsContainer>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {selectedPipelineName ? (
            activeQueues.length > 0 ? (
              <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4">
                {activeQueues.map((queueName) => (
                  <div
                    key={queueName}
                    className="border rounded-md p-3 bg-white shadow-sm"
                  >
                    <h4 className="text-sm font-medium mb-2">{queueName}</h4>
                    <div className="min-h-[200px] flex items-center justify-center bg-gray-100 rounded-md overflow-hidden relative">
                      {queueDataMap[queueName]?.frame ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={`data:image/jpeg;base64,${queueDataMap[queueName].frame}`}
                          alt={`Queue: ${queueName}`}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "contain",
                          }}
                        />
                      ) : queueDataMap[queueName]?.error ? (
                        <div className="text-sm text-red-500">
                          {queueDataMap[queueName].error}
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          Waiting for data...
                        </div>
                      )}
                    </div>
                    {queueDataMap[queueName]?.metadata && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        <pre className="overflow-x-auto">
                          {JSON.stringify(
                            queueDataMap[queueName].metadata,
                            null,
                            2
                          )}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="w-full text-center text-sm text-muted-foreground h-8 mt-2">
                <p>Select queues to visualize data</p>
              </div>
            )
          ) : (
            <div className="w-full text-center text-sm text-muted-foreground h-8 mt-2">
              <p>Select a pipeline first to enable visualization</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default VisualizationCard;
