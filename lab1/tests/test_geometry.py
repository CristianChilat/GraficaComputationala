import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import point_in_rect, segment_hits_rect, clamp_step_inside


def test_point_inside_rect():
    assert point_in_rect(0, 0, -10, -10, 10, 10) is True
    assert point_in_rect(11, 0, -10, -10, 10, 10) is False


def test_segment_hits_rect_crossing():
    # horizontal segment through rect
    assert segment_hits_rect(-20, 0, 20, 0, -5, -5, 5, 5) is True


def test_segment_misses_rect():
    assert segment_hits_rect(-20, 20, 20, 20, -5, -5, 5, 5) is False


def test_clamp_step_stops_at_edge():
    # window half-size 100; step would go to x=110 -> stay at edge
    nx, ny = clamp_step_inside(95, 0, 110, 0, 100, 100)
    assert nx == 100
    assert ny == 0
