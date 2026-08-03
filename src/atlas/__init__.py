"""
ATLAS: Adaptive Thinking and Learning Architecture System

A dynamic knowledge management framework that integrates pattern language
approaches with question-oriented procedures to manage and interpret
meaning and context across diverse knowledge domains.
"""

__version__ = "1.0.0"
__author__ = "Active Inference Institute"
__license__ = "CC-BY-4.0"

# Core imports for easy access
from .core.engine import ATLASEngine
from .entities.entity import Entity
from .patterns.pattern import Pattern
from .queries.iquery import iQuery
from .interfaces.prompt_interface import PromptInterface

# Make key classes available at package level
__all__ = [
    "ATLASEngine",
    "Entity",
    "Pattern",
    "iQuery",
    "PromptInterface",
    "__version__",
]