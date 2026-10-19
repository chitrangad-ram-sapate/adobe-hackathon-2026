---
name: site-access-audit
description: >-
  Gate 1 of an AI-discoverability audit: determine whether a machine can reach a site's content at all. Checks robots.txt including AI-assistant crawler directives, CDN/WAF user-agent gating, noindex directives, canonical correctness, HTTPS and host duplication, TLS validity, sitemap health, redirect chains and soft 404s. Use as part of the brand-ai-readiness-audit marketplace, or alone to diagnose why a site is absent from search results and AI answers despite looking healthy in a browser.
license: MIT
allowed-tools: Bash, Read
---

# Site access audit (gate 1)

Part of the `brand-ai-readiness-audit` marketplace. Composed by the
`audit-orchestrator` entrypoint, which crawls the site once and passes the
shared cache to this skill.

## When to use

Use when a site appears entirely missing from AI answers and search results, when a team reports "we're just not showing up anywhere", or as gate 1 of a full readiness audit. Access failures make every later gate moot, so run this first and read its findings first.

## Inputs

- `--cache <dir>` - a crawl cache written by
  `skills/audit-orchestrator/scripts/fetch_site.py`.

## What it checks

- **robots.txt** - reachability (a 5xx here is treated as disallow-all by several crawlers), blanket
  `Disallow: /`, orphaned directives that crawlers silently ignore, and per-agent rules.
- **AI crawler directives** - blocks are separated into *retrieval* agents (which fetch live to compose and cite
  an answer) and *training* agents. Blocking retrieval is nearly always accidental and costs citations directly;
  blocking training is a legitimate policy choice and is reported at `info`, never as a defect.
- **Edge gating** - a differential probe fetches the same URL with a plain client and a browser user agent.
  A 403 or challenge for one and 200 for the other is a bot-management rule that makes the site invisible to every
  AI fetcher while looking perfectly healthy to its owners.
- **Indexability** - `noindex` in meta robots or the `X-Robots-Tag` header on pages meant to be found.
- **Canonicals** - cross-domain canonicals, pages collapsing into the homepage, missing self-references.
- **Origins** - apex and www both serving 200 without converging, HTTP not redirecting to HTTPS, TLS failures.
- **Discovery** - sitemap presence, validity, declaration in robots.txt, and `lastmod` truthfulness.
- **Health** - broken internal links and sitemap entries, long redirect chains, soft 404s.

## Procedure

```bash
python skills/site-access-audit/scripts/check_access.py --cache ./cache
```

Reads the shared crawl cache produced by the orchestrator and emits
`{findings, checks_skipped, notes}` as JSON on stdout. It performs no network requests of its own, so it is
fast, repeatable, and safe to re-run against a saved cache while iterating.

## Output

A JSON object with `findings[]`, `checks_skipped[]` and `notes[]`. Every finding is built through `auditlib.findings.finding()`, so it carries `check_id` (`ACC-NNN`), `severity`, `gate`, an `evidence` sentence containing the measurement, `mechanism`, `confidence`, `method` and a `suggested_action` with ordered steps, effort, owner and a verification instruction.

## Rules

- **Read-only.** This skill never modifies the audited site, and issues no network requests to it.
- **Applicability first.** Every check declares the site types and page types it applies to. Where a check does
  not apply, or a required capability was unavailable, it is recorded in `checks_skipped` with a reason rather
  than guessed at.
- **Evidence carries the measurement.** A finding's `evidence` states the numbers behind it, never a restatement
  of its title.
- **Severity follows the shared rubric** in `skills/audit-orchestrator/references/severity-rubric.md`.

## Reference files

- `references/ai-crawlers.md` - the full check catalogue, with each check's thresholds, mechanism, and its explicit
  *do not flag when* conditions.
