---
name: render-extractability-audit
description: >-
  Gate 2 of an AI-discoverability audit: determine whether a machine can read what a human sees. Measures the JavaScript render gap between the raw HTTP response and the executed DOM, detects empty application shells and hydration-only content, and finds facts locked inside images, scanned PDFs, iframes and collapsed regions. Also checks semantic document structure. Use when a site is reachable but appears empty or thin to crawlers and AI assistants.
license: MIT
allowed-tools: Bash, Read
---

# Render and extractability audit (gate 2)

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when a site is reachable but assistants describe it vaguely or not at all, when it is built as a single-page application, or as gate 2 of a full readiness audit.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

- **Render gap** - raw-response text versus executed-DOM text, reported as a coverage ratio. Where a browser
  engine is available this is measured (`method: rendered`, high confidence); where it is not, it is estimated
  from application-shell markup, framework markers, response size and text volume (`method: heuristic`, medium
  confidence) and the limitation is recorded. The check never claims a measurement that did not happen.
- **Hydration-only content** - content shipped as serialised JSON (`__NEXT_DATA__` and equivalents) rather than
  prose. Milder than an empty shell, and a different fix: the data is already in the response, it just needs
  rendering.
- **Facts locked in non-text** - data-bearing images with no alt text or HTML equivalent; PDFs with no text layer
  (scanned pages, from which extractors recover nothing); primary content inside third-party iframes; text hidden
  in tabs and accordions at load time.
- **Document structure** - H1 presence and uniqueness, heading-level skips, `main`/`article` landmarks, declared
  language.

## Procedure

```bash
python skills/render-extractability-audit/scripts/check_render.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`RND-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/render-gap-playbook.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
