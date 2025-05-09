from ...handlers import HandlerFactory
from .handlers import ArmControlHandler, CalibrateHandler, DetectHandler
from .pipeline import Pipeline

HandlerFactory.register_for_pipeline(Pipeline, "calibrate", CalibrateHandler)
HandlerFactory.register_for_pipeline(Pipeline, "detect", DetectHandler)
HandlerFactory.register_for_pipeline(Pipeline, "arm_control", ArmControlHandler)

__all__ = ["ArmControlHandler", "CalibrateHandler", "DetectHandler", "Pipeline"]
