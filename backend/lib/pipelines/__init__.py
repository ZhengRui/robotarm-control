from .base import BasePipeline
from .factory import PipelineFactory
from .process import SignalPriority
from .yahboom_pipelines import YahboomPickAndPlacePipeline

# To be more flexible, we can load default.yaml here and register same pipeline class
# for different names if there is a pipeline class specified for each name in default.yaml

# Register available pipelines
PipelineFactory.register_pipeline("yahboom_pick_and_place", YahboomPickAndPlacePipeline)

__all__ = [
    "BasePipeline",
    "PipelineFactory",
    "SignalPriority",
    "YahboomPickAndPlacePipeline",
]
