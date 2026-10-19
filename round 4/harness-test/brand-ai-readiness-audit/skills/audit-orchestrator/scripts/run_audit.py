#!/usr/bin/env python3
"""Entrypoint driver: one URL in, one audit report out.

Pipeline:

    fetch_site.py        crawl once into the shared cache
    profile_site.py      classify site type and platform (the applicability gate)
    <detectors>          each reads the cache, writes findings JSON
    plan_remediation.py  rewrite fixes for the detected platform, add proactive items
    compose_report.py    de-duplicate, rank, score, emit the single report

Each detector is a separate process reading the same cache, so one detector
failing, timing out, or being absent from the marketplace degrades that gate's
coverage and nothing else. Detectors that are not present are recorded as
skipped rather than silently ignored.

Usage:
    python run_audit.py https://example.com --out report.json --markdown report.md
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

HERE = os.path.dirname(os.path.abspath(__file__))


def _marketplace_root():
    here = HERE
    while here != os.path.dirname(here):
        if os.path.isfile(os.path.join(here, "marketplace.json")):
            return here
        here = os.path.dirname(here)
    sys.exit("marketplace.json not found: run this script from inside the marketplace directory")


ROOT = _marketplace_root()

# Detector key -> script path, in the order the gates are read. The key is used
# in the output filename so the composer can map findings back to a gate.
DETECTORS = [
    ("access",     "skills/site-access-audit/scripts/check_access.py"),
    ("render",     "skills/render-extractability-audit/scripts/check_render.py"),
    ("schema",     "skills/structured-data-audit/scripts/check_schema.py"),
    ("answer",     "skills/answer-readiness-audit/scripts/check_answer_readiness.py"),
    ("entity",     "skills/entity-corroboration-audit/scripts/check_identity.py"),
    ("engagement", "skills/engagement-audit/scripts/check_engagement.py"),
]

PLANNER = "skills/remediation-planner/scripts/plan_remediation.py"


def run(argv, timeout, label):
    """Run a step, returning (ok, stdout, message). Never raises."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "", f"{label} exceeded its {timeout:.0f}s time budget"
    except OSError as e:
        return False, "", f"{label} could not be started: {e}"
    if result.returncode != 0:
        # Prefer a structured error from the step's own JSON output; fall back
        # to stderr. Taking the last line of stdout would report "}" from a
        # pretty-printed JSON object, which tells the reader nothing.
        message = ""
        try:
            message = str(json.loads(result.stdout or "{}").get("error") or "")
        except (json.JSONDecodeError, AttributeError):
            pass
        if not message:
            lines = [l for l in (result.stderr or "").strip().splitlines() if l.strip()]
            message = lines[-1] if lines else f"exit code {result.returncode}"
        return False, result.stdout, f"{label} failed: {message}"
    return True, result.stdout, ""


def main():
    ap = argparse.ArgumentParser(description="Audit a website for AI discoverability and on-site engagement")
    ap.add_argument("target", help="URL or bare domain to audit")
    ap.add_argument("--out", default="audit-report.json")
    ap.add_argument("--markdown", help="also write a human-readable report to this path")
    ap.add_argument("--cache", help="cache directory to use or reuse (default: a temporary directory)")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--budget", type=float, default=270.0,
                    help="total wall-clock seconds for the whole audit (default keeps it under 5 minutes)")
    ap.add_argument("--no-render", action="store_true", help="skip JavaScript rendering even if available")
    ap.add_argument("--reuse-cache", action="store_true", help="skip the crawl and use an existing cache")
    ap.add_argument("--keep-cache", action="store_true")
    args = ap.parse_args()

    started = time.time()
    cache_dir = args.cache or tempfile.mkdtemp(prefix="ai-readiness-")
    work_dir = os.path.join(cache_dir, "_findings")
    os.makedirs(work_dir, exist_ok=True)
    problems = []

    def remaining():
        return max(5.0, args.budget - (time.time() - started))

    # 1. Crawl. Given roughly two thirds of the budget: everything else reads
    #    from the cache and is fast, so the crawl is the only phase that can
    #    meaningfully overrun.
    if not args.reuse_cache:
        crawl_budget = min(remaining() * 0.65, 200.0)
        ok, out, message = run(
            [sys.executable, os.path.join(ROOT, "skills/audit-orchestrator/scripts/fetch_site.py"),
             args.target, "--cache", cache_dir, "--max-pages", str(args.max_pages),
             "--budget", str(round(crawl_budget, 1))]
            + (["--no-render"] if args.no_render else []),
            timeout=crawl_budget + 60, label="crawl",
        )
        if not ok:
            print(json.dumps({"ok": False, "error": message, "stdout": out[-2000:]}, indent=2))
            return 2
        try:
            crawl_result = json.loads(out)
        except json.JSONDecodeError:
            crawl_result = {}
        if crawl_result.get("unreachable"):
            # The crawler still wrote a cache, and already recorded the
            # unreachability in its limitations. Continue the pipeline so the
            # run ends in a valid report saying so, rather than in no output at
            # all - an empty result tells the reader nothing about whether the
            # tool or the site was at fault. No note is appended here: doing so
            # would duplicate the cache's own limitation, and would make a
            # crawling run differ from a re-analysis of the same cache.
            pass

    # 2. Profile. Every detector's applicability gate depends on this, so a
    #    failure here is recorded and the run continues with site_type unknown,
    #    which makes the detectors more conservative rather than less.
    ok, _out, message = run(
        [sys.executable, os.path.join(ROOT, "skills/audit-orchestrator/scripts/profile_site.py"),
         "--cache", cache_dir],
        timeout=min(60, remaining()), label="profile",
    )
    if not ok:
        problems.append(message)

    # 3. Detectors.
    for key, relative in DETECTORS:
        script = os.path.join(ROOT, relative)
        if not os.path.isfile(script):
            problems.append(f"detector '{key}' is not present in this marketplace; its gate was not audited")
            continue
        ok, out, message = run(
            [sys.executable, script, "--cache", cache_dir],
            timeout=min(90, remaining()), label=f"detector {key}",
        )
        if not ok:
            problems.append(message)
            continue
        try:
            payload = json.loads(out)
        except json.JSONDecodeError:
            problems.append(f"detector {key} emitted output that is not valid JSON")
            continue
        with open(os.path.join(work_dir, f"{key}.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    # 4. Remediation planning: platform-specific steps and proactive items.
    planner = os.path.join(ROOT, PLANNER)
    if os.path.isfile(planner):
        ok, _out, message = run(
            [sys.executable, planner, "--cache", cache_dir, "--findings-dir", work_dir,
             "--proactive-out", os.path.join(cache_dir, "proactive.json")],
            timeout=min(60, remaining()), label="remediation planner",
        )
        if not ok:
            problems.append(message)

    # 5. Compose.
    compose_argv = [
        sys.executable, os.path.join(ROOT, "skills/audit-orchestrator/scripts/compose_report.py"),
        "--cache", cache_dir, "--findings-dir", work_dir, "--out", args.out,
        "--duration", str(round(time.time() - started, 1)),
    ]
    if args.markdown:
        compose_argv += ["--markdown", args.markdown]
    ok, out, message = run(compose_argv, timeout=min(90, remaining() + 60), label="compose")
    if not ok:
        print(json.dumps({"ok": False, "error": message}, indent=2))
        return 3

    # Any step that degraded is recorded in the report itself, not just on the
    # console - a report must always say what it could not do.
    if problems:
        try:
            with open(args.out, encoding="utf-8") as fh:
                report = json.load(fh)
            report.setdefault("audit", {}).setdefault("limitations", []).extend(problems)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, ensure_ascii=False)
        except (OSError, json.JSONDecodeError):
            pass

    summary = json.loads(out) if out.strip().startswith("{") else {}
    summary.update({"duration_seconds": round(time.time() - started, 1),
                    "cache": cache_dir if args.keep_cache else None,
                    "degraded_steps": problems})
    print(json.dumps(summary, indent=2))

    if not args.keep_cache and not args.cache:
        shutil.rmtree(cache_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
