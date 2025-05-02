"use client";

import { useState, useLayoutEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import {
  Loader2,
  Settings,
  List,
  RefreshCw,
  Download,
  MoreHorizontal,
} from "lucide-react";

export default function Dashboard() {
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(
    "YahboomPickAndPlace"
  );
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Status state, will be updated from API in the future
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [currentStatus, setCurrentStatus] = useState("PICKING");

  // Signal state to track selected signal
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);

  // Queue state to track selected queue
  const [selectedQueue, setSelectedQueue] = useState<string | null>(null);

  // Placeholder data - replace with actual API calls later
  const availablePipelines = ["YahboomPickAndPlace", "OtherPipeline"];
  const pipelineStatuses = [
    "IDLE",
    "RUNNING",
    "CALIBRATING",
    "PICKING",
    "PLACING",
  ];
  const pipelineSignals = ["STOP", "PAUSE", "RESUME", "RESET", "CALIBRATE"];
  const pipelineQueues = [
    "CAMERA",
    "PROCESS",
    "DETECTION",
    "ARM_STATE",
    "ROBOT_CONTROL",
  ];

  const MIN_SIZE_IN_PIXELS = 400;
  const MAX_SIZE_IN_PIXELS = 500;
  const [minSize, setMinSize] = useState(24);
  const [maxSize, setMaxSize] = useState(36);

  // First effect just for turning off loading
  useLayoutEffect(() => {
    const screenWidth = window.innerWidth;
    setMinSize((MIN_SIZE_IN_PIXELS / screenWidth) * 100);
    setMaxSize((MAX_SIZE_IN_PIXELS / screenWidth) * 100);
    setIsLoading(false);
  }, []);

  // Handle toggle change for pipeline running state
  const handleToggleChange = (checked: boolean) => {
    setPipelineRunning(checked);
    console.log("Toggle changed to:", checked);
  };

  // Handle signal selection
  const handleSignalClick = (signal: string) => {
    setSelectedSignal(signal);
    console.log("Signal selected:", signal);
    // Here you would send the signal to the backend
  };

  // Handle queue selection
  const handleQueueClick = (queue: string) => {
    setSelectedQueue(queue);
    console.log("Queue selected:", queue);
    // Here you would connect to the queue for visualization
  };

  // If still loading, show a spinning loader using Lucide React
  if (isLoading) {
    return (
      <div className="h-screen w-full bg-background flex items-center justify-center">
        <Loader2
          className="h-8 w-8 text-primary animate-spin"
          strokeWidth={1.5}
        />
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-background transition-all duration-200">
      <div className="flex justify-center py-4 border-b border-border/30">
        <h1 className="text-2xl font-bold">Modulus Robot Control</h1>
      </div>
      <PanelGroup
        direction="horizontal"
        className="h-[calc(100%-4rem)]"
        autoSaveId="dashboard-layout-horizontal"
        id="dashboard-layout-horizontal"
      >
        {/* Left Panel */}
        <Panel
          defaultSize={minSize}
          minSize={minSize}
          maxSize={maxSize}
          className="p-.5 pl-3 pt-3 pb-3 flex flex-col overflow-hidden"
          order={1}
        >
          <PanelGroup
            direction="vertical"
            className="flex-1"
            autoSaveId="dashboard-layout-vertical"
          >
            {/* Pipeline Selection with integrated toggle */}
            <Panel defaultSize={30} minSize={20} className="flex flex-col">
              <Card className="shadow-sm rounded-md p-0 flex-1 overflow-auto border-0 bg-gray-200 gap-0">
                <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
                  <div className="flex justify-between items-center gap-3 w-full">
                    <Select
                      onValueChange={(value) => {
                        setSelectedPipeline(value);
                      }}
                      value={selectedPipeline ?? ""}
                    >
                      <SelectTrigger className="text-sm font-semibold !h-6 !focus:ring-0 !focus:ring-offset-0 shadow-none px-0 border-0 w-auto min-w-[80px]">
                        <SelectValue placeholder="Select Pipeline" />
                      </SelectTrigger>
                      <SelectContent>
                        {availablePipelines.map((pipeline) => (
                          <SelectItem
                            key={pipeline}
                            value={pipeline}
                            className="text-sm"
                          >
                            {pipeline}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <div className="flex items-center gap-2">
                      {/* Show both labels on md screens and up */}
                      <span
                        className={cn(
                          "text-[10px] font-semibold hidden md:inline",
                          pipelineRunning
                            ? "text-muted-foreground"
                            : "text-primary"
                        )}
                      >
                        Off
                      </span>
                      <Switch
                        checked={pipelineRunning}
                        onCheckedChange={(checked) => {
                          console.log("Switch clicked, new value:", checked);
                          handleToggleChange(checked);
                        }}
                        id="pipeline-switch"
                      />
                      {/* On larger screens, show the right label conditionally */}
                      <span
                        className={cn(
                          "text-[10px] font-semibold hidden md:inline",
                          pipelineRunning
                            ? "text-primary"
                            : "text-muted-foreground"
                        )}
                      >
                        On
                      </span>

                      {/* On smaller screens, show just one label based on state */}
                      <span
                        className={cn(
                          "text-[10px] font-semibold md:hidden",
                          pipelineRunning
                            ? "text-primary"
                            : "text-muted-foreground"
                        )}
                      >
                        {pipelineRunning ? "On" : "Off"}
                      </span>
                    </div>
                  </div>
                </div>
                <CardContent className="px-5 py-3 overflow-y-auto h-full">
                  <h2 className="text-sm font-semibold mb-2">Status</h2>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {pipelineStatuses.map((status) => (
                      <div
                        key={status}
                        className={cn(
                          "inline-flex items-center rounded-full px-3 py-1 text-[8px] font-semibold",
                          status === currentStatus
                            ? "bg-black text-white"
                            : "border border-muted bg-background text-muted-foreground"
                        )}
                      >
                        {status}
                      </div>
                    ))}
                  </div>

                  <div className="h-px bg-gray-300/50 my-2"></div>

                  <h2 className="text-sm font-semibold mb-2">Signals</h2>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {pipelineSignals.map((signal) => (
                      <button
                        key={signal}
                        type="button"
                        onClick={() => handleSignalClick(signal)}
                        disabled={!selectedPipeline || !pipelineRunning}
                        className={cn(
                          "inline-flex items-center rounded-full px-3 py-1 text-[8px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                          !selectedPipeline || !pipelineRunning
                            ? "opacity-50 cursor-not-allowed"
                            : "cursor-pointer",
                          signal === selectedSignal
                            ? "bg-primary text-primary-foreground hover:bg-primary/90"
                            : "border border-muted bg-background hover:bg-muted/80 text-muted-foreground"
                        )}
                      >
                        {signal}
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Panel>

            {/* Vertical resize handle */}
            <PanelResizeHandle className="h-2 flex items-center justify-center my-1">
              <div className="w-12 h-1 rounded-full bg-border/50 hover:bg-primary/60 transition-colors" />
            </PanelResizeHandle>

            {/* Configuration Area */}
            <Panel defaultSize={70} minSize={50} className="flex flex-col">
              <Card className="shadow-sm rounded-md p-0 flex-1 overflow-auto border-0 bg-gray-200 gap-0">
                <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
                  <h2 className="text-sm font-semibold">Configuration</h2>
                </div>
                <CardContent className="px-5 py-3 h-full flex flex-col overflow-y-auto">
                  <div className="flex-1 text-sm text-muted-foreground">
                    {selectedPipeline ? (
                      <p>
                        Configuration options for {selectedPipeline} will appear
                        here.
                      </p>
                    ) : (
                      <p>Select a pipeline to view configuration options.</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Panel>
          </PanelGroup>
        </Panel>

        {/* Horizontal resize handle */}
        <PanelResizeHandle className="w-2 flex items-center justify-center mx-1">
          <div className="h-12 w-1 rounded-full bg-border/50 hover:bg-primary/60 transition-colors" />
        </PanelResizeHandle>

        {/* Main Content */}
        <Panel className="p-.5 pt-3 pb-3 pr-3" order={2}>
          <Card className="h-full shadow-sm rounded-md overflow-auto border-0 bg-gray-200 p-0 gap-0">
            <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
              <div className="flex justify-between items-center w-full">
                <h3 className="text-sm font-semibold">Visualization</h3>
                <div className="flex items-center gap-2">
                  {/* Icon buttons group */}
                  <button
                    className="size-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                    title="Refresh"
                  >
                    <RefreshCw className="size-4" />
                  </button>
                  <button
                    className="size-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                    title="Settings"
                  >
                    <Settings className="size-4" />
                  </button>
                  <button
                    className="size-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                    title="Download"
                  >
                    <Download className="size-4" />
                  </button>
                  <button
                    className="size-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                    title="Logs"
                  >
                    <List className="size-4" />
                  </button>
                  <button
                    className="size-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                    title="More options"
                  >
                    <MoreHorizontal className="size-4" />
                  </button>
                </div>
              </div>
            </div>
            <CardContent className="px-5 py-3 flex flex-col h-full overflow-y-auto">
              {/* Stream queues section */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">Stream Queues</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  {pipelineQueues.map((queue) => (
                    <button
                      key={queue}
                      type="button"
                      onClick={() => handleQueueClick(queue)}
                      disabled={!selectedPipeline || !pipelineRunning}
                      className={cn(
                        "inline-flex items-center rounded-full px-3 py-1 text-[8px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        !selectedPipeline || !pipelineRunning
                          ? "opacity-50 cursor-not-allowed"
                          : "cursor-pointer",
                        queue === selectedQueue
                          ? "bg-primary text-primary-foreground hover:bg-primary/90"
                          : "border border-muted bg-background hover:bg-muted/80 text-muted-foreground"
                      )}
                    >
                      {queue}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex-1 flex items-start justify-center"></div>
            </CardContent>
          </Card>
        </Panel>
      </PanelGroup>
    </div>
  );
}
