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

## API Specifications

### REST Endpoints

#### 1. `GET /pipelines`
**Purpose:** Get information about all available pipelines with optional detail level

**Query Parameters:**
- `level`: (`basic` | `detailed`, default: `basic`)
  - `basic`: Returns just names and running status
  - `detailed`: Returns full information including status, signals, configs, queues

**Response:**
```json
// level=basic
{
  "available_pipelines": ["yahboom_pick_and_place", "other_pipeline"],
  "running_pipelines": ["yahboom_pick_and_place"]
}

// level=detailed
{
  "pipelines": [
    {
      "name": "yahboom_pick_and_place",
      "running": true,
      "status": "CALIBRATING",
      "available_signals": ["STOP", "PAUSE", "CALIBRATE"],
      "available_states": ["IDLE", "RUNNING", "CALIBRATING", "PICKING", "PLACING"],
      "configuration": {
        "dataloader": { /* current config */ },
        "detect": { /* current config */ }
      },
      "queues": ["camera_frames", "detection_results"]
    },
    {
      "name": "other_pipeline",
      "running": false,
      // other detailed info if pipeline exists in registry
    }
  ]
}
```

#### 2. `GET /pipeline/{pipeline_name}`
**Purpose:** Get detailed information about a specific pipeline

**Path Parameters:**
- `pipeline_name`: Name of the pipeline

**Response:**
```json
{
  "name": "yahboom_pick_and_place",
  "running": true,
  "status": "CALIBRATING",
  "available_signals": ["STOP", "PAUSE", "CALIBRATE"],
  "available_states": ["IDLE", "RUNNING", "CALIBRATING", "PICKING", "PLACING"],
  "configuration": {
    "dataloader": { /* current config */ },
    "detect": { /* current config */ }
  },
  "queues": ["camera_frames", "detection_results"]
}
```

#### 3. `POST /pipeline/{pipeline_name}/start`
**Purpose:** Start a specific pipeline

**Path Parameters:**
- `pipeline_name`: Name of the pipeline to start

**Request Body:**
```json
{
  "debug": true
}
```

**Response:**
```json
{
  "status": "success",
  "pipeline": "yahboom_pick_and_place",
  "message": "Pipeline started successfully"
}
```

#### 4. `POST /pipeline/{pipeline_name}/stop`
**Purpose:** Stop a running pipeline

**Path Parameters:**
- `pipeline_name`: Name of the pipeline to stop

**Response:**
```json
{
  "status": "success",
  "pipeline": "yahboom_pick_and_place",
  "message": "Pipeline stopped successfully"
}
```

#### 5. `POST /pipeline/{pipeline_name}/signal/{signal_name}`
**Purpose:** Send a signal to a running pipeline

**Path Parameters:**
- `pipeline_name`: Name of the target pipeline
- `signal_name`: Name of the signal to send

**Query Parameters:**
- `priority`: (`HIGH` | `NORMAL`, default: `NORMAL`) - Signal priority

**Response:**
```json
{
  "status": "success",
  "pipeline": "yahboom_pick_and_place",
  "signal": "CALIBRATE",
  "message": "Signal sent successfully"
}
```

#### 6. `POST /pipeline/{pipeline_name}/config`
**Purpose:** Update pipeline configuration

**Path Parameters:**
- `pipeline_name`: Name of the pipeline to configure

**Request Body:**
```json
{
  "dataloader": {
    "process": {
      "queue": "custom_queue",
      "wait": true
    }
  },
  "detect": {
    "init": {
      "color_hsv_thresholds": {
        "red": [[0, 50, 50], [10, 255, 255]]
      }
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "pipeline": "yahboom_pick_and_place",
  "message": "Configuration updated successfully",
  "applied_config": {
    // The new effective configuration
  }
}
```

#### 7. `GET /pipeline/{pipeline_name}/config/schema`
**Purpose:** Get configuration schema for dynamic UI rendering

**Path Parameters:**
- `pipeline_name`: Name of the pipeline

**Response:**
```json
{
  "dataloader": {
    "type": "object",
    "properties": {
      "init": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "enum": ["redis", "imagezmq"],
            "description": "Backend type for loading data"
          },
          "host": {
            "type": "string",
            "description": "Server host address"
          },
          // other properties
        }
      },
      "process": {
        "type": "object",
        "properties": {
          "queue": {
            "type": "string",
            "description": "Redis queue name for frames"
          },
          "wait": {
            "type": "boolean",
            "description": "Whether to wait for frames if none available"
          }
          // other properties
        }
      }
    }
  },
  // schemas for other components
}
```

### WebSocket Endpoints

WebSocket connections are used exclusively for real-time state broadcasting from the server to clients. All client actions and commands are sent through the REST endpoints, which provide immediate acknowledgments via HTTP responses. WebSockets complement this by pushing state changes to all connected clients, ensuring everyone has the current view of the system.

#### 1. `ws/pipeline/{pipeline_name}`
**Purpose:** Stream real-time pipeline status updates and events

**Path Parameters:**
- `pipeline_name`: Name of the pipeline to monitor

**Message Types:**
- `connection_status`: Sent when WebSocket connection is established
- `status_update`: When pipeline state or status changes
- `config_update`: When pipeline configuration is modified
- `lifecycle_event`: When pipeline is started or stopped
- `notification`: Errors, warnings, or information messages

**Connected Message (from server to client):**
```json
{
  "type": "connection_status",
  "connected": true,
  "pipeline": "yahboom_pick_and_place",
  "timestamp": 1633028145.123
}
```

**Status Update Message:**
```json
{
  "type": "status_update",
  "pipeline": "yahboom_pick_and_place",
  "status": "PICKING",
  "previous_status": "CALIBRATING",
  "timestamp": 1633028145.123
}
```

**Configuration Change Message:**
```json
{
  "type": "config_update",
  "pipeline": "yahboom_pick_and_place",
  "changes": {
    "detect.color_hsv_thresholds.red": [[0, 50, 50], [10, 255, 255]]
  },
  "timestamp": 1633028145.123
}
```

**Error/Warning Message:**
```json
{
  "type": "notification",
  "pipeline": "yahboom_pick_and_place",
  "level": "error", // or "warning", "info"
  "message": "Failed to connect to robot arm",
  "timestamp": 1633028145.123
}
```

**Lifecycle Event Message:**
```json
{
  "type": "lifecycle_event",
  "pipeline": "yahboom_pick_and_place",
  "event": "stopped", // or "started"
  "timestamp": 1633028145.123
}
```

#### 2. `ws/pipeline/{pipeline_name}/queue/{queue_name}`
**Purpose:** Stream real-time frame data and processing results from a specific queue

**Path Parameters:**
- `pipeline_name`: Name of the pipeline
- `queue_name`: Name of the queue to stream (e.g., "camera_frames", "detection_results")

**Message Types:**
- `connection_status`: Sent when WebSocket connection is established
- `frame`: Image frame data with metadata
- `detection`: Processing results like object detections
- `metrics`: Performance metrics related to this queue's processing

**Connected Message:**
```json
{
  "type": "connection_status",
  "connected": true,
  "pipeline": "yahboom_pick_and_place",
  "queue": "camera_frames",
  "timestamp": 1633028145.123
}
```

**Frame Data Message:**
```json
{
  "type": "frame",
  "pipeline": "yahboom_pick_and_place",
  "queue": "camera_frames",
  "frame_id": 1234,
  "frame_data": "base64_encoded_image",
  "metadata": {
    "width": 640,
    "height": 480,
    "format": "jpeg"
  },
  "timestamp": 1633028145.123
}
```

**Detection Results Message:**
```json
{
  "type": "detection",
  "pipeline": "yahboom_pick_and_place",
  "queue": "detection_results",
  "frame_id": 1234,
  "detections": [
    {
      "class": "red",
      "confidence": 0.98,
      "bbox": [100, 150, 50, 50]
    },
    {
      "class": "green",
      "confidence": 0.95,
      "bbox": [300, 200, 60, 60]
    }
  ],
  "timestamp": 1633028145.123
}
```
