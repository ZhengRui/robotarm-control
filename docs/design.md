# System Architecture Design

## Overview

The Modulus Robot Arm Control system follows a modern, robust architecture designed for responsiveness, maintainability, and extensibility. This document provides a detailed examination of the system's components, their interactions, and the underlying design principles.

## Core Architectural Concepts

### 1. Pipeline as State Machines

At the heart of our system are pipelines, which function as state machines:

```
┌─────────────────────────────────────────────┐
│ Pipeline                                    │
│                                             │
│  ┌─────────┐      ┌─────────┐      ┌─────┐ │
│  │ IDLE    │─────▶│ RUNNING │─────▶│ ... │ │
│  └─────────┘      └─────────┘      └─────┘ │
│       ▲                │                    │
│       └────────────────┘                    │
│                                             │
└─────────────────────────────────────────────┘
```

Each pipeline:
- Maintains a current state (e.g., IDLE, CALIBRATING, PICKING, PLACING)
- Responds to signals by transitioning between states
- Executes different logic in each state via the `step()` method
- Encapsulates a complete robot behavior workflow

The state machine design enables:
- Clear separation of concerns between different operational phases
- Predictable behavior transitions
- Simplified debugging and monitoring
- Graceful handling of unexpected situations

### 2. Multi-Process Architecture

To ensure stability and responsiveness, the system employs a multi-process architecture:

```
┌───────────────────┐     ┌───────────────────────────────┐
│                   │     │ Process 1                     │
│                   │     │ ┌───────────┐  ┌───────────┐  │
│                   │     │ │ Pipeline  │  │ Signal    │  │
│  FastAPI Server   │◄───►│ │ Instance  │◄─┤ Thread    │  │
│                   │     │ └───────────┘  └───────────┘  │
│                   │     └───────────────────────────────┘
│                   │
│                   │     ┌───────────────────────────────┐
│                   │     │ Process 2                     │
│                   │     │ ┌───────────┐  ┌───────────┐  │
│                   │     │ │ Pipeline  │  │ Signal    │  │
│                   │◄───►│ │ Instance  │◄─┤ Thread    │  │
└───────────────────┘     │ └───────────┘  └───────────┘  │
                          └───────────────────────────────┘
```

Each pipeline runs in its own dedicated process, providing:
- Isolation from other pipelines for stability
- Independent lifecycle management
- Protection against crashes affecting the entire system
- Efficient utilization of multi-core systems

### 3. Priority-based Signal Handling

Signals (commands) to pipelines are processed through a priority queue system:

```
                  ┌─────────────────┐
                  │ Signal Priority │
                  │                 │
HIGH PRIORITY ──► │  1. Emergency   │ ──┐
                  │  2. User Cmd    │   │   ┌───────────────┐
                  │  3. Automatic   │   ├──►│ Pipeline      │
                  │                 │   │   │ State Machine │
LOW PRIORITY  ──► │  4. Telemetry   │ ──┘   └───────────────┘
                  └─────────────────┘
```

This ensures:
- Critical commands (e.g., emergency stop) are processed first
- User interactions remain responsive even under load
- Background operations don't interfere with time-sensitive commands
- The system can handle bursts of signals while maintaining responsiveness

## Component Hierarchy

### Layer 1: FastAPI Server (API Layer)

The FastAPI server provides the external interface to the system:

```
┌────────────────────────────────────────────────────┐
│ FastAPI Server                                     │
│                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ GET /status │  │ POST /signal│  │ GET /pipelines│
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │    PipelineFactory     │
            └────────────────────────┘
```

Key responsibilities:
- Exposing RESTful endpoints for pipeline management
- Converting HTTP requests to internal method calls
- Validating input parameters
- Returning appropriate status codes and responses
- Handling startup and shutdown events

### Layer 2: PipelineFactory (Factory Layer)

The PipelineFactory serves as a singleton access point to the pipeline system:

```
┌────────────────────────────────────────────────────┐
│ PipelineFactory                                    │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ register_pipeline() │  │ create_pipeline()    │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ send_signal()       │  │ get_status()         │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │    PipelineManager     │
            └────────────────────────┘
```

Key responsibilities:
- Maintaining a registry of available pipeline types
- Providing static methods for pipeline operations
- Abstracting the complexity of pipeline management
- Creating a clean interface for the API layer

### Layer 3: PipelineManager (Management Layer)

The PipelineManager handles multiple pipeline instances:

```
┌────────────────────────────────────────────────────┐
│ PipelineManager                                    │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ create_pipeline()   │  │ stop_pipeline()      │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ send_signal()       │  │ get_status()         │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
                         │
                         ▼
       ┌────────────────────────────────────┐
       │          PipelineProcess           │
       └────────────────────────────────────┘
```

Key responsibilities:
- Tracking all active pipeline processes
- Managing pipeline lifecycle (creation, termination)
- Routing signals to appropriate pipelines
- Aggregating status information
- Handling cleanup on shutdown

### Layer 4: PipelineProcess (Process Layer)

The PipelineProcess encapsulates a pipeline running in a separate process:

```
┌────────────────────────────────────────────────────┐
│ PipelineProcess                                    │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ start()             │  │ stop()               │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ send_signal()       │  │ get_status()         │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
           │                        │
           │                        │
┌──────────▼─────────┐    ┌─────────▼──────────┐
│  signal_queue       │    │  status_queue      │
│  (IPC Queue)        │    │  (IPC Queue)       │
└────────────────────┘     └────────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────────────────────────────────────┐
│ Pipeline Process (separate Python process)       │
│                                                  │
│  ┌───────────────┐         ┌───────────────────┐ │
│  │ Signal Thread │─────────► BasePipeline      │ │
│  └───────────────┘         │ Implementation    │ │
│                            └───────────────────┘ │
└──────────────────────────────────────────────────┘
```

Key responsibilities:
- Process lifecycle management (start, stop, monitor)
- Inter-process communication through queues
- Signal routing to the pipeline instance
- Status reporting back to the manager
- Handling process termination gracefully

### Layer 5: BasePipeline (Pipeline Layer)

The BasePipeline defines the interface for all pipeline implementations:

```
┌────────────────────────────────────────────────────┐
│ BasePipeline (Abstract)                            │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ handle_signal()     │  │ step()               │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │ current_state       │  │ available_signals    │ │
│  └─────────────────────┘  └──────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
                         │
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼─────────────┐  ┌──────────────▼───────────┐
│ YahboomPickAndPlace  │  │ Other Pipeline           │
│ Pipeline             │  │ Implementations          │
└──────────────────────┘  └────────────────────────────┘
```

Key responsibilities:
- Defining the pipeline interface
- Loading configuration from YAML
- Initializing handlers
- Processing state transitions
- Executing state-specific logic

## Signal Flow

Signals follow a well-defined path through the system:

1. **Initiation**: The API server receives a POST request to `/signal`
2. **Routing**: PipelineFactory forwards to PipelineManager
3. **Queueing**: PipelineManager routes to the appropriate PipelineProcess
4. **IPC**: Signal is placed in the process's signal_queue
5. **Thread Processing**: Signal thread in the process picks up the signal
6. **Priority Handling**: Signals are sorted by priority
7. **Delivery**: `handle_signal()` is called on the pipeline instance
8. **State Transition**: Pipeline may change state based on the signal
9. **Execution**: Next `step()` call reflects the new state

## Data Flow

Data flows through the pipeline handlers in each step:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│ DataLoader     │────►│ Detect         │────►│ ArmControl    │
│ Handler        │     │ Handler        │     │ Handler       │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
     │                        │                       │
     │                        │                       │
     ▼                        ▼                       ▼
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                     Pipeline State                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Each handler:
- Processes input data (frames, detected objects, etc.)
- Updates its internal state
- Passes processed data to the next handler
- May publish debug information (when in debug mode)

## Configuration System

The pipeline is configured through a layered approach:

```
┌────────────────┐
│ default.yaml   │  Default configuration for all pipelines
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ config_override│  Runtime overrides (via API or command line)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Pipeline       │  Instance-specific configurations
│ Configuration  │
└────────────────┘
```

This approach enables:
- Sensible defaults for all pipelines
- Pipeline-specific customizations
- Runtime parameter tuning
- Configuration reuse across similar pipelines

## Current Known Challenges

### 1. Blocking Image Reception

The current implementation uses `imagezmq` with a blocking `recv_jpg()` call:

```python
# In DataLoaderHandler.process()
rpi_name, msg = self.hub.recv_jpg()  # Blocks until image is received
```

This causes issues:
- Pipeline cannot check the stop_event while waiting for an image
- Clean shutdown becomes difficult
- Responsiveness to signals can be delayed

### 2. Planned Solution: Redis Integration

The planned Redis integration will solve this issue through non-blocking operations:

```python
# Future implementation with Redis
frame_data = self.redis.blpop("camera_frames", timeout=0.1)  # Non-blocking with timeout
if not frame_data:
    return None  # Allow pipeline to check stop_event
```

Benefits:
- Non-blocking operation with timeouts
- Pipeline can check stop_event regularly
- Improved system responsiveness
- Better error handling

## Future Development

### 1. Web-based Visualization UI

The planned web UI will provide:

```
┌────────────────────────────────────────────────────────┐
│ Web UI                                                 │
│                                                        │
│  ┌─────────────────┐    ┌──────────────────────────┐   │
│  │ Pipeline Control│    │ Handler Visualization    │   │
│  │                 │    │                          │   │
│  │ ┌─────────────┐ │    │ ┌──────────┐ ┌─────────┐ │   │
│  │ │ Start/Stop  │ │    │ │ Camera   │ │ Object  │ │   │
│  │ └─────────────┘ │    │ │ Feed     │ │ Detect  │ │   │
│  │                 │    │ └──────────┘ └─────────┘ │   │
│  │ ┌─────────────┐ │    │                          │   │
│  │ │ Signals     │ │    │ ┌─────────────────────┐  │   │
│  │ └─────────────┘ │    │ │ Arm Control Status  │  │   │
│  └─────────────────┘    │ └─────────────────────┘  │   │
│                         └──────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

This will enable:
- Remote monitoring and control
- Visualization of processing steps
- Debugging assistance
- System status overview

### 2. Real-time Data Streaming

Using Redis Pub/Sub for streaming intermediate results:

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│ Pipeline    │     │              │     │ Web UI         │
│ Handlers    │────►│  Redis       │────►│ Visualization  │
│             │     │  Pub/Sub     │     │                │
└─────────────┘     └──────────────┘     └────────────────┘
```

Benefits:
- Real-time visualization of pipeline internals
- Non-intrusive monitoring
- Performance tuning insights
- Enhanced debugging capabilities

## Conclusion

The Modulus Robot Arm Control system embodies key architectural principles:

1. **Separation of Concerns**: Each component has a clear, focused responsibility
2. **Fault Isolation**: Process-based architecture prevents cascading failures
3. **Responsive Design**: Priority queues ensure critical operations aren't delayed
4. **Configuration Over Code**: YAML-based configuration enables flexibility
5. **Extensibility**: New pipelines can be added without modifying core code

These principles create a robust foundation for robot control applications while enabling future enhancements like Redis integration and web-based visualization.
