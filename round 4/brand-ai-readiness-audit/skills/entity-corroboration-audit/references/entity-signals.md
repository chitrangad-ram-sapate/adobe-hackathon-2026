# Gate 4 check catalogue: entity, corroboration and freshness

## Scope limit, stated on every run

This skill reads **only the audited site**. It never queries a search engine,
Wikidata, or any external source. Real off-site corroboration cannot be
observed without those, so what is measured instead is whether the site does
the things that *enable* corroboration: publishing identity links, citable
facts, and dates.

That limit is written into the detector's `notes` on every run and surfaces in
the report. Claiming to have checked the wider web when it was never consulted
would be exactly the kind of unearned confidence this marketplace is built to
avoid.

## Identity authorities versus social profiles

`sameAs` links are split, because the two do very different work:

- **Authorities** - Wikipedia, Wikidata, LinkedIn, Crunchbase, GitHub,
  Bloomberg, SEC, Companies House, OpenCorporates, G2, Capterra, Trustpilot.
  These *disambiguate*: they are what a system uses to decide that two mentions
  refer to the same organisation.
- **Social** - X/Twitter, Facebook, Instagram, YouTube, TikTok, Pinterest,
  Threads, Mastodon. These establish presence. They are easy to create and
  rarely used as a reference point, so they contribute little to identity
  resolution.

A site with ten social links and no authority link has a `sameAs` array and
still no identity graph, which is why `ENT-003` exists as its own check.

## The description-consistency measure

Four fields commonly carry a brand's self-description: `meta description`,
`og:description`, `twitter:description`, and Organization schema `description`.
They are compared pairwise by Jaccard similarity over word tokens of 4+
characters. Below 0.35 overlap the pair is reported as divergent.

Only descriptions longer than 30 characters are compared, and fewer than two
present means the check skips rather than concluding anything.

---


## Off-site verification: what the audit does and does not do

Three checks (`ENT-011`, `ENT-012`, `ENT-013`) leave the audited origin. They
are the only part of the marketplace that does.

**Only explicit assertions are followed.** The audit fetches the URLs in the
`sameAs` array and nothing else. `sameAs` means "this profile is the same entity
as this brand", so following it verifies a claim the site actually made.
Ordinary homepage links are deliberately not followed: a site links to plenty of
third-party pages it does not own - an issue tracker, a Wikipedia article about a
technology it happens to use - and treating those as identity claims would fault
a brand for a profile that was never theirs. That also leaves no host-pattern
list to maintain, and nothing to fit to the sites we happened to test.

**The audit never searches for the brand.** No search API, no directory lookup,
no guessing at profile URLs from the brand name. It cannot discover a profile the
site failed to declare - `ENT-002` already covers that absence.

**Blocked is not dead.** Many platforms refuse automated clients. A 404 or 410 is
a confirmed dead link; a 403, 429 or robots-disallowed fetch is an *unverified*
profile, recorded in `audit.limitations` and never charged to the site as a
defect. This distinction is what makes `ENT-011` usable at all, since a dead
link is detectable even on hosts that block us.

**Guardrails.** At most 8 profiles per audit, each host's own `robots.txt`
consulted before its first fetch, read-only GET, no credentials, inside the
crawl's existing time budget. `--no-offsite` disables the step entirely.

**Determinism.** The fetches happen in the crawl phase and their results are
stored in the cache, so re-analysing one crawl stays byte-identical. Two live
crawls can still differ - third-party pages change, and hosts block
intermittently - exactly as they can for the audited site itself.

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `ENT-001` | Two self-descriptions overlap by under 35% | medium | Fewer than two descriptions over 30 characters exist - there is nothing to disagree. |
| `ENT-002` | No `sameAs` links declared anywhere | medium if Organization markup exists, else low | Any `sameAs` is present. Severity is lower without Organization markup because `SDA-003`/`SDA-006` already covers the larger problem. |
| `ENT-003` | `sameAs` exists but contains no identity authority | low | Any authority link is present. |
| `ENT-004` | Profiles linked on the homepage are absent from `sameAs` | low | All linked profiles are declared. |
| `ENT-005` | Homepage title is 4 words or fewer with no category noun, no authority `sameAs`, and the brand token is 12 characters or shorter | medium | Any of those conditions fails. Long distinctive names are unlikely to collide, and the skip records that reasoning explicitly. |
| `ENT-006` | Fewer than 2 of {About page, founding/location statement, citable quantified figure} present | medium if 2+ missing, low if 1 | All three present, or About plus a founding fact. |
| `ENT-007` | 40%+ of pages, and at least 2, show a copyright year 2 or more years old | low | The year is current or last year. A January visit to a site that has not yet rolled its footer is not a defect. |
| `ENT-008` | 50%+ of 3+ sampled articles have no date in markup or opening text | medium | Fewer than 3 articles sampled. |
| `ENT-009` | 60%+ of 3+ sampled articles declare no author | low | Fewer than 3 articles sampled. |
| `ENT-010` | More than one distinct phone number across the site | medium | Site type is not local_business. Multi-number sites are normal for larger organisations; NAP consistency is a local-search concern specifically. |
| `ENT-011` | A declared `sameAs` profile returns 404 or 410 | medium, blast-radius scaled | Any other status. A 403, 429 or robots-disallowed fetch is *unverified*, never dead - the two are never conflated. |
| `ENT-012` | At least two reachable declared profiles, and half or more of them, carry no link to the site and never name its domain | low | Fewer than two profiles could be fetched, fewer than two are one-way, or under half are. One unreciprocated profile out of two is not a pattern - half of them do point back. |
| `ENT-013` | Every fetched profile shares under 6% of its vocabulary with the homepage description | low | Any fetched profile agrees, or no profile carried 30+ words. Requires unanimity precisely because off-site text is noisy. |
