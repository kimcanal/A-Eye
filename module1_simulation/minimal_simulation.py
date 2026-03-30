from __future__ import annotations

"""Minimal runnable scaffold for Module 1.

Role: create a tiny city scenario, move the vehicles for a few steps, and
write logs that can be inspected later.

This is not a full 3D engine. It is a lightweight simulation skeleton that
represents the Module 1 requirements in executable form.
"""

from dataclasses import asdict, dataclass
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


def step_entities(entities: list[Entity], city_size: tuple[int, int]) -> list[str]:
    w, h = city_size
    events: list[str] = []

    for e in entities:
        if e.kind in {"passenger", "obstacle"}:
            continue
        old = (e.x, e.y)
        dx = RNG.choice([-1, 0, 1])
        dy = RNG.choice([-1, 0, 1])
        e.x = max(0, min(w - 1, e.x + dx))
        e.y = max(0, min(h - 1, e.y + dy))
        if (e.x, e.y) != old:
            events.append(f"{e.entity_id}:{e.kind} moved {old}->{(e.x, e.y)}")

    return events


def snapshot(step: int, entities: list[Entity], events: list[str]) -> dict:
    return {
        "step": step,
        "entity_count": len(entities),
        "taxi_count": sum(1 for e in entities if e.kind == "taxi"),
        "passenger_count": sum(1 for e in entities if e.kind == "passenger"),
        "obstacle_count": sum(1 for e in entities if e.kind == "obstacle"),
        "events": events,
        "entities": [asdict(e) for e in entities],
    }


def main() -> None:
    scenario = Scenario()
    entities = make_entities(scenario)
    out_dir = Path("outputs/module1")
    out_dir.mkdir(parents=True, exist_ok=True)

    logs = []
    logs.append(snapshot(0, entities, ["scenario initialized"]))

    for step in range(1, scenario.steps + 1):
        events = step_entities(entities, scenario.city_size)
        if not events:
            events = ["no movement events"]
        logs.append(snapshot(step, entities, events))

    output_file = out_dir / "module1_simulation_log.json"
    output_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "city_size": list(scenario.city_size),
        "passengers": scenario.passengers,
        "taxis": scenario.taxis,
        "regular_vehicle_types": list(scenario.regular_vehicle_types),
        "vehicles_per_type": scenario.vehicles_per_type,
        "autonomous_vehicles": scenario.autonomous_vehicles,
        "obstacles": scenario.obstacles,
        "steps": scenario.steps,
        "total_entities": len(entities),
        "output_file": str(output_file),
    }
    summary_file = out_dir / "module1_summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {output_file}")
    print(f"saved: {summary_file}")
    print(f"total entities: {len(entities)}")
    print(f"steps: {scenario.steps}")


if __name__ == "__main__":
    main()
