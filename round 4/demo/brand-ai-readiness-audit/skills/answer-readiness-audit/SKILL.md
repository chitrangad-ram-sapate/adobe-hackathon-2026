---
name: answer-readiness-audit
description: >-
  Gate 3b of an AI-discoverability audit: check whether a page contains a sentence worth quoting. Detects missing plain-language identity statements, abstract marketing headlines that name no category, generic or duplicated titles and descriptions, pricing and contact facts absent from readable text, the absence of question-and-answer content, and gaps in comparison and use-case coverage. Use when a site is crawlable and well-marked-up but still never quoted by AI assistants.
license: MIT
allowed-tools: Bash, Read
---

# Answer readiness audit (gate 3b)

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when a site is technically sound - reachable, rendered, marked up - and assistants still fail to describe the brand, or describe it in someone else's words; or as gate 3 of a full readiness audit.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

Assistants compose answers by lifting short, self-contained passages. A page can pass every technical
check and still contribute nothing, because it never states in plain words what the organisation is, who it is
for, or what anything costs. Brand copy is written for a reader who already has the context; an extractive system
has none and cannot infer a category from a slogan.

- **Identity statement** - does the homepage contain a sentence combining the brand name, a descriptive verb and a
  category noun? Checked across the opening text, the meta description and the Organization schema description.
- **Headline concreteness** - an H1 that names an ambition rather than a business gives retrieval nothing to match.
- **Titles and descriptions** - missing, placeholder ("Home"), or duplicated across pages.
- **Commercial facts in text** - a pricing page with no number; a contact page with no phone or email as
  selectable text.
- **Answer shape** - whether the site publishes anything as a question with a self-contained answer.
- **Query surface** - whether comparison, alternatives, use-case and how-to pages exist, since a large share of
  assistant questions are comparative or qualifying.

Several checks here are linguistic and are deliberately emitted at `confidence: medium` with
`method: heuristic` - signals for a human to confirm, never measurements.

## Procedure

```bash
python skills/answer-readiness-audit/scripts/check_answer_readiness.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`ANS-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/answer-patterns.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
