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

### Redis Server Setup

Redis is required for data streaming and pipeline communication. Follow these steps to install and configure Redis:

1. **Install Redis**:

   **On Ubuntu/Debian**:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

   **On macOS**:
   ```bash
   brew install redis
   ```

   **On Windows**:
   Install using Windows Subsystem for Linux (WSL) or download from [Redis for Windows](https://github.com/microsoftarchive/redis/releases).

2. **Start Redis**:

   **On Ubuntu/Debian**:
   ```bash
   sudo systemctl start redis-server
   ```

   **On macOS**:
   ```bash
   brew services start redis
   ```

   **On Windows**:
   Run the redis-server.exe application.

3. **Verify Installation**:
   ```bash
   redis-cli ping
   ```

   You should receive a `PONG` response.

4. **Configure Redis for Remote Connections** (Optional, only if accessing Redis from other machines):

   Edit the Redis configuration file:

   **On Ubuntu/Debian**:
   ```bash
   sudo nano /etc/redis/redis.conf
   ```

   **On macOS**:
   ```bash
   nano $(brew --prefix)/etc/redis.conf
   ```

   Make the following changes:
   - Change `bind 127.0.0.1` to `bind 0.0.0.0` to allow connections from any IP
   - Set `protected-mode no` to disable protected mode (required for Redis 6.0 and newer)
   - Optionally, set a password by uncommenting the `requirepass` line and adding a strong password

   Save and restart Redis:

   **On Ubuntu/Debian**:
   ```bash
   sudo systemctl restart redis-server
   ```

   **On macOS**:
   ```bash
   brew services restart redis
   ```

   Remember to update the Redis connection settings in your environment configuration file if you set a password.

5. The default configuration in the project uses localhost:6379. If you need to change these settings, update them in your environment's configuration file.

### Remote Robot Control Setup

This setup is **only needed when the robot arm is connected to a different machine** than the one running the backend server. If your robot arm is directly connected to the machine running the backend, you can skip this section.

If you're using a remote robot control configuration (with `remote_addr` set in your configuration file):

1. **Download the Server_280.py script**:

   Download the MyCobot280 remote control server script from:
   ```
   https://github.com/modulus-inc/modulus-robotarm-control/blob/main/demo/Server_280.py
   ```

2. **Run the script on the remote machine**:

   The remote machine needs to be physically connected to the robot arm.
   ```bash
   # On the remote machine
   python Server_280.py
   ```

3. **Configure your environment**:

   Make sure your `dev.yaml` or `prod.yaml` file has the `remote_addr` set to the IP address of the remote machine.
   ```yaml
   # Example configuration
   handlers:
     robot_control:
       init:
         remote_addr: "192.168.1.100"  # IP address of remote machine
   ```

This setup enables the backend to send control commands to a remote machine that is directly connected to the robot arm.

### Starting the Backend Server

Start the server:

```bash
python main.py
```

You can specify the environment and initial pipeline:

```bash
ENV=dev PIPELINE=yahboom_pick_and_place python main.py
```

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

## Running the Streaming Client

The backend system is designed to process image frames, but it needs a source of data to operate. Once the backend server is running, it waits for streaming data inputs before the pipelines can process anything meaningful.

To stream data to the system:

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
- `--time-window`: Set latest time window in seconds for Redis memory management

### Complete Data Flow

When running a complete system:

1. **The streaming client** captures frames from a camera or video file and sends them to Redis
2. **The backend pipeline** receives these frames through its DataLoaderHandler
3. **Pipeline handlers** process the frames (detection, control calculations, etc.)
4. **The frontend dashboard** connects to the backend through:
   - REST API for pipeline operations (start/stop)
   - WebSockets for real-time updates and frame data

With this setup, you can:
- Start a pipeline from the dashboard
- Send control signals to change pipeline behavior
- Visualize the streaming frames and processing results in real-time
- See the robot arm respond to the detected objects

The frontend connects to the published queues of each pipeline, allowing you to monitor what the pipeline "sees" and how it's processing the data.

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

## Implementing a Custom Pipeline

The Modulus Robot Arm Control system is designed to be extensible through custom pipelines. Here's how to implement your own:

### 1. Create a New Pipeline Module

Create a new directory for your pipeline under `backend/lib/pipelines/`:

```
backend/lib/pipelines/my_custom_pipeline/
├── __init__.py
├── config.yaml
├── handlers/
│   ├── __init__.py
│   └── custom_handler.py
└── pipeline.py
```

### 2. Implement Your Pipeline Class

Create a `pipeline.py` file that implements the pipeline state machine:

<details>
<summary>click to expand code: pipeline.py</summary>

```python
from typing import Dict, List, Optional, Any, Set
import json
from enum import Enum, auto
from pydantic import BaseModel

from ...utils.logger import get_logger
from ..base import BasePipeline

logger = get_logger("my_custom_pipeline")

class PipelineState(str, Enum):
    """Pipeline state enumeration."""
    IDLE = "IDLE"
    INIT = "INIT"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"

class PipelineSignal(str, Enum):
    """Pipeline signal enumeration."""
    START = "start"
    STOP = "stop"
    RESET = "reset"

class PipelineQueue(str, Enum):
    """Pipeline queue enumeration."""
    FRAMES = "frames"
    DEBUG = "debug"

class CustomConfigSchema(BaseModel):
    """Schema for pipeline configuration validation."""
    parameter1: str
    parameter2: int

class Pipeline(BasePipeline):
    """Custom pipeline implementation."""

    def __init__(self, pipeline_name: str) -> None:
        """Initialize the pipeline.

        Args:
            pipeline_name: Name of the pipeline instance
        """
        super().__init__(pipeline_name)

        # Define current state
        self._current_state = PipelineState.IDLE

    @property
    def current_state(self) -> str:
        """Get the current state of the pipeline.

        Returns:
            Current state as a string
        """
        return self._current_state.value

    @classmethod
    def get_available_signals(cls) -> List[str]:
        """Get the list of available signals.

        Returns:
            List of signal names
        """
        return [signal.value for signal in PipelineSignal]

    @classmethod
    def get_available_states(cls) -> List[str]:
        """Get the list of possible pipeline states.

        Returns:
            List of state names
        """
        return [state.value for state in PipelineState]

    @classmethod
    def get_available_queues(cls) -> List[str]:
        """Get the list of available data queues.

        Returns:
            List of queue names
        """
        return [queue.value for queue in PipelineQueue]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get the configuration schema for this pipeline.

        Returns:
            Configuration schema as a dictionary
        """
        return CustomConfigSchema.schema()

    def handle_signal(self, signal_name: str, **kwargs: Any) -> None:
        """Handle incoming signals.

        Args:
            signal_name: Name of the signal to handle
            **kwargs: Additional signal parameters
        """
        logger.info(f"Handling signal: {signal_name}")

        if signal_name == PipelineSignal.START.value and self._current_state == PipelineState.IDLE:
            self._current_state = PipelineState.INIT
        elif signal_name == PipelineSignal.STOP.value:
            self._current_state = PipelineState.IDLE
        elif signal_name == PipelineSignal.RESET.value:
            self._current_state = PipelineState.IDLE
            # Reset any pipeline state here

    def step(self) -> None:
        """Execute a single pipeline step based on current state."""
        if self._current_state == PipelineState.IDLE:
            # Do nothing in IDLE state
            pass

        elif self._current_state == PipelineState.INIT:
            logger.info("Initializing pipeline")
            # Perform initialization tasks
            self._current_state = PipelineState.RUNNING

        elif self._current_state == PipelineState.RUNNING:
            # Get data from data loader handler
            data_loader = self.handlers.get("data_loader")
            if data_loader:
                # Get process parameters from config
                data_loader_params = self.config.get("handlers", {}).get("data_loader", {}).get("process", {})
                result = data_loader.process(**data_loader_params)

                frame = None
                if result and "frame" in result:
                    frame = result["frame"]

                if frame is None:
                    return

                # Process frame with your custom handlers
                custom_handler = self.handlers.get("custom_handler")
                if custom_handler:
                    # Get custom handler process parameters
                    custom_handler_params = self.config.get("handlers", {}).get("custom_handler", {}).get("process", {})
                    result = custom_handler.process(frame=frame, **custom_handler_params)

                    # Publish debug visualization if debug mode is enabled
                    debug_image = result.get("debug_image")
                    if debug_image is not None:
                        self.publish_to_queue(
                            PipelineQueue.DEBUG.value,
                            base64.b64encode(debug_image.tobytes()).decode("utf-8") # assume debug_image is ndarray/cvimage
                        )

                    # Check for completion conditions
                    if result.get("status") == "complete":
                        self._current_state = PipelineState.COMPLETE

                # Always publish the original frame to the frames queue
                self.publish_to_queue(
                    PipelineQueue.FRAMES.value,
                    base64.b64encode(frame.tobytes()).decode("utf-8") # assue frame is ndarray/cvimage
                )

        elif self._current_state == PipelineState.COMPLETE:
            logger.info("Pipeline execution complete")
            self._current_state = PipelineState.IDLE
```

</details>

### 3. Create Pipeline Configuration

Define a `config.yaml` file for your pipeline's default configuration:

<details>
<summary>click to expand code: config.yaml</summary>

```yaml
Pipeline:
  # Redis settings
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: null

  # Handler configuration
  handlers:
    data_loader:
      init:
        backend: "redis"  # will use redis settings from the above redis block
      process:
        wait: false

    custom_handler:
      init:
        parameter1: "value1"
        parameter2: 42
      process:
        debug: false
```

</details>

### 4. Implement Custom Handlers

Create your custom handlers in the `handlers` directory:

<details>
<summary>click to expand code: custom_handler.py</summary>

```python
# custom_handler.py
from typing import Any, Dict

from ....handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    """Custom processing handler."""

    def __init__(self, parameter1: str = "", parameter2: int = 0) -> None:
        """Initialize the handler.

        Args:
            parameter1: First parameter
            parameter2: Second parameter
        """
        self.parameter1 = parameter1
        self.parameter2 = parameter2

    def process(self, frame: Any = None, debug: bool = False) -> Dict[str, Any]:
        """Process the input frame.

        Args:
            frame: Input frame to process
            debug: Enable debug mode to visualize processing steps

        Returns:
            Processing results
        """
        # Implement your custom processing logic here
        result = {
            "data": None
        }

        # Example processing
        if frame is not None:
            # Do something with the frame
            # ...
            result["data"] = "Processed data"

            # Optional debug visualization
            if debug:
                # Create debug visualizations for monitoring
                result["debug_image"] = frame  # Example: return visualized frame

        return result
```

</details>

### 5. Register Handlers

In your pipeline module's `__init__.py`, register the handlers:

```python
from ...handlers import HandlerFactory
from .handlers.custom_handler import CustomHandler
from .pipeline import Pipeline

# Register custom handlers for this pipeline
HandlerFactory.register_for_pipeline(Pipeline, "custom_handler", CustomHandler)

__all__ = ["Pipeline", "CustomHandler"]
```

### 6. Register Pipeline

In the main `backend/lib/pipelines/__init__.py` file, register your pipeline:

```python
# Add your import
from .my_custom_pipeline import Pipeline as MyCustomPipeline

# Add your pipeline registration
PipelineFactory.register_pipeline("my_custom_pipeline", MyCustomPipeline)

# Update __all__ to include your pipeline
__all__ = [
    "BasePipeline",
    "PipelineFactory",
    "SignalPriority",
    "YahboomPickAndPlacePipeline",
    "ModulusPipeline",
    "MyCustomPipeline",  # Add this line
]
```

### 7. Add Pipeline to Environment Configuration

Add your pipeline to your environment configuration file (e.g., `backend/config/dev.yaml`):

```yaml
# Existing pipelines
yahboom_pick_and_place:
   pipeline: yahboom_pick_and_place

# Your new pipeline
my_custom_pipeline:
   pipeline: my_custom_pipeline
   # Environment-specific overrides
   handlers:
   custom_handler:
      init:
         parameter1: "custom_value"
```

### 8. Using Your Custom Pipeline

After implementation, you can use your pipeline through the API:

```bash
# Start your custom pipeline
curl -X POST "http://localhost:8000/pipeline/start?pipeline_name=my_custom_pipeline"

# Send signals to your pipeline
curl -X POST "http://localhost:8000/pipeline/signal?pipeline_name=my_custom_pipeline&signal_name=start"
```

Or start it automatically when the server launches:

```bash
ENV=dev PIPELINE=my_custom_pipeline python main.py
```

This framework allows you to focus on implementing the specific business logic for your pipeline while leveraging the existing infrastructure for process management, configuration, and API integration.

## Next Steps

- **Pipeline Configuration UI**: Add interfaces for modifying pipeline configurations
