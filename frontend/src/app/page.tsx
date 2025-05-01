import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Dashboard() {
  return (
    <div className="flex h-screen w-full">
      {/* Left Sidebar - Configuration Panel */}
      <div className="w-80 border-r bg-muted/40 p-4">
        <div className="flex items-center mb-6">
          <h1 className="font-semibold text-lg">Modulus Robot Control</h1>
        </div>

        {/* Pipeline Selection */}
        <div className="mb-6">
          <h2 className="text-sm font-medium mb-2">Available Pipelines</h2>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">
                No pipelines available
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Pipeline Controls */}
        <div className="mb-6">
          <h2 className="text-sm font-medium mb-2">Controls</h2>
          <div className="space-y-2">
            <Button variant="outline" className="w-full">
              Start Pipeline
            </Button>
            <Button variant="outline" className="w-full">
              Stop Pipeline
            </Button>
          </div>
        </div>

        {/* Pipeline Status */}
        <div className="mb-6">
          <h2 className="text-sm font-medium mb-2">Status</h2>
          <Card>
            <CardHeader className="py-2 px-4">
              <CardTitle className="text-sm">Pipeline Status</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-4">
              <p className="text-sm text-muted-foreground">Not connected</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Main Content - Visualization Area */}
      <div className="flex-1 p-6 bg-background">
        <Card className="h-full flex items-center justify-center">
          <CardContent className="text-center">
            <h3 className="text-lg font-medium mb-2">Frame Visualization</h3>
            <p className="text-sm text-muted-foreground">
              Connect to a pipeline queue to see frames
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
