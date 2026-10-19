---
name: audit-orchestrator
description: >-
  Audit any public website for the root causes of poor AI discoverability and
  poor on-site engagement, and emit one structured report of evidence-backed
  findings with prioritized fixes. Crawls the site once into a shared cache,
  profiles it, runs every detector skill in the marketplace against that cache,
  then de-duplicates, ranks and scores their findings into a single JSON report.
  Use when asked why a brand is missing, uncited or misrepresented in AI
  assistants, why visitors who arrive do not engage, or for any request to audit
  or assess a site's AI readiness, AI visibility, crawlability or citability.
license: MIT
allowed-tools: Bash, Read, Write
---

# Brand AI-readiness audit - orchestrator (entrypoint)

The entrypoint of the `brand-ai-readiness-audit` marketplace. Given one URL it
runs the whole audit and produces one report.

## When to use

Use for any request of the form "audit this site", "why doesn't ChatGPT/Claude/
Perplexity know about us", "why aren't we cited by AI", "is our site AI-ready",
"why do visitors bounce", or "what should we fix to be found and quoted".

Do **not** use to change a website. This marketplace is recommend-only: it
issues GET and HEAD requests to the audited site and never modifies it.

## Inputs

- **Required:** a URL or bare domain (`example.com`, `https://example.com/docs`).
- Optional: `--max-pages` (default 30), `--budget` seconds (default 270),
  `--no-render`, `--markdown <path>`, `--keep-cache`.

## Procedure

Run the pipeline. It is deterministic and needs nothing but Python 3.9+:

```bash
python skills/audit-orchestrator/scripts/run_audit.py <url> \
    --out audit-report.json --markdown audit-report.md
```

That script performs these steps in order. Run them individually only when
debugging:

1. **Crawl** - `scripts/fetch_site.py` resolves the live origin (trying https/
   http and apex/www), fetches `robots.txt`, discovers URLs from sitemaps and
   homepage links, samples pages stratified by page type, runs the access
   probes, optionally renders a few pages with a browser engine, and writes
   everything to a cache directory. Every page is fetched once, here, and never
   again.
2. **Profile** - `scripts/profile_site.py` classifies the site type
   (ecommerce / saas / local business / publisher / documentation / brochure /
   marketplace) and fingerprints the CMS or framework. **This gates every
   downstream check**; see `references/site-profiles.md`.
3. **Detect** - each detector skill runs as a separate process against the same
   cache, emitting `{findings, checks_skipped, notes}` on stdout:
   `site-access-audit` (gate 1), `render-extractability-audit` (gate 2),
   `structured-data-audit` and `answer-readiness-audit` (gate 3),
   `entity-corroboration-audit` (gate 4), `engagement-audit`. A detector that
   fails, times out or is absent degrades its own gate and nothing else, and
   the report records it.
4. **Plan remediation** - `remediation-planner` rewrites each fix for the
   detected platform and produces the proactive recommendations.
5. **Compose** - `scripts/compose_report.py` de-duplicates overlapping
   findings, applies gate precedence, sorts deterministically, assigns
   `F-001...` ids, scores each gate, and writes the report.

Then read the report and summarise for the user: lead with the headline, the
critical and high findings in order, and what to do first. Do not restate every
low finding in prose - the report already carries them.

## Output

One JSON report validated against `references/report-schema.json`. It contains
at minimum `site`, `audited_at`, a severity-count `summary`, and `findings[]`
where each finding has `id`, `title`, `severity`, `evidence` and
`suggested_action`. It additionally carries per-finding `check_id`, `gate`,
`mechanism`, `confidence`, `method` and `evidence_detail`; per-gate `scores`;
`proactive_recommendations[]`; and an `audit` block recording what was
measured, what was skipped and why, and what could not be determined.

Validate with:

```bash
python skills/audit-orchestrator/scripts/validate_report.py audit-report.json
```

## Rules this skill enforces

- **Recommend-only.** Never modify the audited site. GET and HEAD only, no
  forms, no authenticated areas, robots.txt obeyed for every crawled URL.
- **Never claim an unperformed measurement.** If a capability was missing (no
  browser engine, no external lookup), affected findings carry
  `method: heuristic` with reduced confidence and the gap is listed in
  `audit.limitations`.
- **Absence of evidence is not a finding.** A page that could not be fetched is
  a limitation, never a defect charged to the site.
- **Severity comes from `references/severity-rubric.md`**, not from judgement
  in the moment.
- **Bounded.** The whole audit stays inside its wall-clock budget by reducing
  coverage and recording the reduction.

## Tool requirements

Declared in each skill's `allowed-tools` frontmatter and kept minimal:

- **Every skill** needs `Bash` (to run its own Python script) and `Read`.
- **Only this entrypoint** additionally needs `Write`, to save the report.
- No skill requires network tools of its own: all HTTP is performed by
  `fetch_site.py` during the single crawl, and every detector reads the
  resulting cache from disk.
- No skill requires an API key, an external service, or a package install. The
  manifest is self-contained.

## Reference files

- `references/report-schema.json` - the output contract.
- `references/severity-rubric.md` - gates, severity, confidence, priority, scoring, and the false-positive rules.
- `references/site-profiles.md` - site types and which checks each enables.
- `references/runtime-budget.md` - how the 5-minute budget is allocated and degraded.
