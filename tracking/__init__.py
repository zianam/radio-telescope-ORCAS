"""Telescope tracking: where should we point?

Public API (import from here, not from the individual files):

    from tracking import PointingCalculator, default_catalog
"""

from .config import ObserverConfig
from .models import Pointing
from .pointing import PointingCalculator
from .targets import (
    FixedSourceTarget,
    SolarSystemTarget,
    Target,
    TargetCatalog,
    UnknownTargetError,
    default_catalog,
)

__all__ = [
    "ObserverConfig",
    "Pointing",
    "PointingCalculator",
    "Target",
    "SolarSystemTarget",
    "FixedSourceTarget",
    "TargetCatalog",
    "UnknownTargetError",
    "default_catalog",
]
