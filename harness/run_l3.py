"""L3 benchmark runner — control vs AgensFlow treatment.

For each task × arm × trial:
  1. Snapshot the repo into a fresh tmp dir (so each trial sees a clean
     working tree — no cross-trial state pollution).
  2. If arm == treatment: run `agensflow-mcp init --base <hosted>` inside
     the snapshot to install hooks + .mcp.json. Source the env.
  3. Spawn `claude --print --max-turns N <task.prompt>` against the
     snapshot. Capture stdout, stderr, wall-clock, exit code.
  4. Run the deterministic verifier on stdout.
  5. Record the trial in trials.jsonl.

Two arms:
  - control:   plain Claude Code, no hooks, no MCP
  - treatment: hooks installed pointing at hosted AgensFlow

Usage:
  python -m harness.run_l3 \\
      --base https://<your-instance>.ondigitalocean.app \\
      --trials 3 \\
      --max-turns 6 \\
      --tasks tasks.yaml \\
      --out results/run-<date>/

The harness is intentionally simple — every paranoid surface is logged
to disk so a bad run can be diagnosed without re-running.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-not-found]

from harness.verifiers import verify


REPO_ROOT = Path(__file__).parent.parent
SKIP_DIRS = {".git", "results", "harness", "__pycache__", ".pytest_cache",
             ".claude", ".agensflow"}


def _snapshot_repo(dst: Path) -> None:
    """Copy the repo into dst, excluding test artifacts and per-user dirs."""
    dst.mkdir(parents=True, exist_ok=True)
    for entry in REPO_ROOT.iterdir():
        if entry.name in SKIP_DIRS or entry.name.startswith("."):
            continue
        if entry.is_dir():
            shutil.copytree(entry, dst / entry.name, symlinks=False,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(entry, dst / entry.name)


def _install_agensflow(snapshot: Path, base: str) -> None:
    """Run `agensflow-mcp init` inside snapshot — installs hooks and
    registers the MCP server in user scope (auto-trusted, --print friendly).
    """
    proc = subprocess.run(
        ["agensflow-mcp", "init", "--base", base],
        cwd=snapshot,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"agensflow-mcp init failed: stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )


def _run_claude(snapshot: Path, prompt: str, max_turns: int,
                allowed_tools: list[str], env: dict[str, str]) -> dict[str, Any]:
    """Spawn claude --print and capture the result.

    --allowedTools takes a single comma-separated arg, not repeated
    flags. Multiple `--allowedTools X --allowedTools Y` invocations
    cause the second to consume the prompt, surfacing as
    "Input must be provided" with exit 1.
    """
    cmd = ["claude", "--print", "--max-turns", str(max_turns),
           "--allowedTools", ",".join(allowed_tools),
           "--",  # end-of-options: stop --allowedTools from eating the prompt
           prompt]

    t0 = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=snapshot,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    elapsed = time.monotonic() - t0
    return {
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returncode": proc.returncode,
        "elapsed_s": elapsed,
    }


# Heuristic: claude exited fast + empty + with error → almost certainly
# rate-limit or quota, NOT a real trial outcome. Such trials should not
# be silently counted as "success=False".
_RATE_LIMIT_PHRASES = (
    "rate limit", "rate_limit", "too many requests",
    "quota", "usage limit", "5-hour", "session limit",
)


def _looks_like_rate_limit(result: dict) -> bool:
    combined = (result["stdout"] + " " + result["stderr"]).lower()
    if any(p in combined for p in _RATE_LIMIT_PHRASES):
        return True
    if (result["returncode"] != 0
        and result["elapsed_s"] < 8.0
        and len(result["stdout"]) < 200):
        return True
    return False


def _trial(arm: str, task: dict, trial_idx: int, base: str,
           max_turns: int, retry_sleep: float = 60.0) -> dict[str, Any]:
    """One trial of one task under one arm. Returns a row for trials.jsonl."""
    snapshot = Path(tempfile.mkdtemp(prefix=f"l3-{arm}-{task['id']}-{trial_idx}-"))
    try:
        _snapshot_repo(snapshot)

        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(snapshot)

        if arm == "treatment":
            _install_agensflow(snapshot, base)
            # Source the env file — read the exports and inject.
            env_file = snapshot / ".claude" / "agensflow.env"
            for line in env_file.read_text().splitlines():
                if line.startswith("export "):
                    key, _, value = line[len("export "):].partition("=")
                    env[key.strip()] = value.strip()
            # MCP tools deliberately not allowlisted — see _install_agensflow.
            allowed_tools = ["Read", "Glob", "Grep", "Bash", "Task"]
        else:
            allowed_tools = ["Read", "Glob", "Grep", "Bash", "Task"]

        result = _run_claude(snapshot, task["prompt"], max_turns, allowed_tools, env)

        # If looks like rate-limit: sleep and retry ONCE.
        rate_limited = _looks_like_rate_limit(result)
        if rate_limited:
            print(f"      ⚠ rate-limit detected (elapsed={result['elapsed_s']:.1f}s, rc={result['returncode']}); "
                  f"sleeping {retry_sleep:.0f}s before single retry",
                  flush=True)
            time.sleep(retry_sleep)
            result = _run_claude(snapshot, task["prompt"], max_turns, allowed_tools, env)
            # Still rate-limited after retry? Mark trial explicitly so report can exclude.
            if _looks_like_rate_limit(result):
                return {
                    "task_id": task["id"], "regime": task["regime"],
                    "arm": arm, "trial": trial_idx,
                    "success": False,
                    "reason": "rate-limited (excluded from analysis)",
                    "rate_limited": True,
                    "claude_returncode": result["returncode"],
                    "elapsed_s": result["elapsed_s"],
                    "stdout_chars": len(result["stdout"]),
                    "stderr_chars": len(result["stderr"]),
                    "stderr_tail": result["stderr"][-600:],
                    "stdout_tail": result["stdout"][-600:],
                }

        verdict = verify(
            result["stdout"],
            must_mention=task.get("must_mention", []),
            must_not_mention=task.get("must_not_mention", []),
            must_match=task.get("must_match", []),
            must_not_match=task.get("must_not_match", []),
        )

        return {
            "task_id": task["id"],
            "regime": task["regime"],
            "arm": arm,
            "trial": trial_idx,
            "success": verdict.success,
            "reason": verdict.reason,
            "claude_returncode": result["returncode"],
            "elapsed_s": result["elapsed_s"],
            "stdout_chars": len(result["stdout"]),
            "stderr_chars": len(result["stderr"]),
            # Keep the actual error message when claude failed — otherwise
            # debugging "why is success=False" requires re-running by hand.
            "stderr_tail": result["stderr"][-600:] if result["returncode"] != 0 else "",
            "stdout_tail": result["stdout"][-600:],
        }
    finally:
        shutil.rmtree(snapshot, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(prog="harness.run_l3")
    parser.add_argument("--base", required=True,
                        help="hosted AgensFlow base URL")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--max-turns", type=int, default=6)
    parser.add_argument("--tasks", default="tasks.yaml")
    parser.add_argument("--out", required=True,
                        help="output directory (will be created)")
    parser.add_argument("--arms", default="control,treatment",
                        help="comma-separated arms to run")
    parser.add_argument("--only-task", help="run a single task id (for debugging)")
    parser.add_argument("--include-tasks", default=None,
                        help="comma-separated list of task ids to run (excludes others)")
    parser.add_argument("--sleep-between-trials", type=float, default=0.0,
                        help="seconds to sleep between trials — use ~3s to stay under "
                             "Claude Code's rapid-fire rate limit during long runs")
    args = parser.parse_args()

    tasks_path = REPO_ROOT / args.tasks if not Path(args.tasks).is_absolute() else Path(args.tasks)
    tasks = yaml.safe_load(tasks_path.read_text())["tasks"]
    if args.only_task:
        tasks = [t for t in tasks if t["id"] == args.only_task]
    if args.include_tasks:
        wanted = {x.strip() for x in args.include_tasks.split(",") if x.strip()}
        tasks = [t for t in tasks if t["id"] in wanted]
    if not tasks:
        print("  no tasks selected after filters", file=sys.stderr)
        return 1

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    trials_path = out_dir / "trials.jsonl"

    total = len(tasks) * len(arms) * args.trials
    print(f"  tasks: {len(tasks)}  arms: {arms}  trials/cell: {args.trials}  total: {total}")

    done = 0
    t0 = time.monotonic()
    with trials_path.open("w") as f:
        for task in tasks:
            for arm in arms:
                for trial_idx in range(args.trials):
                    done += 1
                    try:
                        row = _trial(arm, task, trial_idx, args.base, args.max_turns)
                    except Exception as exc:
                        row = {
                            "task_id": task["id"], "regime": task["regime"],
                            "arm": arm, "trial": trial_idx,
                            "success": False, "reason": f"harness-error: {exc}",
                            "claude_returncode": -1, "elapsed_s": 0,
                            "stdout_chars": 0, "stderr_chars": 0,
                        }
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                    if args.sleep_between_trials > 0:
                        time.sleep(args.sleep_between_trials)
                    elapsed = time.monotonic() - t0
                    eta = (total - done) * (elapsed / done) if done else 0
                    print(
                        f"  [{done:>3d}/{total}]  {arm:<10s} {task['id']:<14s} "
                        f"trial={trial_idx}  success={row['success']}  "
                        f"{row['elapsed_s']:>5.1f}s  eta={eta:.0f}s",
                        flush=True,
                    )

    print(f"\n  ✓ wrote {trials_path}")
    print("  next: python -m harness.report --in", trials_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
