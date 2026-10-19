# AI-readiness audit: loom.com

*2026-09-24T19:01:56Z - 30 pages analysed*

**16 findings on loom.com: the most severe is critical and sits at the extract gate - the site's facts are hard for a machine to quote. Start with "Product pages have no Product structured data".**

## Readiness score: 64.7/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 97 | Can a machine reach the content |
| Render | 72 | Can a machine read what visitors see |
| Extract | 21 | Can a machine quote a specific fact |
| Trust | 84 | Will the fact be believed and repeated |
| Engagement | 65 | Do arriving visitors orient and act |

## Findings (16)

critical 1 - high 2 - medium 9 - low 3 - info 1

### F-001 - Product pages have no Product structured data

**CRITICAL** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 7 of 7 sampled product pages carry no Product markup, e.g. https://www.loom.com/products/1080p-screen-recorder.

**Why it matters.** The Product type is how a machine learns what is this product and what does it cost. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (critical priority, medium effort, engineering).** Add Product JSON-LD to the product page template.

- Add a `Product` JSON-LD block to the product template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, offers, image, description, brand.
- Emit it once per page from the template so new pages inherit it automatically.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/products/1080p-screen-recorder
- https://www.loom.com/products/4k-screen-recorder
- https://www.loom.com/products/acer-screen-recorder
- https://www.loom.com/products/advanced-screen-recorder
- https://www.loom.com/products/ai-screen-recorder

### F-002 - Primary content appears to live inside an iframe

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-010`

**Evidence.** 1 sampled pages have under 200 words of their own body text while embedding third-party frames, e.g. https://www.loom.com/code-review (153 words, embeds https://www.loom.com/embed/07e5fa891322484486e1380923f080c5?disable_analytics=true).

**Why it matters.** An iframe's content belongs to the framed document, not to the page that embeds it. Indexing and retrieval attribute that content to the other URL, so the brand's page is treated as an empty container and the substance is credited elsewhere - or, when the frame is blocked from crawling, to nobody.

**Fix (medium priority, high effort, engineering).** Move the primary content into the page itself and keep iframes for supporting media.

- Render the content server-side in the host page instead of embedding it.
- Where the source is a third-party system (booking, listings, documentation), use its API or feed to render the same data as HTML on this domain.
- Keep at minimum a text summary of the framed content in the host page.

**Verify.** Re-run check RND-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/code-review

### F-003 - Pricing pages contain no readable price

**HIGH** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 7 of 8 sampled pricing/product pages contain no numeric price in their text, e.g. https://www.loom.com/products/1080p-screen-recorder.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (high priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/products/1080p-screen-recorder
- https://www.loom.com/products/4k-screen-recorder
- https://www.loom.com/products/acer-screen-recorder
- https://www.loom.com/products/advanced-screen-recorder
- https://www.loom.com/products/ai-screen-recorder

### F-004 - Much of the page text is hidden behind tabs or accordions at load time

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-011`

**Evidence.** 9 sampled pages hide more than 40% of their body text in collapsed regions, e.g. https://www.loom.com/pricing keeps 1540 of 2298 words in {'details': 14}.

**Why it matters.** The text is in the HTML, so this is milder than a render gap - but content hidden at load time is weighted down or dropped by some extractors, and a visitor who does not click never reads it. Specifications, FAQs and shipping terms are the usual casualties, and they are exactly the facts people ask assistants about.

**Fix (high priority, low effort, design).** Show the highest-value content expanded by default and keep collapsing for genuine overflow.

- Expand the first panel of each accordion or tab group by default.
- Move facts people search for - price, dimensions, delivery, compatibility, hours - into always-visible text.
- Where an FAQ is collapsed for layout, add FAQPage structured data so the pairs remain machine-readable.

**Verify.** Re-run check RND-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/pricing
- https://www.loom.com/products/1080p-screen-recorder
- https://www.loom.com/products/4k-screen-recorder
- https://www.loom.com/products/acer-screen-recorder
- https://www.loom.com/products/advanced-screen-recorder

### F-005 - No contact details appear as text

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-007`

**Evidence.** Neither an email address nor a phone number appears in the text of 1 sampled contact/home page(s) (https://www.loom.com/use-case/support).

**Why it matters.** "How do I contact them" is one of the most common questions asked about any organisation. Details that exist only inside a contact form, an image, or a script-rendered widget cannot be extracted, so the answer is either absent or taken from a third-party directory listing that the brand does not control and may not have updated.

**Fix (high priority, low effort, content).** Publish a phone number, an email address and a postal address as selectable text.

- Put the details in HTML text, using `tel:` and `mailto:` links.
- Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).
- Keep a contact form if preferred - but alongside the details, not instead of them.

**Verify.** Re-run check ANS-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/use-case/support

### F-006 - The site publishes nothing in a question-and-answer shape

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-008`

**Evidence.** Across 30 sampled pages there are 2 question-shaped headings, no FAQ page and no FAQPage markup.

**Why it matters.** Retrieval works by matching a user's question against candidate passages. Content already written as a question with a self-contained answer matches directly; the same information written as narrative prose has to be located inside a longer passage first, which is less reliable and often loses to a competitor who wrote it the other way.

**Fix (medium priority, medium effort, content).** Publish the questions customers actually ask, each with a self-contained answer.

- Collect the real questions from sales calls, support tickets and site search logs.
- Write each answer to stand alone - it should make sense quoted without the question or the page around it.
- Use the customer's wording for the question, not internal product vocabulary.
- Mark the block up as FAQPage so the pairing is explicit.

**Verify.** Re-run check ANS-008 and confirm it no longer fires.

### F-007 - The brand describes itself differently in different places on the same page

**MEDIUM** - discoverability / trust gate - confidence high (static) - check `ENT-001`

**Evidence.** 3 pair(s) of self-descriptions on the homepage share little vocabulary; the Organization schema description and the meta description overlap by only 6% ("Loom is the video messaging platform for work. It enables a more effec" vs "Best free online screen recording tool with advanced video editing and").

**Why it matters.** These fields are read by different consumers, and together they form the brand's self-description. When they disagree, a system has no single authoritative account of what the brand is; it either hedges, blends them into something the brand never said, or prefers a third-party description that at least appears consistently.

**Fix (high priority, low effort, marketing).** Write one canonical description of the organisation and use it in every one of these fields.

- Agree a single sentence describing what the organisation is, who it serves and where.
- Use it verbatim in the meta description, og:description, twitter:description and the Organization schema `description`.
- Use the same sentence in off-site profiles - LinkedIn, Crunchbase, directories - so the description the wider web repeats matches the site.

**Verify.** Re-run check ENT-001 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/

### F-008 - The site publishes few verifiable facts about the organisation itself

**MEDIUM** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 6 sampled page(s): no About page was found; no founding date, headquarters or 'based in' statement appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (medium priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-009 - Pages load many render-blocking or third-party scripts

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-005`

**Evidence.** 1 of 30 sampled pages load 16 render-blocking scripts from up to 0 third-party hosts, e.g. https://www.loom.com/desktop.

**Why it matters.** A render-blocking script stops the page being displayed until it has downloaded and executed, and each additional third-party host adds a DNS lookup and TLS handshake before that can even begin. The visitor sees nothing while this happens, and any one of those third parties being slow makes the brand's own site feel slow.

**Fix (medium priority, medium effort, engineering).** Defer non-essential scripts and cut the number of third-party origins.

- Add `defer` or `async` to every script that is not required for first paint.
- Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.
- Load remaining third-party scripts through a single tag manager, after first paint.
- Self-host small critical dependencies to remove a connection setup from the critical path.

**Verify.** Re-run check ENG-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/desktop

### F-010 - Media is set to play automatically

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-009`

**Evidence.** 1 of 30 sampled pages contain a video or audio element with the autoplay attribute, e.g. https://www.loom.com/.

**Why it matters.** Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays the content they came for, and - where sound is involved - is a common reason for closing a tab immediately.

**Fix (high priority, low effort, design).** Require an explicit play action, or at minimum keep autoplay muted and deferred.

- Remove autoplay and show a poster image with a visible play control.
- If a background video is essential to the design, keep it muted, short, and loaded after the primary content.
- Respect prefers-reduced-motion.

**Verify.** Re-run check ENG-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/

### F-011 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 29 of 30 sampled pages, and 3 of those pages carry under 120 words of body text, e.g. https://www.loom.com/community.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.loom.com/community
- https://www.loom.com/cookie-policy
- https://www.loom.com/desktop

### F-012 - Key pages exist but are not linked from the homepage

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-013`

**Evidence.** The site has about page(s) that the homepage does not link to, among 15 homepage links.

**Why it matters.** A page that exists but is not reachable from the front door is effectively hidden from visitors browsing the site, and receives little of the internal linking that signals its importance. The pages this most often affects - contact, pricing - are the ones visitors go looking for first.

**Fix (high priority, low effort, design).** Link the key destinations from the primary navigation or footer.

- Add links to the about page(s) in the header navigation or footer.
- Make sure the navigation is present in the served HTML, not added by script after load.

**Verify.** Re-run check ENG-013 and confirm it no longer fires.

### F-013 - Sitemap entries mostly lack <lastmod> dates

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-014`

**Evidence.** 0 of 371 sitemap URLs carry a <lastmod> value.

**Why it matters.** Crawlers use <lastmod> to decide what to re-fetch. Without it they re-crawl on their own schedule, so updated pages can be represented in answers by a stale copy for far longer than necessary.

**Fix (medium priority, low effort, engineering).** Emit an accurate <lastmod> for every sitemap URL.

- Populate <lastmod> from the content's real last-modified time, not the build time.
- Do not set every URL to the same timestamp on each deploy - crawlers learn to distrust it.

*On Next.js:*
- Add `app/sitemap.ts` (or `next-sitemap`) and ensure it enumerates dynamic routes.

**Verify.** Re-run check ACC-014 and confirm it no longer fires.

### F-014 - Nested pages carry no breadcrumb structured data

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-010`

**Evidence.** 21 of 21 sampled nested pages have no BreadcrumbList markup.

**Why it matters.** Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the kind an assistant links someone straight into - acquires context about what it is part of. They also give the brand a labelled path in results rather than a bare URL.

**Fix (medium priority, low effort, engineering).** Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.

- Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.
- Render a matching visible trail; it serves the same orientation purpose for the reader.
- Keep the markup and the visible trail identical.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-010 and confirm it no longer fires.

### F-015 - No skip-to-content link is provided

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-015`

**Evidence.** None of the 30 sampled pages offers a skip-to-content link.

**Why it matters.** Keyboard and screen-reader users must otherwise traverse the entire navigation on every page before reaching the content. It is a small omission with a disproportionate cost for the visitors it affects.

**Fix (medium priority, low effort, engineering).** Add a skip link as the first focusable element on every page.

- Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in <body>.
- Give the main content container the matching id and make the link visible on focus.

**Verify.** Re-run check ENG-015 and confirm it no longer fires.

### F-016 - AI training crawlers are blocked (recorded, not flagged as a defect)

**INFO** - discoverability / access gate - confidence high (static) - check `ACC-004`

**Evidence.** 1 training-corpus agents are disallowed: gptbot.

**Why it matters.** Training crawlers build the corpus a model learns from. Blocking them reduces the chance the brand is known from model memory, but does not affect live retrieval or citation. This is a policy choice with a known cost, not a misconfiguration.

**Fix (low priority, low effort, marketing).** No action required unless the brand wants to be recalled from model memory as well as cited.

- Keep this block if opting out of training is deliberate.
- If it was not deliberate, allow GPTBot, ClaudeBot, Google-Extended and CCBot to be learned from.

**Verify.** No verification needed; this is an observation.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish honest comparison and 'is this right for me' pages

**MEDIUM priority, high effort.** A large share of the questions put to assistants are comparative or qualifying. If the brand does not answer them, review sites and competitors' comparison pages do - and those are the sources that get cited. Even-handed pages that say where an alternative is the better fit are cited more often than promotional ones, because they read as reliable.

- Write comparisons against the alternatives buyers genuinely evaluate, including the cases where the alternative wins.
- Publish `for <industry>` or `for <role>` pages describing the specific situation each serves.
- Title each page as the question it answers.
- Keep them current - a comparison against an outdated competitor version damages credibility.

### P-002 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

### P-003 - Strengthen the brand's identity graph across authoritative sources

**MEDIUM priority, medium effort.** Entity confusion is one of the main causes of an assistant describing a brand inaccurately. The defence is a consistent, mutually linked set of identity records: the same canonical description, the same legal name, the same location, asserted in several places that reference one another.

- Create or claim a Wikidata item; it is openly editable and widely consumed as an identity reference.
- Align the description on LinkedIn, Crunchbase, GitHub and industry directories with the site's canonical sentence, word for word.
- Declare each of them in the site's Organization `sameAs`, and link back where the platform allows.
- Use the qualified brand name consistently - `<Brand>, the <category> for <audience>` - so the distinguishing phrase is what gets repeated.

### P-004 - Design interior pages for visitors who arrive without context

**MEDIUM priority, low effort.** Assistant referrals land deep in a site rather than on the homepage, and they arrive with no idea whose site they are on. Pages built on the assumption that the visitor came through the front door lose them immediately - so the more successful the discoverability work, the more traffic this wastes.

- Ensure every page states the organisation's name and what it does, in text.
- Add breadcrumbs so a visitor can see where they have landed.
- End each page with a next step chosen for that page's subject.
- Review the pages assistants most often cite and treat each as a potential first impression.

### P-005 - Segment assistant-referred traffic so this work can be evaluated

**LOW priority, low effort.** AI-referred visits behave differently from search visits: they land deeper, arrive with more context, and convert on different pages. Without a separate segment they are averaged into search traffic and the effect of any discoverability work is invisible.

- Create an analytics segment for known assistant referrers and review it separately.
- Report on landing page, onward navigation and conversion for that segment specifically.
- Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.

## What this audit could not determine

- 4 of 5 declared external profile(s) could not be verified because the host blocked the request, disallows it in robots.txt, or the time budget ran out. Those profiles are reported as unverified, never as defects. Run with --no-offsite to skip off-site verification entirely.

## Checks skipped (and why)

- `ANS-002` - homepage H1 is unrecognised vocabulary rather than identifiable marketing abstraction; not flagged to avoid a false positive
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-012` - only 1 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 contact page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 pricing page(s) lacked expected markup - too few to conclude a pattern
