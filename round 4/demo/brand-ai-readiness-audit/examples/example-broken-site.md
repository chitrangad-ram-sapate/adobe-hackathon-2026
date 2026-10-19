# AI-readiness audit: shop.example

*2026-09-09T13:27:05Z - 6 pages analysed*

**29 findings on shop.example: the most severe is critical and sits at the access gate - machines may not reach or discover all of the site. Start with "AI assistant retrieval crawlers are blocked in robots.txt".**

## Readiness score: 31.6/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 38 | Can a machine reach the content |
| Render | 38 | Can a machine read what visitors see |
| Extract | 0 | Can a machine quote a specific fact |
| Trust | 81 | Will the fact be believed and repeated |
| Engagement | 21 | Do arriving visitors orient and act |

## Findings (29)

critical 2 - high 9 - medium 10 - low 7 - info 1

### F-001 - AI assistant retrieval crawlers are blocked in robots.txt

**CRITICAL** - discoverability / access gate - confidence high (static) - check `ACC-003`

**Evidence.** 2 retrieval agents are disallowed from /: oai-searchbot (OpenAI), perplexitybot (Perplexity); e.g. rule 'Disallow: /' at line 8.

**Why it matters.** These are the agents that fetch a page live while composing an answer and then cite it. Blocking them is different from blocking training crawlers: it removes the brand from answers that would have linked back to the site, so it costs referral traffic directly and immediately. It is very often set by accident, by copying a blocklist intended to opt out of model training.

**Fix (critical priority, low effort, engineering).** Allow retrieval agents (OpenAI, Perplexity) while keeping any training opt-out you intend.

- Separate the two decisions: keep `Disallow: /` for training crawlers if that is a deliberate policy, but allow the retrieval agents (OAI-SearchBot, ChatGPT-User, Claude-User, Claude-SearchBot, PerplexityBot, Meta-ExternalFetcher).
- Give each retrieval agent its own `User-agent` group with `Disallow:` left empty, since the most specific matching group wins and a broad block would otherwise still apply.
- Confirm the same agents are not also blocked at the CDN or WAF layer - robots.txt is advisory and an edge rule will override your intent (see ACC-008).

*On Next.js:*
- Add `app/robots.ts` or a static `public/robots.txt`.

**Verify.** Re-run check ACC-003; no agent with purpose=retrieval should be disallowed from /.

### F-002 - Pages are served as an empty JavaScript application shell

**CRITICAL** - discoverability / render gate - confidence medium (heuristic) - check `RND-002`

**Evidence.** 5 of 5 sampled content pages return a 41 KB response containing only 4 words of text alongside client-framework markers, e.g. https://shop.example/.

**Why it matters.** The server sends an application shell and the content is fetched and assembled in the browser. A fetcher that does not execute JavaScript receives the shell - a page that is technically 200 OK and effectively blank - so nothing on it can be indexed, retrieved or quoted.

**Fix (high priority, high effort, engineering).** Server-render the content routes, or pre-render them to static HTML.

- Switch these routes to server-side rendering or static generation in the framework already in use.
- Confirm the fix at the transport layer, not in the browser: `curl -s <url>` must contain the page text.
- If the application cannot be server-rendered, publish a pre-rendered static copy of the highest-value pages and serve it to non-browser clients from the edge.

*On Next.js:*
- Move the affected routes off client-only rendering: use server components, `generateStaticParams` for static routes, or `getServerSideProps` in the pages router.
- Confirm the fix at the transport layer - `curl -s <url>` must contain the page's text, not just the hydration payload in `__NEXT_DATA__` or the flight stream.

**Verify.** Install a browser engine and re-run; RND-001 will measure the gap exactly.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-003 - The homepage never states in plain words what the organisation is

**HIGH** - discoverability / extract gate - confidence medium (heuristic) - check `ANS-001`

**Evidence.** None of the first 1 sentences on the homepage, the meta description, or any Organization description combines the brand name with a descriptive verb and a category noun. Opening line: "We use cookies".

**Why it matters.** When an assistant is asked what a company does, it looks for a sentence that says so. If the page communicates identity through imagery, layout and implication instead, there is nothing to lift - so the assistant either declines to describe the brand or reconstructs a description from third parties, which is where misrepresentation begins.

**Fix (high priority, low effort, content).** Add one plain declarative sentence near the top of the homepage stating what the organisation is, who it serves, and where.

- Write a sentence of the form: "shop is a <category> that <does what> for <who>, based in <where>."
- Place it in the first screen of the homepage as body text - not inside an image, a video, or a carousel.
- Mirror the same sentence in the meta description and in the Organization schema `description` field so all three agree.
- Keep it literal. A slogan can sit above it; the literal sentence is what gets quoted.

**Verify.** Re-run check ANS-001; a sentence naming the brand, a verb and a category noun should appear in the homepage's opening text.

**Affected URLs (sample).**
- https://shop.example/

### F-004 - Pricing pages contain no readable price

**HIGH** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 3 of 3 sampled pricing/product pages contain no numeric price in their text, e.g. https://shop.example/pricing.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (high priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b

### F-005 - Structured data blocks contain invalid JSON and are discarded

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-001`

**Evidence.** 6 JSON-LD blocks failed to parse, e.g. on https://shop.example/: line 1 col 32: Illegal trailing comma before end of object.

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
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-006 - The site publishes no structured data at all

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-003`

**Evidence.** None of the 6 sampled pages contain JSON-LD, microdata or RDFa markup.

**Why it matters.** Without structured data, every fact on the site has to be inferred from prose. Inference is lossy and unattributed: a system that is unsure what the company is, what it sells, or what something costs will prefer a source that states those facts explicitly - typically a directory or a competitor - and cite that instead.

**Fix (high priority, medium effort, engineering).** Add JSON-LD for the site's core entities, starting with Organization and WebSite on the homepage.

- Add an `Organization` (or `LocalBusiness`) block on the homepage with name, url, logo, description and sameAs links to the brand's authoritative profiles.
- Add a `WebSite` block naming the site as a whole.
- Then add the type that matches each page class: Product/Offer on product pages, Article on posts, FAQPage on question-and-answer content, BreadcrumbList on nested pages.
- Generate the markup from the same data the page renders, so the two can never disagree.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-003; the homepage should expose at least Organization and WebSite.

### F-007 - Product pages have no Product structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 2 of 2 sampled product pages carry no Product markup, e.g. https://shop.example/products/kit-a.

**Why it matters.** The Product type is how a machine learns what is this product and what does it cost. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (high priority, medium effort, engineering).** Add Product JSON-LD to the product page template.

- Add a `Product` JSON-LD block to the product template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, offers, image, description, brand.
- Emit it once per page from the template so new pages inherit it automatically.

*On Next.js:*
- Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is present in the server-rendered HTML rather than added on the client.
- Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b

### F-008 - Home pages have no Organization/WebSite structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://shop.example/.

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
- https://shop.example/

### F-009 - Interior pages give a visitor arriving from outside no context

**HIGH** - engagement / engagement gate - confidence high (static) - check `ENG-001`

**Evidence.** 5 of 5 sampled interior pages fail to name the organisation in their content or offer a clear route onward, e.g. https://shop.example/pricing (names brand: False, links home: False, internal links: 0).

**Why it matters.** Visitors referred by an assistant land on the page that answered their question, not on the homepage, and they arrive with no idea who the site belongs to. A page that assumes the visitor has already seen the homepage gives them nothing to orient against and no next step, so the session ends there. Every improvement to discoverability sends more traffic into this failure.

**Fix (high priority, medium effort, design).** Make every interior page self-contained: say who this is, and offer an obvious next step.

- Ensure the organisation's name and a one-line description of what it does appear on every page, in content or a persistent header - not only in the logo image.
- Add a visible breadcrumb trail so the visitor can see where they have landed.
- End each page with a relevant next step: related pages, the product it belongs to, or a way to get in touch - chosen for that page's subject, not a generic footer.
- Test by opening an interior page in a fresh window: is it obvious whose site this is and what to do next?

**Verify.** Re-run check ENG-001; each interior page should name the brand and offer onward routes.

**Affected URLs (sample).**
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about
- https://shop.example/contact

### F-010 - Key pages offer no clear action to take

**HIGH** - engagement / engagement gate - confidence high (static) - check `ENG-002`

**Evidence.** 5 of 5 sampled conversion-relevant pages contain no link or button whose text describes an action, e.g. https://shop.example/.

**Why it matters.** A visitor who has just read the answer to their question is at the point of highest intent. If the page offers nothing to do next, that intent expires - and because assistant-referred visitors arrive mid-journey rather than at the start, they are unusually likely to leave rather than go looking for the next step themselves.

**Fix (high priority, low effort, design).** Give each key page one obvious primary action, described by what it does.

- Add a single visually primary action per page: 'Book a site survey', 'See pricing', 'Start a trial'.
- Label it with the outcome, not the mechanism - 'Get a quote' rather than 'Submit'.
- Place one instance within the first screen and repeat it at the end of longer pages.

**Verify.** Re-run check ENG-002 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-011 - Pages do not declare a mobile viewport

**HIGH** - engagement / engagement gate - confidence high (static) - check `ENG-007`

**Evidence.** 6 of 6 sampled pages have no viewport meta tag.

**Why it matters.** Without a viewport declaration, mobile browsers render the page at desktop width and scale it down, so text is unreadable and controls are too small to hit. Most assistant-referred traffic arrives on mobile, which makes this the first experience many visitors have of the brand.

**Fix (high priority, low effort, engineering).** Add a responsive viewport meta tag and verify the layout adapts.

- Add `<meta name="viewport" content="width=device-width, initial-scale=1">` to the base template.
- Confirm the layout reflows rather than requiring horizontal scrolling.
- Check that tap targets are large enough and body text is at least 16px.

**Verify.** Re-run check ENG-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-012 - No XML sitemap was found

**MEDIUM** - discoverability / access gate - confidence high (static) - check `ACC-012`

**Evidence.** No sitemap was declared in robots.txt and 0 conventional location(s) (none reachable) returned 0 parseable sitemap URLs across 6 crawled pages.

**Why it matters.** Without a sitemap, a crawler can only find pages by following links from pages it has already fetched. Pages that are linked only from JavaScript menus, paginated archives, or nowhere at all are never discovered, and cannot be cited.

**Fix (high priority, low effort, engineering).** Publish an XML sitemap and declare it in robots.txt.

- Generate a sitemap listing every canonical, indexable URL, with an accurate <lastmod> per URL.
- Add `Sitemap: https://<site>/sitemap.xml` to robots.txt.
- Split into a sitemap index if the site exceeds 50,000 URLs or 50 MB uncompressed.
- Regenerate it automatically on publish, so <lastmod> stays truthful.

*On Next.js:*
- Add `app/sitemap.ts` (or `next-sitemap`) and ensure it enumerates dynamic routes.

**Verify.** Re-run check ACC-012 and confirm it no longer fires.

### F-013 - Missing pages return 200 instead of 404 (soft 404)

**MEDIUM** - discoverability / access gate - confidence high (probe) - check `ACC-026`

**Evidence.** A URL that cannot exist (https://shop.example/x) returned status 200 with 240 words of content.

**Why it matters.** When every URL returns success, a crawler cannot tell real pages from mistakes. Nonexistent URLs enter the index as thin duplicates, budget is spent fetching them, and the signal that a page has been removed never reaches the systems that need it.

**Fix (medium priority, medium effort, engineering).** Return a real 404 status for URLs that do not exist.

- Serve HTTP 404 (or 410 for permanently removed pages) with the error page body.
- In client-rendered apps, ensure the server - not just the router - returns the 404 status.
- Keep the error page useful: search, top links, and a route back into the site.

**Verify.** Re-run check ACC-026 and confirm it no longer fires.

### F-014 - The site tells non-JavaScript clients that it will not work

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-004`

**Evidence.** 6 of 6 sampled pages contain a <noscript> block stating JavaScript is required, e.g. "You need to enable JavaScript to run this app.".

**Why it matters.** This message is the fallback a non-JavaScript client actually receives. Where it appears, it confirms the page's real content is unavailable without script execution - and for a text extractor, this sentence may be the most prominent text on the page.

**Fix (medium priority, medium effort, engineering).** Provide real content in <noscript>, or server-render the page so the fallback is unnecessary.

- Server-render the primary content (see RND-001/RND-002).
- Until then, put the page's core text - headline, description, key facts, links - inside <noscript> so something meaningful is readable.

*On Next.js:*
- Move the affected routes off client-only rendering: use server components, `generateStaticParams` for static routes, or `getServerSideProps` in the pages router.
- Confirm the fix at the transport layer - `curl -s <url>` must contain the page's text, not just the hydration payload in `__NEXT_DATA__` or the flight stream.

**Verify.** Re-run check RND-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-015 - Pages have no H1 heading

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-012`

**Evidence.** 6 of 6 sampled pages contain no <h1> element, e.g. https://shop.example/.

**Why it matters.** The H1 is the most reliable statement of what a page is about, and extractive systems lean on it heavily when deciding whether a page answers a question and what to call it in a citation. Without one, the page's topic has to be inferred from body text, which is less reliable.

**Fix (high priority, low effort, content).** Give every page exactly one H1 that states the page's subject in plain words.

- Add a single <h1> per page containing the page's real subject, not a slogan or the site name.
- Style it freely - the level is a structural statement, not a visual one.

**Verify.** Re-run check RND-012 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-016 - Pages have missing or placeholder titles

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-004`

**Evidence.** 6 of 6 sampled pages have no title or a generic one, e.g. https://shop.example/ is titled "Home".

**Why it matters.** A page titled "Home" tells a retrieval system nothing about the brand or the subject, and produces a citation nobody clicks. It is also the label the page carries in every system that ever references it.

**Fix (high priority, low effort, content).** Write a descriptive, unique title for every page.

- Name the subject and the brand: `Warehouse robots for distributors - Northwind Robotics`.
- Keep it under about 60 characters so it is not truncated in results.

*On Next.js:*
- Export `metadata` or `generateMetadata` per route so each page has its own title and description.

**Verify.** Re-run check ANS-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-017 - No contact details appear as text

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-007`

**Evidence.** Neither an email address nor a phone number appears in the text of 1 sampled contact/home page(s) (https://shop.example/contact).

**Why it matters.** "How do I contact them" is one of the most common questions asked about any organisation. Details that exist only inside a contact form, an image, or a script-rendered widget cannot be extracted, so the answer is either absent or taken from a third-party directory listing that the brand does not control and may not have updated.

**Fix (high priority, low effort, content).** Publish a phone number, an email address and a postal address as selectable text.

- Put the details in HTML text, using `tel:` and `mailto:` links.
- Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).
- Keep a contact form if preferred - but alongside the details, not instead of them.

**Verify.** Re-run check ANS-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/contact

### F-018 - Nothing on the site distinguishes this brand from others with the same name

**MEDIUM** - discoverability / trust gate - confidence medium (heuristic) - check `ENT-005`

**Evidence.** The homepage title is "Home" - 1 word(s) with no category qualifier - and no identity-authority sameAs link is declared for the name "shop".

**Why it matters.** Several organisations, products and places routinely share a name. With no category in the title and no link to an identity authority, a system has nothing to tell them apart, so facts about a similarly named entity get attributed to this brand and vice versa. This is the mechanism behind most cases of an assistant describing a company as something it is not.

**Fix (high priority, low effort, marketing).** Qualify the brand everywhere it is named, and link to an identity authority.

- Change the homepage title to `Shop - <what it is> for <who>` so the name never appears unqualified.
- Add Organization schema with `description`, `address` and `sameAs` links to Wikidata, LinkedIn and a company register.
- Use the qualified form consistently in off-site profiles and press mentions, so the distinguishing phrase is what the wider web repeats.

**Verify.** Re-run check ENT-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/

### F-019 - The site publishes few verifiable facts about the organisation itself

**MEDIUM** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 1 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text; no named, quantified fact (customers, employees, locations) appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (medium priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-020 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 6 of 6 sampled pages, and 6 of those pages carry under 120 words of body text, e.g. https://shop.example/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-021 - Pages are dead ends with almost no onward links

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-011`

**Evidence.** 6 of 6 sampled pages contain 2 or fewer links to other pages on the site, e.g. https://shop.example/ has 0.

**Why it matters.** A visitor who finishes a page with nowhere to go leaves. Internal links are also how discovery propagates: pages that nothing links onward from are crawled less and understood as less connected to the rest of the site, so the deeper content stays invisible.

**Fix (medium priority, medium effort, content).** Add contextual internal links and a relevant next step to every page.

- Link from body text to the related products, articles or documentation the page mentions.
- Add a 'related' block chosen by subject rather than by recency.
- Ensure the primary navigation is present in the HTML of every page, not injected by script.

**Verify.** Re-run check ENG-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-022 - Most pages have no canonical URL declared

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-020`

**Evidence.** 6 of 6 sampled pages have no rel=canonical link.

**Why it matters.** Without a canonical, the same content reachable through tracking parameters, trailing-slash variants or both host names is treated as several competing pages. Authority is split across the duplicates and none of them is a clear best answer.

**Fix (medium priority, low effort, engineering).** Add a self-referencing canonical to every indexable page.

- Add `<link rel="canonical">` to the base template, populated with the page's own absolute URL.
- Normalise it: one host, one scheme, consistent trailing slash, no tracking parameters.

*On Next.js:*
- Set `alternates.canonical` in each route's metadata to the page's own absolute URL.

**Verify.** Re-run check ACC-020 and confirm it no longer fires.

### F-023 - Internal links and sitemap entries point at pages that fail to load

**LOW** - discoverability / access gate - confidence high (static) - check `ACC-024`

**Evidence.** 1 of 7 crawled URLs returned an error, e.g. https://shop.example/gone (404).

**Why it matters.** Every dead link is a discovery path that terminates, and a visitor who reaches one usually leaves rather than navigating back. Dead entries in a sitemap additionally teach crawlers to trust the sitemap less.

**Fix (low priority, medium effort, engineering).** Fix or remove the broken URLs from links and from the sitemap.

- Repair the links, or redirect the old URLs to their current equivalents with a 301.
- Remove URLs that no longer exist from the sitemap.
- Add a build-time link check so this does not regress.

**Verify.** Re-run check ACC-024 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/gone

### F-024 - Pages have no <main> or <article> landmark

**LOW** - discoverability / render gate - confidence high (static) - check `RND-013`

**Evidence.** 6 of 6 sampled pages wrap their content in generic containers with no <main> or <article> element.

**Why it matters.** Content extractors use landmarks to separate the article from the navigation, header and footer that repeat on every page. Without them the boundary is guessed, and boilerplate is regularly quoted as though it were page content.

**Fix (medium priority, low effort, engineering).** Wrap the unique content of each page in <main>, and each self-contained item in <article>.

- Add one <main> per page around the content that is unique to it.
- Use <article> for individually meaningful items - posts, products, listings.
- Keep navigation in <nav>, site header in <header>, site footer in <footer>.

**Verify.** Re-run check RND-013 and confirm it no longer fires.

**Affected URLs (sample).**
- https://shop.example/
- https://shop.example/pricing
- https://shop.example/products/kit-a
- https://shop.example/products/kit-b
- https://shop.example/about

### F-025 - The document language is not declared

**LOW** - discoverability / render gate - confidence high (static) - check `RND-014`

**Evidence.** 6 of 6 sampled pages have no lang attribute on <html>.

**Why it matters.** The language declaration tells retrieval systems which language queries this page can answer, and tells screen readers which voice to use. Undeclared pages are sometimes assigned the wrong language and dropped from results in their real one.

**Fix (medium priority, low effort, engineering).** Declare the page language on the <html> element.

- Add `lang="<language code>"` to <html> in the base template.
- For multilingual sites, emit the correct code per locale and add rel=alternate hreflang links.

**Verify.** Re-run check RND-014 and confirm it no longer fires.

### F-026 - Most pages have no meta description

**LOW** - discoverability / extract gate - confidence high (static) - check `ANS-005`

**Evidence.** 6 of 6 sampled pages have no meta description.

**Why it matters.** The meta description is a pre-written, self-contained summary of the page. Where it is absent a summary is generated from whatever text happens to be near the top - often navigation or a cookie notice - so the brand loses control of how the page is described.

**Fix (low priority, medium effort, content).** Write a one-sentence meta description for every page.

- Summarise what the page answers in 120-155 characters, as a complete sentence.
- Write it as a standalone statement - it is frequently read without the page around it.

*On Next.js:*
- Export `metadata` or `generateMetadata` per route so each page has its own title and description.

**Verify.** Re-run check ANS-005 and confirm it no longer fires.

### F-027 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, and 0 external brand profile links appear on the page.

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
- https://shop.example/

### F-028 - No skip-to-content link is provided

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-015`

**Evidence.** None of the 6 sampled pages offers a skip-to-content link.

**Why it matters.** Keyboard and screen-reader users must otherwise traverse the entire navigation on every page before reaching the content. It is a small omission with a disproportionate cost for the visitors it affects.

**Fix (medium priority, low effort, engineering).** Add a skip link as the first focusable element on every page.

- Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in <body>.
- Give the main content container the matching id and make the link visible on focus.

**Verify.** Re-run check ENG-015 and confirm it no longer fires.

### F-029 - No analytics instrumentation was detected

**INFO** - engagement / engagement gate - confidence medium (static) - check `ENG-016`

**Evidence.** No recognised analytics or tag-management script was found across 6 sampled pages.

**Why it matters.** Without measurement there is no way to tell whether any engagement change helped, and no way to see assistant-referred traffic arriving on deep pages - which is the traffic this audit's discoverability fixes are intended to produce.

**Fix (low priority, low effort, marketing).** Add privacy-respecting analytics and segment traffic by referrer so AI referrals are visible.

- Install an analytics tool appropriate to the site's privacy posture and consent obligations.
- Create a segment for assistant referrers so the effect of discoverability work can be observed separately from search.
- Track landing page and onward navigation, since deep-linked arrivals are the population these engagement findings concern.

**Verify.** Re-run check ENG-016 and confirm it no longer fires.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish an /llms.txt index of the site's most quotable pages

**MEDIUM priority, low effort.** Assistants that fetch pages live have to guess which URLs carry the facts they need. An llms.txt file is an emerging convention for stating that explicitly - a short, plain-text map of the pages a machine should read first. It costs almost nothing, and where it is honoured it puts the brand in control of which pages represent it.

- Create `/llms.txt`: an H1 with the organisation's name, a blockquote with the one-line description, then linked sections for the pages that answer real questions - what the company does, products, pricing, contact, documentation.
- Keep it to the pages a machine should read first, not a mirror of the sitemap.
- Optionally publish clean Markdown mirrors of those pages and link them from it.
- Keep it current: a stale index is worse than none, because it directs readers to the wrong pages.

### P-002 - Publish answers to the questions customers actually ask, in their words

**MEDIUM priority, medium effort.** Retrieval matches a user's question against candidate passages. Content already written as a question with a self-contained answer matches directly, while the same information as narrative prose has to be located inside a longer passage first. The wording matters as much as the format: customers ask in their own vocabulary, not the brand's product names.

- Collect the real questions from sales calls, support tickets and site search logs.
- Publish each with an answer that stands alone when quoted out of context.
- Use the customer's phrasing in the question; introduce internal product vocabulary in the answer.
- Mark the block up as FAQPage.

### P-003 - Publish honest comparison and 'is this right for me' pages

**MEDIUM priority, high effort.** A large share of the questions put to assistants are comparative or qualifying. If the brand does not answer them, review sites and competitors' comparison pages do - and those are the sources that get cited. Even-handed pages that say where an alternative is the better fit are cited more often than promotional ones, because they read as reliable.

- Write comparisons against the alternatives buyers genuinely evaluate, including the cases where the alternative wins.
- Publish `for <industry>` or `for <role>` pages describing the specific situation each serves.
- Title each page as the question it answers.
- Keep them current - a comparison against an outdated competitor version damages credibility.

### P-004 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

## Checks skipped (and why)

- `ANS-002` - no H1 on the homepage; covered by RND-012
- `ANS-008` - only 6 pages sampled; too small a site for the absence of question-and-answer content to indicate a gap
- `ANS-009` - too few known URLs to judge content coverage
- `ENG-012` - homepage exposes too few links to assess navigation reach
- `ENT-001` - fewer than two self-descriptions present to compare
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `RND-001` - no JavaScript engine available; render gap estimated statically by RND-002
- `RND-005` - thin text is already explained by the render-gap finding
- `RND-006` - no images found on the sampled pages
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 about page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 contact page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 pricing page(s) lacked expected markup - too few to conclude a pattern
- `SDA-010` - fewer than 3 nested pages sampled
