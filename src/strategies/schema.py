import json
from pathlib import Path

_BIAS_FIELD = {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0,
}

_ADJUSTMENT = {
    "type": "object",
    "required": ["condition", "biases"],
    "properties": {
        "condition": {"type": "string"},
        "biases": {
            "type": "object",
            "additionalProperties": {"type": "number"},
        },
    },
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "required": ["name", "race", "initial_biases", "priority_formulas"],
    "properties": {
        "name": {"type": "string"},
        "race": {"type": "string"},
        "description": {"type": "string"},
        "initial_biases": {
            "type": "object",
            "additionalProperties": _BIAS_FIELD,
        },
        "scouting_adjustments": {
            "type": "array",
            "items": _ADJUSTMENT,
        },
        "priority_formulas": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "meta": {
            "type": "object",
            "properties": {
                "bias_speed": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "scout_decay_rate": {"type": "number", "minimum": 0.0},
                "max_workers": {"type": "integer", "minimum": 1},
                "target_bases": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


def validate(data: dict) -> list[str]:
    errors = []

    required = SCHEMA.get("required", [])
    for key in required:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    if "initial_biases" in data:
        for key, value in data["initial_biases"].items():
            if not isinstance(value, (int, float)):
                errors.append(f"initial_biases.{key}: expected number, got {type(value).__name__}")
            elif value < 0.0 or value > 1.0:
                errors.append(f"initial_biases.{key}: value {value} outside [0.0, 1.0]")

    if "scouting_adjustments" in data:
        for i, adj in enumerate(data["scouting_adjustments"]):
            if not isinstance(adj, dict):
                errors.append(f"scouting_adjustments[{i}]: expected object")
                continue
            if "condition" not in adj:
                errors.append(f"scouting_adjustments[{i}]: missing 'condition'")
            if "biases" not in adj:
                errors.append(f"scouting_adjustments[{i}]: missing 'biases'")

    if "meta" in data and data["meta"]:
        meta = data["meta"]
        if "bias_speed" in meta:
            v = meta["bias_speed"]
            if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
                errors.append(f"meta.bias_speed: {v} outside [0.0, 1.0]")

    return errors


class ValidationError(Exception):
    pass
