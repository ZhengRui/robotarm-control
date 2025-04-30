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

### 4. Dual Backend Data Streaming Architecture

The system supports two interchangeable backends for image data streaming:

```
┌───────────────┐                     ┌───────────────┐
│               │      ImageZMQ       │               │
│  Streaming    ├────────────────────►│  Pipeline     │
│  Client       │                     │  Process      │
│               │       Redis         │               │
│               ├────────────────────►│               │
└───────────────┘                     └───────────────┘
```

This design provides:
- Flexibility to choose the appropriate backend based on requirements
- Backwards compatibility with existing ImageZMQ implementations
- Enhanced performance and reliability with Redis
- Seamless transition between backends with consistent APIs

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

### Layer 6: Data Streaming System (Streaming Layer)

The data streaming system provides interfaces for sending and receiving image data:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Streaming Layer                                                        │
│                                                                        │
│  ┌───────────────────────────────┐       ┌────────────────────────────┐│
│  │ DataStream                    │       │ DataLoaderHandler          ││
│  │                               │       │                            ││
│  │ ┌─────────────────────────┐   │       │ ┌──────────────────────┐   ││
│  │ │ ImageZMQDataStreamClient│   │       │ │ ImageZMQDataLoader   │   ││
│  │ └─────────────────────────┘   │       │ └──────────────────────┘   ││
│  │                               │       │                            ││
│  │ ┌─────────────────────────┐   │       │ ┌──────────────────────┐   ││
│  │ │ RedisDataStreamClient   │   │       │ │ RedisDataLoader      │   ││
│  │ └─────────────────────────┘   │       │ └──────────────────────┘   ││
│  │                               │       │                            ││
│  └───────────────────────────────┘       └────────────────────────────┘│
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

Key responsibilities:
- Providing a consistent API for image streaming regardless of backend
- Managing connections to image sources
- Handling encoding/decoding of image data
- Implementing memory management for queues
- Supporting metadata with image frames

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

The system employs a layered configuration approach with a clear hierarchy of selection and overrides:

```
┌─────────────────────────────┐  Server Initialization Parameters
│ Command-line Args / ENV     │  • ENV=[dev|prod]   - Selects which config to load
│                             │  • PIPELINE=name    - Selects pipeline to auto-start
│                             │  • DEBUG=[true|false] - Toggles debug mode
└──────────────┬──────────────┘
               │ Selects
               ▼
┌─────────────────────────────┐
│ config/{env}.yaml           │  Environment-specific pipeline configurations
│ (dev.yaml, prod.yaml)       │  Detailed settings for handlers, backends,
│                             │  and pipeline behaviors
└──────────────┬──────────────┘
               │ Merged with
               ▼
┌─────────────────────────────┐
│ lib/pipelines/default.yaml  │  System-wide pipeline defaults
│                             │  (used for any settings not specified in
│                             │  the environment config)
└──────────────┬──────────────┘
               │ Applied to
               ▼
┌─────────────────────────────┐
│ Pipeline Instance State     │  Runtime state maintained by each
│                             │  pipeline instance during execution
└─────────────────────────────┘
```

Key points about this configuration system:

• **Selection Process**:
  - Command-line args and ENV variables determine *which* config file to load (dev/prod)
  - They also specify which pipeline to auto-start, if any
  - They don't override the content of config files, just select which ones to use

• **Configuration Merging**:
  - The selected environment config (`config/{env}.yaml`) provides environment-specific settings
  - Any settings not found in the environment config are taken from the system defaults
  - The merged configuration is then used to initialize the pipeline

• **Server Startup Behavior**:
  - If the `PIPELINE` environment variable is set, the specified pipeline starts automatically
  - Without the `PIPELINE` variable, the server starts with no active pipelines
  - The `ENV` variable determines which configuration file to load (defaults to `dev`)

• **API Control**:
  - Regardless of initialization, pipelines can be started, stopped, and managed via API endpoints
  - `/pipelines/start`, `/pipelines/stop`, `/signal`, etc.

## Redis Integration

### Design Overview

The system now implements Redis as an alternative backend for image streaming:

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│                │     │              │     │                │
│ DataStream     │────►│  Redis       │────►│ DataLoader     │
│ (Client)       │     │  Server      │     │ (Handler)      │
│                │     │              │     │                │
└────────────────┘     └──────────────┘     └────────────────┘
```

### Implementation Details

1. **Client Side (DataStream)**
   - Abstract `DataStreamClient` base class with backend-agnostic interface
   - `ImageZMQDataStreamClient` for backward compatibility
   - `RedisDataStreamClient` for modern, non-blocking operation
   - Base64 encoding for JSON compatibility in Redis

2. **Server Side (DataLoaderHandler)**
   - Abstract `BaseDataLoaderHandler` interface
   - `ImageZMQDataLoaderHandler` for backward compatibility
   - `RedisDataLoaderHandler` for non-blocking operation
   - Support for waiting with timeouts or immediate return

3. **Memory Management**
   - Configurable memory limits via `max_frames` parameter
   - Time-based cleanup via `time_window` parameter (in seconds)
   - Automatic queue trimming to prevent memory overflow
   - Time-stamped frames for chronological management

### Benefits

The Redis integration delivers several important benefits:

1. **Non-blocking Operation**
   - Timeouts allow the pipeline to check for shutdown signals
   - Improved responsiveness to control commands
   - Better pipeline termination handling

2. **Memory Management**
   - Prevents memory leaks from unbounded queue growth
   - Two complementary approaches:
     - Frame count limit with `max_frames`
     - Time-based expiration with `time_window`
   - Automatic cleanup of outdated frames

3. **Scalability**
   - Support for multiple consumers of the same stream
   - Ability to distribute processing across multiple nodes
   - Higher throughput compared to point-to-point communication

4. **Reliability**
   - Persistence options for critical applications
   - Built-in handling for connection issues
   - Greater fault tolerance in network environments

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
6. **Interchangeable Backends**: Support for both ImageZMQ (not recommended) and Redis backends
