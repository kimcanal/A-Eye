from __future__ import annotations

"""Minimal runnable scaffold for Module 1.

This module creates a tiny city scenario, moves vehicles for a few steps,
and writes machine-readable logs that can be reused by later documentation
or Unity integration work.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from random import Random
import sys

# 패키지 내부 스크립트 직접 실행 시 발생하는 Import 에러 방지를 위해 프로젝트 최상위 경로 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from module1_simulation.minimal_stub import DEFAULT_SCENARIO, Scenario
from module1_simulation.render_simulation import render_from_log


RNG = Random(42)


@dataclass
class Entity:
    entity_id: str
    kind: str
    x: int
    y: int


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
    scenario = DEFAULT_SCENARIO
    entities = make_entities(scenario)
    out_dir = Path("outputs/module1")
    out_dir.mkdir(parents=True, exist_ok=True)

    logs = [snapshot(0, entities, ["scenario initialized"])]

    for step in range(1, scenario.steps + 1):
        events = step_entities(entities, scenario.city_size)
        logs.append(snapshot(step, entities, events or ["no movement events"]))

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
    render_outputs = render_from_log(output_file, out_dir)
    summary.update(render_outputs)
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"saved: {output_file}")
    print(f"saved: {summary_file}")
    print(f"saved: {render_outputs['overview_image']}")
    print(f"saved: {render_outputs['animation_gif']}")
    print(f"total entities: {len(entities)}")
    print(f"steps: {scenario.steps}")


if __name__ == "__main__":
    main()
