# Frontend UI Development

## Requirements

1. **Dashboard Layout**:
   - A modern, clean dashboard interface for monitoring and controlling robot arm pipelines

2. **Pipeline Management**:
   - List available pipelines
   - Start/stop pipeline operations
   - Monitor pipeline status (state, running/idle, etc.)

3. **Handler Configuration**:
   - Display current configuration for each pipeline handler
   - Allow users to modify handler configurations via UI elements
   - Derive configuration options from defaults.yaml
   - Update configurations dynamically

4. **Signal Control**:
   - Show available signals for each pipeline
   - Provide UI for sending signals to control pipeline behavior
   - Potentially treat configuration updates as signals to the pipeline

5. **Process Visualization**:
   - Connect to pipeline data queues
   - Display streamed process frames/results
   - Real-time visualization of what the pipeline is seeing/processing

## Design Decisions

### Frontend Stack
- Next.js with TypeScript for the application framework
- Tailwind CSS for styling
- Shadcn UI components for dashboard UI elements

### UI Layout
- Left side: Foldable configuration panel for the active pipeline
- Right side: Visualization area for streamed frames
- Flat layout rather than tabbed interface for better visibility

### Communication Architecture
- **Backend Pipeline Communication**: Continue using Redis for all inter-process communication
  - Maintain existing DataStream and DataLoaderHandler implementations
  - Leverage Redis benefits: decoupling, persistence, multiple consumers, performance

- **Browser-Backend Bridge**: FastAPI WebSockets integration
  - WebSocket endpoints in FastAPI to subscribe to Redis queues
  - Connection manager to handle WebSocket lifecycle
  - Async Redis subscribers that forward messages to WebSocket clients
  - Authentication and error handling

- **Data Flow**:
  ```
  Pipeline Processes ⟷ Redis ⟷ FastAPI WebSocket Bridge ⟷ Browser (Next.js)
  ```

## Implementation Plan
1. Set up Next.js frontend with TypeScript, Tailwind CSS, and Shadcn UI
2. Implement FastAPI WebSocket endpoints for real-time communication
3. Create frontend dashboard layout
4. Implement pipeline management features
5. Add configuration panel and signal controls
6. Integrate frame visualization components
7. Add authentication and error handling

## Implementation Considerations
- Architecture approach (React, WebSockets, REST API)
- UI organization (dashboard, detail views, tabs)
- Technical considerations (streaming, dynamic forms, WebSockets)
- Potential challenges (YAML to UI, image streaming, state management)
