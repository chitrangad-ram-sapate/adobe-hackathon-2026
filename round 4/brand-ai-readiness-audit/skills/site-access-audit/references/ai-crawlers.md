# Gate 1 check catalogue: access

Every check below states what it measures, why it matters mechanically, and -
critically - **when it must not fire**. A check without a "do not flag when"
clause is not finished.

---

## The crawler taxonomy this gate depends on

Blocking a crawler is not one decision. It is two, and conflating them is the
single most common cause of accidental invisibility.

| Purpose | What the agent does | Cost of blocking it |
| --- | --- | --- |
| **retrieval** | Fetches a page live while composing an answer, and usually cites it | The brand disappears from answers that would have linked to it. Immediate, direct loss of referral traffic. |
| **training** | Collects a corpus used to train a model | The brand is less likely to be known from model memory. A legitimate policy choice with a slow, diffuse cost. |
| **both** | One token covers both behaviours | Blocking costs both. |

Retrieval agents recognised by this skill: `OAI-SearchBot`, `ChatGPT-User`,
`Claude-Web`, `Claude-User`, `Claude-SearchBot`, `PerplexityBot`,
`Perplexity-User`, `Meta-ExternalFetcher`, `YouBot`.

Training agents: `GPTBot`, `ClaudeBot`, `anthropic-ai`, `Google-Extended`,
`Applebot-Extended`, `CCBot`, `Bytespider`, `meta-externalagent`, `cohere-ai`,
`Diffbot`, `Timpibot`, `omgili`.

Dual-purpose: `GoogleOther`, `Applebot`, `Amazonbot`.

Classic search crawlers are tracked separately (`Googlebot`, `bingbot`,
`DuckDuckBot`, `Slurp`, `YandexBot`, `Baiduspider`) because several assistants
ground their answers on a conventional index rather than crawling directly - so
excluding search crawlers removes a brand from AI answers *indirectly*, through
a path most teams never think to check.

**Path matching** follows de-facto RFC 9309 semantics: longest matching rule
wins, `Allow` wins ties, `*` is a wildcard, `$` anchors the end. The most
specific matching `User-agent` group applies, and the `*` group is used only
when no named group matches - which is why adding an allow rule to the `*`
group does *not* override a named agent's `Disallow: /`.

---

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `ACC-000` | No origin variant returned HTML to either the auditor's user agent or a browser user agent | critical | Any variant returned HTML. When this fires it is the **only** finding in the report, and the report says so: the absence of other findings is not evidence that the rest of the site is sound. Only the access gate is scored, because no later gate could be measured. |
| `ACC-001` | robots.txt returns 5xx, times out, or is otherwise unfetchable | high | It returns 404. An absent robots.txt correctly means "no restrictions" and is not a defect. |
| `ACC-002` | The `User-agent: *` group disallows `/` | critical | A narrower disallow exists (`/admin/`, `/cart`). Only a rule matching `/` itself counts. |
| `ACC-003` | Any *retrieval*-purpose agent is disallowed from `/` | critical | Only training agents are blocked - that is `ACC-004`, reported at info. |
| `ACC-004` | Only training agents are blocked | **info** | Never treated as a defect. Reported so the reader knows the cost of a choice they may have made deliberately. |
| `ACC-005` | A classic search crawler is disallowed | critical (Googlebot) / high | `ACC-002` already fired - the site-wide block covers it, and the composer suppresses the duplicate. |
| `ACC-006` | robots.txt contains directives crawlers silently ignore (rules before any `User-agent` line, missing separators) | medium | The file parses cleanly. Comments and blank lines are not defects. |
| `ACC-008` | Plain-client UA gets 401/403/405/406/429/503 while a browser UA gets 200 | critical | Both agents get the same status. Both blocked equally is a different problem (the site is down, or genuinely private). |
| `ACC-009` | Both return 200, but the plain client receives under 40% of the browser's word count | high | The browser response has under 100 words - too small a sample for the ratio to mean anything. |
| `ACC-010` | The crawled homepage body matches a bot-challenge signature | critical | No challenge markers present. When this fires, every other finding in the report was measured against the challenge page, and the report says so. |
| `ACC-011` | A sitemap declared in robots.txt returns non-200 or parses to zero URLs | high | No sitemap is declared at all - that is `ACC-012`. |
| `ACC-012` | No sitemap found in robots.txt or at the three conventional paths | high, or medium on sites of 8 or fewer crawlable pages | A working sitemap was found anywhere. Small sites are downgraded because link-following genuinely suffices for them. |
| `ACC-013` | A working sitemap exists but robots.txt does not declare it | low | robots.txt has a `Sitemap:` line. |
| `ACC-014` | Under half of sitemap URLs carry `<lastmod>` | low | Most entries have it. |
| `ACC-015` | Every one of 20+ sitemap URLs shares one identical `<lastmod>` | low | Fewer than 20 URLs, or the values vary. A small site legitimately rebuilt at once looks the same as a bad signal. |
| `ACC-016` | `noindex` in meta robots or `X-Robots-Tag` on pages of an important type | critical if the homepage, else high (blast-radius scaled) | The page is a legal, account, search or utility page, or is served from a transactional host (`checkout.`, `secure.`, `account.`, `login.`, `my.`, `billing.`), where noindex is correct behaviour rather than a defect. |
| `ACC-018` | A canonical points at a different registrable domain | critical | The target is the same site (subdomains count as the same site). |
| `ACC-019` | 25%+ of sampled pages, and at least 2, canonicalise to the homepage | high | Only the homepage does (which is correct), or the sample is under 3 comparable pages. |
| `ACC-020` | 60%+ of sampled pages, and at least 3, have no canonical at all | low | `ACC-018` fired - a wrong canonical is the bigger problem, and reporting both muddies the fix. |
| `ACC-021` | Two https origins both return 200 and resolve to different final URLs | medium | They converge on one final URL - a redirect is working correctly. |
| `ACC-022` | An `http://` origin returns 200 and stays on http | medium | It redirects to https. |
| `ACC-023` | TLS validation fails on any probed origin | critical | Validation succeeds. Note the fetcher retries once without verification so the content can still be audited; the failure is still reported. |
| `ACC-024` | Crawled URLs discovered from links or the sitemap return 4xx/5xx | medium (blast-radius scaled) | The failing URLs were probe URLs rather than real links. |
| `ACC-025` | A URL needs 3 or more redirect hops | low | One or two hops - normal and harmless. |
| `ACC-026` | A URL that cannot exist returns 200 with 30+ words | medium | It returns 404, 410, or a near-empty 200. |

---

## Two failure modes this gate treats specially

**The site blocks the auditor itself.** If no origin answers this auditor's user
agent but one answers a browser user agent, the crawl continues with a browser
user agent so the rest of the audit can run at all - and the substitution is
disclosed three times over: in `ACC-008`, in `audit.limitations`, and in the
crawl metadata. Returning nothing would hide the single most valuable thing this
audit can tell that owner. Pass `--no-ua-fallback` to disable the substitution
and have the run report the site as unreachable instead.

**Nothing answers at all.** The crawler still writes a cache, the pipeline still
runs, and the report still validates - carrying `ACC-000` and nothing else. An
empty result would leave the reader unable to tell whether the tool or the site
was at fault.

## Notes on deliberate omissions

- **`llms.txt` absence is not a finding.** It is an emerging convention, not a
  standard, and no site is defective for lacking one. It is emitted as a
  proactive recommendation by `remediation-planner` instead.
- **`Crawl-delay` is honoured, not flagged.** A slow crawl directive is the
  site's right. The crawler obeys it, caps its own page budget to stay within
  the time budget, and records the reduction as a limitation.
- **Rate limits are not probed.** Deliberately triggering a 429 to see whether
  a site rate-limits would be an abusive test. The check reports a 429 only if
  one is encountered incidentally.
