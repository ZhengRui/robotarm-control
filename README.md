# Modulus Robot Arm Control

A modular system for controlling robot arms with computer vision integration. This project provides a framework for using cameras to detect objects and guide a robot arm to pick, place, and manipulate them.

## Features

- **Object Detection**: Color-based object detection and tracking
- **Robot Control**: Control of Yahboom MyCobot 280 robot arm
- **Pipeline Architecture**: Modular pipeline system with priority-based signal handling
- **FastAPI Integration**: Modern web API for controlling pipelines and sending signals
- **Process Management**: Multi-process architecture for reliable pipeline execution
- **Configurable**: Adjust for different robot setups, detection parameters, and tasks

## Installation

### Prerequisites

- Python 3.8 or newer
- USB connection to the robot arm (for control functionality)
- Camera (USB webcam, IP camera, or video file)

### Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd modulus-robotarm-control
   ```

2. Create a virtual environment and activate it using uv:
   ```bash
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

## Usage

### Starting the Server

Run the server with a specific pipeline:

```bash
python -m backend.main --pipeline yahboom_pick_and_place
```

Or set the initial pipeline through environment variables:

```bash
PIPELINE=yahboom_pick_and_place DEBUG=true python -m backend.main
```

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

## Project Structure

- `backend/`: Main server implementation
  - `app/`: FastAPI application and endpoints
  - `lib/`: Core functionality
    - `pipelines/`: Pipeline implementations with process-based architecture
    - `handlers/`: Specialized handlers for vision and robot control
- `examples/`: Client-side demonstration code
- `docs/`: Documentation files

## TODO

- **Redis Integration**: Replace blocking imagezmq with Redis-based image streaming
- **Web-based UI**: Develop a frontend for visualizing handler results and controlling pipelines
- **Real-time Visualization**: Stream intermediate processing results to the UI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
