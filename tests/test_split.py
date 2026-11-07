from chainsentinel.split import split_seeds

ADDRS = [f"0x{i:040x}" for i in range(100)]


def test_split_is_disjoint_and_complete():
    seeds, holdout = split_seeds(ADDRS, seed_frac=0.2, seed=42)
    assert set(seeds).isdisjoint(holdout)
    assert set(seeds) | set(holdout) == set(ADDRS)
    assert len(seeds) == 20


def test_split_is_deterministic_and_order_independent():
    a = split_seeds(ADDRS, seed_frac=0.2, seed=42)
    b = split_seeds(list(reversed(ADDRS)), seed_frac=0.2, seed=42)
    assert a == b


def test_different_seed_gives_different_split():
    assert split_seeds(ADDRS, seed=1)[0] != split_seeds(ADDRS, seed=2)[0]
