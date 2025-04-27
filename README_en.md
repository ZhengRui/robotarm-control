# Modulus Robot Arm Control

A modular system for controlling robot arms with computer vision integration. This project provides a framework for using cameras to detect objects and guide a robot arm to pick, place, and manipulate them.

## Features

- **Object Detection**: Color-based object detection and tracking
- **Robot Control**: Control of Yahboom MyCobot 280 robot arm
- **Client-Server Architecture**: Separate image processing server from client cameras
- **Modular Design**: Swap out different handlers for detection, calibration, and control
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
2. The default port is set to `/dev/ttyUSB0`. If your robot is connected to a different port, you'll need to specify it when running the handlers.

## Usage

### Starting the Server

Run the server with a specific handler:

```bash
python server.py --handler detect
```

Available handlers:
- `detect`: For object detection only
- `calibrate`: For calibrating the camera-to-robot coordinate system
- `armcontrol`: For robot arm control with object detection

Use the `--debug` flag to enable visualization:

```bash
python server.py --handler detect --debug
```

### Running the Client

The client streams images to the server for processing:

```bash
python -m examples/streaming.py --source webcam:0 --server 127.0.0.1
```

Options for `--source`:
- `webcam:0`, `webcam:1`, etc.: For webcam devices
- Path to a video file: For streaming from a recorded video
- Path to an image or directory of images: For processing static images

Additional options:
- `--max_size`: Maximum size of the longer side of the image (default: 800)
- `--keep_size`: Keep original image size
- `--jpg_quality`: JPEG compression quality (1-100)
- `--lossless`: Send raw frames without compression
- `--autoplay`: Automatically advance through image sources
- `--enable_freeze`: Enable pausing with spacebar
- `--write_to`: Directory to save processed images

## Project Structure

- `server.py`: Main server implementation
- `handlers/`: Specialized modules for different tasks
  - `detect.py`: Object detection handler
  - `armcontrol.py`: Robot arm control handler
  - `calibrate.py`: Calibration handler
- `examples/`: Client-side demonstration code
- `utils/`: Helper utilities
- `docs/`: Documentation files
  - `status.md`: Detailed status report
  - `pymycobot_api_docs.md`: Robot API documentation
