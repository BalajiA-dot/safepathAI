"""Transparent baseline scoring; use this fallback whenever a pilot model is unavailable."""
from dataclasses import dataclass

WEIGHTS = {"lighting": .30, "crime": .25, "crowd": .20, "emergency": .15, "traffic": .10}
@dataclass(frozen=True)
class Score:
    total: float
    confidence: str

def score_segment(factors: dict[str, float], has_lighting_data: bool = True) -> Score:
    """Score five 0–100 factors, neutralising unknown lighting rather than assuming dark."""
    values = {key: max(0, min(100, factors.get(key, 50))) for key in WEIGHTS}
    if not has_lighting_data: values["lighting"] = 50
    return Score(round(sum(values[k] * weight for k, weight in WEIGHTS.items()), 2), "high" if has_lighting_data else "low_data")

def score_route(segments: list[tuple[float, Score]]) -> float:
    """Return the required length-weighted mean; tuples are (length_m, segment score)."""
    total_length = sum(length for length, _ in segments)
    if total_length <= 0: raise ValueError("A route needs positive segment length")
    return round(sum(length * score.total for length, score in segments) / total_length, 2)
