# Modulus Robot Arm Control - Status Report

## Repository Overview

This repository contains a modular system for robot arm control with integrated computer vision capabilities, primarily focused on controlling a Yahboom MyCobot 280 robot arm. The system is built on a client-server architecture that enables real-time processing of visual data to guide robotic manipulation tasks.

## Core Components

### 1. Server Architecture

The system uses a server-client architecture where:
- The server (server.py) receives image data via imagezmq
- Images are processed by specialized handlers for detection or control
- Results are sent back to the client

### 2. Handler Modules

The system employs a modular handler approach:

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

- **CalibrateHandler**:
  - Likely used for calibrating the camera-to-robot coordinate system
  - Not fully explored in this analysis

### 3. Vision Processing

- Uses OpenCV for image processing
- Implements color-based object detection using HSV thresholds
- Calculates contours and object properties (center, bounding box, orientation)
- Transforms pixel coordinates to robot arm coordinates

### 4. Robot Control

- Uses pymycobot library to control the MyCobot280
- Supports standard movement operations:
  - Moving to specific coordinates
  - Controlling the gripper
  - Executing pick and place sequences
  - Moving to predefined positions for sorting or stacking

### 5. Client Tools

- Streaming client (examples/streaming.py) for sending image data to the server
- Supports various input sources (webcam, image files, video files)
- Includes visualization options and data compression settings

## Current Implementation Status

### Working Features

1. **Object Detection**:
   - Color-based detection of square objects
   - Real-time processing of camera feeds
   - Coordinate transformation from pixel to robot space

2. **Robot Control**:
   - Basic movement and gripper operations
   - Pick and place functionality
   - Object sorting by color
   - Stacking operations

3. **Client-Server Communication**:
   - Image transmission via imagezmq
   - JSON-based response protocol
   - Support for various image sources

## Technical Details

### Dependencies

Main dependencies include:
- imagezmq: For network-based image transmission
- OpenCV: For image processing and computer vision
- pymycobot: For robot arm control
- NumPy: For numerical operations

### Code Structure

The codebase is organized in a modular fashion:
- Root directory contains the main server code
- handlers/ directory contains specialized processing modules
- utils/ directory likely contains helper functions
- examples/ directory contains client-side demonstration code

### Configuration

The system supports configuration through:
- Command-line arguments for core functionality
- Object initialization parameters for detailed behavior customization
- HSV color thresholds for object detection
- Coordinate mappings for camera-to-robot transformations
