---
name: engagement-audit
description: >-
  Audit the on-site engagement half of AI readiness: why visitors who arrive do not stay. Checks whether interior pages give context to a visitor deep-linked from an assistant, whether pages offer a clear action, page weight and render-blocking scripts, mobile viewport and image handling, interruptive overlays and autoplay, dead-end pages, navigation reach, form friction and accessibility blockers. Use when traffic arrives but bounces, or alongside discoverability checks in a full readiness audit.
license: MIT
allowed-tools: Bash, Read
---

# On-site engagement audit

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when a site gets traffic that does not convert or explore, when improving discoverability is about to send more traffic into a poor experience, or as the engagement half of a full readiness audit.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

The framing that drives this skill: **a visitor sent by an assistant does not arrive on the homepage.**
They are deep-linked into whichever page answered their question, they arrive with no brand context, and part of
their answer has already been given to them elsewhere. Pages built for someone who came through the front door
lose them.

- **Standalone context** - do interior pages name the organisation, say what it is, and offer a route onward?
  This is the signature check: it is simultaneously an engagement defect and the reason discoverability wins get
  wasted.
- **Action clarity** - a clear primary action per key page; repeated undescriptive labels ("Learn more") that tell
  neither a visitor nor a machine where a link goes.
- **Weight and speed** - HTML document size, render-blocking scripts, third-party origin count, server response
  time. All transport-level proxies, labelled as such; no browser paint metric is claimed.
- **Mobile** - viewport declaration, image dimensions and lazy loading.
- **Interruption** - autoplay media, and consent or subscription overlays that appear to gate content. A consent
  banner alone is never flagged: it is a legal requirement in many jurisdictions.
- **Retention** - dead-end pages with no onward links, key destinations missing from homepage navigation.
- **Forms and accessibility** - unlabelled controls, excessive required fields, missing skip links.
- **Measurement** - absence of analytics, reported at `info`, because engagement work cannot be evaluated blind.

## Procedure

```bash
python skills/engagement-audit/scripts/check_engagement.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`ENG-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/engagement-heuristics.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
