from app.optimizer import Candidate, allocate_budget


def test_moq_and_budget_constraints():
    candidates = [
        Candidate("A", 6, 18, 1_000, 400, 15, 0.9),
        Candidate("B", 4, 12, 2_000, 600, 10, 0.6),
    ]
    result = allocate_budget(candidates, budget=20_000)
    assert result["A"] % 6 == 0
    assert result["B"] % 4 == 0
    assert result["A"] * 1_000 + result["B"] * 2_000 <= 20_000


def test_optimizer_is_deterministic():
    candidates = [Candidate("A", 2, 8, 1_000, 300, 8, 0.8)]
    assert allocate_budget(candidates, 5_000) == allocate_budget(candidates, 5_000)

