from typing import Any, Dict, Optional

from .base import BasePipeline
from .yahboom_pipelines import YahboomPickAndPlacePipeline


class PipelineFactory:
    """Factory for creating pipeline instances."""

    @staticmethod
    def create_pipeline(pipeline_name: str, config_override: Optional[Dict[str, Any]] = None, debug: bool = False):
        """Create a pipeline instance based on name and config.

        Args:
            pipeline_name: Name of the pipeline to create
            config_override: Optional configuration to override defaults
            debug: Whether to enable debug mode

        Returns:
            Instance of the requested pipeline

        Raises:
            ValueError: If pipeline_name is unknown
        """
        if pipeline_name == "yahboom_pick_and_place":
            return YahboomPickAndPlacePipeline(config_override=config_override, debug=debug)
        else:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")


__all__ = ["BasePipeline", "PipelineFactory", "YahboomPickAndPlacePipeline"]
