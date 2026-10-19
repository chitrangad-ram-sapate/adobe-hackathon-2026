# AI-readiness audit: duolingo.com

*2026-09-26T10:21:52Z - 28 pages analysed*

**22 findings on duolingo.com: the most severe is critical and sits at the render gate - machines cannot read what visitors can see. Start with "Page content is assembled by JavaScript and is missing from the server response".**

## Readiness score: 58.2/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 94 | Can a machine reach the content |
| Render | 38 | Can a machine read what visitors see |
| Extract | 53 | Can a machine quote a specific fact |
| Trust | 73 | Will the fact be believed and repeated |
| Engagement | 38 | Do arriving visitors orient and act |

## Findings (22)

critical 1 - high 3 - medium 10 - low 8 - info 0

### F-001 - Page content is assembled by JavaScript and is missing from the server response

**CRITICAL** - discoverability / render gate - confidence high (rendered) - check `RND-001`

**Evidence.** On 3 of 3 rendered pages the raw HTML contains less text than the browser DOM; worst case https://www.duolingo.com/ ships 0 words against 163 after JavaScript (0% coverage).

**Why it matters.** Most AI retrieval fetchers and many crawlers read the HTTP response without running JavaScript. Whatever the client assembles afterwards does not exist for them, so the page is fetched successfully and found to contain almost nothing worth quoting - the site is reachable and still uncitable.

**Fix (high priority, high effort, engineering).** Server-render or pre-render the content that currently only appears after JavaScript runs.

- Move the primary content - headings, body copy, prices, specifications, contact details - into the server-rendered HTML so it is present in the first response.
- Use the framework's server-side rendering or static generation mode for these routes rather than client-only rendering.
- Where full SSR is impractical, pre-render the top templates to static HTML and hydrate afterwards.
- Verify with `curl -s <url> | wc -w`: the raw response should contain the page's real text.

*On unknown:*
- Render the content on the server for the affected routes and verify with `curl -s <url>` that the text is in the response body.

**Verify.** Re-run check RND-001; raw-to-rendered word coverage should exceed 0.75 on every content page.

**Affected URLs (sample).**
- https://www.duolingo.com/
- https://www.duolingo.com/team
- https://schools.duolingo.com/help

### F-002 - Home pages have no Organization/WebSite structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://www.duolingo.com/.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (high priority, medium effort, engineering).** Add Organization JSON-LD to the home page template.

- Add a `Organization` JSON-LD block to the home template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/

### F-003 - Interior pages give a visitor arriving from outside no context

**HIGH** - engagement / engagement gate - confidence high (static) - check `ENG-001`

**Evidence.** 13 of 13 sampled interior pages fail to name the organisation in their content or offer a clear route onward, e.g. https://www.duolingo.com/team (names brand: True, links home: False, internal links: 0).

**Why it matters.** Visitors referred by an assistant land on the page that answered their question, not on the homepage, and they arrive with no idea who the site belongs to. A page that assumes the visitor has already seen the homepage gives them nothing to orient against and no next step, so the session ends there. Every improvement to discoverability sends more traffic into this failure.

**Fix (high priority, medium effort, design).** Make every interior page self-contained: say who this is, and offer an obvious next step.

- Ensure the organisation's name and a one-line description of what it does appear on every page, in content or a persistent header - not only in the logo image.
- Add a visible breadcrumb trail so the visitor can see where they have landed.
- End each page with a relevant next step: related pages, the product it belongs to, or a way to get in touch - chosen for that page's subject, not a generic footer.
- Test by opening an interior page in a fresh window: is it obvious whose site this is and what to do next?

**Verify.** Re-run check ENG-001; each interior page should name the brand and offer onward routes.

**Affected URLs (sample).**
- https://www.duolingo.com/team
- https://www.duolingo.com/contact
- https://schools.duolingo.com/help
- https://www.duolingo.com/help
- https://www.duolingo.com/careers

### F-004 - Key pages offer no clear action to take

**HIGH** - engagement / engagement gate - confidence high (static) - check `ENG-002`

**Evidence.** 7 of 9 sampled conversion-relevant pages contain no link or button whose text describes an action, e.g. https://www.duolingo.com/.

**Why it matters.** A visitor who has just read the answer to their question is at the point of highest intent. If the page offers nothing to do next, that intent expires - and because assistant-referred visitors arrive mid-journey rather than at the start, they are unusually likely to leave rather than go looking for the next step themselves.

**Fix (high priority, low effort, design).** Give each key page one obvious primary action, described by what it does.

- Add a single visually primary action per page: 'Book a site survey', 'See pricing', 'Start a trial'.
- Label it with the outcome, not the mechanism - 'Get a quote' rather than 'Submit'.
- Place one instance within the first screen and repeat it at the end of longer pages.

**Verify.** Re-run check ENG-002 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/
- http://contest.duolingo.com/
- https://englishtest.duolingo.com/
- https://incubator.duolingo.com/
- https://schools.duolingo.com/

### F-005 - The site tells non-JavaScript clients that it will not work

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-004`

**Evidence.** 2 of 28 sampled pages contain a <noscript> block stating JavaScript is required, e.g. "You need to enable JavaScript to view our careers page.".

**Why it matters.** This message is the fallback a non-JavaScript client actually receives. Where it appears, it confirms the page's real content is unavailable without script execution - and for a text extractor, this sentence may be the most prominent text on the page.

**Fix (medium priority, medium effort, engineering).** Provide real content in <noscript>, or server-render the page so the fallback is unnecessary.

- Server-render the primary content (see RND-001/RND-002).
- Until then, put the page's core text - headline, description, key facts, links - inside <noscript> so something meaningful is readable.

*On unknown:*
- Render the content on the server for the affected routes and verify with `curl -s <url>` that the text is in the response body.

**Verify.** Re-run check RND-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/careers
- https://incubator.duolingo.com/apply

### F-006 - Pages have no H1 heading

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-012`

**Evidence.** 26 of 28 sampled pages contain no <h1> element, e.g. https://www.duolingo.com/.

**Why it matters.** The H1 is the most reliable statement of what a page is about, and extractive systems lean on it heavily when deciding whether a page answers a question and what to call it in a citation. Without one, the page's topic has to be inferred from body text, which is less reliable.

**Fix (high priority, low effort, content).** Give every page exactly one H1 that states the page's subject in plain words.

- Add a single <h1> per page containing the page's real subject, not a slogan or the site name.
- Style it freely - the level is a structural statement, not a visual one.

**Verify.** Re-run check RND-012 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/
- http://contest.duolingo.com/
- https://englishtest.duolingo.com/
- https://incubator.duolingo.com/
- https://schools.duolingo.com/

### F-007 - Pages have missing or placeholder titles

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-004`

**Evidence.** 9 of 28 sampled pages have no title or a generic one, e.g. https://www.duolingo.com/ is titled "Duolingo".

**Why it matters.** A page titled "Home" tells a retrieval system nothing about the brand or the subject, and produces a citation nobody clicks. It is also the label the page carries in every system that ever references it.

**Fix (high priority, low effort, content).** Write a descriptive, unique title for every page.

- Name the subject and the brand: `Warehouse robots for distributors - Northwind Robotics`.
- Keep it under about 60 characters so it is not truncated in results.

*On unknown:*
- Set the values in the shared layout with a per-page override, so a new page cannot ship without them.

**Verify.** Re-run check ANS-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/
- http://contest.duolingo.com/
- https://incubator.duolingo.com/
- https://www.duolingo.com/team
- https://www.duolingo.com/contact

### F-008 - No contact details appear as text

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-007`

**Evidence.** Neither an email address nor a phone number appears in the text of 1 sampled contact/home page(s) (https://www.duolingo.com/contact).

**Why it matters.** "How do I contact them" is one of the most common questions asked about any organisation. Details that exist only inside a contact form, an image, or a script-rendered widget cannot be extracted, so the answer is either absent or taken from a third-party directory listing that the brand does not control and may not have updated.

**Fix (high priority, low effort, content).** Publish a phone number, an email address and a postal address as selectable text.

- Put the details in HTML text, using `tel:` and `mailto:` links.
- Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).
- Keep a contact form if preferred - but alongside the details, not instead of them.

**Verify.** Re-run check ANS-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/contact

### F-009 - Question-and-answer content is not marked up as an FAQ

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-009`

**Evidence.** 1 pages contain 6+ question-shaped headings with no FAQPage markup, e.g. https://blog.duolingo.com/ asks "Why is English spelling so tricky?".

**Why it matters.** Question-and-answer pairs are the most directly quotable content a site can publish, because the question already matches the shape of what users ask. Marking them up hands a retrieval system a pre-matched pair instead of asking it to locate the answer inside a page of prose.

**Fix (high priority, low effort, content).** Add FAQPage structured data wrapping the existing questions and answers.

- Emit `FAQPage` with a `mainEntity` array of `Question`/`acceptedAnswer` pairs built from the headings and body already on the page.
- Keep the answers self-contained: each should make sense quoted on its own, without the question above it or the paragraph before it.
- Only mark up genuine questions the page answers - inventing pairs for markup's sake is treated as spam by consumers.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://blog.duolingo.com/

### F-010 - The brand describes itself differently in different places on the same page

**MEDIUM** - discoverability / trust gate - confidence high (static) - check `ENT-001`

**Evidence.** 2 pair(s) of self-descriptions on the homepage share little vocabulary; the meta description and the og:description overlap by only 11% ("Duolingo is the world's most popular way to learn a language. It's 100" vs "Learn languages by playing a game. It's 100% free, fun, and scientific").

**Why it matters.** These fields are read by different consumers, and together they form the brand's self-description. When they disagree, a system has no single authoritative account of what the brand is; it either hedges, blends them into something the brand never said, or prefers a third-party description that at least appears consistently.

**Fix (high priority, low effort, marketing).** Write one canonical description of the organisation and use it in every one of these fields.

- Agree a single sentence describing what the organisation is, who it serves and where.
- Use it verbatim in the meta description, og:description, twitter:description and the Organization schema `description`.
- Use the same sentence in off-site profiles - LinkedIn, Crunchbase, directories - so the description the wider web repeats matches the site.

**Verify.** Re-run check ENT-001 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/

### F-011 - Nothing on the site distinguishes this brand from others with the same name

**MEDIUM** - discoverability / trust gate - confidence medium (heuristic) - check `ENT-005`

**Evidence.** The homepage title is "Duolingo" - 1 word(s) with no category qualifier - and no identity-authority sameAs link is declared for the name "duolingo".

**Why it matters.** Several organisations, products and places routinely share a name. With no category in the title and no link to an identity authority, a system has nothing to tell them apart, so facts about a similarly named entity get attributed to this brand and vice versa. This is the mechanism behind most cases of an assistant describing a company as something it is not.

**Fix (high priority, low effort, marketing).** Qualify the brand everywhere it is named, and link to an identity authority.

- Change the homepage title to `Duolingo - <what it is> for <who>` so the name never appears unqualified.
- Add Organization schema with `description`, `address` and `sameAs` links to Wikidata, LinkedIn and a company register.
- Use the qualified form consistently in off-site profiles and press mentions, so the distinguishing phrase is what the wider web repeats.

**Verify.** Re-run check ENT-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/

### F-012 - The site publishes few verifiable facts about the organisation itself

**MEDIUM** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 1 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text; no named, quantified fact (customers, employees, locations) appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (medium priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-013 - Pages load many render-blocking or third-party scripts

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-005`

**Evidence.** 2 of 28 sampled pages load 31 render-blocking scripts from up to 6 third-party hosts, e.g. https://blog.duolingo.com/.

**Why it matters.** A render-blocking script stops the page being displayed until it has downloaded and executed, and each additional third-party host adds a DNS lookup and TLS handshake before that can even begin. The visitor sees nothing while this happens, and any one of those third parties being slow makes the brand's own site feel slow.

**Fix (medium priority, medium effort, engineering).** Defer non-essential scripts and cut the number of third-party origins.

- Add `defer` or `async` to every script that is not required for first paint.
- Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.
- Load remaining third-party scripts through a single tag manager, after first paint.
- Self-host small critical dependencies to remove a connection setup from the critical path.

**Verify.** Re-run check ENG-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://blog.duolingo.com/
- https://status.duolingo.com/

### F-014 - Pages are dead ends with almost no onward links

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-011`

**Evidence.** 18 of 21 sampled pages contain 2 or fewer links to other pages on the site, e.g. https://www.duolingo.com/ has 0.

**Why it matters.** A visitor who finishes a page with nowhere to go leaves. Internal links are also how discovery propagates: pages that nothing links onward from are crawled less and understood as less connected to the rest of the site, so the deeper content stays invisible.

**Fix (medium priority, medium effort, content).** Add contextual internal links and a relevant next step to every page.

- Link from body text to the related products, articles or documentation the page mentions.
- Add a 'related' block chosen by subject rather than by recency.
- Ensure the primary navigation is present in the HTML of every page, not injected by script.

**Verify.** Re-run check ENG-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/
- http://contest.duolingo.com/
- https://englishtest.duolingo.com/
- https://incubator.duolingo.com/
- https://schools.duolingo.com/

### F-015 - Sitemap entries mostly lack <lastmod> dates

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-014`

**Evidence.** 0 of 104 sitemap URLs carry a <lastmod> value.

**Why it matters.** Crawlers use <lastmod> to decide what to re-fetch. Without it they re-crawl on their own schedule, so updated pages can be represented in answers by a stale copy for far longer than necessary.

**Fix (medium priority, low effort, engineering).** Emit an accurate <lastmod> for every sitemap URL.

- Populate <lastmod> from the content's real last-modified time, not the build time.
- Do not set every URL to the same timestamp on each deploy - crawlers learn to distrust it.

**Verify.** Re-run check ACC-014 and confirm it no longer fires.

### F-016 - Internal links and sitemap entries point at pages that fail to load

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-024`

**Evidence.** 2 of 30 crawled URLs returned an error, e.g. https://englishtest.duolingo.com/faq (403), http://static.duolingo.com/s3/DuolingoReport_Final.pdf (fetch_error: EOFError: Compressed file ended before the end-of-stream marker was reached).

**Why it matters.** Every dead link is a discovery path that terminates, and a visitor who reaches one usually leaves rather than navigating back. Dead entries in a sitemap additionally teach crawlers to trust the sitemap less.

**Fix (low priority, medium effort, engineering).** Fix or remove the broken URLs from links and from the sitemap.

- Repair the links, or redirect the old URLs to their current equivalents with a 301.
- Remove URLs that no longer exist from the sitemap.
- Add a build-time link check so this does not regress.

**Verify.** Re-run check ACC-024 and confirm it no longer fires.

**Affected URLs (sample).**
- https://englishtest.duolingo.com/faq
- http://static.duolingo.com/s3/DuolingoReport_Final.pdf

### F-017 - Pages have no <main> or <article> landmark

**LOW** - discoverability / render gate - confidence high (static) - check `RND-013`

**Evidence.** 27 of 28 sampled pages wrap their content in generic containers with no <main> or <article> element.

**Why it matters.** Content extractors use landmarks to separate the article from the navigation, header and footer that repeat on every page. Without them the boundary is guessed, and boilerplate is regularly quoted as though it were page content.

**Fix (medium priority, low effort, engineering).** Wrap the unique content of each page in <main>, and each self-contained item in <article>.

- Add one <main> per page around the content that is unique to it.
- Use <article> for individually meaningful items - posts, products, listings.
- Keep navigation in <nav>, site header in <header>, site footer in <footer>.

**Verify.** Re-run check RND-013 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/
- http://contest.duolingo.com/
- http://pillow.duolingo.com/
- https://englishtest.duolingo.com/
- https://incubator.duolingo.com/

### F-018 - The document language is not declared

**LOW** - discoverability / render gate - confidence high (static) - check `RND-014`

**Evidence.** 18 of 28 sampled pages have no lang attribute on <html>.

**Why it matters.** The language declaration tells retrieval systems which language queries this page can answer, and tells screen readers which voice to use. Undeclared pages are sometimes assigned the wrong language and dropped from results in their real one.

**Fix (medium priority, low effort, engineering).** Declare the page language on the <html> element.

- Add `lang="<language code>"` to <html> in the base template.
- For multilingual sites, emit the correct code per locale and add rel=alternate hreflang links.

**Verify.** Re-run check RND-014 and confirm it no longer fires.

### F-019 - Nested pages carry no breadcrumb structured data

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-010`

**Evidence.** 5 of 5 sampled nested pages have no BreadcrumbList markup.

**Why it matters.** Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the kind an assistant links someone straight into - acquires context about what it is part of. They also give the brand a labelled path in results rather than a bare URL.

**Fix (medium priority, low effort, engineering).** Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.

- Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.
- Render a matching visible trail; it serves the same orientation purpose for the reader.
- Keep the markup and the visible trail identical.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-010 and confirm it no longer fires.

### F-020 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, and 0 external brand profile links appear on the page.

**Why it matters.** sameAs is the machine-readable claim that this site, this company registry entry, this LinkedIn page and this Wikipedia article are one entity. Without it, corroborating facts scattered across those sources are not recognised as being about the same organisation, so each one stands alone and is weaker - and a similarly named organisation can be confused with this one.

**Fix (medium priority, low effort, marketing).** Declare sameAs links from Organization schema to every profile the brand controls.

- Add a `sameAs` array to the Organization block listing the brand's authoritative profiles.
- Prioritise identity authorities over social reach: Wikidata, Wikipedia, LinkedIn, Crunchbase, a company register entry, GitHub - these disambiguate; a follower count does not.
- Make the links reciprocal where possible: the profile should link back to the site.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check ENT-002 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.duolingo.com/

### F-021 - Images have no dimensions and are not lazy-loaded

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-008`

**Evidence.** 25 of 28 sampled images declare no width/height and 28 do not use loading="lazy".

**Why it matters.** Without declared dimensions the browser cannot reserve space, so content jumps as images arrive and visitors tap the wrong thing. Without lazy loading, images far below the fold compete for bandwidth with content the visitor is waiting to read.

**Fix (medium priority, low effort, engineering).** Declare intrinsic width and height on images and lazy-load those below the fold.

- Set width and height attributes matching the image's intrinsic aspect ratio.
- Add `loading="lazy"` to images below the fold, and leave it off the main hero image.
- Serve modern formats with responsive `srcset` sizes.

**Verify.** Re-run check ENG-008 and confirm it no longer fires.

### F-022 - No skip-to-content link is provided

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-015`

**Evidence.** None of the 28 sampled pages offers a skip-to-content link.

**Why it matters.** Keyboard and screen-reader users must otherwise traverse the entire navigation on every page before reaching the content. It is a small omission with a disproportionate cost for the visitors it affects.

**Fix (medium priority, low effort, engineering).** Add a skip link as the first focusable element on every page.

- Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in <body>.
- Give the main content container the matching id and make the link visible on focus.

**Verify.** Re-run check ENG-015 and confirm it no longer fires.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

### P-002 - Segment assistant-referred traffic so this work can be evaluated

**LOW priority, low effort.** AI-referred visits behave differently from search visits: they land deeper, arrive with more context, and convert on different pages. Without a separate segment they are averaged into search traffic and the effect of any discoverability work is invisible.

- Create an analytics segment for known assistant referrers and review it separately.
- Report on landing page, onward navigation and conversion for that segment specifically.
- Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.

## Checks skipped (and why)

- `ANS-002` - no H1 on the homepage; covered by RND-012
- `ANS-006` - site type is unknown; a published price is not expected
- `ANS-009` - site type is unknown; comparison and use-case pages are not expected
- `ENG-012` - homepage exposes too few links to assess navigation reach
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-011` - the site declares no external profiles to verify
- `ENT-012` - only 0 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-005` - thin text is already explained by the render-gap finding
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 about page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 careers page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 contact page(s) lacked expected markup - too few to conclude a pattern
- `SDA-008` - no product or pricing pages were sampled
