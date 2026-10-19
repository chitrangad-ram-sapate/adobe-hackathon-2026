# Gate 3b check catalogue: answer readiness

## Why this gate exists separately from structured data

Structured data makes facts *typed*. This gate asks whether the page contains a
**quotable sentence**. Retrieval systems assemble answers from passages, and a
site can be crawlable, rendered and thoroughly marked up while still giving an
extractor nothing to lift - because the prose was written for a reader who
already knows what the company is.

## The identity-statement pattern

The shape an extractor can use to answer "what is X":

> **`<Brand>` is a `<category noun>` that `<does what>` for `<audience>`, based in `<place>`.**

Three components are detected:

- **Brand token** - from Organization/WebSite schema `name`, falling back to the
  registrable domain.
- **Descriptive verb** - `is`, `provides`, `builds`, `makes`, `sells`, `helps`,
  `enables`, `operates`, `serves` and similar.
- **Category noun** - `platform`, `agency`, `manufacturer`, `clinic`,
  `retailer`, `charity`, `robots`, `equipment` and similar.

The check searches the homepage's opening sentences, the meta description, and
the Organization schema `description`. **The fact only has to be extractable
somewhere prominent, not in one specific place** - a site that states it clearly
in its meta description passes.

This is linguistic, so it is emitted at `method: heuristic`,
`confidence: medium`. It is a signal for a human to confirm, never a
measurement.

---

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `ANS-001` | No identity sentence in the homepage opening, the meta description, or the Organization description | high | Any one of the three carries it. |
| `ANS-002` | Homepage H1 contains no category noun, and either uses aspirational marketing vocabulary or is 3 words or fewer | medium | The H1 is longer than 3 words and uses vocabulary the check does not recognise. Unrecognised is not the same as abstract, and the skip is recorded with that reason - this is the check most at risk of false positives, so it declines to guess. |
| `ANS-003` | Pages share identical titles, with 4+ titled pages sampled | medium (blast-radius scaled) | `ANS-004` fired - placeholder titles explain the duplication, and the composer keeps only the more specific finding. |
| `ANS-004` | 25%+ of pages, and at least 2, have a missing or generic title (`Home`, `Welcome`, `Untitled`, under 12 characters) | medium | Titles are descriptive, even if imperfect. |
| `ANS-005` | 50%+ of pages, and at least 3, have no meta description | low | Most pages have one. |
| `ANS-006` | 60%+ of pricing/product pages contain no numeric price in text | high, or medium if all of them use explicit quote-request language | Site type is not saas/ecommerce/marketplace, or no pricing pages were sampled. Quote-based pricing is downgraded, not dismissed: an indicative range is still extractable where silence is not. |
| `ANS-007` | Neither an email nor a phone number appears as text on the contact or home page | high for a local business, else medium | Either is present. A form-only contact route is a legitimate choice for many businesses, which is why this is not high by default. |
| `ANS-008` | No question-shaped headings, no FAQ page, no FAQPage markup | medium | Fewer than 8 pages sampled. A small brochure site with no FAQ is small, not defective. |
| `ANS-009` | 3 or more of {comparison, use-case, how-to, faq} URL patterns absent | low | Site type is not saas/ecommerce/marketplace/documentation, or fewer than 10 URLs are known. |

## Deliberate omissions

- **No readability scoring.** Reading-level formulas are unreliable across
  domains and languages, and a technical page legitimately reads as technical.
- **No keyword density or term-frequency checks.** They model an era of search
  that no longer determines citation, and would generate advice that is
  actively wrong.
- **No word-count minimum for its own sake.** Length is not the goal;
  extractability is. A concise page that states its facts plainly is a good
  page, and `RND-005`'s floors exist to catch pages with nothing to quote, not
  pages that could be longer.
