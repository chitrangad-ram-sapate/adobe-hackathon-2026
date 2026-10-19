# Remediation playbooks

## How a finding becomes a platform-specific instruction

Detectors never know what CMS a site runs, and should not. Each check is mapped
to a remediation **topic**, and each topic has a playbook per platform:

```
finding.check_id  ->  topic  ->  PLAYBOOKS[platform][topic]  ->  suggested_action.platform_specific
```

Topics: `robots`, `sitemap`, `canonical`, `noindex`, `redirects`, `notfound`,
`edge`, `ssr`, `jsonld`, `meta`, `media`, `template`.

A new detector check inherits platform guidance simply by declaring its topic
in `CHECK_TOPIC` - no playbook needs editing. This keeps the matrix small and
means the guidance cannot silently fall out of date as checks are added.

## The confidence gate

Platform-specific steps are emitted **only when the platform was identified
with high or medium confidence**. Below that, a generic fallback is used and
the label reads "this stack" rather than naming a platform.

This matters more than it looks. Telling a team to edit
`snippets/product-schema.liquid` when they do not run Shopify is worse than
saying nothing: it destroys trust in the whole report. The profiler
additionally restricts fingerprinting to the audited origin's own host, because
a blog or docs subdomain very often runs on something entirely different and
would otherwise produce a confident, wrong answer.

## Platforms with playbooks

Adobe Experience Manager, Adobe Edge Delivery Services, Adobe Commerce
(Magento), Shopify, WordPress, Drupal, Next.js, Nuxt, Webflow, Squarespace,
Wix, HubSpot CMS - plus a generic fallback for everything else.

Each entry names the actual file, template or admin screen. A few examples of
the level of specificity intended:

- **AEM / jsonld** - the page component's HTL template
  (`customheaderlibs.html`), populated from page properties or a Content
  Fragment model through a Sling Model, so authors cannot leave it blank.
- **AEM / robots** - the dispatcher, not the repository, and check for a cached
  staging copy.
- **Edge Delivery / meta** - the document's metadata table, since that is where
  authors actually control it.
- **Shopify / robots** - `robots.txt.liquid`; the file cannot be edited directly.
- **WordPress / noindex** - Settings > Reading > "Discourage search engines",
  which is the single most common cause of an accidentally invisible
  WordPress site, before any plugin setting.
- **Next.js / ssr** - server components or `generateStaticParams`, and verify at
  the transport layer with `curl`, because the content appearing in
  `__NEXT_DATA__` is not the same as it being readable.

## Proactive recommendations

Emitted as `proactive_recommendations[]`, kept strictly separate from findings:
a finding has evidence of a problem, a recommendation does not. Each is gated
so the report never asks for the same thing twice.

| ID | Recommendation | Gated on |
| --- | --- | --- |
| llms.txt | Publish an index of the site's most quotable pages | `/llms.txt` did not return 200 |
| Citable facts | A facts-and-figures page other sources can cite | `ENT-006` not already a finding |
| Question content | Answers to real customer questions, in their words | `ANS-008` and `SDA-009` not already findings |
| Query surface | Honest comparison and "is this right for me" pages | commercial site type, `ANS-009` not already a finding |
| Non-text redundancy | Every fact in an image, video or PDF also as text | always - it is a standing editorial rule, not a defect |
| Identity graph | Wikidata, aligned profile descriptions, reciprocal links | `ENT-002` and `ENT-003` not already findings |
| Standalone pages | Design interior pages for context-free arrivals | `ENG-001` not already a finding |
| Referral segmentation | Segment assistant-referred traffic in analytics | `ENG-016` not already a finding |
