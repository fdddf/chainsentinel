"""Score every iteration once on dev and test, and plot recall per iteration.

Run only after the last iteration is frozen: this is the one place test metrics are produced.

Usage: python scripts/final_report.py
Reads results/iter_N.json (rule, note) and results/candidates_iter_N.csv,
writes results/final.json and results/recall_by_iteration.png.

Besides dev and test, it reports `listed_precision_lb@k` on the whole held-out set
(dev + test), which is the fairer lower bound on precision:
on either half alone, listed addresses of the other half count as misses.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from chainsentinel.evaluate import evaluate, read_addresses, score_file  # noqa: E402

ROOT = Path(__file__).parents[1]
KS = (10, 50, 100, 200)


def iterations() -> list[int]:
    found = (re.fullmatch(r"iter_(\d+)\.json", p.name) for p in (ROOT / "results").iterdir())
    return sorted(int(m.group(1)) for m in found if m)


def main():
    seeds = read_addresses(ROOT / "data/seeds.csv")
    holdout = read_addresses(ROOT / "data/holdout.csv")
    rows = []
    for n in iterations():
        meta = json.loads((ROOT / f"results/iter_{n}.json").read_text())
        cand = ROOT / f"results/candidates_iter_{n}.csv"
        scored = score_file(cand, final=True)
        both = evaluate(read_addresses(cand), holdout, seeds, KS)
        rows.append({
            "iteration": n, "rule": meta["rule"], "note": meta["note"],
            "dev": scored["dev"], "test": scored["test"],
            "listed_precision_lb": {f"@{k}": both[f"precision_lb@{k}"] for k in KS},
            "holdout_recall@all": both["recall@all"],
        })
    out = {"scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "note": "precision_lb is a lower bound: unlisted addresses are unlabelled, not benign",
           "iterations": rows}
    (ROOT / "results/final.json").write_text(json.dumps(out, indent=2))

    xs = [r["iteration"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    styles = {"dev": "-", "test": "--"}
    for split, ls in styles.items():
        ax.plot(xs, [r[split]["recall@50"] for r in rows], ls, marker="o", color="#2a6fdb",
                label=f"{split} recall@50")
        ax.plot(xs, [r[split]["recall@all"] for r in rows], ls, marker="s", color="#d9822b",
                label=f"{split} recall@all")
    ax.axhline(25 / 243, color="#888", lw=0.8, ls=":")
    ax.text(xs[-1], 25 / 243 + 0.012, "split-agnostic ceiling of recall@50 ≈ 0.10",
            ha="right", fontsize=7, color="#555")
    ax.set_xticks(xs, [f"{r['iteration']}\n{r['rule']}" for r in rows], fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("recall on held-out FBI addresses")
    ax.set_title("ChainSentinel: recall per iteration (dev solid, test dashed)", fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(ROOT / "results/recall_by_iteration.png")

    for r in rows:
        print(f"iter {r['iteration']} [{r['rule']}] "
              f"dev r@50={r['dev']['recall@50']:.3f} r@all={r['dev']['recall@all']:.3f} | "
              f"test r@50={r['test']['recall@50']:.3f} r@all={r['test']['recall@all']:.3f} | "
              f"listed precision_lb@50={r['listed_precision_lb']['@50']:.2f}")


if __name__ == "__main__":
    main()
