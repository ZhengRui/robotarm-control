from typing import Any, Dict, Union

from .arm_control import ArmControlHandler
from .calibrate import CalibrateHandler
from .data_loader import DataLoaderHandler
from .detect import DetectHandler


class HandlerFactory:
    """Factory for creating handler instances."""

    @staticmethod
    def create_handler(
        handler_type: str, config: Dict[str, Any]
    ) -> Union[CalibrateHandler, DetectHandler, ArmControlHandler, DataLoaderHandler]:
        """Create a handler instance based on type and config.

        Args:
            handler_type: Type of handler to create
            config: Configuration for the handler

        Returns:
            Instance of the requested handler

        Raises:
            ValueError: If handler_type is unknown
        """
        if handler_type == "calibrate":
            return CalibrateHandler(**config)
        elif handler_type == "detect":
            return DetectHandler(**config)
        elif handler_type == "armcontrol":
            return ArmControlHandler(**config)
        elif handler_type == "dataloader":
            return DataLoaderHandler(**config)
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")


__all__ = ["CalibrateHandler", "DataLoaderHandler", "DetectHandler", "HandlerFactory"]
