"""Aggregate trials.jsonl into a control-vs-treatment comparison.

Produces:
  summary.json — per-regime success rate, mean elapsed, by arm
  summary.txt  — human-readable comparison
  per_task.csv — every (task_id, arm) combination

Statistical significance: with N=3 trials × 10 tasks = 30 per arm we
don't have enough samples for a serious p-value claim. The report
reports raw rates + 95% Wilson intervals so you can see what's signal
vs noise.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. More accurate than
    normal approximation at small N."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def load_trials(path: Path, *, include_rate_limited: bool = False) -> list[dict[str, Any]]:
    """Load trials, excluding rate-limited ones by default so they don't
    pollute success/latency stats. Trials with `rate_limited=true` are
    explicitly tagged by the harness; older runs without that field are
    heuristically identified as elapsed<5s + empty stdout + nonzero rc."""
    rows: list[dict[str, Any]] = []
    excluded = 0
    for line in path.open():
        if not line.strip():
            continue
        t = json.loads(line)
        # Rate-limit signatures in observed Claude Code output:
        #  - stdout contains "session limit" / "rate limit" / "usage limit"
        #  - elapsed is tiny (<5s) AND rc != 0 (fast-fail, not a real run)
        combined = (t.get("stdout_tail", "") + " " + t.get("stderr_tail", "")).lower()
        rate_limit_phrases = ("session limit", "rate limit", "rate_limit",
                              "usage limit", "too many requests", "quota")
        is_rate_limited = (
            t.get("rate_limited")
            or any(p in combined for p in rate_limit_phrases)
            or (t.get("elapsed_s", 0) < 5.0
                and t.get("claude_returncode", 0) != 0
                and t.get("stdout_chars", 0) < 200)
        )
        if is_rate_limited and not include_rate_limited:
            excluded += 1
            continue
        rows.append(t)
    if excluded:
        print(f"  excluded {excluded} rate-limited trial(s) from analysis "
              "(use --include-rate-limited to include)")
    return rows


def summarize(trials: list[dict]) -> dict[str, Any]:
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for t in trials:
        by_arm[t["arm"]].append(t)

    overall: dict[str, Any] = {}
    by_regime: dict[str, dict[str, Any]] = defaultdict(dict)
    by_task: dict[str, dict[str, Any]] = defaultdict(dict)

    for arm, rows in by_arm.items():
        n = len(rows)
        succ = sum(1 for r in rows if r["success"])
        elapsed_mean = sum(r["elapsed_s"] for r in rows) / max(1, n)
        lo, hi = wilson_interval(succ, n)
        overall[arm] = {
            "n": n,
            "success": succ,
            "success_rate": succ / max(1, n),
            "wilson_lo": lo,
            "wilson_hi": hi,
            "elapsed_mean_s": elapsed_mean,
        }

        regimes: dict[str, list[dict]] = defaultdict(list)
        tasks: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            regimes[r["regime"]].append(r)
            tasks[r["task_id"]].append(r)

        for regime, rr in regimes.items():
            n_r = len(rr)
            s_r = sum(1 for r in rr if r["success"])
            e_r = sum(r["elapsed_s"] for r in rr) / max(1, n_r)
            by_regime[regime][arm] = {
                "n": n_r, "success": s_r, "success_rate": s_r / max(1, n_r),
                "elapsed_mean_s": e_r,
            }

        for task_id, rr in tasks.items():
            n_t = len(rr)
            s_t = sum(1 for r in rr if r["success"])
            e_t = sum(r["elapsed_s"] for r in rr) / max(1, n_t)
            by_task[task_id][arm] = {
                "n": n_t, "success": s_t, "success_rate": s_t / max(1, n_t),
                "elapsed_mean_s": e_t,
                "regime": rr[0]["regime"],
            }

    return {"overall": overall, "by_regime": dict(by_regime),
            "by_task": dict(by_task)}


def write_text_report(summary: dict, out: Path) -> None:
    lines = [
        "AgensFlow L3 benchmark — control vs treatment",
        "=" * 60,
        "",
        "OVERALL",
    ]
    for arm, agg in summary["overall"].items():
        lines.append(
            f"  {arm:<10s}  success={agg['success']}/{agg['n']}  "
            f"rate={agg['success_rate']:.1%}  "
            f"(Wilson 95%: {agg['wilson_lo']:.1%}-{agg['wilson_hi']:.1%})  "
            f"avg={agg['elapsed_mean_s']:.1f}s"
        )

    lines.append("")
    lines.append("BY REGIME")
    for regime, arms in sorted(summary["by_regime"].items()):
        lines.append(f"  {regime}")
        for arm, agg in arms.items():
            lines.append(
                f"    {arm:<10s}  {agg['success']}/{agg['n']}  "
                f"({agg['success_rate']:.1%})  avg={agg['elapsed_mean_s']:.1f}s"
            )

    lines.append("")
    lines.append("BY TASK")
    for task_id, arms in sorted(summary["by_task"].items()):
        first = next(iter(arms.values()))
        lines.append(f"  {task_id}  ({first['regime']})")
        for arm, agg in arms.items():
            lines.append(
                f"    {arm:<10s}  {agg['success']}/{agg['n']}  "
                f"avg={agg['elapsed_mean_s']:.1f}s"
            )

    out.write_text("\n".join(lines) + "\n")


def write_csv(summary: dict, out: Path) -> None:
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "regime", "arm", "n", "success", "success_rate", "elapsed_mean_s"])
        for task_id, arms in sorted(summary["by_task"].items()):
            for arm, agg in arms.items():
                w.writerow([
                    task_id, agg["regime"], arm, agg["n"],
                    agg["success"], f"{agg['success_rate']:.4f}",
                    f"{agg['elapsed_mean_s']:.2f}",
                ])


def main() -> int:
    parser = argparse.ArgumentParser(prog="harness.report")
    parser.add_argument("--in", dest="inp", required=True,
                        help="path to trials.jsonl")
    parser.add_argument("--out-dir", default=None,
                        help="output directory (default: same dir as input)")
    parser.add_argument("--include-rate-limited", action="store_true",
                        help="don't exclude rate-limited trials")
    args = parser.parse_args()

    inp = Path(args.inp)
    out_dir = Path(args.out_dir) if args.out_dir else inp.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    trials = load_trials(inp, include_rate_limited=args.include_rate_limited)
    summary = summarize(trials)

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    write_text_report(summary, out_dir / "summary.txt")
    write_csv(summary, out_dir / "per_task.csv")

    print((out_dir / "summary.txt").read_text())
    print(f"  ✓ wrote {out_dir / 'summary.json'}")
    print(f"  ✓ wrote {out_dir / 'summary.txt'}")
    print(f"  ✓ wrote {out_dir / 'per_task.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
