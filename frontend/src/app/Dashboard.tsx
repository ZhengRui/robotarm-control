"use client";

import { useState, useLayoutEffect, useCallback } from "react";
import { useAtom } from "jotai";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectLabel,
  SelectGroup,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { Loader2 } from "lucide-react";
import {
  selectedPipelineNameAtom,
  selectedSignalAtom,
  isMobileAtom,
} from "@/atoms";
import MobileResizeHandle from "./MobileResizeHandle";
import VisualizationCard from "./VisualizationCard";
import { ReadOnlySelect } from "@/components/ui/custom-select";
import {
  useGetPipelines,
  useGetPipeline,
  useStartPipeline,
  useStopPipeline,
  useSendSignal,
  usePipelineWebSocket,
} from "@/hooks";

const Dashboard = () => {
  // Get data from atoms
  const [selectedPipelineName, setSelectedPipelineName] = useAtom(
    selectedPipelineNameAtom
  );
  const [selectedSignal, setSelectedSignal] = useAtom(selectedSignalAtom);
  const [isMobile, setIsMobile] = useAtom(isMobileAtom);

  // Local state (only for UI loading and layout)
  const [isLoading, setIsLoading] = useState(true);
  const [pipelinePanelHeight, setPipelinePanelHeight] = useState(300);
  const [configurationPanelHeight, setConfigurationPanelHeight] = useState(350);
  const [visualizationPanelHeight, setVisualizationPanelHeight] = useState(300);
  const [minSize, setMinSize] = useState(24);
  const [maxSize, setMaxSize] = useState(36);

  // Query hooks
  const { data: pipelinesData, isLoading: isPipelinesLoading } =
    useGetPipelines(false);
  const { data: pipelineData } = useGetPipeline(selectedPipelineName, true);

  // Derived values from API data
  const availablePipelines = pipelinesData?.pipelines.map((p) => p.name) || [];
  const pipelineRunning = pipelineData?.running || false;
  const currentState = pipelineData?.state || "stopped";

  // Available states from selected pipeline
  const pipelineStates = pipelineData?.available_states || ["stopped"];

  // Available signals from selected pipeline
  const pipelineSignals = pipelineData?.available_signals || [];

  // Mutation hooks
  const { mutate: startPipeline } = useStartPipeline();
  const { mutate: stopPipeline } = useStopPipeline();
  const { mutate: sendSignal } = useSendSignal();

  // WebSocket connection
  usePipelineWebSocket(selectedPipelineName);

  const MIN_SIZE_IN_PIXELS = 400;
  const MAX_SIZE_IN_PIXELS = 500;

  // First effect just for turning off loading and setting up responsive layout
  useLayoutEffect(() => {
    const screenWidth = window.innerWidth;
    setMinSize(
      (Math.min(MIN_SIZE_IN_PIXELS, screenWidth / 3) / screenWidth) * 100
    );
    setMaxSize(
      (Math.min(MAX_SIZE_IN_PIXELS, screenWidth / 2) / screenWidth) * 100
    );

    if (screenWidth < 640) {
      setIsMobile(true);
    }

    setIsLoading(false);
  }, [setIsMobile]);

  // Handle panel resize functions
  const handlePipelinePanelResize = useCallback((delta: number) => {
    setPipelinePanelHeight((prev) => Math.max(150, prev + delta)); // Minimum height of 150px
  }, []);

  const handleConfigurationPanelResize = useCallback((delta: number) => {
    setConfigurationPanelHeight((prev) => Math.max(150, prev + delta)); // Minimum height of 150px
  }, []);

  const handleVisualizationPanelResize = useCallback((delta: number) => {
    setVisualizationPanelHeight((prev) => Math.max(150, prev + delta)); // Minimum height of 150px
  }, []);

  // Handle toggle change for pipeline running state
  const handleToggleChange = (checked: boolean) => {
    if (!selectedPipelineName) return;

    if (checked) {
      startPipeline(
        { pipelineName: selectedPipelineName, debug: false },
        {
          onError: (error) => console.error("Failed to start pipeline:", error),
        }
      );
    } else {
      stopPipeline(selectedPipelineName, {
        onError: (error) => console.error("Failed to stop pipeline:", error),
      });
    }
  };

  // Handle signal selection
  const handleSignalClick = (signal: string) => {
    if (!selectedPipelineName || !pipelineRunning) return;

    sendSignal(
      { pipelineName: selectedPipelineName, signalName: signal },
      {
        onSuccess: () => setSelectedSignal(signal),
        onError: (error) => console.error("Failed to send signal:", error),
      }
    );
  };

  // If still loading, show a spinning loader using Lucide React
  if (isLoading || isPipelinesLoading) {
    return (
      <div className="h-screen w-full bg-background flex items-center justify-center">
        <Loader2
          className="h-8 w-8 text-primary animate-spin"
          strokeWidth={1.5}
        />
      </div>
    );
  }

  // Render different layouts for mobile and desktop
  if (isMobile) {
    return (
      <div className="min-h-screen w-full bg-background transition-all duration-200">
        <div className="flex justify-center py-4 border-b border-border/30">
          <h1 className="text-2xl font-bold">Modulus Robot Control</h1>
        </div>

        {/* Mobile layout uses simple flex column instead of PanelGroup */}
        <div className="flex flex-col p-3 gap-0 pb-20">
          {/* Pipeline Panel */}
          <div
            className="w-full"
            style={{ height: `${pipelinePanelHeight}px` }}
          >
            <Card className="shadow-sm rounded-md p-0 overflow-auto border-0 bg-gray-200 gap-0 h-full">
              <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
                <div className="flex justify-between items-center gap-3 w-full">
                  <Select
                    onValueChange={(value) => {
                      setSelectedPipelineName(value);
                    }}
                    value={selectedPipelineName || ""}
                    defaultValue=""
                    onOpenChange={() => {
                      // Reset any potential selection/highlight when opening
                      if (!selectedPipelineName) {
                        setTimeout(() => {
                          const activeElement =
                            document.activeElement as HTMLElement;
                          if (activeElement) {
                            activeElement.blur();
                          }
                        }, 0);
                      }
                    }}
                  >
                    <SelectTrigger className="text-sm font-semibold !h-6 !focus:ring-0 !focus:ring-offset-0 !focus-visible:ring-0 !focus-visible:ring-offset-0 !ring-0 !ring-offset-0 shadow-none px-0 border-0 w-auto min-w-[150px] text-left outline-none focus:outline-none">
                      <SelectValue placeholder="Select Pipeline" />
                    </SelectTrigger>
                    <SelectContent
                      className="rounded-md overflow-hidden"
                      align="start"
                    >
                      <SelectGroup>
                        <SelectLabel className="px-3 py-1 border-b border-gray-100 text-xs font-semibold text-left">
                          Select Pipeline
                        </SelectLabel>
                        {availablePipelines.map((pipeline: string) => (
                          <SelectItem
                            key={pipeline}
                            value={pipeline}
                            className="text-sm rounded-none hover:bg-gray-100 text-left pl-3 data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[state=checked]:bg-transparent data-[state=checked]:text-foreground !focus:bg-transparent !outline-none"
                          >
                            {pipeline}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                  <div className="flex items-center gap-2">
                    {/* Show both labels on md screens and up */}
                    <span
                      className={cn(
                        "text-xs font-semibold hidden md:inline",
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
                      id="pipeline-switch-mobile"
                      disabled={!selectedPipelineName}
                    />
                    {/* On larger screens, show the right label conditionally */}
                    <span
                      className={cn(
                        "text-xs font-semibold hidden md:inline",
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
                        "text-xs font-semibold md:hidden",
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
              <CardContent className="px-5 py-3 overflow-y-auto h-[calc(100%-3rem)]">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-sm font-semibold">State</h2>
                  <div className="flex items-center">
                    <ReadOnlySelect
                      value={selectedPipelineName ? currentState : ""}
                      options={selectedPipelineName ? pipelineStates : []}
                      label="State"
                      width="120px"
                      placeholder="Select Pipeline First"
                      disabled={!selectedPipelineName}
                    />
                  </div>
                </div>

                <div className="h-px bg-gray-300/50 my-2"></div>

                <h2 className="text-sm font-semibold mb-2">Signals</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {selectedPipelineName ? (
                    pipelineSignals.map((signal: string) => (
                      <button
                        key={signal}
                        type="button"
                        onClick={() => handleSignalClick(signal)}
                        disabled={!selectedPipelineName || !pipelineRunning}
                        style={{
                          boxSizing: "border-box",
                        }}
                        className={cn(
                          "inline-flex items-center justify-center rounded-full px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring h-7 min-w-[50px]",
                          !selectedPipelineName || !pipelineRunning
                            ? "opacity-50 cursor-not-allowed"
                            : "cursor-pointer",
                          signal === selectedSignal
                            ? "bg-primary text-primary-foreground hover:bg-primary/90 border border-transparent"
                            : "border border-muted bg-background hover:bg-muted/80 text-muted-foreground"
                        )}
                      >
                        {signal}
                      </button>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Select a pipeline to view available signals
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resize handle between Pipeline and Configuration panel */}
          <MobileResizeHandle onResize={handlePipelinePanelResize} />

          {/* Configuration Panel */}
          <div
            className="w-full"
            style={{ height: `${configurationPanelHeight}px` }}
          >
            <Card className="shadow-sm rounded-md p-0 overflow-auto border-0 bg-gray-200 gap-0 h-full">
              <div className="sticky top-0 bg-gray-300 px-5 py-3 z-10 border-b border-gray-300/30 h-12 flex items-center">
                <h2 className="text-sm font-semibold">Configuration</h2>
              </div>
              <CardContent className="px-5 py-3 h-[calc(100%-3rem)] flex flex-col overflow-y-auto">
                <div className="flex-1 text-sm text-muted-foreground">
                  {selectedPipelineName ? (
                    <p>
                      Configuration options for {selectedPipelineName} will
                      appear here.
                    </p>
                  ) : (
                    <p>Select a pipeline to view configuration options.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Resize handle between Configuration and Visualization panel */}
          <MobileResizeHandle onResize={handleConfigurationPanelResize} />

          {/* Visualization Panel */}
          <div
            className="w-full"
            style={{ height: `${visualizationPanelHeight}px` }}
          >
            <VisualizationCard />
          </div>

          {/* Resize handle below Visualization panel */}
          <MobileResizeHandle onResize={handleVisualizationPanelResize} />

          {/* Empty space div that gives extra room to scroll */}
          <div className="w-full h-4"></div>
        </div>
      </div>
    );
  }

  // Desktop layout with PanelGroup
  return (
    <div className="h-screen w-full bg-background transition-all duration-200">
      <div className="flex justify-center py-4 border-b border-border/30">
        <h1 className="text-2xl font-bold">Modulus Robot Control</h1>
      </div>
      <div className="h-[calc(100%-4rem)]">
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
                          setSelectedPipelineName(value);
                        }}
                        value={selectedPipelineName || ""}
                        defaultValue=""
                        onOpenChange={() => {
                          // Reset any potential selection/highlight when opening
                          if (!selectedPipelineName) {
                            setTimeout(() => {
                              const activeElement =
                                document.activeElement as HTMLElement;
                              if (activeElement) {
                                activeElement.blur();
                              }
                            }, 0);
                          }
                        }}
                      >
                        <SelectTrigger className="text-sm font-semibold !h-6 !focus:ring-0 !focus:ring-offset-0 !focus-visible:ring-0 !focus-visible:ring-offset-0 !ring-0 !ring-offset-0 shadow-none px-0 border-0 w-auto min-w-[150px] text-left outline-none focus:outline-none">
                          <SelectValue placeholder="Select Pipeline" />
                        </SelectTrigger>
                        <SelectContent
                          className="rounded-md overflow-hidden"
                          align="start"
                        >
                          <SelectGroup>
                            <SelectLabel className="px-3 py-1 border-b border-gray-100 text-xs font-semibold text-left">
                              Select Pipeline
                            </SelectLabel>
                            {availablePipelines.map((pipeline: string) => (
                              <SelectItem
                                key={pipeline}
                                value={pipeline}
                                className="text-sm rounded-none hover:bg-gray-100 text-left pl-3 data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[state=checked]:bg-transparent data-[state=checked]:text-foreground !focus:bg-transparent !outline-none"
                              >
                                {pipeline}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                      <div className="flex items-center gap-2">
                        {/* Show both labels on md screens and up */}
                        <span
                          className={cn(
                            "text-xs font-semibold hidden md:inline",
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
                          disabled={!selectedPipelineName}
                        />
                        {/* On larger screens, show the right label conditionally */}
                        <span
                          className={cn(
                            "text-xs font-semibold hidden md:inline",
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
                            "text-xs font-semibold md:hidden",
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
                    <div className="flex items-center justify-between mb-2">
                      <h2 className="text-sm font-semibold">State</h2>
                      <div className="flex items-center">
                        <ReadOnlySelect
                          value={selectedPipelineName ? currentState : ""}
                          options={selectedPipelineName ? pipelineStates : []}
                          label="State"
                          width="120px"
                          placeholder="Select Pipeline First"
                          disabled={!selectedPipelineName}
                        />
                      </div>
                    </div>

                    <div className="h-px bg-gray-300/50 my-2"></div>

                    <h2 className="text-sm font-semibold mb-2">Signals</h2>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {selectedPipelineName ? (
                        pipelineSignals.map((signal: string) => (
                          <button
                            key={signal}
                            type="button"
                            onClick={() => handleSignalClick(signal)}
                            disabled={!selectedPipelineName || !pipelineRunning}
                            style={{
                              boxSizing: "border-box",
                            }}
                            className={cn(
                              "inline-flex items-center justify-center rounded-full px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring h-7 min-w-[50px]",
                              !selectedPipelineName || !pipelineRunning
                                ? "opacity-50 cursor-not-allowed"
                                : "cursor-pointer",
                              signal === selectedSignal
                                ? "bg-primary text-primary-foreground hover:bg-primary/90 border border-transparent"
                                : "border border-muted bg-background hover:bg-muted/80 text-muted-foreground"
                            )}
                          >
                            {signal}
                          </button>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          Select a pipeline to view available signals
                        </p>
                      )}
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
                      {selectedPipelineName ? (
                        <p>
                          Configuration options for {selectedPipelineName} will
                          appear here.
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
            <VisualizationCard />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
};

export default Dashboard;
