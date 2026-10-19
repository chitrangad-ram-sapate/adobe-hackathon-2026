---
name: entity-corroboration-audit
description: >-
  Gate 4 of an AI-discoverability audit: check whether an extracted fact will be believed and repeated. Detects self-inconsistent brand descriptions across title, meta, social tags and structured data; entity ambiguity where nothing distinguishes a brand from others sharing its name; a missing sameAs identity graph; the absence of citable published facts; and staleness signals including stale copyright years and undated, unattributed articles. Also verifies off-site: fetches the external profiles the site declares in sameAs and reports the ones that no longer resolve or never point back. Use when AI assistants confuse a brand with something else or hedge when describing it.
license: MIT
allowed-tools: Bash, Read
---

# Entity and corroboration audit (gate 4)

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when assistants confuse the brand with a similarly named entity, hedge when asked about it, or repeat an outdated description; or as gate 4 of a full readiness audit.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

- **Self-consistency** - the meta description, og:description, twitter:description and Organization schema
  description compared pairwise. Four conflicting self-descriptions leave a system with no authoritative account,
  so it hedges or prefers a third-party one.
- **Identity graph** - `sameAs` links, split into identity *authorities* (Wikidata, Wikipedia, LinkedIn,
  Crunchbase, company registers) which disambiguate, and social profiles which mostly do not. Also finds profiles
  linked on the page but never declared.
- **Entity ambiguity** - an unqualified brand name in the title with no authority link, on a short, collision-prone
  name. This is the mechanism behind most cases of an assistant describing a company as something it is not.
- **Corroboration surface** - whether the site publishes anything the wider web *could* repeat: founding date,
  headquarters, leadership, named quantified figures.
- **Freshness** - stale copyright years, articles with no publication date in text or markup, articles with no
  named author.
- **NAP consistency** - conflicting phone numbers across the site, for local businesses only.

**Scope limit, stated on every run:** this skill reads only the audited site. It never consults external sources,
so it measures whether the site *enables* corroboration, not whether corroboration exists. The report says so in
`notes`.

## Procedure

```bash
python skills/entity-corroboration-audit/scripts/check_identity.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`ENT-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/entity-signals.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
