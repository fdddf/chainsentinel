import pytest

from chainsentinel.evaluate import evaluate

SEEDS = {"0xs1", "0xs2"}
HOLDOUT = {"0xh1", "0xh2", "0xh3", "0xh4"}


def test_seeds_in_ranking_are_ignored():
    # A rule that just returns the seeds must not get credit.
    m = evaluate(["0xs1", "0xh1", "0xs2", "0xu1"], holdout=HOLDOUT, seeds=SEEDS, ks=(2,))
    assert m["recall@2"] == pytest.approx(1 / 4)
    assert m["hits@2"] == 1


def test_precision_is_a_lower_bound_and_named_so():
    m = evaluate(["0xh1", "0xu1", "0xh2", "0xu2"], holdout=HOLDOUT, seeds=SEEDS, ks=(4,))
    assert m["precision_lb@4"] == pytest.approx(2 / 4)
    assert "precision@4" not in m


def test_case_insensitive_and_deduplicated():
    m = evaluate(["0xH1", "0xh1", "0xh2"], holdout=HOLDOUT, seeds=SEEDS, ks=(2,))
    assert m["hits@2"] == 2


def test_k_larger_than_ranking():
    m = evaluate(["0xh1"], holdout=HOLDOUT, seeds=SEEDS, ks=(50,))
    assert m["recall@50"] == pytest.approx(1 / 4)
    assert m["n_candidates"] == 1
