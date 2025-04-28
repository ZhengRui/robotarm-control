import argparse

import uvicorn

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Robot Arm Control Server")
    parser.add_argument(
        "--pipeline", type=str, default=None, help="Name of the pipeline to start on application startup (optional)"
    )
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug mode for the pipeline")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API server on")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload on code changes")

    args = parser.parse_args()

    # Set environment variables for the arguments so they're passed to the FastAPI app
    import os

    if args.pipeline:
        os.environ["PIPELINE"] = args.pipeline
    if args.debug:
        os.environ["DEBUG"] = "true"

    # Run the server
    uvicorn.run("app.api.serv:app", host="0.0.0.0", port=args.port, log_level="info", reload=args.reload)
