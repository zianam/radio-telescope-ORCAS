"""The core math: (target, time) -> azimuth/altitude.

This file never prints, never opens a serial port, and never knows that a motor
exists. It only answers one question: "where should the telescope point?"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from skyfield.api import Loader, wgs84

from .config import ObserverConfig
from .models import Pointing
from .targets import Target


class PointingCalculator:
    """Computes where targets appear in the sky for one observing site.

    Encapsulation: Skyfield's timescale, ephemeris, and observer objects are
    created once in __init__ and kept private. Callers just use `compute()`.
    Loading the ephemeris is slow (and downloads it the first time), so we do
    it once here instead of on every call.
    """

    def __init__(self, config: ObserverConfig | None = None) -> None:
        self._config = config or ObserverConfig()

        loader = Loader(str(self._config.ephemeris_dir))
        self._timescale = loader.timescale()
        self._ephemeris = loader(self._config.ephemeris_file)  # downloads if missing

        site = wgs84.latlon(
            self._config.latitude_deg,
            self._config.longitude_deg,
            elevation_m=self._config.elevation_m,
        )
        # "Earth's center + a spot on its surface" = our telescope.
        self._observer = self._ephemeris["earth"] + site

    @property
    def config(self) -> ObserverConfig:
        return self._config

    def compute(self, target: Target, when: datetime | None = None) -> Pointing:
        """Return the pointing for `target` at time `when` (default: right now).

        `when` must be timezone-aware so there's never any doubt about what
        time it means. Passing a fixed time makes results repeatable, which is
        what makes testing possible.
        """
        if when is None:
            t = self._timescale.now()
        else:
            if when.tzinfo is None:
                raise ValueError("`when` must be timezone-aware, e.g. datetime(..., tzinfo=timezone.utc)")
            t = self._timescale.from_datetime(when)

        astrometric = self._observer.at(t).observe(target.skyfield_object(self._ephemeris))
        alt, az, distance = astrometric.apparent().altaz()

        return Pointing(
            target_name=target.name,
            timestamp=t.utc_datetime().astimezone(timezone.utc),
            azimuth_deg=float(az.degrees),
            altitude_deg=float(alt.degrees),
            distance_au=float(distance.au),
            observable=bool(alt.degrees >= self._config.min_altitude_deg),
        )

    def compute_many(
        self, targets: Iterable[Target], when: datetime | None = None
    ) -> list[Pointing]:
        """Compute several targets at the SAME instant (so they're comparable)."""
        if when is None:
            when = datetime.now(timezone.utc)
        return [self.compute(target, when) for target in targets]