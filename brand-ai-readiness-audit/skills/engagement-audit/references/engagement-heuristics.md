# Engagement check catalogue

## The framing: assistant referrals land deep

A visitor sent by an AI assistant does not arrive on the homepage. They are
deep-linked into whichever page answered their question, they arrive with no
brand context, and part of their answer has already been given to them
elsewhere. Two consequences shape this whole skill:

1. **Interior pages are landing pages.** A page that only makes sense to
   someone who navigated in from the front door will lose them. `ENG-001` is
   the signature check for exactly this, and it is simultaneously an engagement
   defect and the reason discoverability wins get thrown away.
2. **Intent is high and patience is low.** These visitors are mid-journey, not
   at the start. They will not hunt for a next step, and they will not fill in
   nine required fields to ask a question.

## Measurement honesty

No browser was used, so **no paint or layout-shift metric is claimed**. What is
measured is transport-level and markup-level: HTML response size,
render-blocking script count, third-party origin count, and wall-clock response
time from the auditor's own network location. Every such finding carries a
`method_note` in `evidence_detail` saying so, and confidence is `medium`.
Sub-resources are never fetched, so total page weight is explicitly not
reported.

---

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `ENG-001` | 30%+ of interior pages, and at least 2, neither name the organisation nor offer a route onward | high (blast-radius scaled) | Fewer than 3 interior pages sampled. Legal pages and section fronts are excluded, since they legitimately differ. |
| `ENG-002` | 50%+ of conversion-relevant pages, and at least 2, contain no action-describing link or button | high | Fewer than 2 such pages sampled. Only home/product/pricing/about/case-study pages are considered - a docs page needs no CTA. |
| `ENG-003` | A vague label (`Learn more`, `Read more`, `Click here`) repeats 4+ times | low | Labels are descriptive, or repeat fewer than 4 times. |
| `ENG-004` | HTML response over 1.2 MB | medium | Under the threshold. Measured on the document alone, which is stated in the finding. |
| `ENG-005` | 8+ render-blocking scripts, or 12+ distinct third-party script origins | medium | Scripts are `async`, `defer` or `type=module` - those do not block rendering and are not counted. |
| `ENG-006` | 30%+ of pages, and at least 2, took over 2.5s to return | medium | Faster responses. Network-dependent, so confidence is medium and the caveat is in the finding. |
| `ENG-007` | 50%+ of pages, and at least 2, have no viewport meta | high | A viewport tag is present. |
| `ENG-008` | Over 70% of images lack dimensions *and* over 70% lack lazy loading | low | Fewer than 10 images sampled, or either condition alone. Both are required because either alone is a common, defensible choice. |
| `ENG-009` | A `<video>` or `<audio>` element carries `autoplay` | medium | No autoplay attribute. |
| `ENG-010` | Overlay markup on 80%+ of pages **and** pages with under 120 words behind it | medium, `confidence: low` | Only the overlay is present. **A consent banner alone is never flagged** - it is a legal requirement in many jurisdictions. It becomes a finding only when paired with evidence that content is actually being withheld. |
| `ENG-011` | 30%+ of pages, and at least 2, have 2 or fewer onward internal links | medium | Fewer than 4 pages sampled. Legal pages excluded. |
| `ENG-012` | Over 40% of form fields, and at least 3, have no label, `aria-label` or `aria-labelledby` | medium | Search forms and forms with no visible fields are excluded; hidden, submit and button inputs are not counted. |
| `ENG-013` | A contact/about/pricing page exists but the homepage does not link to it | medium | The page does not exist, or is linked. Requires 3+ homepage links to judge at all. |
| `ENG-014` | A form requires 7 or more fields | medium | Fewer required fields. Optional fields are not counted. |
| `ENG-015` | No skip-to-content link on any page | low | Any page has one, or fewer than 4 pages were sampled. |
| `ENG-016` | No recognised analytics or tag manager found | **info** | Any analytics is detected, or fewer than 3 pages sampled. Never a defect - reported because engagement work cannot be evaluated blind. |

## Deliberate omissions

- **No colour-contrast check.** Resolving computed colours needs a style
  engine. Reporting contrast from inline styles alone would miss most of the
  page and produce confident, wrong results.
- **No Core Web Vitals.** They require field data or a real browser. An
  invented LCP figure would be worse than none.
- **No tap-target measurement.** Same reason: it needs layout.
