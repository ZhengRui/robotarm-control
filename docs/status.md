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
- YAML-based configuration system for flexible pipeline setup

### 2. API Server

The system now uses FastAPI for a modern web API:
- RESTful endpoints for pipeline management
- Support for starting, stopping, and listing available pipelines
- Signal transmission with priority levels (HIGH, NORMAL)
- Status reporting for active pipelines
- Automatic startup of initial pipeline (configurable via environment variables)

### 3. Handler System

The system employs a modular handler approach:

- **DataLoaderHandler**:
  - Receives image frames from input sources via imagezmq
  - Provides frames to the pipeline for processing
  - Currently uses a blocking call that we plan to replace with Redis

- **DetectHandler**:
  - Identifies colored objects (red, green, blue, yellow)
  - Processes frames to detect contours and calculate object properties
  - Maps pixel coordinates to real-world coordinates for robot control
  - Returns object information including position, bounding box, and orientation

- **ArmControlHandler**:
  - Controls the Yahboom robot arm for pick-and-place operations
  - Implements movement sequences for grasping objects
  - Supports different tasks (pick_and_place, pick_and_stack)
  - Includes coordinate transformations and gripper control

### 4. Pipeline Management

- **PipelineFactory**: Creates and manages pipeline instances
- **PipelineManager**: Coordinates multiple pipeline processes
- **PipelineProcess**: Encapsulates a pipeline running in a separate process
- **BasePipeline**: Abstract base class for all pipeline implementations
- Signal priority system for handling important commands first

### 5. Type System

- Comprehensive type annotations throughout the codebase
- Mypy validation for type safety
- Clear interfaces between components

## Current Implementation Status

### Working Features

1. **Pipeline Architecture**:
   - Process-based pipelines with clean lifecycle management
   - Priority-based signal handling system
   - Multi-threading for non-blocking operation
   - Configuration-driven pipeline setup

2. **API Server**:
   - FastAPI-based web service for controlling pipelines
   - RESTful endpoints for pipeline management
   - JSON-based status reporting
   - Signal transmission with priority support

3. **Robot Control**:
   - Pipeline-based control system
   - Signal-driven state management
   - Object detection integration
   - Coordinate transformation system

### Known Issues

1. **Blocking Image Reception**:
   - The `imagezmq` library uses blocking calls which can prevent clean pipeline shutdown
   - This is a critical issue planned to be addressed with Redis integration

## Future Development

### Planned Enhancements

1. **Redis Integration**:
   - Replace blocking imagezmq with Redis-based image streaming
   - Enable non-blocking image reception with timeouts
   - Add support for distributed processing of image data

2. **Web-based UI**:
   - Develop a frontend for visualizing handler results
   - Provide real-time visualization of intermediate processing steps
   - Create an intuitive interface for controlling pipelines and sending signals

3. **Real-time Visualization**:
   - Stream intermediate processing results to the UI
   - Enable debugging and monitoring of pipeline state
   - Provide insights into object detection and robot control

## Technical Details

### Dependencies

Main dependencies include:
- FastAPI: For the web API server
- imagezmq: For network-based image transmission (to be replaced with Redis)
- OpenCV: For image processing and computer vision
- pymycobot: For robot arm control
- NumPy: For numerical operations

### Code Structure

The codebase is organized in a modular fashion:
- `backend/`: Main application package
  - `app/`: FastAPI application and endpoints
  - `lib/`: Core functionality
    - `pipelines/`: Pipeline implementations and management
    - `handlers/`: Specialized processing modules
    - `utils/`: Helper functions and utilities
- `examples/`: Client-side demonstration code
- `docs/`: Documentation files

### Configuration

The system supports configuration through:
- YAML files for pipeline and handler configuration
- Environment variables for server and pipeline settings
- Command-line arguments for development and testing
- JSON-based API for runtime configuration
