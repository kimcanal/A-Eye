from __future__ import annotations

"""Minimal runnable scaffold for Module 1.

This is not a full 3D engine. It is a lightweight simulation skeleton that
creates the required objects, advances a few time steps, and prints/logs the
state so the Module 1 requirements are represented in executable form.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from random import Random


RNG = Random(42)


@dataclass
class Entity:
    entity_id: str
    kind: str
    x: int
    y: int


@dataclass
class Scenario:
    city_size: tuple[int, int] = (3, 3)
    passengers: int = 5
    taxis: int = 3
    regular_vehicle_types: tuple[str, ...] = ("sedan", "suv", "van", "compact")
    vehicles_per_type: int = 5
    autonomous_vehicles: int = 1
    obstacles: int = 2
    steps: int = 5


def make_entities(s: Scenario) -> list[Entity]:
    entities: list[Entity] = []
    w, h = s.city_size

    for i in range(s.passengers):
        entities.append(Entity(f"p{i+1}", "passenger", RNG.randrange(w), RNG.randrange(h)))
    for i in range(s.taxis):
        entities.append(Entity(f"t{i+1}", "taxi", RNG.randrange(w), RNG.randrange(h)))
    for vehicle_kind in s.regular_vehicle_types:
        for i in range(s.vehicles_per_type):
            entities.append(Entity(f"{vehicle_kind[:2]}{i+1}", vehicle_kind, RNG.randrange(w), RNG.randrange(h)))
    for i in range(s.autonomous_vehicles):
        entities.append(Entity(f"av{i+1}", "autonomous_vehicle", RNG.randrange(w), RNG.randrange(h)))
    for i in range(s.obstacles):
        entities.append(Entity(f"o{i+1}", "obstacle", RNG.randrange(w), RNG.randrange(h)))

    return entities


def step_entities(entities: list[Entity], city_size: tuple[int, int]) -> None:
    w, h = city_size
    for e in entities:
        if e.kind in {"passenger", "obstacle"}:
            continue
        dx = RNG.choice([-1, 0, 1])
        dy = RNG.choice([-1, 0, 1])
        e.x = max(0, min(w - 1, e.x + dx))
        e.y = max(0, min(h - 1, e.y + dy))


def snapshot(step: int, entities: list[Entity]) -> dict:
    return {
        "step": step,
        "entities": [asdict(e) for e in entities],
    }


def main() -> None:
    scenario = Scenario()
    entities = make_entities(scenario)
    out_dir = Path("outputs/module1")
    out_dir.mkdir(parents=True, exist_ok=True)

    logs = []
    logs.append(snapshot(0, entities))

    for step in range(1, scenario.steps + 1):
        step_entities(entities, scenario.city_size)
        logs.append(snapshot(step, entities))

    output_file = out_dir / "module1_simulation_log.json"
    output_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {output_file}")
    print(f"entities: {len(entities)}")
    print(f"steps: {scenario.steps}")


if __name__ == "__main__":
    main()
