"use client";

import { useState, useLayoutEffect, useCallback } from "react";
import { useAtom } from "jotai";
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
import { Loader2 } from "lucide-react";
import {
  selectedPipelineAtom,
  pipelineRunningAtom,
  currentStatusAtom,
  selectedSignalAtom,
  isMobileAtom,
  availablePipelinesAtom,
  pipelineStatusesAtom,
  pipelineSignalsAtom,
} from "@/atoms";
import MobileResizeHandle from "./MobileResizeHandle";
import VisualizationCard from "./VisualizationCard";
import { ReadOnlySelect } from "@/components/ui/custom-select";

const Dashboard = () => {
  const [selectedPipeline, setSelectedPipeline] = useAtom(selectedPipelineAtom);
  const [pipelineRunning, setPipelineRunning] = useAtom(pipelineRunningAtom);
  const [isLoading, setIsLoading] = useState(true);
  const [currentStatus] = useAtom(currentStatusAtom);
  const [selectedSignal, setSelectedSignal] = useAtom(selectedSignalAtom);
  const [isMobile, setIsMobile] = useAtom(isMobileAtom);

  // New state for mobile panel heights
  const [pipelinePanelHeight, setPipelinePanelHeight] = useState(300);
  const [configurationPanelHeight, setConfigurationPanelHeight] = useState(350);
  const [visualizationPanelHeight, setVisualizationPanelHeight] = useState(300);

  // Get data from atoms
  const [availablePipelines] = useAtom(availablePipelinesAtom);
  const [pipelineSignals] = useAtom(pipelineSignalsAtom);
  const [pipelineStatuses] = useAtom(pipelineStatusesAtom);

  const MIN_SIZE_IN_PIXELS = 400;
  const MAX_SIZE_IN_PIXELS = 500;
  const [minSize, setMinSize] = useState(24);
  const [maxSize, setMaxSize] = useState(36);

  // First effect just for turning off loading
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
                  <h2 className="text-sm font-semibold">Status</h2>
                  <div className="flex items-center">
                    <ReadOnlySelect
                      value={currentStatus}
                      options={pipelineStatuses}
                      label="Status"
                      width="120px"
                    />
                  </div>
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
                      style={{
                        boxSizing: "border-box",
                      }} /* Ensure border is included in size calc */
                      className={cn(
                        "inline-flex items-center justify-center rounded-full px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring h-7 min-w-[50px]",
                        !selectedPipeline || !pipelineRunning
                          ? "opacity-50 cursor-not-allowed"
                          : "cursor-pointer",
                        signal === selectedSignal
                          ? "bg-primary text-primary-foreground hover:bg-primary/90 border border-transparent"
                          : "border border-muted bg-background hover:bg-muted/80 text-muted-foreground"
                      )}
                    >
                      {signal}
                    </button>
                  ))}
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
                      <h2 className="text-sm font-semibold">Status</h2>
                      <div className="flex items-center">
                        <ReadOnlySelect
                          value={currentStatus}
                          options={pipelineStatuses}
                          label="Status"
                          width="120px"
                        />
                      </div>
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
                          style={{
                            boxSizing: "border-box",
                          }} /* Ensure border is included in size calc */
                          className={cn(
                            "inline-flex items-center justify-center rounded-full px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring h-7 min-w-[50px]",
                            !selectedPipeline || !pipelineRunning
                              ? "opacity-50 cursor-not-allowed"
                              : "cursor-pointer",
                            signal === selectedSignal
                              ? "bg-primary text-primary-foreground hover:bg-primary/90 border border-transparent"
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
                          Configuration options for {selectedPipeline} will
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
