"use client";

import { useAtom } from "jotai";
import { Card, CardContent } from "@/components/ui/card";
import {
  RefreshCw,
  Settings,
  List,
  Download,
  MoreHorizontal,
} from "lucide-react";
import {
  selectedPipelineAtom,
  pipelineRunningAtom,
  selectedQueueAtom,
  pipelineQueuesAtom,
} from "@/atoms";
import { MultiSelect, Tag, TagsContainer } from "@/components/ui/custom-select";

const VisualizationCard = () => {
  const [selectedPipeline] = useAtom(selectedPipelineAtom);
  const [pipelineRunning] = useAtom(pipelineRunningAtom);
  const [selectedQueues, setSelectedQueues] = useAtom(selectedQueueAtom);
  const [pipelineQueues] = useAtom(pipelineQueuesAtom);

  // Handle queue selection (now supports multi-select)
  const handleQueueSelection = (newSelection: string[]) => {
    setSelectedQueues(newSelection);
  };

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
              options={pipelineQueues}
              onChange={handleQueueSelection}
              disabled={!selectedPipeline || !pipelineRunning}
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

        <div className="flex-1 flex items-start justify-center min-h-[100px]">
          {selectedQueues.length > 0 ? (
            <div className="w-full text-center text-sm text-muted-foreground h-8 mt-2">
              <p className="line-clamp-2">
                Visualizing {selectedQueues.length} queue(s):{" "}
                {selectedQueues.join(", ")}
              </p>
            </div>
          ) : (
            <div className="w-full text-center text-sm text-muted-foreground h-8 mt-2">
              <p>Select queues to visualize data</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default VisualizationCard;
