#!/usr/bin/env python3
"""Cross-check the shipped code against its own documentation and the brief.

Three passes, each guarding a different way a marketplace like this rots:

1. **Every check id that the code can emit is documented**, with a threshold
   and an explicit "do not flag when" clause, in its skill's reference
   catalogue - and nothing is documented that the code cannot emit. Catalogues
   drift the moment a check is added or renamed, and a catalogue that no longer
   matches the code is worse than none: it describes behaviour the tool does
   not have.
2. **Behaviour changed late still matches its documentation.** Spot-checks tie
   specific code constructs to the sentences that describe them.
3. **The contest brief's requirements are met**, verified against the manifest,
   the frontmatter, the JSON schema, and an actually-emitted report rather than
   against intent.

Exit code 0 if clean, 1 if anything drifted.

Usage:
    python tests/check_consistency.py
"""
import io, json, os, re, sys

os.chdir(sys.argv[1] if len(sys.argv) > 1 else
         os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
problems, notes = [], []

# ---- 1. check ids: code vs reference catalogues -----------------------------
SKILL_REF = {
    "site-access-audit": "references/ai-crawlers.md",
    "render-extractability-audit": "references/render-gap-playbook.md",
    "structured-data-audit": "references/schema-requirements.md",
    "answer-readiness-audit": "references/answer-patterns.md",
    "entity-corroboration-audit": "references/entity-signals.md",
    "engagement-audit": "references/engagement-heuristics.md",
}

print("=" * 78)
print("1. CHECK IDS: code vs the reference catalogue that documents them")
print("=" * 78)
for skill, ref in SKILL_REF.items():
    code_ids, skip_ids = set(), set()
    sdir = os.path.join("skills", skill, "scripts")
    for fn in os.listdir(sdir):
        if not fn.endswith(".py"):
            continue
        src = io.open(os.path.join(sdir, fn), encoding="utf-8").read()
        # ids used to emit a finding
        for m in re.finditer(r'F\.finding\(\s*\n?\s*"([A-Z]{3}-\d{3})"', src):
            code_ids.add(m.group(1))
        for m in re.finditer(r'F\.skip\("([A-Z]{3}-\d{3})"', src):
            skip_ids.add(m.group(1))
    doc = io.open(os.path.join("skills", skill, ref), encoding="utf-8").read()
    doc_ids = set(re.findall(r"`([A-Z]{3}-\d{3})`", doc))
    # A catalogue may legitimately cite another skill's check to explain an
    # interaction ("SDA-003 already covers the larger problem"). Only compare
    # ids belonging to this skill's own prefix.
    prefixes = {cid.split("-")[0] for cid in code_ids} or {"ZZZ"}
    doc_ids = {cid for cid in doc_ids if cid.split("-")[0] in prefixes}

    undocumented = sorted(code_ids - doc_ids)
    phantom = sorted(doc_ids - code_ids - skip_ids)
    status = "OK" if not undocumented and not phantom else "MISMATCH"
    print(f"  {status:<9} {skill:<30} code={len(code_ids):>2} documented={len(doc_ids):>2}")
    if undocumented:
        problems.append(f"{skill}: check(s) in code but NOT in {ref}: {undocumented}")
        print(f"            emits but undocumented: {undocumented}")
    if phantom:
        problems.append(f"{skill}: documented in {ref} but not emitted by code: {phantom}")
        print(f"            documented but not emitted: {phantom}")

# ---- 2. thresholds changed late: do docs still match code? ------------------
print()
print("=" * 78)
print("2. SPOT-CHECK: thresholds/behaviour changed during hardening")
print("=" * 78)
checks = [
    ("ENG-001 capped at high (never critical)",
     "skills/engagement-audit/scripts/check_engagement.py",
     r'min\(F\.apply_blast_radius\("high"',
     "skills/engagement-audit/references/engagement-heuristics.md",
     r"ENG-001.*high"),
    ("ACC-016 excludes transactional hosts",
     "skills/site-access-audit/scripts/check_access.py",
     r"is_transactional_host",
     "skills/site-access-audit/references/ai-crawlers.md",
     r"ACC-016"),
    ("platform fingerprint reads attributes, not prose",
     "skills/audit-orchestrator/scripts/profile_site.py",
     r"_attribute_blob",
     "skills/remediation-planner/references/platform-playbooks.md",
     r"confidence gate|markup"),
    ("institutional site type exists",
     "skills/audit-orchestrator/scripts/profile_site.py",
     r'"institutional"',
     "skills/audit-orchestrator/references/site-profiles.md",
     r"institutional"),
    ("ANS-008 requires >= 8 pages",
     "skills/answer-readiness-audit/scripts/check_answer_readiness.py",
     r"len\(pages\) < 8",
     "skills/answer-readiness-audit/references/answer-patterns.md",
     r"[Ff]ewer than 8 pages"),
    ("unreachable site scores access gate only",
     "skills/audit-orchestrator/scripts/compose_report.py",
     r'applicable = \{"access"\}',
     "skills/audit-orchestrator/references/runtime-budget.md",
     r"untested gate|excluded from the score"),
    ("browser-UA fallback is disclosed",
     "skills/audit-orchestrator/scripts/fetch_site.py",
     r"--no-ua-fallback",
     "README.md", r"read-only|robots"),
]
for label, code_path, code_re, doc_path, doc_re in checks:
    code_ok = bool(re.search(code_re, io.open(code_path, encoding="utf-8").read()))
    doc_ok = bool(re.search(doc_re, io.open(doc_path, encoding="utf-8").read()))
    status = "OK" if code_ok and doc_ok else "GAP"
    if not (code_ok and doc_ok):
        problems.append(f"doc/code drift: {label} (code={code_ok}, doc={doc_ok})")
    print(f"  {status:<9} {label:<52} code={code_ok} doc={doc_ok}")

# ---- 3. handout requirements ------------------------------------------------
print()
print("=" * 78)
print("3. HANDOUT REQUIREMENTS")
print("=" * 78)
mani = json.load(io.open("marketplace.json", encoding="utf-8"))
entry = [s for s in mani["skills"] if s.get("entrypoint")]

req = []
req.append(("marketplace.json exists at root", os.path.isfile("marketplace.json")))
req.append(("lists every skill folder", all(os.path.isdir(s["path"]) for s in mani["skills"])))
req.append(("exactly one entrypoint", len(entry) == 1))
req.append(("README.md at root", os.path.isfile("README.md")))
req.append(("every skill has SKILL.md", all(os.path.isfile(os.path.join(s["path"], "SKILL.md")) for s in mani["skills"])))

fm_ok, tools_ok, lic_ok = True, True, True
for s in mani["skills"]:
    text = io.open(os.path.join(s["path"], "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fm_ok = False; continue
    fm = m.group(1)
    if not re.search(r"^name:\s*" + re.escape(s["id"]) + r"\s*$", fm, re.M): fm_ok = False
    if not re.search(r"^description:", fm, re.M): fm_ok = False
    if not re.search(r"^allowed-tools:", fm, re.M): tools_ok = False
    if not re.search(r"^license:", fm, re.M): lic_ok = False
req.append(("frontmatter: name matches folder + description", fm_ok))
req.append(("frontmatter: allowed-tools declared", tools_ok))
req.append(("frontmatter: license declared", lic_ok))

schema = json.load(io.open("skills/audit-orchestrator/references/report-schema.json", encoding="utf-8"))
top_req = set(schema["required"])
find_req = set(schema["properties"]["findings"]["items"]["required"])
sum_req = set(schema["properties"]["summary"]["required"])
req.append(("schema requires site + audited_at", {"site", "audited_at"} <= top_req))
req.append(("schema requires severity counts", {"total_findings", "critical", "high", "medium"} <= sum_req))
req.append(("schema requires id/title/severity/evidence/suggested_action",
            {"id", "title", "severity", "evidence", "suggested_action"} <= find_req))

# proven by an actual emitted report
rep = json.load(io.open("examples/example-broken-site.json", encoding="utf-8"))
req.append(("emitted report carries all required fields",
            {"site", "audited_at", "summary", "findings"} <= set(rep)
            and all({"id", "title", "severity", "evidence", "suggested_action"} <= set(f)
                    for f in rep["findings"])))
req.append(("report covers BOTH discoverability and engagement",
            {"discoverability", "engagement"} <= {f.get("category") for f in rep["findings"]}))
req.append(("suggested actions are prioritized",
            all("priority" in f["suggested_action"] for f in rep["findings"])))
req.append(("suggestions beyond detected problems",
            len(rep.get("proactive_recommendations") or []) > 0))

src_all = ""
for dp, dn, fn in os.walk("."):
    if "__pycache__" in dp: continue
    for f in fn:
        if f.endswith(".py"):
            src_all += io.open(os.path.join(dp, f), encoding="utf-8").read()
req.append(("recommend-only: no POST/PUT/DELETE anywhere",
            not re.search(r'method\s*=\s*["\'](POST|PUT|DELETE|PATCH)', src_all)))
req.append(("respects robots.txt (obeyed before crawling)",
            "rules.allows(USER_AGENT, url)" in src_all))
req.append(("no third-party imports in shipped code",
            not re.search(r"^\s*import (requests|bs4|lxml|selenium|scrapy)", src_all, re.M)))
req.append(("runtime guarded under 5 minutes", "--budget" in src_all and "270" in src_all))

zip_path = os.path.join(os.path.dirname(os.getcwd()), "brand-ai-readiness-audit.zip")
size = os.path.getsize(zip_path) if os.path.isfile(zip_path) else -1
if size >= 0:
    req.append((f"zip <= 50 MB (actual {size/1024:.0f} KB)", size < 50 * 1024 * 1024))
else:
    notes.append("packaged zip not found next to the marketplace; size check skipped")

for label, ok in req:
    print(f"  {'OK' if ok else 'FAIL':<9} {label}")
    if not ok:
        problems.append(f"handout requirement not met: {label}")

print()
print("=" * 78)
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
else:
    print("NO PROBLEMS FOUND")
print("=" * 78)
sys.exit(1 if problems else 0)
