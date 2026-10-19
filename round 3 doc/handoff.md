# Handoff — Adobe University Hackathon 2026, Round 3

*Last session: 2026-09-09 (session 3). Brief lives in `d:/Adobe/handout.md` (+ `handout.pdf`).*
*This file is session state and is deliberately NOT inside the submission zip.*

---

## 1) Goal

Build an Agent Skill Marketplace that audits any website for the root causes of
poor **AI discoverability** (not found/cited by AI assistants) and poor
**on-site engagement**, and emits one structured report of evidence-backed
findings with prioritized fixes. Graded on generalization to unseen sites, so
the artifact — not any single report — is the deliverable.

---

## 2) Current state

**Submission deadline: 13 September 2026.**

**A verified, submittable fallback is frozen at
`d:/Adobe/backup/brand-ai-readiness-audit-SUBMITTABLE-2026-09-09.zip`**
(51 files, 244 KB, CRC clean, all suites green). If anything below is not fully
green by the Sep 11 gate, submit that file as-is and stop. Do not edit it.

**`d:/Adobe/brand-ai-readiness-audit.zip` is CURRENT and submittable** — 251 KB,
51 files, repacked after Gap 1 and Gap 2 both passed their gates and re-verified
from a clean-room extract. This is the file to submit. The `backup/` copy is the
older pre-gap-closing fallback; prefer the current zip.

**Zip root convention is decided and settled: keep it.** The zip contains a
top-level `brand-ai-readiness-audit/` folder holding `marketplace.json`. The
brief calls that folder "marketplace root (this is what you zip)" and asks for
"a zip of the marketplace root directory", so including the directory is the
literal reading, and it avoids scattering 51 files on unzip. Do not repack.

| Verification | Result |
| --- | --- |
| Handout requirements | **20/20** (`tests/check_consistency.py`) |
| Offline fixture tests | **30/30** (`tests/run_tests.py`) |
| `skills-ref validate` | **8/8 skills valid** |
| Generalization corpus | **71/71 sites** complete, schema-valid, 0 crashes, 0 over 5-min ceiling |
| Doc/code consistency | **No problems** |
| Clean-room from zip | unzip → tests → live audit → valid report, zero setup |

8 skills, 1 entrypoint (`audit-orchestrator`). Python stdlib only, no deps.
Runtime ~3–90s per site depending on size.

**Open / known gaps (all deliberate, none blocking):**
- Site type resolves on 48% of corpus (23 agreed / 18 `unknown` / 1 misclassified).
  Conservative by design: `unknown` suppresses type-gated checks, trading recall
  for precision. Raising this further needs labelled ground truth, not more
  heuristics. The remaining miss is `wwf.org.uk` (charity with a large newsroom
  read as a publisher); `.org.uk` is an open registry, so the authoritative-domain
  rule correctly does not rescue it.
- **Appendix D is now substantially addressed** (session 3): the audit verifies
  the profiles a site declares in `sameAs` for reachability and reciprocity. It
  still never *searches* for the brand, so corroboration beyond declared
  profiles remains measured as whether the site enables it. That residue is
  deliberate — searching would need an external service and would weaken the
  "audits a website" scope.
- **Appendix F (email summarization) not addressed** — judged out of scope for a
  website audit.
- **`RND-001` is now validated in the wild** (session 3): 0 false positives
  across 71 sites, and confirmed to catch real gaps (notion.com 0.570,
  diagrams.net 0.034). Playwright remains OPTIONAL; without it the audit still
  degrades to `RND-002` heuristics, which is unchanged and still honest.
- No precision ground truth: firing rates flag suspicious checks for a human,
  which is not the same as verifying a finding is correct.

---

## 3) Active files

Root: `d:/Adobe/brand-ai-readiness-audit/`

**Most likely to need changes:**
- `skills/audit-orchestrator/scripts/profile_site.py` — site-type classifier and
  platform fingerprint. **This is the file to touch if raising recall.**
- `skills/audit-orchestrator/scripts/fetch_site.py` — crawl, origin resolution,
  browser-UA fallback, probes.
- `skills/audit-orchestrator/scripts/compose_report.py` — dedupe, gate
  precedence, scoring.
- `lib/auditlib/` — shared stdlib toolkit (`http, urls, htmlx, robots, schema,
  cache, findings`). `findings.py` enforces the severity rubric in code.

**Six detectors** (one per gate), each `skills/<name>/scripts/check_*.py` with a
matching `references/*.md` catalogue holding every threshold and *do not flag
when* clause. **Code and catalogue must stay in sync** — enforced by
`tests/check_consistency.py`.

**Tests:** `tests/run_tests.py` (offline fixtures), `tests/harness.py`,
`tests/generalization_batch.py` + `tests/sites.txt` (71 live sites),
`tests/check_consistency.py` (docs vs code vs brief).

---

## 4) Changes made (session 3 — gap closing)

**Playwright is now installed on this machine** (`pip install playwright`,
`python -m playwright install chromium`). It stays OPTIONAL in the artifact;
installing it is what allowed the measured render path to be exercised at all.

### Gap 2 — measured render path: CLOSED, validated

Two real bugs, both of which only appear on live sites:

1. **`RND-001` measured the wrong thing.** It compared `strip_tags(raw)`
   against `visible_text(rendered)` — two different extractors, both counting
   whole-page text including nav and footer. JavaScript routinely expands
   mega-menus without adding a quotable word, so server-rendered pages looked
   like SPAs. python.org read 73% coverage while its `main_text` was
   *byte-identical* (335 words both sides).
   Now measured as `page.doc.main_word_count / rendered_doc.main_word_count` —
   same extractor, main content only.
   - Precision AND recall both improved: false positives on server/static sites
     8→0 (all now 0.993–1.000); notion.com's genuine gap (122→214 main words,
     0.570) is now CAUGHT, having been MISSED at 0.828 before.
   - Class separation is now clean: server/static ≥0.993, client-rendered
     ≤0.034, so the 0.75 threshold sits in open space.
   - **Corpus: `RND-001` fired 0/71.** No false positives anywhere.
2. **Genuine SPAs were silently skipped.** `try_render` waited for
   `networkidle` and dropped any page that timed out — so the check was
   blindest exactly where render gaps are worst (Telegram, Excalidraw only
   render via fallback). Added a `domcontentloaded` fallback + settle delay,
   and a `finally` that closes pages which previously leaked on error.

Corpus with rendering on: 71/71 complete, schema-valid, 0 crashes, 0 over the
5-min ceiling, max 119s (rendering cost ~12s on the worst site).

### Gap 1 — off-site corroboration (Appendix D): BUILT, GATE PENDING

`ENT-011` (declared profile 404s), `ENT-012` (reachable profiles never link
back), `ENT-013` (off-site description shares almost no vocabulary with the
site). Verification runs in `fetch_site.py` during the **crawl phase**, results
stored in `extras["offsite"]`, so re-analysing one crawl stays deterministic —
the rubric explicitly scores "deterministic; safe".

**Only `sameAs` is followed.** The first version also followed homepage links to
known profile hosts; live testing showed that pulled in
`wikipedia.org/wiki/Tkinter` and `github.com/python/cpython/issues` from
python.org — incidental content links, not identity claims. Firing a
reciprocity finding on an issue tracker would be a plain false positive. Now
only explicit `sameAs` assertions are verified, which also deleted the
host-pattern regex — one less thing fitted to the sites we happened to test.

Guardrails: max 8 profiles, per-host `robots.txt` honoured before first fetch,
read-only GET, inside the existing crawl budget, `--no-offsite` disables.
**Blocked is not dead**: 404/410 = dead link; 403/429/robots-disallowed =
*unverified*, recorded in `audit.limitations`, never charged to the site.

Docs/manifest synced: `marketplace.json` `safety.network` now states the real
scope (was "audited site only" — that had become false), entity `SKILL.md`
description, `references/entity-signals.md` (rows + a section on what off-site
verification does and does not do), and the README's "consulted no external
source" paragraph, which was also false.

Tests: 36/36 (5 new off-site fixtures incl. the negatives — blocked ≠ dead,
reciprocal profiles don't fire, silent when disabled). Consistency: clean.

**Gap 1 PASSED its corpus gate** — but only on the second attempt. The first
run came back **68/71 schema-valid**, a real regression:

- Cause: the off-site findings declared `method="rendered"`, which in this
  codebase means *measured with a JavaScript engine*, and `validate_report.py`
  enforces it. On three sites (lush, elpais, zeit) rendering failed while
  off-site verification succeeded, so the finding claimed a capability the run
  did not have.
- Fix: those checks now declare `method="external"` (the vocabulary already
  existed), and the validator's `external` rule accepts `offsite_verification`
  alongside `web_search`. **`web_search` was deliberately NOT set true** — the
  audit does not search, and setting it would have silenced the error with a lie.
- Second issue found while inspecting: `ENT-012` fired on lush.com from 1 of 2
  reachable profiles, hitting the 50% bar while the title claimed "the profiles
  do not point back" when half of them did. Tightened to require **at least two**
  one-way profiles as well as half. It now fires 0/71 — dormant on this corpus,
  which is the intended precision-over-recall trade.

Final gate: **71/71 complete, 71/71 schema-valid, 0 warnings, 0 crashes, 0 over
the 5-min ceiling** (max 127s), determinism IDENTICAL on same-crawl re-analysis
for all 3 sampled sites. Firing rates: `ENT-011` 1/71, `ENT-012` 0/71,
`ENT-013` 0/71.

Real finding it produced: zeit.de declares `flipboard.com/@ZEITONLINE` in
`sameAs`, which returns 404 — a dead identity claim, exactly the Appendix D
capability that was missing.

Note: the allbirds row in the *informational* live-re-crawl column shows
`0/17 checks shared, 9->0 pages`. That is the known rate-limiting from repeated
runs against the same domain (see §5), not a determinism regression — the
same-crawl re-analysis column is IDENTICAL.

---

## 4b) Changes made (session 2)

Verified the packaged artifact end to end, settled the zip-root question, and
fixed one real classifier defect found while spot-checking a live run.

1. **Re-verified everything from the shipped zip**: 30/30 offline tests, 20/20
   handout requirements, zip intact and byte-identical to the working tree,
   clean-room extract → live audit → schema-valid report.
2. **Zip root convention decided — keep the top-level folder** (see §2).
3. **Fixed: registry-controlled domains could be outvoted by content shape.**
   gov.uk classified as `media_publisher` because Article schema + article URLs
   scored 4.5 against the government-domain vote of 4.0. Because the margin was
   this narrow, the site classified *differently between runs* — which is why
   the README had recorded only one misclassification while a live run showed
   two. `.gov`/`.mil`/`.gov.uk`/`.edu`/`.ac.uk` are now **authoritative**
   (resolve `institutional` at high confidence, override recorded in
   `site_type_signals`) rather than merely heavily weighted. Raising the weight
   instead would only have deferred the collision to the next generic signal.
   Open registries (`.org`, `.org.uk`, `.ngo`) deliberately still only vote.
   - This is a precedence rule keyed on registry restriction, **not**
     corpus-fitting: it generalizes to every such domain. Confirmed on
     `cam.ac.uk`, which is not in the corpus → `institutional`/high.
   - Corpus effect: agreed 21→23, `unknown` 20→18, misclassified 1→1, 71/71
     still complete, 0 crashes, 0 over the 5-min ceiling.
   - `README.md` stats and `references/site-profiles.md` updated to match.

---

## 4c) Changes made (session 1)

Built the whole marketplace, then hardened it against a 71-site corpus. Bugs
found and fixed, all of which only appear on real sites:

1. **Bot-managed origins produced no report at all** (Akamai/Cloudflare 403 to
   non-browser UA). The most valuable finding was failing silently. Now falls
   back to a browser UA, **discloses the substitution** in `ACC-008` +
   `audit.limitations` + crawl metadata; `--no-ua-fallback` disables it.
2. **Apex resolved 200 but redirected to a `www` host that blocked us** → 0
   pages from a healthy site. Now re-verifies the resolved origin.
3. **Unreachable sites scored 92/100** — untested gates were credited 100. Now
   only the access gate is scored, and `ACC-000` is emitted.
4. **Platform false positive:** stripe.com → "WooCommerce, high confidence"
   because its docs *mention* WooCommerce. Fingerprint now reads markup
   attribute values, not prose.
5. **`noindex` on checkout subdomains** reported as a defect; it's correct
   behaviour. Transactional hosts excluded.
6. **`ENG-001` escalating to `critical`** — engagement can't make a brand
   invisible site-wide. Capped at `high`.
7. **UnicodeEncodeError** on non-Latin scripts under Windows console encoding.
   All JSON pipes forced to UTF-8.
8. **`allowed-tools` frontmatter was missing** (handout requires it). Added to
   all 8 skills, minimal surface.
9. Added `institutional` site type (gov/academic/charity) — that whole class
   previously fell through to `unknown`.
10. Doc/code drift fixed: `ACC-000` undocumented; `SDA-005/006` IDs assembled by
    f-string (ungreppable); `ACC-016` stale exclusion clause.
11. **Corrected an overclaim in the README**: determinism is guaranteed for
    re-analysis of one crawl, NOT for two live crawls of a changing site.

---

## 5) Failed attempts — do not repeat

- **Bash heredocs with long content fail** in this environment ("unexpected EOF
  while looking for matching `''`"). Short ones work. **For any multi-line
  patch: write a `.py` patch script to the scratchpad with the Write tool, then
  execute it.** This cost several retries.
- **`/tmp/...` paths get mangled** by MSYS path translation in the Bash tool —
  a path passed as an argv gets converted, the same literal inside a Python
  string does not, so they silently disagree. Use the full Windows scratchpad
  path.
- **Determinism test design was wrong**: comparing a crawl-run against a
  reuse-cache run reported false "DIFFERENT". The real claim is one crawl,
  **two analysis passes**. Fixed in `generalization_batch.py`.
- **Broadly lowering site-type thresholds backfired** — a Japanese news site
  classified as `documentation`. Reverted to requiring a *structural* signal
  (URL patterns) before text/code heuristics may vote. Do not re-loosen without
  ground truth; this is the fit-to-examples trap the brief warns about.
- **Running the batch at 10 workers repeatedly against the same domains** got
  allbirds/everlane rate-limited, polluting results. Determinism sample is now
  spread across segments and paced.
- **Do not edit package code while `generalization_batch.py` is running.** It
  spawns a fresh audit process per site, so edits mid-run mix old and new code
  across the corpus and the result cannot be trusted.
- **Offline fixtures do not exercise the crawl phase.** A missing `import re` in
  `fetch_site.py` passed 31/31 tests and only failed on the first live run.
  Always do one live audit after touching `fetch_site.py`.
- **Do not measure a render gap on whole-page text.** It measures furniture, not
  content — see §4. Compare `main_text` with the same extractor on both sides.
- Do not "fix" `unknown` site types by special-casing corpus sites — that is
  fitting to examples and will hurt the generalization score. The one principled
  exception found so far: a signal that is *externally verified* (a
  registry-restricted TLD) may override the vote, because it generalizes to
  every site holding that suffix rather than to the corpus. Content-shape
  signals never qualify.
- When a vote margin is narrow (4.5 vs 4.0), the classification is **unstable
  across runs**, so a single live spot-check can disagree with the recorded
  corpus stats without either being wrong. Check the vote tally
  (`manifest.json` → `profile.site_type_votes`, via `--keep-cache`) before
  concluding a doc is stale.

---

## 6) Next steps (in order)

Gaps 1 and 2 are both CLOSED, verified, repacked and re-verified from the zip
(36/36 tests, consistency clean, live audit on mozilla.org — not in the corpus —
valid with both capabilities active).

1. **Sep 10-12 are freeze days. No new features.** The artifact is green; the
   largest remaining risk to the submission is a change landed near the
   deadline. Anything found broken gets reverted, not fixed.
2. **Submit `d:/Adobe/brand-ai-readiness-audit.zip` on Sep 13.**

Deliberately NOT attempted (and should not be, before the deadline):
- **Gap 3, precision ground truth.** Needs a human adjudicating findings against
  live pages; competes directly with the freeze. Remains documented as a known
  limitation, which is a defensible position.
- **Appendix F (email summarization).** Out of scope for a website audit;
  bolting it on would dilute the entrypoint's single responsibility, which the
  rubric rewards.

Optional, only if there is time and appetite — in value order:

2. **Build a labelled ground-truth set** (~30 sites, manually verified findings)
   to measure precision properly. This is the only way to justify raising
   site-type recall. Highest value, highest effort.
3. **Install Playwright and validate the `RND-001` measured path** on real SPAs.
   Currently untested outside fixtures.
4. **Off-site corroboration** for Appendix D — would need an external search
   capability and a decision about whether that breaks the "self-contained
   manifest, no external service" rule.

**Do not** add more checks tuned against `tests/sites.txt`. Remaining gains are
in labelled data and manual review, not more code.

---

## Quick commands

```bash
cd d:/Adobe/brand-ai-readiness-audit

python tests/run_tests.py                    # 30 offline fixture tests
python tests/check_consistency.py            # docs vs code vs brief
python tests/generalization_batch.py         # 71 live sites, ~5 min
python tests/generalization_batch.py --segment saas --limit 5   # quick

python skills/audit-orchestrator/scripts/run_audit.py example.com \
    --out report.json --markdown report.md
python skills/audit-orchestrator/scripts/validate_report.py report.json
```

Repack:
```bash
cd d:/Adobe && python -c "
import os, zipfile
root='brand-ai-readiness-audit'; skip={'__pycache__','.git'}
with zipfile.ZipFile('brand-ai-readiness-audit.zip','w',zipfile.ZIP_DEFLATED) as z:
    for dp,dn,fn in os.walk(root):
        dn[:]=[d for d in dn if d not in skip]
        for f in sorted(fn):
            if f.endswith(('.pyc','.zip')): continue
            p=os.path.join(dp,f); z.write(p, os.path.relpath(p,'.'))
    print(len(z.namelist()),'files')"
```
