import pytest
from app.elo import elo_probability, elo_update, k_decay, mean_center

@pytest.mark.parametrize("rating_a, rating_b, expected", [
    (1000, 1000, 0.5),
    (1200, 1000, pytest.approx(0.7597, 0.001)),
    (1000, 1200, pytest.approx(0.2402, 0.001)),
])
def test_elo_probability(rating_a, rating_b, expected):
    assert elo_probability(rating_a, rating_b) == expected

def test_elo_update_win():
    new_a, new_b = elo_update(1000, 1000, winner=0, k=32)
    assert new_a > 1000
    assert new_b < 1000

def test_elo_update_loss():
    new_a, new_b = elo_update(1000, 1000, winner=1, k=32)
    assert new_a < 1000
    assert new_b > 1000

def test_k_decay():
    assert k_decay(32, 1) == 32
    assert k_decay(32, 4) == pytest.approx(16, 0.1)

def test_mean_center():
    scores = [10, 20, 30]
    centered = mean_center(scores)
    assert sum(centered) == pytest.approx(0)
    assert centered[0] < 0 and centered[2] > 0 