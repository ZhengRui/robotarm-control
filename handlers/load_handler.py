def load_handler(handler: str):
    if handler.lower() == "calibrate":
        from .calibrate import CalibrateHandler

        handler = CalibrateHandler()

    return handler
