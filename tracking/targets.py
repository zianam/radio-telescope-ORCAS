"""Things the telescope can point at.

Design: `Target` is an abstract base class (an "interface with a bit of shared
code"). Every kind of target knows how to turn itself into a Skyfield object.
The calculator only ever talks to `Target`, so adding a new kind of target
(a satellite, a comet) means adding a class here and changing nothing else.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from skyfield.api import Star


class UnknownTargetError(ValueError):
    """Raised when a target name isn't in the catalog."""


class Target(ABC):
    """Anything the telescope can be pointed at."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def skyfield_object(self, ephemeris):
        """Return the Skyfield object to observe, given the loaded ephemeris."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._name!r})"


class SolarSystemTarget(Target):
    """A planet, the Sun, or the Moon, looked up in the JPL ephemeris.

    In de421.bsp the outer planets only exist as system barycenters, which is
    accurate enough for pointing, so we map friendly names to ephemeris keys.
    """

    _EPHEMERIS_KEYS = {
        "sun": "sun",
        "moon": "moon",
        "mercury": "mercury",
        "venus": "venus",
        "mars": "mars barycenter",
        "jupiter": "jupiter barycenter",
        "saturn": "saturn barycenter",
        "uranus": "uranus barycenter",
        "neptune": "neptune barycenter",
        "pluto": "pluto barycenter",
    }

    def __init__(self, name: str) -> None:
        key = name.strip().lower()
        if key not in self._EPHEMERIS_KEYS:
            raise UnknownTargetError(
                f"{name!r} is not a solar-system target. "
                f"Choices: {', '.join(self._EPHEMERIS_KEYS)}"
            )
        super().__init__(key)
        self._ephemeris_key = self._EPHEMERIS_KEYS[key]

    @classmethod
    def known_names(cls) -> list[str]:
        return list(cls._EPHEMERIS_KEYS)

    def skyfield_object(self, ephemeris):
        return ephemeris[self._ephemeris_key]


class FixedSourceTarget(Target):
    """A star or radio source at fixed J2000 coordinates (RA in HOURS, Dec in degrees).

    Proper motion is ignored, which is fine for a telescope with a beam
    much wider than the arcseconds-per-year these objects drift.
    """

    def __init__(self, name: str, ra_hours: float, dec_degrees: float) -> None:
        if not 0.0 <= ra_hours < 24.0:
            raise ValueError(f"ra_hours must be in [0, 24), got {ra_hours}")
        if not -90.0 <= dec_degrees <= 90.0:
            raise ValueError(f"dec_degrees must be in [-90, 90], got {dec_degrees}")
        super().__init__(name)
        self._ra_hours = ra_hours
        self._dec_degrees = dec_degrees

    def skyfield_object(self, ephemeris):
        return Star(ra_hours=self._ra_hours, dec_degrees=self._dec_degrees)


class TargetCatalog:
    """Looks targets up by name, and lets you register new ones.

    Solar-system names are resolved automatically; fixed sources are
    registered explicitly.
    """

    def __init__(self) -> None:
        self._fixed: dict[str, FixedSourceTarget] = {}

    def register(self, target: FixedSourceTarget) -> None:
        self._fixed[target.name.lower()] = target

    def get(self, name: str) -> Target:
        key = name.strip().lower()
        if key in self._fixed:
            return self._fixed[key]
        try:
            return SolarSystemTarget(key)
        except UnknownTargetError:
            raise UnknownTargetError(
                f"Unknown target {name!r}. Available: {', '.join(self.names())}"
            ) from None

    def names(self) -> list[str]:
        return SolarSystemTarget.known_names() + sorted(self._fixed)


def default_catalog() -> TargetCatalog:
    """The built-in catalog: solar system plus a few classic radio sources.

    Coordinates are approximate J2000 values (good to well under a degree).
    Double-check them against Stellarium or SIMBAD before relying on them.
    """
    catalog = TargetCatalog()
    catalog.register(FixedSourceTarget("cas-a", ra_hours=23.3900, dec_degrees=58.8150))
    catalog.register(FixedSourceTarget("cyg-a", ra_hours=19.9912, dec_degrees=40.7339))
    catalog.register(FixedSourceTarget("sgr-a", ra_hours=17.7611, dec_degrees=-29.0078))
    return catalog