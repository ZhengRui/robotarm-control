"use client";

import { useState } from "react";
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

  // Only the selected queues need to be local state
  const [selectedQueues, setSelectedQueues] = useState<string[]>([]);

  // Store queue data received from websockets
  const [queueDataMap, setQueueDataMap] = useState<Record<string, QueueData>>(
    {}
  );

  // Derived values directly from pipelineData
  const pipelineRunning = pipelineData?.running || false;
  const pipelineQueues = pipelineData?.available_queues || [];

  // Handle queue selection (now supports multi-select)
  const handleQueueSelection = (newSelection: string[]) => {
    setSelectedQueues(newSelection);
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
    selectedQueues,
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
              selectedValues={selectedQueues}
              options={selectedPipelineName ? pipelineQueues : []}
              onChange={handleQueueSelection}
              disabled={!selectedPipelineName || !pipelineRunning}
              placeholder="Select queues"
            />
          </div>

          {/* Selected queue tags display */}
          {selectedQueues.length > 0 && (
            <TagsContainer>
              {selectedQueues.map((queue) => (
                <Tag
                  key={queue}
                  label={queue}
                  onRemove={() => {
                    setSelectedQueues(
                      selectedQueues.filter((q) => q !== queue)
                    );
                  }}
                />
              ))}
            </TagsContainer>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {selectedPipelineName ? (
            selectedQueues.length > 0 ? (
              <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-4">
                {selectedQueues.map((queueName) => (
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
