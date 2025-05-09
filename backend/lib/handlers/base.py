from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from .data_loader import FrameResult


class BaseHandler(ABC):
    """Base class for all handlers."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Union[Dict[str, Any], FrameResult]:
        """Process the handler logic."""
        pass
