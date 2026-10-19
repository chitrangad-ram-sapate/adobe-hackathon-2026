# Runtime budget

The brief requires an audit to complete in **under 5 minutes for a typical
site**. The default total budget is 270 seconds, leaving headroom.

## Allocation

| Phase | Budget | Notes |
| --- | --- | --- |
| Crawl | up to 65% of remaining, capped at 200s | The only phase that can meaningfully overrun, because it is the only one doing network I/O |
| Profile | up to 60s | Reads the cache only |
| Each detector | up to 90s | Reads the cache only; typically well under 1s |
| Remediation planner | up to 60s | Reads the cache and findings |
| Compose | up to 90s | Local |

Observed end-to-end on a real 14-page site: **about 20 seconds**, most of it
crawl.

## How the crawl stays bounded

- **Page budget** - 30 pages by default, stratified by page type so a
  3,000-page blog cannot crowd out the pricing and contact pages that carry the
  facts assistants are asked for.
- **Wall-clock deadline** - every phase calls `Budget.ok(need)` before starting
  more work and stops cleanly rather than overrunning.
- **Per-request timeout** - 12s default.
- **Response size cap** - 5 MB, so a pathological page cannot hang or exhaust
  memory.
- **Redirect cap** - 8 hops, with loop detection.
- **Concurrency** - 6 workers, dropping to sequential with a delay when
  robots.txt requests a `Crawl-delay`.
- **Sitemap index following** - one level deep, 10 child sitemaps maximum.

## Degradation, not failure

When the budget runs out the crawl stops and records:

> Crawl stopped early at the Ns time budget; X of Y selected pages were
> fetched. Coverage-based findings are computed over what was fetched.

in `audit.limitations`. Coverage percentages are always reported against what
was actually sampled (`sampled_count` on every finding), never extrapolated to
the whole site.

The same principle applies throughout: a detector that fails or times out
degrades **its own gate only**, is recorded in `audit.limitations`, and its gate
is excluded from the score rather than being awarded 100. An untested gate has
not passed.

## Determinism

**What is guaranteed:** re-analysing the same crawl cache produces a
byte-identical report. All analysis is a pure function of the cache:

- Page ordering is sorted by (type priority, depth, URL) after collection, never
  by thread completion order.
- The 404 probe uses a fixed path, not a random one.
- Findings are sorted by (severity, gate order, check id, title) before `F-NNN`
  ids are assigned.
- Platform ties break alphabetically.

Verify with `--cache <dir> --keep-cache`, then `--cache <dir> --reuse-cache`.
`tests/run_tests.py` asserts this on fixtures and
`tests/generalization_batch.py` asserts it on live sites.

**What is not guaranteed, and cannot be:** that two *live crawls* of the same
site produce the same report. Large sites change between requests, personalise
responses, rotate homepage links and return different link sets, so a different
page sample reflects a different site state rather than a defect. Across the
corpus, re-crawls typically agree on most checks and differ at the margins where
the page sample differed. Every finding carries `sampled_count` for exactly this
reason: a coverage claim is always relative to what that run actually fetched.
