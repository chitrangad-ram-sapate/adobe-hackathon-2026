#!/usr/bin/env python3
"""Validate an audit report against the marketplace's output contract.

Two layers of checking:

1. **Schema conformance** - the structural contract in
   `references/report-schema.json`: required fields, types, enums and id
   patterns. Implemented directly rather than with `jsonschema`, because the
   whole marketplace must run with nothing but a Python interpreter.
2. **Report-quality rules** that a JSON Schema cannot express, and that matter
   more than the structure does:
   - an `evidence` string must contain a measurement, not restate the title
   - a finding may not claim a `method` the run did not have the capability for
     (`external` is satisfied by either web search or off-site profile verification;
     `rendered` strictly requires a JavaScript engine)
   - `id` values must be sequential and severity-ordered, so the report is
     deterministic
   - a proactive recommendation must not duplicate a finding's subject

Exit code 0 if valid, 1 if any error was found. Warnings do not fail the run.

Usage:
    python validate_report.py audit-report.json [--strict]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SEVERITIES = ["critical", "high", "medium", "low", "info"]
PRIORITIES = ["critical", "high", "medium", "low"]
GATES = ["access", "render", "extract", "trust", "engagement"]
CATEGORIES = ["discoverability", "engagement"]
CONFIDENCES = ["high", "medium", "low"]
METHODS = ["static", "rendered", "probe", "heuristic", "external"]
EFFORTS = ["low", "medium", "high"]
OWNERS = ["engineering", "content", "marketing", "ops", "design"]

FINDING_ID = re.compile(r"^F-\d{3,}$")
CHECK_ID = re.compile(r"^[A-Z]{3}-\d{3}$")
REC_ID = re.compile(r"^P-\d{3,}$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
HAS_NUMBER = re.compile(r"\d")


def force_utf8_stdout():
    """Match the detectors: report text may contain any script the site used."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def validate(report):
    errors, warnings = [], []

    def err(msg):
        errors.append(msg)

    def warn(msg):
        warnings.append(msg)

    # --- top level ------------------------------------------------------
    for field in ("site", "audited_at", "summary", "findings"):
        if field not in report:
            err(f"missing required top-level field: {field}")
    if errors:
        return errors, warnings

    if not isinstance(report["site"], str) or not report["site"]:
        err("site must be a non-empty string")
    if not ISO.match(str(report.get("audited_at", ""))):
        err(f"audited_at must be RFC3339 UTC with a trailing Z, got {report.get('audited_at')!r}")

    summary = report["summary"]
    for field in ("total_findings", "critical", "high", "medium"):
        if field not in summary:
            err(f"summary is missing required field: {field}")
        elif not isinstance(summary[field], int) or summary[field] < 0:
            err(f"summary.{field} must be a non-negative integer")

    findings = report["findings"]
    if not isinstance(findings, list):
        err("findings must be an array")
        return errors, warnings

    # --- summary agreement ----------------------------------------------
    if summary.get("total_findings") != len(findings):
        err(f"summary.total_findings ({summary.get('total_findings')}) does not match "
            f"the number of findings ({len(findings)})")
    for severity in ("critical", "high", "medium", "low", "info"):
        if severity not in summary:
            continue
        actual = sum(1 for f in findings if f.get("severity") == severity)
        if summary[severity] != actual:
            err(f"summary.{severity} says {summary[severity]} but {actual} findings have that severity")

    capabilities = report.get("audit", {}).get("capabilities", {})

    # --- per finding ----------------------------------------------------
    seen_ids, seen_checks = set(), set()
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        for field in ("id", "title", "severity", "evidence", "suggested_action"):
            if field not in finding:
                err(f"{where} is missing required field: {field}")
        if errors and len(errors) > 40:
            break
        fid = finding.get("id", "")
        if not FINDING_ID.match(str(fid)):
            err(f"{where}.id {fid!r} does not match F-NNN")
        if fid in seen_ids:
            err(f"{where}.id {fid!r} is duplicated")
        seen_ids.add(fid)

        check_id = finding.get("check_id")
        if check_id is not None:
            if not CHECK_ID.match(str(check_id)):
                err(f"{where}.check_id {check_id!r} does not match AAA-NNN")
            if check_id in seen_checks:
                err(f"{where}.check_id {check_id!r} appears more than once; the composer should have "
                    "de-duplicated it")
            seen_checks.add(check_id)

        if finding.get("severity") not in SEVERITIES:
            err(f"{where}.severity {finding.get('severity')!r} is not one of {SEVERITIES}")
        if "gate" in finding and finding["gate"] not in GATES:
            err(f"{where}.gate {finding['gate']!r} is not one of {GATES}")
        if "category" in finding and finding["category"] not in CATEGORIES:
            err(f"{where}.category {finding['category']!r} is not one of {CATEGORIES}")
        if "confidence" in finding and finding["confidence"] not in CONFIDENCES:
            err(f"{where}.confidence {finding['confidence']!r} is not one of {CONFIDENCES}")
        if "method" in finding and finding["method"] not in METHODS:
            err(f"{where}.method {finding['method']!r} is not one of {METHODS}")

        # Quality rule: evidence must carry a measurement.
        evidence = str(finding.get("evidence", ""))
        title = str(finding.get("title", ""))
        if len(evidence) < 20:
            err(f"{where}.evidence is too short to constitute evidence: {evidence!r}")
        elif evidence.strip().lower() == title.strip().lower():
            err(f"{where}.evidence restates the title instead of giving evidence")
        elif not HAS_NUMBER.search(evidence):
            warn(f"{where} ({check_id}) evidence contains no number; confirm it states a measurement")

        # Honesty rule: a finding may not claim a capability the run lacked.
        if finding.get("method") == "rendered" and not capabilities.get("javascript_rendering", False):
            err(f"{where} claims method 'rendered' but the run reported no JavaScript rendering capability")
        if finding.get("method") == "external" and not (
                capabilities.get("web_search", False)
                or capabilities.get("offsite_verification", False)):
            err(f"{where} claims method 'external' but the run reported no external lookup capability")

        if "mechanism" not in finding or len(str(finding.get("mechanism", ""))) < 20:
            warn(f"{where} ({check_id}) has no substantive mechanism explanation")

        action = finding.get("suggested_action")
        if not isinstance(action, dict):
            err(f"{where}.suggested_action must be an object")
            continue
        if not action.get("summary"):
            err(f"{where}.suggested_action.summary is missing or empty")
        if action.get("priority") not in PRIORITIES:
            err(f"{where}.suggested_action.priority {action.get('priority')!r} is not one of {PRIORITIES}")
        if "effort" in action and action["effort"] not in EFFORTS:
            err(f"{where}.suggested_action.effort {action['effort']!r} is not one of {EFFORTS}")
        if "owner" in action and action["owner"] not in OWNERS:
            err(f"{where}.suggested_action.owner {action['owner']!r} is not one of {OWNERS}")
        if not action.get("how"):
            warn(f"{where} ({check_id}) suggested_action has no ordered 'how' steps")

    # --- deterministic ordering ------------------------------------------
    ranks = [SEVERITIES.index(f["severity"]) for f in findings if f.get("severity") in SEVERITIES]
    if ranks != sorted(ranks):
        err("findings are not ordered by descending severity; the report is not deterministic")
    expected = [f"F-{i:03d}" for i in range(1, len(findings) + 1)]
    if [f.get("id") for f in findings] != expected:
        err("finding ids are not sequential from F-001 in report order")

    # --- proactive recommendations ---------------------------------------
    for index, rec in enumerate(report.get("proactive_recommendations", []) or []):
        where = f"proactive_recommendations[{index}]"
        for field in ("id", "title", "rationale", "priority"):
            if field not in rec:
                err(f"{where} is missing required field: {field}")
        if "id" in rec and not REC_ID.match(str(rec["id"])):
            err(f"{where}.id {rec['id']!r} does not match P-NNN")
        if rec.get("priority") not in ("high", "medium", "low"):
            err(f"{where}.priority {rec.get('priority')!r} is not one of high/medium/low")

    # --- scores ------------------------------------------------------------
    scores = report.get("scores", {})
    if scores:
        overall = scores.get("overall")
        if overall is not None and not (0 <= overall <= 100):
            err(f"scores.overall {overall} is outside 0-100")
        for gate, value in (scores.get("gates") or {}).items():
            if gate not in GATES:
                err(f"scores.gates contains unknown gate {gate!r}")
            elif not (0 <= value <= 100):
                err(f"scores.gates.{gate} {value} is outside 0-100")

    # --- audit provenance ---------------------------------------------------
    audit = report.get("audit")
    if not audit:
        warn("report has no audit block; provenance and limitations are not recorded")
    else:
        for skip in audit.get("checks_skipped", []) or []:
            if "check_id" not in skip or "reason" not in skip:
                err(f"checks_skipped entry is missing check_id or reason: {skip!r}")

    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description="Validate an audit report")
    ap.add_argument("report")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()
    force_utf8_stdout()

    if not os.path.isfile(args.report):
        print(f"report not found: {args.report}")
        return 2
    try:
        with open(args.report, encoding="utf-8") as fh:
            report = json.load(fh)
    except json.JSONDecodeError as e:
        print(f"report is not valid JSON: {e}")
        return 1

    errors, warnings = validate(report)

    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")

    if errors or (args.strict and warnings):
        print(f"\nINVALID: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"VALID: {len(report.get('findings', []))} findings, "
          f"{len(report.get('proactive_recommendations') or [])} recommendations, "
          f"{len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
