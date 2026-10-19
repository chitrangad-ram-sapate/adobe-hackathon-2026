# Site profiles: the applicability gate

## Why this exists

Nearly every bad audit in this problem space comes from applying a checklist
written for one kind of site to a different kind: demanding Product/Offer
markup from a charity, a pricing CTA from a documentation site, opening hours
from a SaaS company. The rubric that grades this marketplace penalises false
positives as heavily as misses, so the profile runs **before any check** and
every check consults it.

Where applicability cannot be established, the check is **skipped and recorded
in `audit.checks_skipped` with a reason** - never fired at a guess. A report
that says what it did not test is more useful than one that quietly assumes.

## Site types

| Type | Recognised by | Enables | Suppresses |
| --- | --- | --- | --- |
| `ecommerce` | Product/Offer schema, product and category URL patterns, commerce phrases in body text | Product/Offer markup checks, price extractability, availability | - |
| `saas` | pricing page, SoftwareApplication/Service schema, trial and per-seat language | pricing extractability, comparison-page coverage, Offer markup | local-business checks |
| `local_business` | LocalBusiness-family schema, address and hours patterns, phone plus street address | NAP consistency, opening-hours markup, contact-details-as-text at high severity | comparison-page coverage |
| `media_publisher` | Article-family schema, many article URLs | article dates and authorship | product and pricing checks |
| `documentation` | many docs URL patterns | comparison and how-to coverage | pricing CTA, Product markup |
| `brochure` | 6 or fewer crawlable pages with no commerce or docs signal | core identity and contact checks | site-scale checks, FAQ-absence, query-surface coverage |
| `marketplace` | listing and seller patterns plus commerce signals | Product/Offer, comparison coverage | - |
| `institutional` | registry-restricted government/academic domain (authoritative, see below), or mission, donation, admissions and public-service language | identity, contact-as-text, accessibility, corroboration | pricing extractability, Product/Offer markup, comparison coverage |
| `unknown` | nothing cleared the confidence bar | conservative defaults only | anything type-specific |

Classification is a weighted vote requiring a score of 2.5 to resolve at all.
**`unknown` is a legitimate outcome and is preferred to a wrong guess**, because
a wrong site type turns on the wrong checks - which is worse than running
fewer.

### Authoritative domains override the vote

A **registry-restricted** suffix - `.gov`, `.mil`, `.gov.uk`, `.edu`, `.ac.uk`
and the `ac.<cc>` family - resolves `institutional` at high confidence
regardless of the tally. These suffixes cannot be registered without being the
body they denote, so they are identity evidence, not a hint, and they outrank
content-shape signals: a government or university that also runs a newsroom is
still a government or university, and "publishes articles" must not outvote
"is a government".

This is a precedence rule, not a heavier weight. Raising the weight would only
postpone the problem until the next generic signal, and the observed margin was
narrow enough (4.5 against 4.0) that the same site classified differently
between runs. The override is recorded in `site_type_signals` so the report
shows the vote it displaced.

Open registries are deliberately excluded. `.org`, `.org.uk` and `.ngo` are
available to any registrant, so they only ever contribute a weighted vote
alongside mission and donation language - which is why a charity with a large
newsroom can still be read as a publisher.

## Page types

Assigned from URL shape, falling back to the page title. `other` is returned
rather than guessing, and checks that need a specific page type simply do not
fire on `other` - costing a little recall and buying a lot of precision.

`home`, `section_home`, `product`, `category`, `pricing`, `article`, `docs`,
`about`, `contact`, `faq`, `legal`, `careers`, `case_study`, `document` (PDF),
`other`.

`account` (login, cart, checkout) and `search` pages are excluded from the
crawl sample entirely: they exist for humans mid-transaction, are legitimately
thin, and auditing them produces noise rather than findings.

A root path that is **not** the audited origin is classified `section_home`, not
`home` - a blog or docs subdomain is a section front, and conflating them would
make homepage-only checks fire several times per site.

## Platform fingerprinting

Weighted signature matching over markup, headers and the `generator` meta tag,
restricted to the audited origin's own host. Used only by
`remediation-planner`, and only at high or medium confidence. See that skill's
`references/platform-playbooks.md` for why the confidence gate matters.

Analytics and experience tooling are recorded too - not as a defect either way,
but so the remediation planner knows what the team already owns, and so
`ENG-016` can note the case where a site has no measurement at all.
