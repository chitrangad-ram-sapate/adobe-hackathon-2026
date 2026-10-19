# AI-readiness audit: grammarly.com

*2026-09-24T19:02:40Z - 30 pages analysed*

**17 findings on grammarly.com: the most severe is critical and sits at the access gate - machines may not reach or discover all of the site. Start with "Canonical tags point to a different domain".**

## Readiness score: 61.9/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 60 | Can a machine reach the content |
| Render | 64 | Can a machine read what visitors see |
| Extract | 25 | Can a machine quote a specific fact |
| Trust | 91 | Will the fact be believed and repeated |
| Engagement | 86 | Do arriving visitors orient and act |

## Findings (17)

critical 1 - high 3 - medium 7 - low 6 - info 0

### F-001 - Canonical tags point to a different domain

**CRITICAL** - discoverability / access gate - confidence high (static) - check `ACC-018`

**Evidence.** 4 of 30 sampled pages declare a canonical URL on another host, e.g. https://www.grammarly.com/careers -> https://superhuman.com/company/careers.

**Why it matters.** A cross-domain canonical instructs indexing systems to attribute the content to the other domain entirely. The brand's own pages are then treated as duplicates, and any citation goes to the other site.

**Fix (critical priority, low effort, engineering).** Point canonical tags at the page's own URL on this domain.

- Set a self-referencing canonical on every indexable page.
- If the content is genuinely syndicated from elsewhere, keep the cross-domain canonical only on the syndicated copies, never on original pages.

*On Next.js:*
- Set `alternates.canonical` in each route's metadata to the page's own absolute URL.

**Verify.** Re-run check ACC-018 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/careers
- https://www.grammarly.com/jobs
- https://www.grammarly.com/careers/culture
- https://www.grammarly.com/careers/inclusion

### F-002 - Facts appear to be locked inside images with no text equivalent

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 114 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. https://static-web.grammarly.com/1e6ajr2k4140/1hJYwlj3UP0e0LXF6zKQiU/cef26ad93e9017fd1c1dea494a2eea70/logo.svg on https://www.grammarly.com/.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (high priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://www.grammarly.com/
- https://www.grammarly.com/2024-state-of-business-communication-germany-report
- https://www.grammarly.com/2025-the-productivity-shift-multilingual
- https://www.grammarly.com/blog/
- https://www.grammarly.com/blog/company/introducing-new-superhuman/

### F-003 - Structured data blocks contain invalid JSON and are discarded

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-001`

**Evidence.** 3 JSON-LD blocks failed to parse, e.g. on https://www.grammarly.com/docs: empty script block.

**Why it matters.** A JSON-LD block that does not parse is dropped in full, silently. The team believes the page publishes structured data, consumers see none, and the failure is invisible without deliberately validating the output.

**Fix (high priority, low effort, engineering).** Fix the JSON syntax so the blocks parse, and validate structured data in the build.

- Correct the reported syntax errors - trailing commas, unescaped quotes inside string values and unquoted keys account for most of them.
- Serialise JSON-LD with a real JSON serialiser rather than string templating in the view layer.
- Add a build-time or CI validation step so a malformed block fails the build instead of shipping.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-001; every ld+json block should parse without modification.

**Affected URLs (sample).**
- https://www.grammarly.com/docs
- https://www.grammarly.com/case-study-generator
- https://www.grammarly.com/privacy

### F-004 - Home pages have no Organization/WebSite structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://www.grammarly.com/.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (high priority, medium effort, engineering).** Add Organization JSON-LD to the home page template.

- Add a `Organization` JSON-LD block to the home template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/

### F-005 - Most images have no alt text

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-007`

**Evidence.** 152 of 419 images across 30 sampled pages (36%) have a missing or empty alt attribute.

**Why it matters.** Alt text is the only description of an image available to a text reader, and it is one of the few places where an image's meaning enters the page's extractable content. Its absence also makes the page unusable with a screen reader, which is an engagement failure as much as a discoverability one.

**Fix (medium priority, medium effort, content).** Add descriptive alt text to meaningful images and empty alt to decorative ones.

- Describe what the image conveys in context, in a sentence fragment.
- Use alt="" for decoration so readers skip it rather than announcing a filename.
- Add an alt field to the CMS image component so authors cannot omit it silently.

**Verify.** Re-run check RND-007 and confirm it no longer fires.

### F-006 - Much of the page text is hidden behind tabs or accordions at load time

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-011`

**Evidence.** 3 sampled pages hide more than 40% of their body text in collapsed regions, e.g. https://www.grammarly.com/docs keeps 524 of 1186 words in {'details': 16}.

**Why it matters.** The text is in the HTML, so this is milder than a render gap - but content hidden at load time is weighted down or dropped by some extractors, and a visitor who does not click never reads it. Specifications, FAQs and shipping terms are the usual casualties, and they are exactly the facts people ask assistants about.

**Fix (high priority, low effort, design).** Show the highest-value content expanded by default and keep collapsing for genuine overflow.

- Expand the first panel of each accordion or tab group by default.
- Move facts people search for - price, dimensions, delivery, compatibility, hours - into always-visible text.
- Where an FAQ is collapsed for layout, add FAQPage structured data so the pairs remain machine-readable.

**Verify.** Re-run check RND-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/docs
- https://www.grammarly.com/case-study-generator
- https://www.grammarly.com/privacy

### F-007 - Different pages share the same title

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 9 of 30 sampled pages share 3 repeated title(s), e.g. "Grammarly Prices and Plans | Grammarly".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (high priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On Next.js:*
- Export `metadata` or `generateMetadata` per route so each page has its own title and description.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/plans
- https://www.grammarly.com/business/pricing
- https://go.grammarly.com/contact/sales
- https://www.grammarly.com/contact/claim-your-discount
- https://www.grammarly.com/c/contact/sales

### F-008 - No contact details appear as text

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-007`

**Evidence.** Neither an email address nor a phone number appears in the text of 4 sampled contact/home page(s) (https://www.grammarly.com/contact).

**Why it matters.** "How do I contact them" is one of the most common questions asked about any organisation. Details that exist only inside a contact form, an image, or a script-rendered widget cannot be extracted, so the answer is either absent or taken from a third-party directory listing that the brand does not control and may not have updated.

**Fix (high priority, low effort, content).** Publish a phone number, an email address and a postal address as selectable text.

- Put the details in HTML text, using `tel:` and `mailto:` links.
- Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).
- Keep a contact form if preferred - but alongside the details, not instead of them.

**Verify.** Re-run check ANS-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/contact
- https://go.grammarly.com/contact/sales
- https://www.grammarly.com/contact/claim-your-discount
- https://www.grammarly.com/contact/early-access

### F-009 - Careers pages have no JobPosting structured data

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 4 of 4 sampled careers pages carry no JobPosting markup, e.g. https://www.grammarly.com/careers.

**Why it matters.** The JobPosting type is how a machine learns what is the role, where, and for how much. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (medium priority, medium effort, engineering).** Add JobPosting JSON-LD to the careers page template.

- Add a `JobPosting` JSON-LD block to the careers template, populated from the same data the page already renders.
- Include the fields that make it answerable: title, datePosted, hiringOrganization, jobLocation, baseSalary, employmentType.
- Emit it once per page from the template so new pages inherit it automatically.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/careers
- https://www.grammarly.com/jobs
- https://www.grammarly.com/careers/culture
- https://www.grammarly.com/careers/inclusion

### F-010 - Question-and-answer content is not marked up as an FAQ

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-009`

**Evidence.** 3 pages contain 16+ question-shaped headings with no FAQPage markup, e.g. https://www.grammarly.com/docs asks "How is docs different from other document editors like Google Docs or ".

**Why it matters.** Question-and-answer pairs are the most directly quotable content a site can publish, because the question already matches the shape of what users ask. Marking them up hands a retrieval system a pre-matched pair instead of asking it to locate the answer inside a page of prose.

**Fix (high priority, low effort, content).** Add FAQPage structured data wrapping the existing questions and answers.

- Emit `FAQPage` with a `mainEntity` array of `Question`/`acceptedAnswer` pairs built from the headings and body already on the page.
- Keep the answers self-contained: each should make sense quoted on its own, without the question above it or the paragraph before it.
- Only mark up genuine questions the page answers - inventing pairs for markup's sake is treated as spam by consumers.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/docs
- https://www.grammarly.com/case-study-generator
- https://www.grammarly.com/privacy

### F-011 - Media is set to play automatically

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-009`

**Evidence.** 3 of 30 sampled pages contain a video or audio element with the autoplay attribute, e.g. https://www.grammarly.com/.

**Why it matters.** Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays the content they came for, and - where sound is involved - is a common reason for closing a tab immediately.

**Fix (high priority, low effort, design).** Require an explicit play action, or at minimum keep autoplay muted and deferred.

- Remove autoplay and show a poster image with a visible play control.
- If a background video is essential to the design, keep it muted, short, and loaded after the primary content.
- Respect prefers-reduced-motion.

**Verify.** Re-run check ENG-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/
- https://www.grammarly.com/blog/company/introducing-new-superhuman/
- https://www.grammarly.com/docs

### F-012 - Nested pages carry no breadcrumb structured data

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-010`

**Evidence.** 15 of 15 sampled nested pages have no BreadcrumbList markup.

**Why it matters.** Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the kind an assistant links someone straight into - acquires context about what it is part of. They also give the brand a labelled path in results rather than a bare URL.

**Fix (medium priority, low effort, engineering).** Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.

- Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.
- Render a matching visible trail; it serves the same orientation purpose for the reader.
- Keep the markup and the visible trail identical.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-010 and confirm it no longer fires.

### F-013 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, although 4 external profile link(s) appear on the page (https://www.facebook.com/grammarly, https://www.instagram.com/grammarly/, https://www.linkedin.com/company/grammarly).

**Why it matters.** sameAs is the machine-readable claim that this site, this company registry entry, this LinkedIn page and this Wikipedia article are one entity. Without it, corroborating facts scattered across those sources are not recognised as being about the same organisation, so each one stands alone and is weaker - and a similarly named organisation can be confused with this one.

**Fix (medium priority, low effort, marketing).** Declare sameAs links from Organization schema to every profile the brand controls.

- Add a `sameAs` array to the Organization block listing the brand's authoritative profiles.
- Prioritise identity authorities over social reach: Wikidata, Wikipedia, LinkedIn, Crunchbase, a company register entry, GitHub - these disambiguate; a follower count does not.
- Make the links reciprocal where possible: the profile should link back to the site.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check ENT-002 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/

### F-014 - The site publishes few verifiable facts about the organisation itself

**LOW** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 1 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (low priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-015 - Articles have no named author in structured data

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-009`

**Evidence.** 3 of 4 sampled articles declare no author.

**Why it matters.** Attribution is part of how a claim's weight is assessed. Named, described authors connect content to a person whose expertise can be established elsewhere; anonymous content has only the domain behind it.

**Fix (low priority, medium effort, content).** Attribute articles to named authors with linked profiles.

- Add `author` as a Person object with `name`, `url` and `sameAs` to the article's structured data.
- Publish author profile pages describing relevant expertise.
- Show the byline visibly as well as in markup.

**Verify.** Re-run check ENT-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.grammarly.com/blog/
- https://www.grammarly.com/blog/engineering/
- https://www.grammarly.com/blog/institutions/

### F-016 - Navigation relies on repeated, undescriptive link text

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-003`

**Evidence.** The link text "learn more" appears 7 times across the sampled pages, alongside 1 such repeated labels in total.

**Why it matters.** Identical undescriptive labels force the visitor to work out where each one goes from its surroundings, which is slow on a screen and impossible for anyone navigating by links alone with a screen reader. The same text also gives search and retrieval systems no signal about what the linked page contains.

**Fix (medium priority, low effort, content).** Replace repeated generic labels with text naming the destination.

- Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.
- Where the visual design requires a short label, add an aria-label carrying the full description.

**Verify.** Re-run check ENG-003 and confirm it no longer fires.

### F-017 - No skip-to-content link is provided

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-015`

**Evidence.** None of the 30 sampled pages offers a skip-to-content link.

**Why it matters.** Keyboard and screen-reader users must otherwise traverse the entire navigation on every page before reaching the content. It is a small omission with a disproportionate cost for the visitors it affects.

**Fix (medium priority, low effort, engineering).** Add a skip link as the first focusable element on every page.

- Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in <body>.
- Give the main content container the matching id and make the link visible on focus.

**Verify.** Re-run check ENG-015 and confirm it no longer fires.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish an /llms.txt index of the site's most quotable pages

**MEDIUM priority, low effort.** Assistants that fetch pages live have to guess which URLs carry the facts they need. An llms.txt file is an emerging convention for stating that explicitly - a short, plain-text map of the pages a machine should read first. It costs almost nothing, and where it is honoured it puts the brand in control of which pages represent it.

- Create `/llms.txt`: an H1 with the organisation's name, a blockquote with the one-line description, then linked sections for the pages that answer real questions - what the company does, products, pricing, contact, documentation.
- Keep it to the pages a machine should read first, not a mirror of the sitemap.
- Optionally publish clean Markdown mirrors of those pages and link them from it.
- Keep it current: a stale index is worse than none, because it directs readers to the wrong pages.

### P-002 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

### P-003 - Design interior pages for visitors who arrive without context

**MEDIUM priority, low effort.** Assistant referrals land deep in a site rather than on the homepage, and they arrive with no idea whose site they are on. Pages built on the assumption that the visitor came through the front door lose them immediately - so the more successful the discoverability work, the more traffic this wastes.

- Ensure every page states the organisation's name and what it does, in text.
- Add breadcrumbs so a visitor can see where they have landed.
- End each page with a next step chosen for that page's subject.
- Review the pages assistants most often cite and treat each as a potential first impression.

### P-004 - Segment assistant-referred traffic so this work can be evaluated

**LOW priority, low effort.** AI-referred visits behave differently from search visits: they land deeper, arrive with more context, and convert on different pages. Without a separate segment they are averaged into search traffic and the effect of any discoverability work is invisible.

- Create an analytics segment for known assistant referrers and review it separately.
- Report on landing page, onward navigation and conversion for that segment specifically.
- Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.

## Checks skipped (and why)

- `ANS-002` - homepage H1 is unrecognised vocabulary rather than identifiable marketing abstraction; not flagged to avoid a false positive
- `ANS-006` - site type is media_publisher; a published price is not expected
- `ANS-009` - site type is media_publisher; comparison and use-case pages are not expected
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-011` - the site declares no external profiles to verify
- `ENT-012` - only 0 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 about page(s) lacked expected markup - too few to conclude a pattern
- `SDA-008` - site type is media_publisher; offer markup is not expected
