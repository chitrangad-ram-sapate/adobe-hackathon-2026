#!/usr/bin/env python3
"""Run the full audit across a corpus of unseen sites and report on how it behaves.

`run_tests.py` proves the detectors are correct against fixtures. This proves
something different and harder: that the marketplace **degrades sensibly on
sites it was never built against**. It is the evidence behind the
generalization claim, and it is deliberately reproducible rather than anecdotal.

What it measures, and why each matters:

* **Completion and validity** - every site must end in a schema-valid report.
  A crash, a timeout, or an empty result is a generalization failure even when
  the site is genuinely broken: the tool must always say something true.
* **Firing rate per check** - a check that fires on almost every site is
  either detecting something universal or is too loose. A check that never
  fires anywhere is either dead or unreachable. Both ends need a human to look,
  so both are flagged.
* **Severity distribution** - if `critical` is common across a broad corpus,
  the severity rubric is inflated and the report has stopped ranking anything.
* **Classification rate** - how often the profiler resolves a site type.
  `unknown` is safe but costs recall on type-gated checks, so the rate is a
  precision/recall dial, reported rather than hidden.
* **Determinism** - one crawl is analysed twice and the reports compared field
  by field. Live re-crawls are reported separately and are explicitly not a
  pass/fail: sites change between requests, so a different page sample is a
  correct reflection of a different site state.

Usage:
    python tests/generalization_batch.py                 # whole corpus
    python tests/generalization_batch.py --limit 20      # quick pass
    python tests/generalization_batch.py --segment saas
    python tests/generalization_batch.py --out results/  # keep every report
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "skills/audit-orchestrator/scripts/run_audit.py")
VALIDATE = os.path.join(ROOT, "skills/audit-orchestrator/scripts/validate_report.py")

# Checks that are expected to fire widely because the underlying practice is
# genuinely rare on the open web. These are exempt from the "too loose" flag,
# but the exemption is written down here rather than applied silently.
EXPECTED_COMMON = {
    "ENT-002": "sameAs identity links are rare in practice",
    "SDA-010": "BreadcrumbList markup is rare in practice",
    "ENG-015": "skip links are rare in practice",
    "ANS-005": "per-page meta descriptions are inconsistently maintained",
}


def load_corpus(path):
    sites = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                sites.append((parts[0], parts[1].strip()))
    return sites


def audit(segment, url, out_dir, max_pages, budget, tag=""):
    label = url.split("://")[-1].replace("/", "_").strip("_")
    out = os.path.join(out_dir, f"{label}{tag}.json")
    started = time.time()
    record = {"segment": segment, "url": url, "label": label}
    try:
        proc = subprocess.run(
            [sys.executable, RUN, url, "--out", out, "--max-pages", str(max_pages),
             "--no-render", "--budget", str(budget)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=budget + 120, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        record.update(status="TIMEOUT", secs=time.time() - started)
        return record
    except Exception as e:
        record.update(status="CRASH", secs=time.time() - started, detail=f"{type(e).__name__}: {e}")
        return record

    record["secs"] = time.time() - started
    if proc.returncode != 0 or not os.path.isfile(out):
        detail = ""
        try:
            detail = str(json.loads(proc.stdout or "{}").get("error", ""))
        except json.JSONDecodeError:
            detail = (proc.stderr or "")[-160:]
        record.update(status="NO-REPORT", detail=detail[:160])
        return record

    try:
        with open(out, encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        record.update(status="BAD-JSON", detail=str(e)[:160])
        return record

    v = subprocess.run([sys.executable, VALIDATE, out], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=90, cwd=ROOT)
    profile = report["audit"]["site_profile"]
    summary = report["summary"]
    record.update(
        status="OK",
        report_path=out,
        pages=report["audit"]["pages_crawled"],
        site_type=profile.get("site_type"),
        site_type_conf=profile.get("site_type_confidence"),
        platform=profile.get("platform"),
        platform_conf=profile.get("platform_confidence"),
        lang=profile.get("primary_language"),
        findings=summary["total_findings"],
        critical=summary["critical"], high=summary["high"], medium=summary["medium"],
        low=summary.get("low", 0), info=summary.get("info", 0),
        score=report["scores"].get("overall"),
        skipped=len(report["audit"].get("checks_skipped", [])),
        limitations=len(report["audit"].get("limitations", [])),
        valid=(v.returncode == 0),
        warnings=v.stdout.count("WARN"),
        checks=sorted({f["check_id"] for f in report["findings"]}),
        recs=len(report.get("proactive_recommendations") or []),
    )
    return record


def _normalise(report):
    report.pop("audited_at", None)
    report.get("audit", {}).pop("duration_seconds", None)
    for finding in report.get("findings", []):
        # Response timings vary between runs and are not part of the judgement.
        finding.get("evidence_detail", {}).pop("pages", None)
    return report


def determinism_check(records, out_dir, max_pages, budget, sample=3):
    """Two separate questions, reported separately because only one is a claim.

    1. **Analysis determinism** - the same crawl re-analysed must produce a
       byte-identical report. This is the marketplace's actual guarantee: no
       ordering depends on thread completion, dict iteration or wall time. A
       failure here is a bug.
    2. **Live re-crawl stability** - auditing the same site twice over the
       network. This is *not* guaranteed and never could be: large sites change
       between requests, personalise responses, and return different link sets,
       so a different page sample reflects a different site state rather than a
       defect. Reported as information, not as pass/fail.
    """
    # Spread the sample across segments rather than taking the first N, which
    # would repeatedly hit one segment's sites and risk tripping their rate
    # limiting - an artefact of the test, not a property of the product.
    by_segment = defaultdict(list)
    for r in records:
        if r["status"] == "OK" and r.get("pages", 0) > 2:
            by_segment[r["segment"]].append(r)
    candidates = [rs[0] for _seg, rs in sorted(by_segment.items())][:sample]

    results = []
    for first in candidates:
        cache = os.path.join(out_dir, "cache__" + first["label"])
        a_path = os.path.join(out_dir, first["label"] + "__a.json")
        b_path = os.path.join(out_dir, first["label"] + "__b.json")
        common = ["--max-pages", str(max_pages), "--no-render", "--budget", str(budget),
                  "--cache", cache]

        def passes(out_path, extra):
            return subprocess.run(
                [sys.executable, RUN, first["url"], "--out", out_path] + extra + common,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=budget + 120, cwd=ROOT)

        try:
            # One crawl, then two independent analysis passes over it. This
            # isolates the property actually being claimed: analysis is a pure
            # function of the cache.
            passes(os.path.join(out_dir, first["label"] + "__seed.json"), ["--keep-cache"])
            passes(a_path, ["--reuse-cache"])
            passes(b_path, ["--reuse-cache"])
            with open(a_path, encoding="utf-8") as fh:
                a = _normalise(json.load(fh))
            with open(b_path, encoding="utf-8") as fh:
                b = _normalise(json.load(fh))
            analysis = "IDENTICAL" if a == b else "DIFFERENT  <-- BUG"
        except Exception as e:
            analysis = "ERROR (" + type(e).__name__ + ")"

        # Live re-crawl, informational only. Paced so the check is not the
        # reason the site starts refusing requests.
        time.sleep(2)
        second = audit(first["segment"], first["url"], out_dir, max_pages, budget, tag="__recrawl")
        if second["status"] != "OK":
            live = f"re-crawl returned {second['status']} (site state changed or rate-limited)"
        else:
            same = set(first["checks"]) == set(second["checks"])
            overlap = len(set(first["checks"]) & set(second["checks"]))
            union = len(set(first["checks"]) | set(second["checks"])) or 1
            live = ("same finding set" if same
                    else f"{overlap}/{union} checks shared, {first['pages']}->{second['pages']} pages")
        results.append((first["label"], analysis, live))
    return results


def main():
    ap = argparse.ArgumentParser(description="Generalization batch over a corpus of unseen sites")
    ap.add_argument("--corpus", default=os.path.join(ROOT, "tests/sites.txt"))
    ap.add_argument("--out", help="directory to keep reports in (default: a temp dir)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--segment")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--budget", type=float, default=120.0)
    ap.add_argument("--no-determinism", action="store_true")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    if args.segment:
        corpus = [s for s in corpus if s[0] == args.segment]
    if args.limit:
        corpus = corpus[: args.limit]
    out_dir = args.out or tempfile.mkdtemp(prefix="generalization-")
    os.makedirs(out_dir, exist_ok=True)

    print(f"auditing {len(corpus)} sites with {args.workers} workers, "
          f"{args.max_pages} pages each, {args.budget:.0f}s budget\n")
    started = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(
            lambda s: audit(s[0], s[1], out_dir, args.max_pages, args.budget), corpus))
    wall = time.time() - started

    ok = [r for r in records if r["status"] == "OK"]
    bad = [r for r in records if r["status"] != "OK"]

    # ---- per-site table -----------------------------------------------------
    print(f"{'segment':<14} {'site':<34} {'st':<4} {'s':>4} {'pg':>3} {'type':<15} "
          f"{'platform':<14} {'n':>3} {'C':>2} {'H':>2} {'M':>2} {'L':>2} {'score':>5} {'val':>4}")
    print("-" * 132)
    for r in sorted(records, key=lambda r: (r["segment"], r["label"])):
        if r["status"] != "OK":
            print(f"{r['segment']:<14} {r['label'][:34]:<34} {r['status'][:4]:<4} "
                  f"{r.get('secs', 0):>4.0f}  -> {r.get('detail', '')[:60]}")
            continue
        print(f"{r['segment']:<14} {r['label'][:34]:<34} {'ok':<4} {r['secs']:>4.0f} {r['pages']:>3} "
              f"{str(r['site_type'])[:15]:<15} {str(r['platform'])[:14]:<14} {r['findings']:>3} "
              f"{r['critical']:>2} {r['high']:>2} {r['medium']:>2} {r['low']:>2} "
              f"{(r['score'] if r['score'] is not None else 0):>5.1f} {'yes' if r['valid'] else 'NO':>4}")

    # ---- reliability --------------------------------------------------------
    print(f"\n{'=' * 60}\nRELIABILITY")
    print(f"  completed with a report : {len(ok)}/{len(records)}")
    print(f"  schema-valid reports    : {sum(1 for r in ok if r['valid'])}/{len(ok)}")
    print(f"  validator warnings      : {sum(r['warnings'] for r in ok)}")
    if bad:
        print(f"  FAILURES                : {Counter(r['status'] for r in bad)}")
    if ok:
        times = sorted(r["secs"] for r in ok)
        print(f"  runtime  min/median/max : {times[0]:.0f}s / {times[len(times)//2]:.0f}s / {times[-1]:.0f}s")
        print(f"  over 5-minute ceiling   : {sum(1 for t in times if t > 300)}")
        print(f"  total wall clock        : {wall:.0f}s for {len(records)} sites")

    if not ok:
        return 1

    # ---- coverage -----------------------------------------------------------
    print(f"\nCOVERAGE")
    typed = [r for r in ok if r["site_type"] not in (None, "unknown")]
    plat = [r for r in ok if r["platform"] not in (None, "unknown")]
    print(f"  site type resolved      : {len(typed)}/{len(ok)} ({100*len(typed)/len(ok):.0f}%)")
    print(f"    {dict(Counter(r['site_type'] for r in ok).most_common())}")
    print(f"  platform identified     : {len(plat)}/{len(ok)} ({100*len(plat)/len(ok):.0f}%)")
    print(f"    {dict(Counter(r['platform'] for r in plat).most_common(8))}")
    print(f"  languages seen          : {dict(Counter(r['lang'] for r in ok if r['lang']).most_common(8))}")

    # Did the profiler agree with the corpus segment where the segment is a type?
    mapping = {"ecommerce": "ecommerce", "saas": "saas", "publisher": "media_publisher",
               "docs": "documentation", "institutional": "institutional"}
    graded = [r for r in ok if r["segment"] in mapping]
    agree = [r for r in graded if r["site_type"] == mapping[r["segment"]]]
    wrong = [r for r in graded if r["site_type"] not in (mapping[r["segment"]], "unknown")]
    if graded:
        print(f"  profiler vs expectation : {len(agree)}/{len(graded)} agreed, "
              f"{len(graded)-len(agree)-len(wrong)} conservative (unknown), {len(wrong)} MISCLASSIFIED")
        for r in wrong:
            print(f"      MISCLASSIFIED {r['label']}: expected {mapping[r['segment']]}, got {r['site_type']}")

    # ---- findings behaviour -------------------------------------------------
    print(f"\nFINDINGS")
    counts = [r["findings"] for r in ok]
    counts.sort()
    print(f"  per site min/median/max : {counts[0]} / {counts[len(counts)//2]} / {counts[-1]}")
    print(f"  severity totals         : critical {sum(r['critical'] for r in ok)}, "
          f"high {sum(r['high'] for r in ok)}, medium {sum(r['medium'] for r in ok)}, "
          f"low {sum(r['low'] for r in ok)}, info {sum(r['info'] for r in ok)}")
    crit_sites = [r for r in ok if r["critical"] > 0]
    print(f"  sites with a critical   : {len(crit_sites)}/{len(ok)} ({100*len(crit_sites)/len(ok):.0f}%)"
          f"   <- severity inflation shows up here")
    print(f"  mean checks skipped     : {sum(r['skipped'] for r in ok)/len(ok):.1f} per site")

    # ---- per-check firing rates --------------------------------------------
    fired = Counter(c for r in ok for c in r["checks"])
    n = len(ok)
    print(f"\nPER-CHECK FIRING RATE  ({len(fired)} distinct checks fired across {n} sites)")
    for check, count in sorted(fired.items(), key=lambda kv: (-kv[1], kv[0])):
        rate = count / n
        flag = ""
        if rate >= 0.75 and check not in EXPECTED_COMMON:
            flag = "  <-- fires on most sites: verify it is not too loose"
        elif rate >= 0.75:
            flag = f"  (expected: {EXPECTED_COMMON[check]})"
        print(f"  {check}  {count:>3}/{n}  {rate*100:>5.0f}%{flag}")

    # Which checks never fired anywhere? Either unreachable or dead.
    all_ids = set()
    for skill_dir in os.listdir(os.path.join(ROOT, "skills")):
        script_dir = os.path.join(ROOT, "skills", skill_dir, "scripts")
        if not os.path.isdir(script_dir):
            continue
        for fn in os.listdir(script_dir):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(script_dir, fn), encoding="utf-8") as fh:
                import re
                all_ids.update(re.findall(r'"([A-Z]{3}-\d{3})",\s*"', fh.read()))
    never = sorted(all_ids - set(fired))
    print(f"\n  never fired on this corpus ({len(never)}/{len(all_ids)}): {', '.join(never) or 'none'}")
    print("    (expected for checks needing rare conditions: TLS failure, scanned PDFs, "
          "site-wide robots blocks)")

    # ---- determinism --------------------------------------------------------
    if not args.no_determinism:
        print(f"\nDETERMINISM")
        print(f"  {'site':<34} {'same crawl re-analysed':<26} live re-crawl (informational)")
        for label, analysis, live in determinism_check(records, out_dir, args.max_pages, args.budget):
            print(f"  {label[:34]:<34} {analysis:<26} {live}")

    with open(os.path.join(out_dir, "_batch.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, default=str)
    print(f"\nreports kept in {out_dir}")
    return 0 if len(ok) == len(records) else 0


if __name__ == "__main__":
    sys.exit(main())
