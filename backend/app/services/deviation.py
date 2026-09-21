"""State-only deviation detector. Spatial distance calculation belongs in PostGIS in production."""
from dataclasses import dataclass
@dataclass
class DeviationDetector:
    threshold_m: float = 50
    consecutive_required: int = 3
    consecutive: int = 0
    def observe(self, distance_m: float) -> bool:
        self.consecutive = self.consecutive + 1 if distance_m > self.threshold_m else 0
        return self.consecutive >= self.consecutive_required
