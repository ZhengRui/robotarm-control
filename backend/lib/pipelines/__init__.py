from .base import BasePipeline
from .factory import PipelineFactory
from .modulus import Pipeline as ModulusPipeline
from .process import SignalPriority
from .yahboom import Pipeline as YahboomPickAndPlacePipeline

PipelineFactory.register_pipeline("yahboom_pick_and_place", YahboomPickAndPlacePipeline)
PipelineFactory.register_pipeline("modulus", ModulusPipeline)

__all__ = [
    "BasePipeline",
    "ModulusPipeline",
    "PipelineFactory",
    "SignalPriority",
    "YahboomPickAndPlacePipeline",
]
