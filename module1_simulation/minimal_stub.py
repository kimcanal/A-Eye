from __future__ import annotations

"""Module 1 scenario blueprint.

This file keeps the scenario definition separate from the runnable simulation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    city_size: tuple[int, int] = (3, 3)
    passengers: int = 5
    taxis: int = 3
    regular_vehicle_types: tuple[str, ...] = ("sedan", "suv", "van", "compact")
    vehicles_per_type: int = 5
    autonomous_vehicles: int = 1
    obstacles: int = 2
    steps: int = 5


DEFAULT_SCENARIO = Scenario()
