# Modulus Robot Arm Control Frontend

A modern dashboard interface for controlling and monitoring robot arm pipelines.

## Tech Stack

- **Next.js**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/UI**: High-quality, accessible UI components

## Architecture

- **Backend Communication**:

  - REST API for basic operations (list pipelines, start/stop)
  - WebSocket bridge for real-time updates and streaming
  - Redis for backend pipeline communication

- **UI Layout**:
  - Left sidebar: Foldable configuration panel for pipeline settings
  - Main area: Visualization of streaming frames and pipeline output

## Development

### Getting Started

```bash
# Install dependencies
bun install

# Run development server
bun dev
```

### Building

```bash
# Build for production
bun run build

# Start production server
bun start
```

## Features

- Pipeline management (list, start, stop)
- Configuration editing
- Signal control
- Real-time frame visualization
- Status monitoring
