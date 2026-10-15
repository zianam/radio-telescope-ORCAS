"""Settings that describe WHERE the telescope is and HOW it should behave.

Everything you might want to change without touching any logic lives here.
Moving the telescope to a new site should be a one-file edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# <project>/tracking/config.py -> parent.parent is the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ObserverConfig:
    """Immutable description of the observing site.

    `frozen=True` means that once created, the values can't be changed by
    accident halfway through a run. To use different settings, build a new
    ObserverConfig instead.
    """

    # TODO: replace these with your telescope's real location.
    latitude_deg: float = 42.3601  # degrees, north is positive
    longitude_deg: float = -71.0589  # degrees, EAST is positive (west is negative)
    elevation_m: float = 10.0  # meters above sea level

    # Targets lower than this are reported as not observable (trees, buildings,
    # and the motors' mechanical limits all live down here).
    min_altitude_deg: float = 5.0

    ephemeris_file: str = "de421.bsp"  # covers roughly 1900-2050
    ephemeris_dir: Path = PROJECT_ROOT / "data" / "ephemeris"

    def __post_init__(self) -> None:
        # Fail loudly at construction time, not with a strange angle later.
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError(f"latitude_deg must be in [-90, 90], got {self.latitude_deg}")
        if not -180.0 <= self.longitude_deg <= 180.0:
            raise ValueError(f"longitude_deg must be in [-180, 180], got {self.longitude_deg}")
        if not -90.0 <= self.min_altitude_deg <= 90.0:
            raise ValueError(f"min_altitude_deg must be in [-90, 90], got {self.min_altitude_deg}")