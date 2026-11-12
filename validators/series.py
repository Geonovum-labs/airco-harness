"""Structural validation for data passed to the plot tool."""

import datetime
import math

from jsonschema import Draft202012Validator

SCHEMA = {
    "type": "object",
    "properties": {
        "points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "value": {"type": ["number", "null"]},
                },
                "required": ["date", "value"],
                "additionalProperties": False,
            },
        },
        "unit": {"type": "string"},
        "reference_plane": {"type": "string"},
        "connect_gaps": {"type": "boolean"},
    },
    "required": ["points", "unit", "reference_plane", "connect_gaps"],
    "additionalProperties": False,
}


def validate(data: object) -> str | None:
    errors = sorted(f"{e.json_path}: {e.message}" for e in Draft202012Validator(SCHEMA).iter_errors(data))
    if errors:
        return "; ".join(errors)
    for point in data["points"]:
        try:
            datetime.date.fromisoformat(point["date"])
        except ValueError:
            return f"invalid date: {point['date']}"
        if point["value"] is not None and not math.isfinite(point["value"]):
            return f"non-finite value on {point['date']}"
    return None
