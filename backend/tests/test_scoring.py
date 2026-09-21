import pytest
from app.services.scoring import score_segment, score_route
from app.services.deviation import DeviationDetector
def test_weighted_baseline_and_neutral_unknown_lighting():
    assert score_segment({"lighting":0,"crime":100,"crowd":100,"emergency":100,"traffic":100}).total == 70
    result=score_segment({"lighting":0,"crime":100,"crowd":100,"emergency":100,"traffic":100}, False)
    assert result.total == 85 and result.confidence == "low_data"
def test_length_weighted_route(): assert score_route([(1,score_segment({x:0 for x in ['lighting','crime','crowd','emergency','traffic']})),(3,score_segment({x:100 for x in ['lighting','crime','crowd','emergency','traffic']}))]) == 75
def test_deviation_needs_consecutive_positions():
    detector=DeviationDetector(); assert not detector.observe(51); assert not detector.observe(51); assert detector.observe(51); assert not detector.observe(1)
