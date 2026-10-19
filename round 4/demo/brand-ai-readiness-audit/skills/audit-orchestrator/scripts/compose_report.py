#!/usr/bin/env python3
"""Compose one audit report from the detectors' separate outputs.

This is where the marketplace becomes a single answer rather than seven
opinions. Composition is not concatenation - it applies four rules that only
make sense with every detector's output in view at once:

1. **De-duplication.** One root cause reported by two detectors is reported
   once, keeping the more specific finding.
2. **Gate precedence.** The gates are sequential. If the access gate is closed
   site-wide, findings from later gates were measured against content nobody
   can reach, so they are demoted and the report says why. Reporting a missing
   FAQ schema at "high" on a site that returns 403 to every crawler is a
   ranking error, not a detection error.
3. **Deterministic ordering and identity.** Findings are sorted by severity,
   then gate order, then check id, and only then assigned F-001... So two runs
   over the same site produce the same ids for the same problems.
4. **Scoring and framing.** Gate scores, an overall score, and a headline a
   non-expert can act on.

Usage:
    python compose_report.py --cache ./cache --findings-dir ./work --out report.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone


def _bootstrap():
    here = os.path.dirname(os.path.abspath(__file__))
    while here != os.path.dirname(here):
        candidate = os.path.join(here, "lib")
        if os.path.isdir(os.path.join(candidate, "auditlib")):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            return
        here = os.path.dirname(here)
    sys.exit("auditlib not found: run this script from inside the marketplace directory")


_bootstrap()

from auditlib import force_utf8_stdout  # noqa: E402
from auditlib import MARKETPLACE_VERSION  # noqa: E402
from auditlib import cache as cache_mod, findings as F  # noqa: E402

# Which gate each detector is responsible for, used to decide which gates can
# legitimately be scored on this run.
DETECTOR_GATES = {
    "access": ["access"],
    "render": ["render"],
    "schema": ["extract"],
    "answer": ["extract"],
    "entity": ["trust"],
    "engagement": ["engagement"],
}

# Findings that mean "no machine can read this site at all". While one of these
# stands, everything measured downstream is provisional.
SITE_WIDE_BLOCKERS = {"ACC-002", "ACC-005", "ACC-008", "ACC-010", "ACC-023"}

# Pairs where two detectors can legitimately observe one root cause. The first
# id is kept; the second is dropped when both are present.
OVERLAP_PRECEDENCE = [
    ("RND-001", "RND-002"),   # a measured render gap outranks the static estimate
    ("RND-001", "RND-005"),   # a render gap explains thin text
    ("RND-002", "RND-005"),
    ("SDA-008", "SDA-007"),   # a missing price outranks generic field completeness
    ("ACC-002", "ACC-003"),   # a site-wide block already covers the AI-agent block
    ("ACC-002", "ACC-005"),
    ("ANS-001", "ANS-002"),   # no identity statement outranks a weak one
    ("ANS-004", "ANS-003"),   # placeholder titles explain the duplicate titles
    ("RND-007", "ENG-012"),   # site-wide missing alt text outranks the a11y roll-up
]


def load_detector_outputs(findings_dir):
    """Read every detector's JSON output from the work directory."""
    findings, skipped, notes, sources = [], [], [], {}
    for path in sorted(glob.glob(os.path.join(findings_dir, "*.json"))):
        name = os.path.basename(path)[:-5]
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            notes.append(f"detector output {name} was unreadable: {e}")
            continue
        detector_findings = payload.get("findings", [])
        for finding in detector_findings:
            finding.setdefault("_source", name)
        findings.extend(detector_findings)
        skipped.extend(payload.get("checks_skipped", []))
        notes.extend(payload.get("notes", []))
        sources[name] = len(detector_findings)
    return findings, skipped, notes, sources


def deduplicate(findings, notes):
    """Collapse repeated check ids and known cross-detector overlaps."""
    by_check = {}
    for finding in findings:
        check_id = finding.get("check_id", "")
        existing = by_check.get(check_id)
        if existing is None:
            by_check[check_id] = finding
            continue
        # Same check reported twice: keep the one with the wider blast radius.
        if finding.get("affected_count", 0) > existing.get("affected_count", 0):
            by_check[check_id] = finding

    present = set(by_check)
    for keep, drop in OVERLAP_PRECEDENCE:
        if keep in present and drop in present:
            by_check.pop(drop, None)
            present.discard(drop)
            notes.append(f"suppressed {drop}: already explained by {keep}")
    return list(by_check.values())


def apply_gate_precedence(findings, notes):
    """Demote later-gate findings while an earlier gate is closed site-wide.

    The gates are sequential, so a structured-data defect on a site no crawler
    can reach is real but not yet actionable - it cannot be the thing to fix
    first. Nothing is hidden: the finding stays in the report with its severity
    adjusted and the reason recorded.
    """
    blockers = [f for f in findings if f.get("check_id") in SITE_WIDE_BLOCKERS
                and f.get("severity") == "critical"]
    if not blockers:
        return findings

    blocker_ids = ", ".join(sorted(b["check_id"] for b in blockers))
    for finding in findings:
        if finding.get("gate") == "access" or finding.get("severity") == "info":
            continue
        if F.SEVERITY_RANK.get(finding["severity"], 9) < F.SEVERITY_RANK["medium"]:
            original = finding["severity"]
            finding["severity"] = "medium"
            finding["suggested_action"]["priority"] = F.priority_for(
                "medium", finding["suggested_action"].get("effort", "medium")
            )
            finding.setdefault("evidence_detail", {})["severity_adjustment"] = (
                f"reduced from {original} to medium: the access gate is closed site-wide ({blocker_ids}), "
                "so this defect cannot affect discoverability until access is restored"
            )
    notes.append(
        f"gate precedence applied: {blocker_ids} closes the access gate site-wide, so later-gate findings "
        "were capped at medium until access is fixed"
    )
    return findings


def build_headline(report, findings):
    """One sentence a non-expert can act on."""
    site = report["site"]
    counts = report["summary"]
    if not findings:
        return (f"No blocking problems were detected on {site} across the four discoverability gates or the "
                "engagement checks that applied to this site type.")
    top = findings[0]
    worst = "critical" if counts["critical"] else "high" if counts["high"] else "medium"
    lead = {
        "access": "machines may not reach or discover all of the site",
        "render": "machines cannot read what visitors can see",
        "extract": "the site's facts are hard for a machine to quote",
        "trust": "the site's identity and claims are hard to corroborate",
        "engagement": "visitors who arrive struggle to orient or act",
    }.get(top.get("gate"), "there are problems affecting discoverability")
    return (
        f"{counts['total_findings']} findings on {site}: the most severe is {worst} and sits at the "
        f"{top.get('gate')} gate - {lead}. Start with \"{top['title']}\"."
    )


def to_markdown(report) -> str:
    """Human-readable rendering of the same data. No facts appear here that
    are not in the JSON; this exists so a non-expert can read the result."""
    lines = []
    summary, scores = report["summary"], report.get("scores", {})
    lines.append(f"# AI-readiness audit: {report['site']}")
    lines.append("")
    lines.append(f"*{report['audited_at']} - {report.get('audit', {}).get('pages_crawled', 0)} pages analysed*")
    lines.append("")
    lines.append(f"**{summary.get('headline', '')}**")
    lines.append("")

    if scores.get("gates"):
        lines.append(f"## Readiness score: {scores.get('overall', 0)}/100")
        lines.append("")
        lines.append("| Gate | Score | What it means |")
        lines.append("| --- | --- | --- |")
        meaning = {
            "access": "Can a machine reach the content",
            "render": "Can a machine read what visitors see",
            "extract": "Can a machine quote a specific fact",
            "trust": "Will the fact be believed and repeated",
            "engagement": "Do arriving visitors orient and act",
        }
        for gate, score in scores["gates"].items():
            lines.append(f"| {gate.title()} | {score} | {meaning.get(gate, '')} |")
        lines.append("")

    lines.append(f"## Findings ({summary['total_findings']})")
    lines.append("")
    lines.append(f"critical {summary['critical']} - high {summary['high']} - medium {summary['medium']} "
                 f"- low {summary.get('low', 0)} - info {summary.get('info', 0)}")
    lines.append("")
    for finding in report["findings"]:
        action = finding["suggested_action"]
        lines.append(f"### {finding['id']} - {finding['title']}")
        lines.append("")
        lines.append(f"**{finding['severity'].upper()}** - {finding.get('category', '')} / "
                     f"{finding.get('gate', '')} gate - confidence {finding.get('confidence', '')} "
                     f"({finding.get('method', '')}) - check `{finding.get('check_id', '')}`")
        lines.append("")
        lines.append(f"**Evidence.** {finding['evidence']}")
        lines.append("")
        if finding.get("mechanism"):
            lines.append(f"**Why it matters.** {finding['mechanism']}")
            lines.append("")
        lines.append(f"**Fix ({action['priority']} priority, {action.get('effort', '')} effort, "
                     f"{action.get('owner', '')}).** {action['summary']}")
        lines.append("")
        for step in action.get("how", []):
            lines.append(f"- {step}")
        if action.get("platform_specific"):
            lines.append("")
            lines.append(f"*On {report.get('audit', {}).get('site_profile', {}).get('platform', 'this platform')}:*")
            for step in action["platform_specific"]:
                lines.append(f"- {step}")
        if action.get("verify"):
            lines.append("")
            lines.append(f"**Verify.** {action['verify']}")
        if finding.get("affected_urls"):
            lines.append("")
            lines.append("**Affected URLs (sample).**")
            for url in finding["affected_urls"][:5]:
                lines.append(f"- {url}")
        lines.append("")

    recs = report.get("proactive_recommendations", [])
    if recs:
        lines.append("## Proactive recommendations")
        lines.append("")
        lines.append("*Improvements where no defect was detected - these strengthen discoverability and "
                     "engagement rather than repairing something broken.*")
        lines.append("")
        for rec in recs:
            lines.append(f"### {rec['id']} - {rec['title']}")
            lines.append("")
            lines.append(f"**{rec['priority'].upper()} priority, {rec.get('effort', '')} effort.** {rec['rationale']}")
            lines.append("")
            for step in rec.get("how", []):
                lines.append(f"- {step}")
            lines.append("")

    audit = report.get("audit", {})
    if audit.get("limitations"):
        lines.append("## What this audit could not determine")
        lines.append("")
        for limitation in audit["limitations"]:
            lines.append(f"- {limitation}")
        lines.append("")
    if audit.get("checks_skipped"):
        lines.append("## Checks skipped (and why)")
        lines.append("")
        for skip in audit["checks_skipped"]:
            lines.append(f"- `{skip['check_id']}` - {skip['reason']}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Compose the final audit report")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--findings-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    ap.add_argument("--duration", type=float, default=0.0)
    args = ap.parse_args()
    force_utf8_stdout()

    cache = cache_mod.load(args.cache)
    raw_findings, skipped, notes, sources = load_detector_outputs(args.findings_dir)

    findings = deduplicate(raw_findings, notes)
    findings = apply_gate_precedence(findings, notes)
    findings = F.sort_findings(findings)
    for index, finding in enumerate(findings, 1):
        finding["id"] = f"F-{index:03d}"
        finding.pop("_source", None)

    # A gate is scored only if the detector responsible for it actually ran.
    # A gate that was never tested is excluded from the mean rather than being
    # awarded 100 - an untested gate has not passed.
    applicable = set()
    for name in sources:
        for key, gates in DETECTOR_GATES.items():
            if key in name:
                applicable.update(gates)
    applicable |= {f["gate"] for f in findings}

    # A detector running is not the same as its gate being testable. With no
    # fetched pages there was nothing for the later gates to measure, and
    # scoring them 100 would report a dead or blocked site as almost healthy -
    # the most misleading output this tool could produce.
    if cache.manifest.get("unreachable") or not cache.html_pages():
        applicable = {"access"}
        notes.append("only the access gate was scored: no page was successfully fetched, so no later gate "
                     "could be measured")

    profile = cache.profile
    proactive_path = os.path.join(args.findings_dir, "..", "proactive.json")
    recommendations = []
    if os.path.exists(proactive_path):
        try:
            with open(proactive_path, encoding="utf-8") as fh:
                recommendations = json.load(fh).get("proactive_recommendations", [])
        except (OSError, json.JSONDecodeError):
            pass

    summary = F.summarize(findings)
    report = {
        "site": cache.site,
        "site_url": cache.site_url,
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "scores": F.score_gates(findings, applicable),
        "audit": {
            "marketplace_version": MARKETPLACE_VERSION,
            "duration_seconds": round(args.duration, 1),
            "pages_crawled": len(cache.html_pages()),
            "pages_requested": cache.manifest.get("pages_requested", len(cache.pages)),
            "site_profile": {
                "site_type": profile.get("site_type", "unknown"),
                "site_type_confidence": profile.get("site_type_confidence", "low"),
                "platform": profile.get("platform", "unknown"),
                "platform_confidence": profile.get("platform_confidence", "low"),
                "hosting_stack": profile.get("hosting_stack", []),
                "analytics": profile.get("analytics", []),
                "primary_language": profile.get("primary_language", ""),
                "page_types_seen": profile.get("page_types_seen", []),
            },
            "checks_run": sorted(sources),
            "detector_finding_counts": sources,
            "checks_skipped": skipped,
            "capabilities": cache.capabilities,
            "limitations": cache.extras.get("limitations", []),
            "notes": notes + cache.extras.get("notes", []),
        },
        "findings": findings,
        "proactive_recommendations": recommendations,
    }
    report["summary"]["headline"] = build_headline(report, findings)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(report))

    print(json.dumps({
        "ok": True, "out": args.out,
        "findings": summary["total_findings"],
        "critical": summary["critical"], "high": summary["high"],
        "score": report["scores"].get("overall"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
