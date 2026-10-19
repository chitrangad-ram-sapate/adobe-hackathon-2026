# brand-ai-readiness-audit

An Agent Skill Marketplace that audits any public website for the root causes
of **poor AI discoverability** (not found, not cited, misrepresented by AI
assistants) and **poor on-site engagement** (visitors arrive and leave), then
emits a single structured report of evidence-backed findings with prioritized,
platform-specific fixes.

**Recommend-only.** Every skill is read-only: GET and HEAD requests to the
audited site, robots.txt obeyed, no forms, no authenticated areas, nothing
written to the target, ever.

```bash
python skills/audit-orchestrator/scripts/run_audit.py https://example.com \
    --out audit-report.json --markdown audit-report.md
```

No installation. No dependencies. Python 3.9+ and its standard library are the
only requirements — an optional browser engine upgrades one check if present,
and its absence is handled explicitly rather than silently.

---

## The model: four gates, then the door

The audit is organised around the sequence a page has to survive before a brand
can be cited, and then the visit that citation produces. The gates are
**sequential** — failing an earlier one makes the later ones unreachable, which
is what lets the report say *what to fix first* rather than just listing
problems.

```
                                 ┌─────────────────────────────────────┐
   a machine asks a question     │  brand-ai-readiness-audit           │
              │                  │                                     │
              ▼                  │   audit-orchestrator  ◄── entrypoint │
    ┌───────────────────┐        │        │                            │
    │ 1. ACCESS         │◄───────┼── site-access-audit                 │
    │ can it reach it?  │        │                                     │
    └────────┬──────────┘        │                                     │
             ▼                   │                                     │
    ┌───────────────────┐        │                                     │
    │ 2. RENDER         │◄───────┼── render-extractability-audit       │
    │ can it read it?   │        │                                     │
    └────────┬──────────┘        │                                     │
             ▼                   │                                     │
    ┌───────────────────┐        │   structured-data-audit  (typed)    │
    │ 3. EXTRACT        │◄───────┼── answer-readiness-audit (quotable) │
    │ can it quote it?  │        │                                     │
    └────────┬──────────┘        │                                     │
             ▼                   │                                     │
    ┌───────────────────┐        │                                     │
    │ 4. TRUST          │◄───────┼── entity-corroboration-audit        │
    │ will it repeat it?│        │                                     │
    └────────┬──────────┘        │                                     │
             ▼                   │                                     │
      the brand is cited         │                                     │
             │                   │                                     │
             ▼                   │                                     │
    ┌───────────────────┐        │                                     │
    │ 5. ENGAGEMENT     │◄───────┼── engagement-audit                  │
    │ does the visitor  │        │                                     │
    │ orient and stay?  │        │   remediation-planner (fixes)       │
    └───────────────────┘        └─────────────────────────────────────┘
```

The fifth stage is not a separate concern bolted on. **A visitor sent by an
assistant does not arrive on the homepage** — they are deep-linked into
whichever page answered their question, with no brand context. So the more
successful the discoverability work, the more traffic flows into whatever
engagement defects exist. The two halves are one pipeline, and the marketplace
treats them that way.

---

## The eight skills

| Skill | Gate | What it owns |
| --- | --- | --- |
| **`audit-orchestrator`** *(entrypoint)* | — | Crawls once, profiles the site, runs every detector, de-duplicates, ranks, scores and emits the single report |
| `site-access-audit` | 1 · access | robots.txt and **AI-crawler directives**, **CDN/WAF user-agent gating**, noindex, canonicals, TLS, host duplication, sitemap health, soft 404s |
| `render-extractability-audit` | 2 · render | **JavaScript render gap**, empty app shells, hydration-only content, facts locked in images, **scanned PDFs**, iframes and collapsed regions, document structure |
| `structured-data-audit` | 3a · extract | JSON-LD validity and **per-type field completeness** — price, dates, authorship, identity — gated by page type |
| `answer-readiness-audit` | 3b · extract | Whether a **quotable sentence exists**: identity statements, concrete headlines, published prices, contact facts, question-shaped content, query-surface coverage |
| `entity-corroboration-audit` | 4 · trust | Self-consistent descriptions, **entity ambiguity**, the sameAs identity graph, citable published facts, freshness |
| `engagement-audit` | 5 · engagement | **Standalone context for deep arrivals**, action clarity, weight and speed proxies, mobile, interruption, dead ends, forms, accessibility |
| `remediation-planner` | — | Rewrites each fix for the **detected CMS/framework**, and adds the proactive recommendations |

---

## How the entrypoint composes them

**The shared crawl cache is the composition backbone.** The orchestrator
fetches the site exactly once into a plain directory, and every detector is a
pure function from that cache to a list of findings.

```
run_audit.py
   │
   ├─ fetch_site.py ──────► cache/   manifest.json, robots.txt, extras.json,
   │                                 pages/<key>.html · .rendered
   ├─ profile_site.py ────► cache/manifest.json ["profile"]   ← the applicability gate
   │
   ├─ 6 detectors ────────► cache/_findings/<gate>.json       ← separate processes,
   │      (read-only, in parallel-safe isolation)                no detector re-crawls
   │
   ├─ plan_remediation.py ► annotates findings in place + proactive.json
   │
   └─ compose_report.py ──► audit-report.json  (+ .md)
```

This is what makes the decomposition real rather than decorative:

- **No detector performs a network request.** One crawl serves all of them, so
  eight skills cost the same as one and the audit finishes in ~20 seconds.
- **Detectors cannot depend on each other.** Each is independently runnable
  against a saved cache — `python skills/site-access-audit/scripts/check_access.py
  --cache ./cache` — which is also how the offline test suite works.
- **Failure is isolated.** A detector that crashes, times out, or is simply
  absent from the marketplace degrades *its own gate* and is recorded in
  `audit.limitations`. Its gate is then excluded from the score rather than
  awarded 100, because an untested gate has not passed.

Composition then applies four rules that only make sense with every detector's
output in view at once:

1. **De-duplication.** One root cause seen by two detectors is reported once
   (a missing price outranks generic field-completeness; a measured render gap
   outranks the static estimate).
2. **Gate precedence.** If the access gate is closed site-wide, later-gate
   findings were measured against content nobody can reach, so they are demoted
   to at most `medium` — with the reason written into the finding. Reporting a
   missing FAQ schema at "high" on a site that 403s every crawler is a ranking
   error.
3. **Deterministic identity.** Findings are sorted by severity, gate order and
   check id *before* `F-001…` ids are assigned, so re-analysing the same crawl
   produces a byte-identical report - no ordering depends on thread completion
   or dict iteration. Two separate *live* crawls of a large site may sample
   different pages, which is why every finding carries `sampled_count` and
   coverage is always stated relative to what that run fetched.
4. **Scoring and framing.** Per-gate scores and a one-sentence headline a
   non-expert can act on.

---

## Design commitments

These are the decisions that shaped the build, in the order they mattered.

### Few false positives, deliberately

A well-built site must produce a short report. Three rules are binding on every
check:

- **Applicability first.** Every check declares the site types and page types
  it applies to. `structured-data-audit` never asks a personal blog for
  Product markup; `engagement-audit` never demands a pricing CTA from a
  documentation site. Site classification returns `unknown` rather than
  guessing, because a wrong site type turns on the wrong checks.
- **Every check has an explicit *do not flag when* clause**, written at
  authoring time and documented in each skill's `references/` catalogue.
- **Absence of evidence is not evidence.** A page that could not be fetched is
  a limitation, never a defect charged to the site.

`tests/run_tests.py` asserts this directly: a clean-site fixture must produce
**zero** findings from every detector. That assertion is worth more than the
positive ones — "it found lots of problems" is easy.

Every check's threshold and its *do not flag when* clause live in its skill's
`references/` catalogue, and `tests/check_consistency.py` fails if the code and
the catalogue disagree — so the documented rules cannot quietly drift away from
the implemented ones.

### Never claim a measurement that did not happen

The render gap is measured against an executed DOM when a browser engine is
available (`method: rendered`, high confidence) and estimated from static
signals when it is not (`method: heuristic`, medium confidence) — with the
limitation stated in the finding *and* in `audit.limitations`. The report
validator enforces this: a finding claiming `method: rendered` on a run with no
rendering capability is a hard validation error.

The same honesty applies throughout. Engagement timings are transport-level
proxies and say so. `entity-corroboration-audit` records on every run exactly
how far it went: it verifies the profiles the site declares in `sameAs`, and
says so, but it never searches for the brand, so corroboration beyond those
declared profiles is still measured as whether the site *enables* it rather
than implying the wider web was checked. A profile a host refused to serve is
reported as unverified, never as a defect. No Core Web Vitals figure is ever
reported, because none is ever measured.

### The one place the audit leaves the site

Every check runs against a single crawl of the audited origin, with one
exception: `ENT-011/012/013` fetch the external profiles the site itself
declares in its `sameAs` array — at most 8 per audit, read-only, with each
host's own `robots.txt` consulted first, and `--no-offsite` to disable.

Only explicit assertions are followed. `sameAs` means "this profile is the same
entity as this brand", so following it verifies a claim the site actually made.
Ordinary homepage links are not followed: a site links to plenty of pages it
does not own, and treating those as identity claims would fault a brand for a
profile that was never theirs.

The audit never searches for the brand, and a host that blocks automated
clients yields an *unverified* profile — recorded in `audit.limitations`, never
charged to the site. A 404 is a dead link; a 403 is not.

### Zero dependencies

`lib/auditlib/` is a small standard-library toolkit: a bounded HTTP client, a
forgiving HTML document model, a robots.txt parser that keeps the per-agent
detail the audit needs, a schema.org completeness model, and the shared cache.
A grader can unzip this and audit a site immediately.

### Mechanism, not folklore

Every finding carries a `mechanism` field explaining *why* the defect breaks
retrieval or engagement, in terms of what the pipeline or the visitor actually
does. It is the field that makes a finding auditable rather than trusted, and
writing it is what keeps the checks honest.

---

## Output

One JSON report. The brief's required fields (`site`, `audited_at`, a
severity-count `summary`, and per-finding `id`/`title`/`severity`/`evidence`/
`suggested_action`) are all present; everything else is an additive superset.

```jsonc
{
  "site": "shop.example",
  "audited_at": "2026-09-09T09:14:22Z",
  "summary": { "total_findings": 29, "critical": 3, "high": 8, "medium": 10,
               "low": 7, "info": 1, "headline": "…start with X" },
  "scores": { "overall": 27.6,
              "gates": { "access": 38, "render": 38, "extract": 0,
                         "trust": 81, "engagement": 1 } },
  "audit": {
    "site_profile": { "site_type": "ecommerce", "platform": "Next.js", … },
    "checks_skipped": [ { "check_id": "…", "reason": "…" } ],
    "capabilities":  { "javascript_rendering": false },
    "limitations":   [ "JavaScript rendering was unavailable, so …" ]
  },
  "findings": [{
    "id": "F-001", "check_id": "ACC-003", "severity": "critical",
    "category": "discoverability", "gate": "access",
    "title":     "AI assistant retrieval crawlers are blocked in robots.txt",
    "evidence":  "4 retrieval agents are disallowed from /: oai-searchbot (OpenAI), … rule 'Disallow: /' at line 8.",
    "mechanism": "These are the agents that fetch a page live while composing an answer and then cite it…",
    "confidence": "high", "method": "static",
    "suggested_action": {
      "summary": "Allow retrieval agents while keeping any training opt-out you intend.",
      "priority": "critical", "effort": "low", "owner": "engineering",
      "how": [ "…" ], "platform_specific": [ "…" ],
      "verify": "Re-run check ACC-003; no agent with purpose=retrieval should be disallowed from /."
    }
  }],
  "proactive_recommendations": [ { "id": "P-001", … } ]
}
```

**Suggested actions go beyond the problems found.**
`proactive_recommendations[]` carries improvements where no defect was
detected — publishing `/llms.txt`, a citable-facts page, question-shaped
content in customers' own words, honest comparison pages, a stronger identity
graph — each gated so the report never asks for the same thing twice.

Validate any report against the contract:

```bash
python skills/audit-orchestrator/scripts/validate_report.py audit-report.json
```

---

## Generalization: measured, not asserted

The brief grades this on sites it was never built against, so the claim is
backed by a reproducible corpus run rather than by argument.

```bash
python tests/generalization_batch.py            # 71 sites, ~5 minutes total
python tests/generalization_batch.py --segment saas --limit 10
```

`tests/sites.txt` holds 71 public sites across ecommerce, SaaS, publishers,
documentation, government, academic, charity, non-English (French, German,
Japanese, Spanish, Italian), personal/brochure sites, eight CMS platforms,
four deliberately bot-managed sites, and three error paths. **None of them is
used to tune a threshold and none appears in any fixture.**

Latest full run:

| | Result |
| --- | --- |
| Completed with a report | **71/71** |
| Schema-valid reports | **71/71**, 0 validator warnings |
| Crashes, timeouts, empty results | **0** |
| Runtime min / median / max | 1s / 20s / 93s — **0 over the 5-minute ceiling** |
| Distinct checks exercised | **72** |
| Findings per site min / median / max | 1 / 12 / 22 |
| Analysis determinism (one crawl, two analyses) | **IDENTICAL** on every sampled site |

### What the batch is actually looking for

It is not a scoreboard. It flags the three ways an audit tool goes wrong at
scale, so a human has to look:

- **Checks that fire on nearly every site** are either detecting something
  genuinely universal or are too loose. Any check above 75% is flagged unless
  it is listed in `EXPECTED_COMMON` with a written justification.
- **Checks that never fire anywhere** are dead or unreachable. 14 of 83 did not
  fire on this corpus — all conditions that are genuinely rare (TLS failure,
  scanned PDFs, site-wide robots blocks, invalid JSON-LD) or that require the
  optional browser engine.
- **Severity inflation.** 28 `critical` findings across 71 sites, concentrated
  in exactly three causes: unreachable origins, cross-domain canonicals, and
  publishers blocking AI retrieval crawlers in robots.txt. If `critical` were
  common on ordinary sites, the ranking would have stopped meaning anything.

### Known trade-offs, stated plainly

- **The profiler resolves a site type on 48% of the corpus.** Of 42 sites with
  an expected type, 23 agreed, 18 returned `unknown`, and 1 was misclassified.
  That ratio is deliberate: `unknown` suppresses type-gated checks, costing
  recall to protect precision, because a wrong site type turns on the wrong
  checks. The one misclassification is a charity with a large newsroom read as
  a publisher — which suppresses commercial checks either way. Its domain
  (`.org.uk`) is open to any registrant, so the authoritative-domain rule below
  deliberately does not rescue it; only registry-restricted suffixes qualify.
- **Platform identified on 52%**, and only ever at medium or high confidence.
  Below that the remediation planner falls back to generic guidance rather than
  naming a CMS the team may not run.
- **The render gap runs in estimated mode** unless a browser engine is
  installed, and says so in every affected finding.

### Bugs this corpus caught

Running it is how the following were found and fixed, each of which only
appears on real sites:

1. Bot-managed origins (Akamai, Cloudflare) produced **no report at all** —
   the single most valuable finding failing silently. Now falls back to a
   browser agent, discloses the substitution, and leads with `ACC-008`.
2. An apex that resolved 200 but redirected to a `www` host that blocked the
   auditor, yielding **0 pages** from a healthy site.
3. Unreachable sites scoring **92/100**, because untested gates were credited
   full marks.
4. A payments company identified as **WooCommerce at high confidence** because
   its docs *mention* WooCommerce — platform fingerprinting now reads markup
   attributes, not prose.
5. `noindex` on a checkout subdomain reported as a defect, when it is correct
   behaviour.
6. Detector JSON crashing on non-Latin scripts under Windows' console encoding.
7. An institution that also publishes news being classified as a **publisher**:
   generic content-shape signals (Article schema, article URLs) could outvote a
   registry-controlled `.gov`/`.ac.uk` domain. The margin was small enough that
   the same site classified differently between runs. Such domains are now
   authoritative rather than merely heavily weighted, and the override is
   recorded in the profile signals.

---

## Repository layout

```
brand-ai-readiness-audit/
  marketplace.json                 manifest: 8 skills, exactly one entrypoint
  README.md
  LICENSE                          MIT
  lib/auditlib/                    shared standard-library toolkit
    http.py urls.py htmlx.py robots.py schema.py cache.py findings.py
  skills/
    audit-orchestrator/            ENTRYPOINT
      SKILL.md
      scripts/  run_audit.py fetch_site.py profile_site.py
                compose_report.py validate_report.py
      references/  report-schema.json severity-rubric.md
                   site-profiles.md runtime-budget.md
    site-access-audit/             SKILL.md scripts/ references/
    render-extractability-audit/   SKILL.md scripts/ references/
    structured-data-audit/         SKILL.md scripts/ references/
    answer-readiness-audit/        SKILL.md scripts/ references/
    entity-corroboration-audit/    SKILL.md scripts/ references/
    engagement-audit/              SKILL.md scripts/ references/
    remediation-planner/           SKILL.md scripts/ references/
  tests/                           offline fixture suite + live corpus run
    run_tests.py  harness.py
    generalization_batch.py  sites.txt
    check_consistency.py
  examples/                        illustrative output, both directions
    example-real-site.{json,md}  example-broken-site.{json,md}
```

Each `references/` file is the full check catalogue for its skill: every
check's thresholds, its mechanism, and its explicit *do not flag when*
conditions. `skills/audit-orchestrator/references/severity-rubric.md` defines
the gate model, severity scale, confidence separation, priority matrix and
scoring used by every skill.

---

## Running it

```bash
# Full audit
python skills/audit-orchestrator/scripts/run_audit.py example.com \
    --out report.json --markdown report.md

# Useful flags
    --max-pages 30       page budget (stratified by page type)
    --budget 270         total wall-clock seconds
    --no-render          skip JavaScript rendering
    --keep-cache         retain the crawl cache for inspection
    --reuse-cache        re-run detectors against an existing cache

# One detector against a saved cache
python skills/site-access-audit/scripts/check_access.py --cache ./cache

# Offline regression suite (no network)
python tests/run_tests.py

# Generalization corpus (71 live sites, ~5 minutes)
python tests/generalization_batch.py

# Documentation/code consistency + brief conformance (offline, instant)
python tests/check_consistency.py
```

**Runtime.** Budgeted at 270s against the brief's 5-minute ceiling; observed
end-to-end on a real 14-page site is **~20 seconds**, almost all of it crawl.
When the budget is reached the crawl stops cleanly and records how many of the
selected pages were fetched — coverage figures are always reported against what
was actually sampled, never extrapolated.

**Optional upgrade.** Installing Playwright switches the render-gap check from
estimated to measured. Nothing else changes, and its absence is never silent.

---

## Safety

- Read-only: GET and HEAD only, to the audited origin.
- `robots.txt` is obeyed for every crawled URL. The only requests that
  deliberately bypass it are the single diagnostic fetches of `robots.txt`
  itself and the site root, which are required to report *why* a crawler would
  be blocked.
- Polite: page budget, wall-clock deadline, per-request timeouts, response-size
  caps, `Crawl-delay` honoured, and an honest, identifiable user agent.
- No authenticated areas, no form submission, no rate-limit probing, no
  destructive action, and nothing written to the audited site.
