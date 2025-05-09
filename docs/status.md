# Modulus Robot Arm Control - Status Report

## Repository Overview

This repository contains a modular system for robot arm control with integrated computer vision capabilities, primarily focused on controlling a Yahboom MyCobot 280 robot arm. The system is built on a pipeline-based architecture that enables real-time processing of visual data and responsive control of the robot arm.

## Core Components

### 1. Pipeline Architecture

The system has evolved to a robust pipeline architecture:
- Pipelines run in separate processes for stability and responsiveness
- Multi-threading within each pipeline for signal handling and pipeline execution
- Priority-based signal queue system for handling user commands
- Clean separation between pipeline management and execution logic
- Modular configuration system with pipeline-specific configuration files

### 2. API Server

The system now uses FastAPI for a modern web API:
- RESTful endpoints for pipeline management
- Support for starting, stopping, and listing available pipelines
- Signal transmission with priority levels (HIGH, NORMAL)
- Status reporting for active pipelines
- Automatic startup of initial pipeline (configurable via environment variables)
- WebSocket endpoints for real-time communication

### 3. Handler System

The system employs a factory-based handler approach:

- **HandlerFactory**:
  - Registers handlers for specific pipeline types
  - Supports common handlers shared across pipelines
  - Dynamic handler instantiation based on configuration
  - Clean error reporting for missing handlers

- **DataLoaderHandler**:
  - Receives image frames from input sources via imagezmq or Redis
  - Provides frames to the pipeline for processing
  - Supports both blocking (ImageZMQ) and non-blocking (Redis) implementations
  - Redis implementation provides better pipeline shutdown handling

- **Pipeline-Specific Handlers**:
  - Specialized handlers like `CalibrateHandler`, `DetectHandler`, and `ArmControlHandler`
  - Organized within pipeline module directories
  - Registered automatically during module initialization
  - Configured through pipeline configuration files

### 4. Pipeline Management

- **PipelineFactory**: Creates and manages pipeline instances with type registry
- **PipelineManager**: Coordinates multiple pipeline processes
- **PipelineProcess**: Encapsulates a pipeline running in a separate process
- **BasePipeline**: Abstract base class defining the pipeline interface
- **Pipeline Implementation**: Concrete pipeline classes with state machine logic

### 5. Data Streaming

- **DataStream**: Streaming interface with pluggable backends
- **ImageZMQDataStreamClient**: Original implementation with blocking behavior
- **RedisDataStreamClient**: New implementation with:
  - Non-blocking operation
  - Memory management via max_frames and time_window settings
  - JSON-based message format with Base64 encoding
  - Metadata support for frames

### 6. WebSocket Integration

- **ConnectionManager**: Central WebSocket connection management
  - Handles connection lifecycles (connect, disconnect)
  - Maps connections to pipeline/queue subscriptions
  - Provides broadcasting methods for messages
  - Manages background tasks for Redis subscriptions
  - Includes error handling and automatic reconnection

- **WebSocket Endpoints**:
  - `/ws/pipeline` - Streams real-time pipeline status updates
  - `/ws/queue` - Streams queue data (frames, detections)
  - Support for connection parameters (pipeline name, queue name)

- **Redis Bridge**:
  - Asynchronous Redis subscription to pipeline channels
  - Efficient message routing to WebSocket clients
  - Background tasks for monitoring pipelines
  - Robust error handling with reconnection logic

- **Message Protocol**:
  - Type-based message format for different data types
  - Timestamps for chronological ordering
  - Standardized structure for client consumption

### 7. Frontend Dashboard

- **Modern UI**: Built with Next.js, TypeScript, and Tailwind CSS
- **Pipeline Management**: Interface for listing, starting, and stopping pipelines
- **Signal Control**: UI for sending signals to control pipeline behavior
- **Visualization**: Real-time display of streaming frames and results
- **Responsive Layout**: Adapts to different screen sizes with resizable panels
- **React Query Integration**: For efficient data fetching and state management
- **WebSocket Connection**: Custom hooks for WebSocket data streaming

### 8. Type System

- Comprehensive type annotations throughout the codebase
- Mypy validation for type safety
- Clear interfaces between components using abstract base classes
- TypeScript types for frontend components and API interactions

## Current Implementation Status

### Working Features

1. **Pipeline Architecture**:
   - Process-based pipelines with clean lifecycle management
   - Priority-based signal handling system
   - Multi-threading for non-blocking operation
   - Configuration-driven pipeline setup
   - Factory pattern for pipeline and handler instantiation

2. **API Server**:
   - FastAPI-based web service for controlling pipelines
   - RESTful endpoints for pipeline management
   - JSON-based status reporting
   - Signal transmission with priority support
   - WebSocket endpoints for real-time data streaming

3. **Robot Control**:
   - Pipeline-based control system
   - Signal-driven state management
   - Object detection integration
   - Coordinate transformation system

4. **Redis Integration**:
   - Full implementation with both client and server components
   - Memory management to prevent queue growth
   - Non-blocking operation with timeout support
   - Configurable time window for memory management
   - WebSocket bridge for sending Redis data to browser clients

5. **WebSocket System**:
   - Complete WebSocket implementation for real-time updates
   - Pipeline status streaming via dedicated endpoint
   - Queue data streaming for visualization
   - Connection management with proper lifecycle handling
   - Error recovery with automatic reconnection
   - Efficient multiplexing to multiple clients

6. **Frontend Dashboard**:
   - Pipeline selection and control interface
   - Signal sending capability
   - Real-time status monitoring
   - Frame visualization from pipeline queues
   - Responsive layout for different devices
   - React Query for API data management
   - WebSocket integration for live updates

### Known Issues

- Configuration updates for running pipelines not yet implemented
- Mobile experience needs further optimization
- Error handling could be improved with more user-friendly notifications
- Video feed performance could be optimized for slower networks

## Future Development

### Planned Enhancements

1. **Pipeline Configuration UI**:
   - Add UI for modifying pipeline configurations
   - Implement backend support for configuration updates
   - Create dynamic form generation based on config schema

2. **Enhanced Visualization**:
   - Add controls for display options (zoom, pan, etc.)

## Technical Details

### Dependencies

#### Backend:
- FastAPI: For the web API server
- imagezmq: For network-based image transmission
- Redis: For non-blocking image streaming
- OpenCV: For image processing and computer vision
- pymycobot: For robot arm control
- NumPy: For numerical operations
- aioredis: For asynchronous Redis operations

#### Frontend:
- Next.js: React framework with server-side rendering
- TypeScript: Type-safe JavaScript
- Tailwind CSS: Utility-first CSS framework
- Shadcn/UI: High-quality UI components
- React Query: Data fetching and caching
- Jotai: Lightweight state management

### Code Structure

The codebase is organized in a modular fashion:

#### Backend Structure:
- `backend/`: Main application package
  - `app/`: FastAPI application and endpoints
    - `api/`: API routes and WebSocket endpoints
    - `utils/`: Helper utilities including WebSocket manager
    - `config.py`: Central configuration loader
  - `lib/`: Core functionality
    - `pipelines/`: Pipeline implementations and management
      - `base.py`: Abstract base class for pipelines
      - `factory.py`: Pipeline registration and creation
      - `manager.py`: Multi-process pipeline management
      - `process.py`: Process encapsulation for pipelines
      - `yahboom/`: Yahboom-specific pipeline implementation
        - `pipeline.py`: Concrete pipeline state machine
        - `config.yaml`: Default pipeline configuration
        - `handlers/`: Pipeline-specific handlers
    - `handlers/`: Handler framework
      - `base.py`: Handler interface definition
      - `factory.py`: Handler registration and creation
      - `data_loader.py`: Data loading handlers (Redis, ImageZMQ)
    - `utils/`: Helper functions and utilities
  - `config/`: Environment-specific configuration
    - `dev.yaml`: Development environment overrides
    - `prod.yaml`: Production environment overrides

#### Frontend Structure:
- `frontend/`: Next.js dashboard
  - `src/`: Source code
    - `app/`: Next.js app router components
      - `Dashboard.tsx`: Main dashboard component
      - `VisualizationCard.tsx`: Frame visualization component
    - `components/`: Reusable UI components
    - `lib/`: Utility functions and API client
    - `hooks/`: Custom React hooks for data and WebSockets

### Configuration System

The system now employs a multi-layered configuration approach:

1. **Pipeline Default Configuration**:
   - Stored in `lib/pipelines/[pipeline_type]/config.yaml`
   - Defines default settings for each pipeline type
   - Includes handler initialization and processing parameters
   - Loaded automatically by the `BasePipeline` class

2. **Environment Overrides**:
   - Stored in `config/[env].yaml` (e.g., `dev.yaml`, `prod.yaml`)
   - Contains environment-specific overrides
   - Selected via the `ENV` environment variable
   - Loaded by the central `app/config.py` module

3. **Configuration Merging**:
   - Environment overrides are merged with pipeline defaults
   - Uses a custom merger with specific rules for lists and dictionaries
   - Allows for partial overrides while maintaining defaults

4. **Handler Configuration**:
   - Each handler has an `init` section for initialization parameters
   - And a `process` section for runtime parameters
   - Debug settings can be configured per handler rather than globally
   - Handlers are instantiated automatically based on these configs

To set up configuration files:
```bash
cp backend/config/dev.example.yaml backend/config/dev.yaml
cp backend/config/prod.example.yaml backend/config/prod.yaml
```

Edit these files to customize settings for your environment.
