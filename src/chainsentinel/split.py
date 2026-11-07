"""Deterministic seed / held-out split of the labelled addresses."""

import random


def split_seeds(addresses, seed_frac: float = 0.2, seed: int = 42) -> tuple[list[str], list[str]]:
    """Return (seeds, holdout), both sorted. Independent of input order."""
    pool = sorted(set(a.lower() for a in addresses))
    rng = random.Random(seed)
    n_seeds = round(len(pool) * seed_frac)
    seeds = sorted(rng.sample(pool, n_seeds))
    chosen = set(seeds)
    holdout = [a for a in pool if a not in chosen]
    return seeds, holdout
