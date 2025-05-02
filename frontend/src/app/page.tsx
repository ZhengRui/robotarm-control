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

  // Second effect for measurements that only runs when isLoading is false
  // useLayoutEffect(() => {
  //   if (isLoading) return; // Don't run if still loading

  //   const panelGroup = document.querySelector(
  //     '[data-panel-group-id="dashboard-layout-horizontal"]'
  //   );

  //   if (!panelGroup) return;

  //   const observer = new ResizeObserver(() => {
  //     const screenWidth = (panelGroup as HTMLElement).offsetWidth;

  //     setMinSize((MIN_SIZE_IN_PIXELS / screenWidth) * 100);
  //     setMaxSize((MAX_SIZE_IN_PIXELS / screenWidth) * 100);
  //   });

  //   observer.observe(panelGroup);

  //   return () => {
  //     observer.disconnect();
  //   };
  // }, [isLoading]); // This runs when isLoading changes to false

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
      <PanelGroup
        direction="horizontal"
        className="h-full"
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
          <h1 className="text-2xl font-bold mb-4 w-full text-center">
            Modulus Robot Control
          </h1>

          <PanelGroup
            direction="vertical"
            className="flex-1"
            autoSaveId="dashboard-layout-vertical"
          >
            {/* Pipeline Selection with integrated toggle */}
            <Panel defaultSize={30} minSize={20} className="flex flex-col">
              <Card className="shadow-sm rounded-md p-0 flex-1 overflow-auto border-0 bg-gray-200">
                <CardContent className="px-5 py-3 overflow-y-auto h-full">
                  <div className="flex justify-between items-center mb-2">
                    <h2 className="text-sm font-semibold">Select Pipeline</h2>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "text-[10px] font-semibold",
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
                      <span
                        className={cn(
                          "text-[10px] font-semibold",
                          pipelineRunning
                            ? "text-primary"
                            : "text-muted-foreground"
                        )}
                      >
                        On
                      </span>
                    </div>
                  </div>
                  <Select
                    onValueChange={(value) => {
                      setSelectedPipeline(value);
                    }}
                    value={selectedPipeline ?? ""}
                  >
                    <SelectTrigger className="text-[10px] font-semibold text-muted-foreground border bg-background !h-6 !focus:ring-0 !focus:ring-offset-0 w-full mb-4 rounded-sm">
                      <SelectValue placeholder="Select a pipeline..." />
                    </SelectTrigger>
                    <SelectContent>
                      {availablePipelines.map((pipeline) => (
                        <SelectItem
                          key={pipeline}
                          value={pipeline}
                          className="text-xs"
                        >
                          {pipeline}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <div className="h-px bg-border/50 my-4"></div>

                  <h2 className="text-sm font-semibold mb-2">Status</h2>
                  <div className="flex flex-wrap gap-2">
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

                  <div className="h-px bg-border/50 my-4"></div>

                  <h2 className="text-sm font-semibold mb-2">Signals</h2>
                  <div className="flex flex-wrap gap-2">
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
              <Card className="shadow-sm rounded-md p-0 flex-1 overflow-auto border-0 bg-gray-200">
                <CardContent className="px-5 py-3 h-full flex flex-col">
                  <h2 className="text-sm font-semibold mb-2">Configuration</h2>
                  <div className="flex-1 overflow-y-auto text-sm text-muted-foreground">
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
        <Panel className="p-.5 pt-15 pb-3 pr-3" order={2}>
          <Card className="h-full shadow-sm rounded-md overflow-auto border-0 bg-gray-200 p-0">
            <CardContent className="px-5 py-3 flex flex-col h-full">
              <div className="flex justify-between items-start mb-4">
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
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center max-w-md">
                  <p className="text-muted-foreground">
                    {selectedPipeline
                      ? `Select a queue from ${selectedPipeline} to visualize frames.`
                      : "Select a pipeline and connect to a queue to see frames."}
                  </p>
                  {/* Debug section */}
                  <div className="mt-4 p-4 bg-muted/10 rounded text-left text-xs">
                    <p>Selected Pipeline: {selectedPipeline || "None"}</p>
                    <p>Running: {pipelineRunning ? "Yes" : "No"}</p>
                    <p>Current Status: {currentStatus}</p>
                    <p>Selected Signal: {selectedSignal || "None"}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </Panel>
      </PanelGroup>
    </div>
  );
}
