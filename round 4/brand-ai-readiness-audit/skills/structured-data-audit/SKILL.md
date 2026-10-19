---
name: structured-data-audit
description: >-
  Gate 3a of an AI-discoverability audit: check whether a site's facts are published as valid, complete, machine-readable structured data. Validates JSON-LD parsing, checks schema.org type coverage gated by page type and site type, and grades per-type required-field completeness - including Product/Offer price and availability, Article dates and authorship, and Organization identity fields. Use when a brand's facts are readable but not being quoted correctly by AI assistants.
license: MIT
allowed-tools: Bash, Read
---

# Structured data audit (gate 3a)

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when assistants describe a brand imprecisely, get its prices or dates wrong, or cite a reseller instead of the brand's own pages; or as gate 3 of a full readiness audit.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

- **Validity** - JSON-LD that fails to parse is discarded silently and in full, so the team believes it has
  structured data and consumers see none. Also detects blocks that are HTML-escaped by the template and only parse
  after unescaping.
- **Presence** - whether any JSON-LD, microdata or RDFa exists at all. Microdata-only sites are credited, not
  penalised.
- **Type coverage by page class** - Organization/WebSite on the homepage, Product on product pages, Article on
  posts, FAQPage on question content, BreadcrumbList on nested pages. Gated by site type and never demanded of a
  page class it does not apply to.
- **Field completeness** - the point of the skill. A `Product` with no `offers`, or an `Organization` with only a
  name, validates and answers nothing. Missing *required* fields are reported per type, together with the question
  that type exists to answer.
- **Price specifically** - the most-asked commercial fact, checked on its own so the finding and the fix are
  precise.
- **Untapped markup** - question-shaped content already on the page that is not marked up as an FAQ.

## Procedure

```bash
python skills/structured-data-audit/scripts/check_schema.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`SDA-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/schema-requirements.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
