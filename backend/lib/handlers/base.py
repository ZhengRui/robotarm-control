from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Union

# Use conditional import to avoid circular import at runtime
# while still providing type information for static type checkers
if TYPE_CHECKING:
    from .data_loader import FrameResult


class BaseHandler(ABC):
    """Base class for all handlers."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Union[Dict[str, Any], "FrameResult"]:
        """Process the handler logic."""
        pass
