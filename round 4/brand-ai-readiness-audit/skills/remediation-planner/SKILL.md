---
name: remediation-planner
description: >-
  Turn audit findings into fixes a team can actually carry out, and add improvements worth making where nothing is broken. Fingerprints the site's CMS or framework - including Adobe Experience Manager, Edge Delivery Services and Commerce, Shopify, WordPress, Drupal, Next.js, Nuxt, Webflow, Squarespace, Wix and HubSpot - and rewrites each suggested action into platform-specific steps, then generates proactive recommendations such as publishing llms.txt, a citable-facts page, question-shaped content and a stronger identity graph. Use after detector skills have run, as part of the brand-ai-readiness-audit marketplace.
license: MIT
allowed-tools: Bash, Read
---

# Remediation planner

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use after the detector skills have produced findings, before the report is composed. This is not a detector: it adds no findings and changes no severities.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.
- `--findings-dir <dir>` - the detector outputs to annotate, in place.
- `--proactive-out <path>` - where to write the proactive recommendations.

## What it checks

Two jobs, both of which need every detector's output plus the site profile, and neither of which belongs
inside a detector.

**1. Platform-specific remediation.** "Add Product JSON-LD" is correct and unhelpful. Each finding is mapped to a
remediation *topic* (jsonld, ssr, robots, sitemap, canonical, meta, media, edge, template and so on), and each
topic has a playbook per platform naming the actual file, template or admin screen to change. Detection stays
generic; prescription becomes specific. Where the platform is unknown - or identified with only low
confidence - a generic fallback is used instead, because telling a team to edit a file in a CMS they do not run is
worse than saying nothing.

**2. Proactive recommendations.** Improvements that strengthen discoverability and engagement where no defect was
found, emitted as `proactive_recommendations[]` and kept strictly separate from findings: a finding has evidence
of a problem, a recommendation does not. Each is gated on site type, on what the crawl found, and on whether the
matching defect is already reported - so the report never asks for the same thing twice.

## Procedure

```bash
python skills/remediation-planner/scripts/plan_remediation.py \
    --cache ./cache --findings-dir ./work --proactive-out ./proactive.json
```

Annotates each finding's `suggested_action.platform_specific` in place and writes the proactive recommendations
to a separate file for the composer to merge.

## Output

Findings JSON annotated in place, plus a file containing `proactive_recommendations[]`. Adds no findings and alters no severities.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/platform-playbooks.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
