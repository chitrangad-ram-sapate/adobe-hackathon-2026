"""Finding construction, severity arithmetic and scoring.

Every detector in the marketplace emits findings through this module, so the
severity rubric in
`skills/audit-orchestrator/references/severity-rubric.md` is enforced by code
rather than by good intentions.
"""

from __future__ import annotations

import json
import sys

from . import force_utf8_stdout

SEVERITIES = ["critical", "high", "medium", "low", "info"]
SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITIES)}
SEVERITY_WEIGHT = {"critical": 40, "high": 20, "medium": 8, "low": 3, "info": 0}

GATES = ["access", "render", "extract", "trust", "engagement"]
GATE_WEIGHT = {"access": 0.20, "render": 0.20, "extract": 0.25, "trust": 0.15, "engagement": 0.20}

# severity x effort -> priority. Encodes the rubric's judgement that a cheap
# fix for a moderate problem should be scheduled before an expensive fix for a
# bad one.
PRIORITY_MATRIX = {
    ("critical", "low"): "critical", ("critical", "medium"): "critical", ("critical", "high"): "high",
    ("high", "low"): "high",         ("high", "medium"): "high",         ("high", "high"): "medium",
    ("medium", "low"): "high",       ("medium", "medium"): "medium",     ("medium", "high"): "medium",
    ("low", "low"): "medium",        ("low", "medium"): "low",           ("low", "high"): "low",
    ("info", "low"): "low",          ("info", "medium"): "low",          ("info", "high"): "low",
}


def priority_for(severity: str, effort: str) -> str:
    return PRIORITY_MATRIX.get((severity, effort), "medium")


def adjust(severity: str, steps: int) -> str:
    """Raise (negative steps) or lower (positive) severity, clamped."""
    idx = SEVERITY_RANK.get(severity, 2) + steps
    idx = max(0, min(len(SEVERITIES) - 1, idx))
    return SEVERITIES[idx]


def apply_blast_radius(severity: str, affected: int, sampled: int) -> str:
    """Scale severity by how much of the sampled site the defect touches.

    Guards against both directions of error: a defect on one page of forty
    reported as if site-wide, and a site-wide defect reported as incidental.
    """
    if not sampled or severity == "info":
        return severity
    share = affected / sampled
    if share >= 0.8 and affected >= 3:
        return adjust(severity, -1)
    if share < 0.2:
        return adjust(severity, 1)
    return severity


def finding(
    check_id: str,
    title: str,
    severity: str,
    category: str,
    gate: str,
    evidence: str,
    mechanism: str,
    action_summary: str,
    how,
    effort: str = "medium",
    owner: str = "engineering",
    confidence: str = "high",
    method: str = "static",
    verify: str = "",
    evidence_detail=None,
    affected_urls=None,
    affected_count=None,
    sampled_count=None,
) -> dict:
    """Build one finding. All detectors go through here.

    `evidence` must contain the measurement, not a restatement of the title -
    that rule is what keeps the report auditable, and it is checked by
    validate_report.py.
    """
    assert severity in SEVERITY_RANK, f"bad severity {severity!r}"
    assert gate in GATES, f"bad gate {gate!r}"
    assert category in ("discoverability", "engagement"), f"bad category {category!r}"
    urls = list(affected_urls or [])
    return {
        "id": "",  # assigned by the orchestrator after deterministic sorting
        "check_id": check_id,
        "title": title,
        "severity": severity,
        "category": category,
        "gate": gate,
        "evidence": evidence,
        "evidence_detail": evidence_detail or {},
        "affected_urls": urls[:10],
        "affected_count": affected_count if affected_count is not None else len(urls),
        "sampled_count": sampled_count or 0,
        "mechanism": mechanism,
        "confidence": confidence,
        "method": method,
        "suggested_action": {
            "summary": action_summary,
            "priority": priority_for(severity, effort),
            "how": list(how),
            "platform_specific": None,
            "effort": effort,
            "owner": owner,
            "verify": verify or f"Re-run check {check_id} and confirm it no longer fires.",
        },
    }


def recommendation(
    rec_id: str, title: str, rationale: str, priority: str, how,
    applies_to=None, effort: str = "medium",
) -> dict:
    return {
        "id": rec_id,
        "title": title,
        "rationale": rationale,
        "priority": priority,
        "how": list(how),
        "applies_to_site_types": list(applies_to or ["*"]),
        "effort": effort,
    }


def score_gates(findings, applicable_gates=None) -> dict:
    """Deterministic 0-100 per gate plus a weighted overall.

    Gates with no applicable checks are excluded from the mean rather than
    silently scored 100 - a site that was never tested for something has not
    passed that test.
    """
    applicable = set(applicable_gates or GATES)
    gates = {}
    for gate in GATES:
        if gate not in applicable:
            continue
        deduction = sum(
            SEVERITY_WEIGHT.get(f["severity"], 0)
            for f in findings if f.get("gate") == gate
        )
        gates[gate] = max(0, 100 - deduction)
    if not gates:
        return {"overall": 100, "gates": {}}
    total_weight = sum(GATE_WEIGHT[g] for g in gates)
    overall = sum(gates[g] * GATE_WEIGHT[g] for g in gates) / total_weight
    return {"overall": round(overall, 1), "gates": gates}


def summarize(findings) -> dict:
    counts = {s: 0 for s in SEVERITIES}
    by_category = {"discoverability": 0, "engagement": 0}
    for f in findings:
        counts[f.get("severity", "medium")] = counts.get(f.get("severity", "medium"), 0) + 1
        cat = f.get("category")
        if cat in by_category:
            by_category[cat] += 1
    return {
        "total_findings": len(findings),
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "info": counts["info"],
        "by_category": by_category,
    }


def sort_findings(findings) -> list:
    """Deterministic ordering: severity, then gate order, then check id.

    Two runs over the same site must produce byte-identical reports, so no
    ordering may depend on dict iteration or crawl completion order.
    """
    return sorted(
        findings,
        key=lambda f: (
            SEVERITY_RANK.get(f.get("severity", "medium"), 9),
            GATES.index(f["gate"]) if f.get("gate") in GATES else 9,
            f.get("check_id", ""),
            f.get("title", ""),
        ),
    )


def emit(findings, skipped=None, notes=None):
    """Detector output contract: one JSON object on stdout."""
    force_utf8_stdout()
    json.dump(
        {
            "findings": findings,
            "checks_skipped": skipped or [],
            "notes": notes or [],
        },
        sys.stdout,
        indent=2,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")


def skip(check_id: str, reason: str) -> dict:
    return {"check_id": check_id, "reason": reason}
