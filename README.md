# Modulus Robot Arm Control

A modular system for controlling robot arms with computer vision integration. This project provides a framework for using cameras to detect objects and guide a robot arm to pick, place, and manipulate them.

## Features

- **Object Detection**: Color-based object detection and tracking
- **Robot Control**: Control of Yahboom MyCobot 280 robot arm
- **Pipeline Architecture**: Modular pipeline system with priority-based signal handling
- **FastAPI Integration**: Modern web API for controlling pipelines and sending signals
- **Process Management**: Multi-process architecture for reliable pipeline execution
- **Redis Integration**: Non-blocking image streaming with memory management
- **Configurable**: Adjust for different robot setups, detection parameters, and tasks
- **Modern Web Dashboard**: Next.js frontend for monitoring and controlling the system

## Project Structure

- `backend/`: Server-side implementation
  - `app/`: FastAPI application and endpoints
  - `lib/`: Core functionality
    - `pipelines/`: Pipeline implementations with process-based architecture
    - `handlers/`: Specialized handlers for vision and robot control
    - `utils/`: Helper functions and utilities
  - `config/`: Configuration files for different environments
- `frontend/`: Next.js dashboard
  - Modern UI for monitoring and controlling pipelines
  - WebSocket integration for real-time updates
- `examples/`: Client-side demonstration code
- `.hooks/`: Project-wide git hooks
- `docs/`: Documentation files

## Backend Setup

### Prerequisites

- Python 3.8 or newer
- USB connection to the robot arm (for control functionality)
- Camera (USB webcam, IP camera, or video file)

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

### Robot Arm Setup

1. Connect the Yahboom MyCobot 280 to your computer via USB
2. The default port is set to `/dev/ttyUSB0`. If your robot is connected to a different port, you'll need to specify it in your configuration.

### Configuration

The system uses YAML configuration files located in the `backend/config/` directory:

- `dev.yaml`: Development environment configuration
- `prod.yaml`: Production environment configuration

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

### Starting the Backend Server

Start the server in debug mode:

```bash
DEBUG=true python train.py
```

For additional control, you can specify a pipeline:

```bash
PIPELINE=yahboom_pick_and_place DEBUG=true python train.py
```

### Running the Streaming Client

To stream video to the system:

```bash
python -m examples.streaming --source /path/to/video.mp4 --keep_size --lossless --enable_freeze --visualization --max-frames 100 --time-window 2
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

- `GET /pipelines`: List all available and running pipelines
- `POST /pipelines/start`: Start a specific pipeline
- `POST /pipelines/stop`: Stop a running pipeline
- `POST /signal`: Send a signal to a running pipeline
- `GET /status`: Get detailed status information for a pipeline

### Example Request

Start a pipeline:
```bash
curl -X POST "http://localhost:8000/pipelines/start" -H "Content-Type: application/json" -d '{"pipeline_name": "yahboom_pick_and_place", "debug": true}'
```

Send a signal:
```bash
curl -X POST "http://localhost:8000/signal?pipeline_name=yahboom_pick_and_place" -H "Content-Type: application/json" -d '{"signal": "pick_red", "priority": "HIGH"}'
```

## Frontend Setup

### Tech Stack

- **Next.js**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/UI**: High-quality, accessible UI components

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
- Configuration editing
- Signal control
- Real-time frame visualization
- Status monitoring

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

- **Additional Robot Models**: Support for different robot arm models and configurations
- **Enhanced UI Features**: Expand dashboard capabilities for better visualization and control
- **Real-time Analytics**: Add metrics and performance monitoring
