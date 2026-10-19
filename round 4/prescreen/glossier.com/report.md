# AI-readiness audit: glossier.com

*2026-09-24T19:02:38Z - 30 pages analysed*

**21 findings on glossier.com: the most severe is high and sits at the access gate - machines may not reach or discover all of the site. Start with "No XML sitemap was found".**

## Readiness score: 55.9/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 80 | Can a machine reach the content |
| Render | 56 | Can a machine read what visitors see |
| Extract | 10 | Can a machine quote a specific fact |
| Trust | 81 | Will the fact be believed and repeated |
| Engagement | 70 | Do arriving visitors orient and act |

## Findings (21)

critical 0 - high 5 - medium 11 - low 5 - info 0

### F-001 - No XML sitemap was found

**HIGH** - discoverability / access gate - confidence high (static) - check `ACC-012`

**Evidence.** No sitemap was declared in robots.txt and 3 conventional location(s) (/en-in/sitemap.xml, /en-in/sitemap_index.xml, /en-in/sitemap-index.xml) returned 0 parseable sitemap URLs across 30 crawled pages.

**Why it matters.** Without a sitemap, a crawler can only find pages by following links from pages it has already fetched. Pages that are linked only from JavaScript menus, paginated archives, or nowhere at all are never discovered, and cannot be cited.

**Fix (high priority, low effort, engineering).** Publish an XML sitemap and declare it in robots.txt.

- Generate a sitemap listing every canonical, indexable URL, with an accurate <lastmod> per URL.
- Add `Sitemap: https://<site>/sitemap.xml` to robots.txt.
- Split into a sitemap index if the site exceeds 50,000 URLs or 50 MB uncompressed.
- Regenerate it automatically on publish, so <lastmod> stays truthful.

*On Shopify:*
- Shopify generates /sitemap.xml automatically; if pages are missing, check they are published and not excluded from the sales channel.

**Verify.** Re-run check ACC-012 and confirm it no longer fires.

### F-002 - Facts appear to be locked inside images with no text equivalent

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 7 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. https://glossier-prod.imgix.net/files/glossier-sept-wardrobe-gwp-homepage-hero-tablet.png?auto=compress,format&cs=srgb&w on https://www.glossier.com/en-in.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (high priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://glossier.com/
- https://help.glossier.com/
- https://help.glossier.com/en-US
- https://www.glossier.com/en-in
- https://www.glossier.com/en-in/products/balm-dotcom-quintet

### F-003 - The homepage never states in plain words what the organisation is

**HIGH** - discoverability / extract gate - confidence medium (heuristic) - check `ANS-001`

**Evidence.** None of the first 6 sentences on the homepage, the meta description, or any Organization description combines the brand name with a descriptive verb and a category noun. Opening line: "limited time Free fragrance, anyone?".

**Why it matters.** When an assistant is asked what a company does, it looks for a sentence that says so. If the page communicates identity through imagery, layout and implication instead, there is nothing to lift - so the assistant either declines to describe the brand or reconstructs a description from third parties, which is where misrepresentation begins.

**Fix (high priority, low effort, content).** Add one plain declarative sentence near the top of the homepage stating what the organisation is, who it serves, and where.

- Write a sentence of the form: "glossier is a <category> that <does what> for <who>, based in <where>."
- Place it in the first screen of the homepage as body text - not inside an image, a video, or a carousel.
- Mirror the same sentence in the meta description and in the Organization schema `description` field so all three agree.
- Keep it literal. A slogan can sit above it; the literal sentence is what gets quoted.

**Verify.** Re-run check ANS-001; a sentence naming the brand, a verb and a category noun should appear in the homepage's opening text.

**Affected URLs (sample).**
- https://www.glossier.com/en-in

### F-004 - Pricing pages contain no readable price

**HIGH** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 8 of 8 sampled pricing/product pages contain no numeric price in their text, e.g. https://www.glossier.com/en-in/products/balm-dotcom.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (high priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in/products/balm-dotcom
- https://www.glossier.com/en-in/products/balm-dotcom-quintet
- https://www.glossier.com/en-in/products/balm-dotcom-quintet?parent_collection=balms
- https://www.glossier.com/en-in/products/balm-dotcom-trio
- https://www.glossier.com/en-in/products/balm-dotcom-trio?parent_collection=balms

### F-005 - Home pages have no Organization/WebSite structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://www.glossier.com/en-in.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (high priority, medium effort, engineering).** Add Organization JSON-LD to the home page template.

- Add a `Organization` JSON-LD block to the home template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in

### F-006 - Page content is assembled by JavaScript and is missing from the server response

**MEDIUM** - discoverability / render gate - confidence high (rendered) - check `RND-001`

**Evidence.** On 1 of 3 rendered pages the raw HTML contains less text than the browser DOM; worst case https://www.glossier.com/en-in/products/balm-dotcom ships 850 words against 1353 after JavaScript (63% coverage).

**Why it matters.** Most AI retrieval fetchers and many crawlers read the HTTP response without running JavaScript. Whatever the client assembles afterwards does not exist for them, so the page is fetched successfully and found to contain almost nothing worth quoting - the site is reachable and still uncitable.

**Fix (medium priority, high effort, engineering).** Server-render or pre-render the content that currently only appears after JavaScript runs.

- Move the primary content - headings, body copy, prices, specifications, contact details - into the server-rendered HTML so it is present in the first response.
- Use the framework's server-side rendering or static generation mode for these routes rather than client-only rendering.
- Where full SSR is impractical, pre-render the top templates to static HTML and hydrate afterwards.
- Verify with `curl -s <url> | wc -w`: the raw response should contain the page's real text.

*On Shopify:*
- Render the content on the server for the affected routes and verify with `curl -s <url>` that the text is in the response body.

**Verify.** Re-run check RND-001; raw-to-rendered word coverage should exceed 0.75 on every content page.

**Affected URLs (sample).**
- https://www.glossier.com/en-in/products/balm-dotcom

### F-007 - Most images have no alt text

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-007`

**Evidence.** 1077 of 1957 images across 30 sampled pages (55%) have a missing or empty alt attribute.

**Why it matters.** Alt text is the only description of an image available to a text reader, and it is one of the few places where an image's meaning enters the page's extractable content. Its absence also makes the page unusable with a screen reader, which is an engagement failure as much as a discoverability one.

**Fix (medium priority, medium effort, content).** Add descriptive alt text to meaningful images and empty alt to decorative ones.

- Describe what the image conveys in context, in a sentence fragment.
- Use alt="" for decoration so readers skip it rather than announcing a filename.
- Add an alt field to the CMS image component so authors cannot omit it silently.

**Verify.** Re-run check RND-007 and confirm it no longer fires.

### F-008 - Pages have no H1 heading

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-012`

**Evidence.** 16 of 30 sampled pages contain no <h1> element, e.g. https://www.glossier.com/en-in.

**Why it matters.** The H1 is the most reliable statement of what a page is about, and extractive systems lean on it heavily when deciding whether a page answers a question and what to call it in a citation. Without one, the page's topic has to be inferred from body text, which is less reliable.

**Fix (high priority, low effort, content).** Give every page exactly one H1 that states the page's subject in plain words.

- Add a single <h1> per page containing the page's real subject, not a slogan or the site name.
- Style it freely - the level is a structural statement, not a visual one.

*On Shopify:*
- Make the change in `theme.liquid` so it applies to every template.

**Verify.** Re-run check RND-012 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in
- https://glossier.com/
- https://life.glossier.com/
- https://www.glossier.com/en-in/pages/about
- https://www.glossier.com/en-in/products/balm-dotcom-quintet

### F-009 - Different pages share the same title

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 14 of 30 sampled pages share 5 repeated title(s), e.g. "Glossier".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (high priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On Shopify:*
- Edit the title and description templates in `theme.liquid` and set per-product values in the admin's search-listing preview.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in
- https://glossier.com/
- https://help.glossier.com/
- https://www.glossier.com/en-in/products/balm-dotcom
- https://www.glossier.com/en-in/products/balm-dotcom-quintet

### F-010 - Contact pages have no Organization structured data

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 2 of 2 sampled contact pages carry no Organization markup, e.g. https://www.glossier.com/en-in/pages/contact-us.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (medium priority, medium effort, engineering).** Add Organization JSON-LD to the contact page template.

- Add a `Organization` JSON-LD block to the contact template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in/pages/contact-us
- https://www.glossier.com/en-in/pages/locations

### F-011 - Organization structured data is missing required fields

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-007`

**Evidence.** 6 Organization nodes omit url (6x), e.g. on https://www.glossier.com/en-in/products/balm-dotcom.

**Why it matters.** The block is present and parses, so it appears to be working - but without url it cannot answer who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Consumers that require these fields discard the node entirely, leaving the page in the same position as one with no markup at all.

**Fix (high priority, low effort, engineering).** Populate the required Organization fields: url.

- Add url to the Organization block, sourced from the same data the page renders.
- Leave a field out entirely rather than emitting an empty string or a placeholder - an empty value is treated as an assertion that the value is empty.
- Validate the output against the type's requirements as part of the build.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in/products/balm-dotcom
- https://www.glossier.com/en-in/products/balm-dotcom-trio
- https://www.glossier.com/en-in/products/balm-dotcom-trio?parent_collection=balms
- https://www.glossier.com/en-in/products/balm-dotcom?parent_collection=balms
- https://www.glossier.com/en-in/products/balm-dotcom?variant=48390723731701

### F-012 - Nothing on the site distinguishes this brand from others with the same name

**MEDIUM** - discoverability / trust gate - confidence medium (heuristic) - check `ENT-005`

**Evidence.** The homepage title is "Glossier" - 1 word(s) with no category qualifier - and no identity-authority sameAs link is declared for the name "glossier".

**Why it matters.** Several organisations, products and places routinely share a name. With no category in the title and no link to an identity authority, a system has nothing to tell them apart, so facts about a similarly named entity get attributed to this brand and vice versa. This is the mechanism behind most cases of an assistant describing a company as something it is not.

**Fix (high priority, low effort, marketing).** Qualify the brand everywhere it is named, and link to an identity authority.

- Change the homepage title to `Glossier - <what it is> for <who>` so the name never appears unqualified.
- Add Organization schema with `description`, `address` and `sameAs` links to Wikidata, LinkedIn and a company register.
- Use the qualified form consistently in off-site profiles and press mentions, so the distinguishing phrase is what the wider web repeats.

**Verify.** Re-run check ENT-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in

### F-013 - The site publishes few verifiable facts about the organisation itself

**MEDIUM** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 1 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text; no named, quantified fact (customers, employees, locations) appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (medium priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-014 - Some pages ship a very large HTML document

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-004`

**Evidence.** 3 of 30 sampled pages return more than 1.2 MB of HTML alone, e.g. https://www.glossier.com/en-in/products/balm-dotcom at 1268 KB (before images, scripts and stylesheets).

**Why it matters.** The HTML document blocks everything else: nothing renders until it has arrived and been parsed. On a mobile connection a document this size costs seconds before the first pixel, and abandonment climbs steeply with every second of delay.

**Fix (medium priority, medium effort, engineering).** Reduce document size by paginating, deferring and trimming inlined data.

- Move large inlined JSON, base64 images and repeated markup out of the document.
- Paginate or lazy-load long lists rather than emitting every item.
- Serve compressed responses (gzip or brotli) and confirm the header is present.

**Verify.** Re-run check ENG-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in/products/balm-dotcom
- https://www.glossier.com/en-in/products/balm-dotcom?parent_collection=balms
- https://www.glossier.com/en-in/products/balm-dotcom?variant=48390723731701

### F-015 - Media is set to play automatically

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-009`

**Evidence.** 4 of 30 sampled pages contain a video or audio element with the autoplay attribute, e.g. https://www.glossier.com/en-in.

**Why it matters.** Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays the content they came for, and - where sound is involved - is a common reason for closing a tab immediately.

**Fix (high priority, low effort, design).** Require an explicit play action, or at minimum keep autoplay muted and deferred.

- Remove autoplay and show a poster image with a visible play control.
- If a background video is essential to the design, keep it muted, short, and loaded after the primary content.
- Respect prefers-reduced-motion.

**Verify.** Re-run check ENG-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in
- https://glossier.com/
- https://www.glossier.com/en-in/products/balm-dotcom-quintet
- https://www.glossier.com/en-in/products/balm-dotcom-quintet?parent_collection=balms

### F-016 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 26 of 30 sampled pages, and 2 of those pages carry under 120 words of body text, e.g. https://life.glossier.com/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://life.glossier.com/
- https://www.glossier.com/en-in/pages/contact-us

### F-017 - The site does not answer comparison, use-case or how-to questions

**LOW** - discoverability / extract gate - confidence medium (static) - check `ANS-009`

**Evidence.** Across 30 known URLs there are no pages matching comparison, faq, how_to, use_case patterns; only none present.

**Why it matters.** A large share of the questions put to assistants are comparative or qualifying - which tool for this job, how does this compare to that, is this suitable for my situation. A site that only describes its own products in its own vocabulary has no passage that matches those questions, so the answer is assembled from review sites and competitors' comparison pages instead.

**Fix (low priority, high effort, marketing).** Publish comparison, use-case and how-to pages in the customer's own words.

- Write honest comparison pages against the alternatives buyers genuinely evaluate, including where the alternative is the better fit - even-handed pages are cited more often than promotional ones.
- Publish `for <audience>` or `for <industry>` pages describing the specific situation each serves.
- Add how-to and getting-started content answering the questions that precede a purchase decision.
- Title and phrase each page as the question it answers.

**Verify.** Re-run check ANS-009 and confirm it no longer fires.

### F-018 - Nested pages carry no breadcrumb structured data

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-010`

**Evidence.** 25 of 25 sampled nested pages have no BreadcrumbList markup.

**Why it matters.** Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the kind an assistant links someone straight into - acquires context about what it is part of. They also give the brand a labelled path in results rather than a bare URL.

**Fix (medium priority, low effort, engineering).** Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.

- Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.
- Render a matching visible trail; it serves the same orientation purpose for the reader.
- Keep the markup and the visible trail identical.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-010 and confirm it no longer fires.

### F-019 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, although 4 external profile link(s) appear on the page (https://www.facebook.com/glossier, https://www.instagram.com/glossier/, https://www.tiktok.com/@glossier).

**Why it matters.** sameAs is the machine-readable claim that this site, this company registry entry, this LinkedIn page and this Wikipedia article are one entity. Without it, corroborating facts scattered across those sources are not recognised as being about the same organisation, so each one stands alone and is weaker - and a similarly named organisation can be confused with this one.

**Fix (medium priority, low effort, marketing).** Declare sameAs links from Organization schema to every profile the brand controls.

- Add a `sameAs` array to the Organization block listing the brand's authoritative profiles.
- Prioritise identity authorities over social reach: Wikidata, Wikipedia, LinkedIn, Crunchbase, a company register entry, GitHub - these disambiguate; a follower count does not.
- Make the links reciprocal where possible: the profile should link back to the site.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check ENT-002 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.glossier.com/en-in

### F-020 - Navigation relies on repeated, undescriptive link text

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-003`

**Evidence.** The link text "here" appears 6 times across the sampled pages, alongside 2 such repeated labels in total.

**Why it matters.** Identical undescriptive labels force the visitor to work out where each one goes from its surroundings, which is slow on a screen and impossible for anyone navigating by links alone with a screen reader. The same text also gives search and retrieval systems no signal about what the linked page contains.

**Fix (medium priority, low effort, content).** Replace repeated generic labels with text naming the destination.

- Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.
- Where the visual design requires a short label, add an aria-label carrying the full description.

**Verify.** Re-run check ENG-003 and confirm it no longer fires.

### F-021 - Images have no dimensions and are not lazy-loaded

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-008`

**Evidence.** 1941 of 1957 sampled images declare no width/height and 1948 do not use loading="lazy".

**Why it matters.** Without declared dimensions the browser cannot reserve space, so content jumps as images arrive and visitors tap the wrong thing. Without lazy loading, images far below the fold compete for bandwidth with content the visitor is waiting to read.

**Fix (medium priority, low effort, engineering).** Declare intrinsic width and height on images and lazy-load those below the fold.

- Set width and height attributes matching the image's intrinsic aspect ratio.
- Add `loading="lazy"` to images below the fold, and leave it off the main hero image.
- Serve modern formats with responsive `srcset` sizes.

**Verify.** Re-run check ENG-008 and confirm it no longer fires.

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

### P-003 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

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

## Checks skipped (and why)

- `ACC-002` - no robots.txt served (404), which correctly means no crawl restrictions
- `ANS-002` - no H1 on the homepage; covered by RND-012
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-011` - the site declares no external profiles to verify
- `ENT-012` - only 0 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-005` - thin text is already explained by the render-gap finding
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 about page(s) lacked expected markup - too few to conclude a pattern
