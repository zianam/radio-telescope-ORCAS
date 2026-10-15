"""Data types that the tracking code hands to the rest of the system."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Pointing:
    """Where to aim the telescope, for one target, at one moment.

    This is the INTERFACE between tracking and hardware. The motor code only
    needs to know about this class, not about Skyfield or astronomy.
    """

    target_name: str
    timestamp: datetime  # timezone-aware, UTC
    azimuth_deg: float  # compass direction: 0 = north, 90 = east, 180 = south
    altitude_deg: float  # angle above the horizon: 0 = horizon, 90 = straight up
    distance_au: float  # distance in astronomical units (meaningless for stars)
    observable: bool  # above the configured minimum altitude?

    @property
    def above_horizon(self) -> bool:
        return self.altitude_deg > 0.0

    def __str__(self) -> str:
        status = "observable" if self.observable else (
            "below minimum altitude" if self.above_horizon else "below horizon"
        )
        text = (
            f"{self.target_name:<12} "
            f"Az={self.azimuth_deg:7.2f}\N{DEGREE SIGN}  "
            f"Alt={self.altitude_deg:6.2f}\N{DEGREE SIGN}  ({status})"
        )
        # Stars have no meaningful distance, so only show it for solar-system objects.
        if math.isfinite(self.distance_au) and self.distance_au < 1000.0:
            text += f"  dist={self.distance_au:.3f} AU"
        return text