"""Tests for the tracking package.

These check PHYSICAL facts (the Sun is high at local noon, a star near the
celestial pole sits at an altitude equal to your latitude) rather than just
copying numbers out of the program, so they catch real mistakes.
"""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from tracking import (
    FixedSourceTarget,
    ObserverConfig,
    PointingCalculator,
    SolarSystemTarget,
    UnknownTargetError,
    default_catalog,
)

BOSTON = ObserverConfig(latitude_deg=42.3601, longitude_deg=-71.0589, elevation_m=10.0)


@pytest.fixture(scope="module")
def calc() -> PointingCalculator:
    # Module scope: loading the ephemeris is slow, so do it once for all tests.
    return PointingCalculator(BOSTON)


@pytest.fixture(scope="module")
def catalog():
    return default_catalog()


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def test_sun_is_high_and_south_near_local_noon_at_solstice(calc, catalog):
    # 17:00 UTC on 21 June is about 1 pm daylight time in Boston: just after solar noon.
    p = calc.compute(catalog.get("sun"), utc(2026, 6, 21, 17, 0))
    assert 69.0 < p.altitude_deg < 73.0  # roughly 90 - latitude + 23.4 degrees
    assert 175.0 < p.azimuth_deg < 200.0  # due south, a little west
    assert p.observable


def test_sun_is_below_horizon_at_local_midnight(calc, catalog):
    p = calc.compute(catalog.get("sun"), utc(2026, 6, 22, 4, 0))
    assert p.altitude_deg < 0
    assert not p.above_horizon
    assert not p.observable


def test_angles_are_in_valid_ranges_for_every_target(calc, catalog):
    when = utc(2026, 3, 15, 3, 0)
    for name in catalog.names():
        p = calc.compute(catalog.get(name), when)
        assert 0.0 <= p.azimuth_deg < 360.0, name
        assert -90.0 <= p.altitude_deg <= 90.0, name


def test_star_at_celestial_pole_sits_at_latitude_altitude_due_north(calc):
    pole = FixedSourceTarget("pole", ra_hours=0.0, dec_degrees=89.99)
    for hour in (0, 6, 12, 18):  # should not move as the Earth rotates
        p = calc.compute(pole, utc(2026, 3, 15, hour, 0))
        assert abs(p.altitude_deg - BOSTON.latitude_deg) < 0.6
        assert min(p.azimuth_deg, 360.0 - p.azimuth_deg) < 3.0


def test_observable_flag_respects_minimum_altitude(catalog):
    strict = PointingCalculator(
        ObserverConfig(latitude_deg=42.3601, longitude_deg=-71.0589, min_altitude_deg=89.0)
    )
    p = strict.compute(catalog.get("sun"), utc(2026, 6, 21, 17, 0))
    assert p.above_horizon and not p.observable


def test_same_time_gives_identical_results(calc, catalog):
    when = utc(2026, 1, 1, 12, 0)
    assert calc.compute(catalog.get("mars"), when) == calc.compute(catalog.get("mars"), when)


def test_compute_many_uses_one_shared_timestamp(calc, catalog):
    results = calc.compute_many([catalog.get("sun"), catalog.get("moon")])
    assert results[0].timestamp == results[1].timestamp


def test_naive_datetime_is_rejected(calc, catalog):
    with pytest.raises(ValueError):
        calc.compute(catalog.get("sun"), datetime(2026, 1, 1, 12, 0))


def test_unknown_target_gives_a_helpful_error(catalog):
    with pytest.raises(UnknownTargetError) as info:
        catalog.get("planet-x")
    assert "mars" in str(info.value)  # the message lists the valid choices


def test_target_names_are_case_and_space_insensitive(catalog):
    assert catalog.get("  Mars ").name == "mars"
    assert SolarSystemTarget("JUPITER").name == "jupiter"


def test_pointing_is_immutable(calc, catalog):
    p = calc.compute(catalog.get("sun"), utc(2026, 6, 21, 17, 0))
    with pytest.raises(FrozenInstanceError):
        p.azimuth_deg = 0.0


def test_config_rejects_impossible_latitude():
    with pytest.raises(ValueError):
        ObserverConfig(latitude_deg=123.0)