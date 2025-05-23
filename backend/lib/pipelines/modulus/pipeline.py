from typing import Any, Dict, Optional

from ..base import BasePipeline


class Pipeline(BasePipeline):
    def __init__(self, pipeline_name: str = "modulus", config_override: Optional[Dict[str, Any]] = None):
        super().__init__(pipeline_name, config_override)

    def handle_signal(self, signal: str) -> None:
        pass

    def step(self) -> None:
        pass
