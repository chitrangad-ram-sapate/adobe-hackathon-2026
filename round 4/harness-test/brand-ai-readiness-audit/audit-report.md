# AI-readiness audit: airtable.com

*2026-09-26T09:33:36Z - 29 pages analysed*

**18 findings on airtable.com: the most severe is high and sits at the render gate - machines cannot read what visitors can see. Start with "Facts appear to be locked inside images with no text equivalent".**

## Readiness score: 65.2/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 97 | Can a machine reach the content |
| Render | 36 | Can a machine read what visitors see |
| Extract | 46 | Can a machine quote a specific fact |
| Trust | 94 | Will the fact be believed and repeated |
| Engagement | 65 | Do arriving visitors orient and act |

## Findings (18)

critical 0 - high 4 - medium 8 - low 6 - info 0

### F-001 - Facts appear to be locked inside images with no text equivalent

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 232 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. https://static.airtable.com/images/marketing-nav-platform-graphic.webp on https://www.airtable.com/.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (high priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://airtable.com/developers
- https://airtable.com/developers/agents
- https://airtable.com/pricing
- https://airtable.com/templates
- https://community.airtable.com/

### F-002 - Primary content appears to live inside an iframe

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-010`

**Evidence.** 5 sampled pages have under 200 words of their own body text while embedding third-party frames, e.g. https://airtable.com/marketplace/category/all-apps (22 words, embeds https://static.airtable.com/html/marketo_widget.html).

**Why it matters.** An iframe's content belongs to the framed document, not to the page that embeds it. Indexing and retrieval attribute that content to the other URL, so the brand's page is treated as an empty container and the substance is credited elsewhere - or, when the frame is blocked from crawling, to nobody.

**Fix (medium priority, high effort, engineering).** Move the primary content into the page itself and keep iframes for supporting media.

- Render the content server-side in the host page instead of embedding it.
- Where the source is a third-party system (booking, listings, documentation), use its API or feed to render the same data as HTML on this domain.
- Keep at minimum a text summary of the framed content in the host page.

**Verify.** Re-run check RND-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://airtable.com/marketplace/category/all-apps
- https://airtable.com/marketplace/category/by-airtable
- https://airtable.com/careers
- https://www.airtable.com/universe/expVVRw3oKWYCJs2t/jobs
- https://airtable.com/marketplace

### F-003 - Pricing pages contain no readable price

**HIGH** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 3 of 5 sampled pricing/product pages contain no numeric price in their text, e.g. https://www.airtable.com/articles/product.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (high priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/articles/product
- https://www.airtable.com/solutions/product
- https://www.airtable.com/lp/product/feature-prioritization

### F-004 - Home pages have no Organization/WebSite structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://www.airtable.com/.

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
- https://www.airtable.com/

### F-005 - Page content is assembled by JavaScript and is missing from the server response

**MEDIUM** - discoverability / render gate - confidence high (rendered) - check `RND-001`

**Evidence.** On 1 of 3 rendered pages the raw HTML contains less text than the browser DOM; worst case https://www.airtable.com/ ships 726 words against 1134 after JavaScript (64% coverage).

**Why it matters.** Most AI retrieval fetchers and many crawlers read the HTTP response without running JavaScript. Whatever the client assembles afterwards does not exist for them, so the page is fetched successfully and found to contain almost nothing worth quoting - the site is reachable and still uncitable.

**Fix (medium priority, high effort, engineering).** Server-render or pre-render the content that currently only appears after JavaScript runs.

- Move the primary content - headings, body copy, prices, specifications, contact details - into the server-rendered HTML so it is present in the first response.
- Use the framework's server-side rendering or static generation mode for these routes rather than client-only rendering.
- Where full SSR is impractical, pre-render the top templates to static HTML and hydrate afterwards.
- Verify with `curl -s <url> | wc -w`: the raw response should contain the page's real text.

*On Next.js:*
- Move the affected routes off client-only rendering: use server components, `generateStaticParams` for static routes, or `getServerSideProps` in the pages router.
- Confirm the fix at the transport layer - `curl -s <url>` must contain the page's text, not just the hydration payload in `__NEXT_DATA__` or the flight stream.

**Verify.** Re-run check RND-001; raw-to-rendered word coverage should exceed 0.75 on every content page.

**Affected URLs (sample).**
- https://www.airtable.com/

### F-006 - Most images have no alt text

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-007`

**Evidence.** 346 of 568 images across 29 sampled pages (61%) have a missing or empty alt attribute.

**Why it matters.** Alt text is the only description of an image available to a text reader, and it is one of the few places where an image's meaning enters the page's extractable content. Its absence also makes the page unusable with a screen reader, which is an engagement failure as much as a discoverability one.

**Fix (medium priority, medium effort, content).** Add descriptive alt text to meaningful images and empty alt to decorative ones.

- Describe what the image conveys in context, in a sentence fragment.
- Use alt="" for decoration so readers skip it rather than announcing a filename.
- Add an alt field to the CMS image component so authors cannot omit it silently.

**Verify.** Re-run check RND-007 and confirm it no longer fires.

### F-007 - Much of the page text is hidden behind tabs or accordions at load time

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-011`

**Evidence.** 2 sampled pages hide more than 40% of their body text in collapsed regions, e.g. https://www.airtable.com/ keeps 471 of 726 words in {'tabpanel': 8}.

**Why it matters.** The text is in the HTML, so this is milder than a render gap - but content hidden at load time is weighted down or dropped by some extractors, and a visitor who does not click never reads it. Specifications, FAQs and shipping terms are the usual casualties, and they are exactly the facts people ask assistants about.

**Fix (high priority, low effort, design).** Show the highest-value content expanded by default and keep collapsing for genuine overflow.

- Expand the first panel of each accordion or tab group by default.
- Move facts people search for - price, dimensions, delivery, compatibility, hours - into always-visible text.
- Where an FAQ is collapsed for layout, add FAQPage structured data so the pairs remain machine-readable.

**Verify.** Re-run check RND-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/
- https://status.airtable.com/

### F-008 - About pages have no Organization structured data

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 3 of 3 sampled about pages carry no Organization markup, e.g. https://www.airtable.com/about.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (medium priority, medium effort, engineering).** Add Organization JSON-LD to the about page template.

- Add a `Organization` JSON-LD block to the about template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/about
- https://www.airtable.com/company/IBM-watsonx-terms
- https://www.airtable.com/company/accessibility

### F-009 - Some pages ship a very large HTML document

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-004`

**Evidence.** 1 of 29 sampled pages return more than 1.2 MB of HTML alone, e.g. https://airtable.com/templates at 1331 KB (before images, scripts and stylesheets).

**Why it matters.** The HTML document blocks everything else: nothing renders until it has arrived and been parsed. On a mobile connection a document this size costs seconds before the first pixel, and abandonment climbs steeply with every second of delay.

**Fix (medium priority, medium effort, engineering).** Reduce document size by paginating, deferring and trimming inlined data.

- Move large inlined JSON, base64 images and repeated markup out of the document.
- Paginate or lazy-load long lists rather than emitting every item.
- Serve compressed responses (gzip or brotli) and confirm the header is present.

**Verify.** Re-run check ENG-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://airtable.com/templates

### F-010 - Pages load many render-blocking or third-party scripts

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-005`

**Evidence.** 2 of 29 sampled pages load 10 render-blocking scripts from up to 4 third-party hosts, e.g. https://community.airtable.com/.

**Why it matters.** A render-blocking script stops the page being displayed until it has downloaded and executed, and each additional third-party host adds a DNS lookup and TLS handshake before that can even begin. The visitor sees nothing while this happens, and any one of those third parties being slow makes the brand's own site feel slow.

**Fix (medium priority, medium effort, engineering).** Defer non-essential scripts and cut the number of third-party origins.

- Add `defer` or `async` to every script that is not required for first paint.
- Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.
- Load remaining third-party scripts through a single tag manager, after first paint.
- Self-host small critical dependencies to remove a connection setup from the critical path.

**Verify.** Re-run check ENG-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://community.airtable.com/
- https://status.airtable.com/

### F-011 - Media is set to play automatically

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-009`

**Evidence.** 3 of 29 sampled pages contain a video or audio element with the autoplay attribute, e.g. https://www.airtable.com/.

**Why it matters.** Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays the content they came for, and - where sound is involved - is a common reason for closing a tab immediately.

**Fix (high priority, low effort, design).** Require an explicit play action, or at minimum keep autoplay muted and deferred.

- Remove autoplay and show a poster image with a visible play control.
- If a background video is essential to the design, keep it muted, short, and loaded after the primary content.
- Respect prefers-reduced-motion.

**Verify.** Re-run check ENG-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/
- https://www.airtable.com/solutions/product
- https://www.airtable.com/ai

### F-012 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 28 of 29 sampled pages, and 10 of those pages carry under 120 words of body text, e.g. https://community.airtable.com/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://community.airtable.com/
- https://support.airtable.com/
- https://www.airtable.com/company/accessibility
- https://www.airtable.com/lp/product/feature-prioritization
- https://www.airtable.com/videos/categories

### F-013 - Internal links and sitemap entries point at pages that fail to load

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-024`

**Evidence.** 1 of 30 crawled URLs returned an error, e.g. https://academy.airtable.com/ (403).

**Why it matters.** Every dead link is a discovery path that terminates, and a visitor who reaches one usually leaves rather than navigating back. Dead entries in a sitemap additionally teach crawlers to trust the sitemap less.

**Fix (low priority, medium effort, engineering).** Fix or remove the broken URLs from links and from the sitemap.

- Repair the links, or redirect the old URLs to their current equivalents with a 301.
- Remove URLs that no longer exist from the sitemap.
- Add a build-time link check so this does not regress.

**Verify.** Re-run check ACC-024 and confirm it no longer fires.

**Affected URLs (sample).**
- https://academy.airtable.com/

### F-014 - Different pages share the same title

**LOW** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 4 of 29 sampled pages share 2 repeated title(s), e.g. "Airtable Pricing | Compare Plans, Features & Costs".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (medium priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On Next.js:*
- Export `metadata` or `generateMetadata` per route so each page has its own title and description.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://airtable.com/pricing
- https://www.airtable.com/pricing
- https://airtable.com/developers
- https://airtable.com/developers/agents

### F-015 - Article structured data is missing required fields

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-007`

**Evidence.** 1 Article nodes omit datePublished (1x), e.g. on https://www.airtable.com/universe/expVVRw3oKWYCJs2t/jobs.

**Why it matters.** The block is present and parses, so it appears to be working - but without datePublished it cannot answer what does this say, when was it said, and who said it. Consumers that require these fields discard the node entirely, leaving the page in the same position as one with no markup at all.

**Fix (medium priority, low effort, engineering).** Populate the required Article fields: datePublished.

- Add datePublished to the Article block, sourced from the same data the page renders.
- Leave a field out entirely rather than emitting an empty string or a placeholder - an empty value is treated as an assertion that the value is empty.
- Validate the output against the type's requirements as part of the build.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/universe/expVVRw3oKWYCJs2t/jobs

### F-016 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, although 5 external profile link(s) appear on the page (https://facebook.com/airtableapp, https://instagram.com/airtable, https://linkedin.com/company/airtable).

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
- https://www.airtable.com/

### F-017 - Articles have no named author in structured data

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-009`

**Evidence.** 3 of 3 sampled articles declare no author.

**Why it matters.** Attribution is part of how a claim's weight is assessed. Named, described authors connect content to a person whose expertise can be established elsewhere; anonymous content has only the domain behind it.

**Fix (low priority, medium effort, content).** Attribute articles to named authors with linked profiles.

- Add `author` as a Person object with `name`, `url` and `sameAs` to the article's structured data.
- Publish author profile pages describing relevant expertise.
- Show the byline visibly as well as in markup.

**Verify.** Re-run check ENT-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.airtable.com/articles
- https://www.airtable.com/articles/agency-project-management
- https://www.airtable.com/articles/agent-audit-log

### F-018 - Navigation relies on repeated, undescriptive link text

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-003`

**Evidence.** The link text "learn more" appears 12 times across the sampled pages, alongside 1 such repeated labels in total.

**Why it matters.** Identical undescriptive labels force the visitor to work out where each one goes from its surroundings, which is slow on a screen and impossible for anyone navigating by links alone with a screen reader. The same text also gives search and retrieval systems no signal about what the linked page contains.

**Fix (medium priority, low effort, content).** Replace repeated generic labels with text naming the destination.

- Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.
- Where the visual design requires a short label, add an aria-label carrying the full description.

**Verify.** Re-run check ENG-003 and confirm it no longer fires.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish an /llms.txt index of the site's most quotable pages

**MEDIUM priority, low effort.** Assistants that fetch pages live have to guess which URLs carry the facts they need. An llms.txt file is an emerging convention for stating that explicitly - a short, plain-text map of the pages a machine should read first. It costs almost nothing, and where it is honoured it puts the brand in control of which pages represent it.

- Create `/llms.txt`: an H1 with the organisation's name, a blockquote with the one-line description, then linked sections for the pages that answer real questions - what the company does, products, pricing, contact, documentation.
- Keep it to the pages a machine should read first, not a mirror of the sitemap.
- Optionally publish clean Markdown mirrors of those pages and link them from it.
- Keep it current: a stale index is worse than none, because it directs readers to the wrong pages.

### P-002 - Publish a facts-and-figures page that other sources can cite

**MEDIUM priority, medium effort.** A claim repeated across many independent sources is treated as reliable; one that exists in a single place is fragile. Journalists, directories, analysts and assistants can only repeat facts that are stated somewhere quotable, in a stable location, with a date attached. Most organisations never publish this, and then wonder why the web describes them inaccurately.

- Create a page carrying the organisation's canonical facts: legal name, founding year, headquarters, leadership, size, key figures - each as a short declarative sentence.
- Date every figure and update them on a fixed schedule.
- Give it a stable URL and link it from the About page, the footer and any press materials.
- Mirror the same values in Organization structured data so they are machine-readable too.

### P-003 - Publish answers to the questions customers actually ask, in their words

**MEDIUM priority, medium effort.** Retrieval matches a user's question against candidate passages. Content already written as a question with a self-contained answer matches directly, while the same information as narrative prose has to be located inside a longer passage first. The wording matters as much as the format: customers ask in their own vocabulary, not the brand's product names.

- Collect the real questions from sales calls, support tickets and site search logs.
- Publish each with an answer that stands alone when quoted out of context.
- Use the customer's phrasing in the question; introduce internal product vocabulary in the answer.
- Mark the block up as FAQPage.

### P-004 - Publish honest comparison and 'is this right for me' pages

**MEDIUM priority, high effort.** A large share of the questions put to assistants are comparative or qualifying. If the brand does not answer them, review sites and competitors' comparison pages do - and those are the sources that get cited. Even-handed pages that say where an alternative is the better fit are cited more often than promotional ones, because they read as reliable.

- Write comparisons against the alternatives buyers genuinely evaluate, including the cases where the alternative wins.
- Publish `for <industry>` or `for <role>` pages describing the specific situation each serves.
- Title each page as the question it answers.
- Keep them current - a comparison against an outdated competitor version damages credibility.

### P-005 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

### P-006 - Design interior pages for visitors who arrive without context

**MEDIUM priority, low effort.** Assistant referrals land deep in a site rather than on the homepage, and they arrive with no idea whose site they are on. Pages built on the assumption that the visitor came through the front door lose them immediately - so the more successful the discoverability work, the more traffic this wastes.

- Ensure every page states the organisation's name and what it does, in text.
- Add breadcrumbs so a visitor can see where they have landed.
- End each page with a next step chosen for that page's subject.
- Review the pages assistants most often cite and treat each as a potential first impression.

### P-007 - Segment assistant-referred traffic so this work can be evaluated

**LOW priority, low effort.** AI-referred visits behave differently from search visits: they land deeper, arrive with more context, and convert on different pages. Without a separate segment they are averaged into search traffic and the effect of any discoverability work is invisible.

- Create an analytics segment for known assistant referrers and review it separately.
- Report on landing page, onward navigation and conversion for that segment specifically.
- Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.

## Checks skipped (and why)

- `ANS-002` - homepage H1 is unrecognised vocabulary rather than identifiable marketing abstraction; not flagged to avoid a false positive
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-011` - the site declares no external profiles to verify
- `ENT-012` - only 0 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-005` - thin text is already explained by the render-gap finding
- `RND-008` - no PDF documents were linked from the sampled pages
