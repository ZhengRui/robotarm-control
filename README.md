# Modulus Robot Arm Control

A modular system for controlling robot arms with computer vision integration. This project provides a framework for using cameras to detect objects and guide a robot arm to pick, place, and manipulate them.

## Features

- **Object Detection**: Color-based object detection and tracking
- **Robot Control**: Control of Yahboom MyCobot 280 robot arm
- **Pipeline Architecture**: Modular pipeline system with priority-based signal handling
- **FastAPI Integration**: Modern web API for controlling pipelines and sending signals
- **Process Management**: Multi-process architecture for reliable pipeline execution
- **Redis Integration**: Non-blocking image streaming with memory management
- **WebSocket Integration**: Real-time updates and data streaming to the frontend
- **Configurable**: Factory-based handler system with layered configuration
- **Modern Web Dashboard**: Next.js frontend for monitoring and controlling the system

## Project Structure

- `backend/`: Server-side implementation
  - `app/`: FastAPI application and endpoints
    - `api/`: REST and WebSocket endpoints
    - `utils/`: Helper utilities including WebSocket manager
    - `config.py`: Central configuration loader
  - `lib/`: Core functionality
    - `pipelines/`: Pipeline implementations with process-based architecture
      - `base.py`: Abstract base class for pipelines
      - `factory.py`: Pipeline registration and creation
      - `manager.py`: Multi-process pipeline management
      - `process.py`: Process encapsulation for pipelines
      - `yahboom/`: Pipeline-specific implementation with handlers
    - `handlers/`: Handler framework
      - `base.py`: Handler interface definition
      - `factory.py`: Handler registration and creation
      - `data_loader.py`: Data loading handlers (Redis, ImageZMQ)
    - `utils/`: Helper functions and utilities
  - `config/`: Environment-specific configuration files
- `frontend/`: Next.js dashboard
  - `src/`: Source code
    - `app/`: Next.js app router components
    - `components/`: Reusable UI components
    - `lib/`: Utility functions and API client
    - `hooks/`: Custom React hooks for data and WebSockets
- `examples/`: Client-side demonstration code
- `.hooks/`: Project-wide git hooks
- `docs/`: Documentation files

## Backend Setup

### Prerequisites

- Python 3.8 or newer
- USB connection to the robot arm (for control functionality)
- Camera (USB webcam, IP camera, or video file)
- Redis server (for data streaming and pipeline communication)

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd modulus-robotarm-control
   ```

2. Create a virtual environment and activate it using uv:
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```

3. Install dependencies using uv:
   ```bash
   uv sync
   ```

   For users in China or experiencing network issues:
   ```bash
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Robot Arm Setup

1. Connect the Yahboom MyCobot 280 to your computer via USB
2. The default port is set to `/dev/ttyUSB0`. If your robot is connected to a different port, you'll need to specify it in your configuration.

### Configuration System

The system employs a multi-layered configuration approach:

1. **Pipeline Default Configuration**:
   - Located in `lib/pipelines/[pipeline_type]/config.yaml`
   - Defines default settings for each pipeline type
   - Includes handler initialization and processing parameters
   - Contains debug settings for individual handlers

2. **Environment Overrides**:
   - Located in `config/[env].yaml` (e.g., `dev.yaml`, `prod.yaml`)
   - Contains environment-specific overrides
   - Selected via the `ENV` environment variable
   - Lists all available pipelines in the environment

You can copy the example files to create your own configurations:

```bash
cp backend/config/dev.example.yaml backend/config/dev.yaml
cp backend/config/prod.example.yaml backend/config/prod.yaml
```

Edit these files to adjust settings like:
- Robot arm port and connection parameters
- Image processing parameters
- Pipeline default behaviors
- Redis connection settings
- Debug settings for specific handlers

### Starting the Backend Server

Start the server:

```bash
python main.py
```

You can specify the environment and initial pipeline:

```bash
ENV=dev PIPELINE=yahboom_pick_and_place python main.py
```

### Running the Streaming Client

To stream video to the system:

```bash
python -m examples.streaming --source webcam:0 --keep_size --lossless --enable_freeze --visualization --max-frames 100 --time-window 0.1
```

Options:
- `--source`: Video file, webcam (webcam:0), or directory of images
- `--keep_size`: Maintain original image dimensions
- `--lossless`: Use lossless encoding for frames
- `--enable_freeze`: Allow pausing the stream with spacebar
- `--visualization`: Show video feed with visualization
- `--max-frames`: Set max number of frames for Redis memory management
- `--time-window`: Set time window in seconds for Redis memory management

### API Endpoints

The system exposes the following API endpoints:

- `GET /pipelines`: List all available pipelines defined in the config file (running and non-running)
- `GET /pipeline`: Get detailed information about a specific pipeline
- `POST /pipeline/start`: Start a specific pipeline
- `POST /pipeline/stop`: Stop a running pipeline
- `POST /pipeline/signal`: Send a signal to a running pipeline

### WebSocket Endpoints

For real-time updates and data streaming:

- `ws/pipeline`: Stream real-time pipeline state updates and events
- `ws/queue`: Stream real-time frame data and processing results

#### WebSocket Connection Parameters

- Pipeline WebSocket: `ws://host:port/ws/pipeline?pipeline_name=<pipeline_name>`
- Queue WebSocket: `ws://host:port/ws/queue?pipeline_name=<pipeline_name>&queue_name=<queue_name>`

### Example Requests

Start a pipeline:
```bash
curl -X POST "http://localhost:8000/pipeline/start?pipeline_name=yahboom_pick_and_place" -H "Content-Type: application/json"
```

Send a signal:
```bash
curl -X POST "http://localhost:8000/pipeline/signal?pipeline_name=yahboom_pick_and_place&signal_name=pick_red&priority=HIGH" -H "Content-Type: application/json"
```

## Frontend Setup

### Tech Stack

- **Next.js**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/UI**: High-quality, accessible UI components
- **React Query**: Data fetching and state management
- **Jotai**: Lightweight state management

### Architecture

- **Backend Communication**:
  - REST API for basic operations (list pipelines, start/stop)
  - WebSocket bridge for real-time updates and streaming
  - Redis for backend pipeline communication

- **UI Layout**:
  - Left sidebar: Foldable configuration panel for pipeline settings
  - Main area: Visualization of streaming frames and pipeline output

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install

# Run development server
bun run dev
```

### Building

```bash
# Build for production
bun run build

# Start production server
bun run start
```

### Features

- Pipeline management (list, start, stop)
- Signal control with available signals list
- Real-time pipeline status monitoring
- Real-time frame visualization from pipeline queues
- Responsive layout for different devices

## Git Hooks Setup

This project uses git hooks to ensure code quality and consistent commit messages.

### Setting Up Hooks

1. First, prepare the Husky hooks in the frontend directory:
   ```bash
   cd frontend
   bun run prepare:husky
   cd ..
   ```

2. Reset the hooks path to use the project's custom hooks:
   ```bash
   git config core.hooksPath .hooks
   ```

This two-step process ensures that both frontend and backend hooks are properly installed. The first command sets up Husky in the frontend directory, but it also changes your git hooks path to `frontend/.husky`. The second command resets the hooks path to the project root's `.hooks` directory, which contains the hooks for the entire project.

### Hook Functions

- **pre-commit**: Runs linting and formatting checks for both frontend and backend code
- **commit-msg**: Validates commit messages according to conventional commit format

## Next Steps

- **Pipeline Configuration UI**: Add interfaces for modifying pipeline configurations
- **Enhanced Visualization**: Add controls for display options and multi-queue visualization
- **User Authentication**: Add secure access with role-based permissions
- **Additional Robot Models**: Support for different robot arm models and configurations
- **Performance Optimizations**: Improve frame rate control and network efficiency
- **Real-time Analytics**: Add metrics and performance monitoring
