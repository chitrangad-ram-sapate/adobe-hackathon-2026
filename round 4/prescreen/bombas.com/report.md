# AI-readiness audit: bombas.com

*2026-09-24T19:02:23Z - 30 pages analysed*

**19 findings on bombas.com: the most severe is critical and sits at the access gate - machines may not reach or discover all of the site. Start with "The site serves content to browsers but blocks non-browser clients".**

## Readiness score: 64.0/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 40 | Can a machine reach the content |
| Render | 57 | Can a machine read what visitors see |
| Extract | 57 | Can a machine quote a specific fact |
| Trust | 94 | Will the fact be believed and repeated |
| Engagement | 81 | Do arriving visitors orient and act |

## Findings (19)

critical 1 - high 1 - medium 12 - low 5 - info 0

### F-001 - The site serves content to browsers but blocks non-browser clients

**CRITICAL** - discoverability / access gate - confidence high (probe) - check `ACC-008`

**Evidence.** The same URL returned 200 with 1131 words to a browser user-agent, and 429 to a plain client (server: Vercel).

**Why it matters.** A CDN, WAF or bot-management rule is filtering by user-agent or TLS fingerprint. Every AI retrieval fetcher and most search crawlers arrive as non-browser clients, so they receive the challenge page instead of the content. The site looks perfectly healthy to its owners, who only ever visit it in a browser, which is why this failure can persist for years unnoticed.

**Fix (critical priority, medium effort, ops).** Allow verified search and AI crawler traffic through the bot-management rules at the edge.

- In the CDN/WAF bot-management configuration, add an allow rule for verified search and AI crawlers rather than relying on user-agent strings alone.
- Verify by reverse-DNS or the vendors' published IP ranges so the allowance cannot be spoofed.
- Re-test with `curl -A 'GPTBot' https://<site>/` and confirm a 200 with real content, not a challenge page.
- Check rate-limit thresholds separately: a 429 to crawlers has the same effect as a block.

*On Shopify:*
- Make this change in the CDN or WAF configuration rather than in application code.

**Verify.** Re-run check ACC-008; both user agents should return 200 with comparable word counts.

### F-002 - The sitemap declared in robots.txt does not work

**HIGH** - discoverability / access gate - confidence high (static) - check `ACC-011`

**Evidence.** https://bombas.com/sitemap.xml returned status 429.

**Why it matters.** robots.txt advertises a sitemap that crawlers then fail to retrieve or parse. Discovery falls back to link-following, so any page not linked from a crawled page - which on most sites means deep product, location and article pages - is never found.

**Fix (high priority, low effort, engineering).** Fix or remove the broken sitemap reference and publish a valid XML sitemap.

- Serve the declared sitemap URL with a 200 and a valid <urlset> or <sitemapindex> body.
- Validate it parses as XML and every <loc> is an absolute URL on this site.
- If the sitemap no longer exists, remove its Sitemap: line from robots.txt.

*On Shopify:*
- Shopify generates /sitemap.xml automatically; if pages are missing, check they are published and not excluded from the sales channel.

**Verify.** Re-run check ACC-011 and confirm it no longer fires.

### F-003 - Page content is assembled by JavaScript and is missing from the server response

**MEDIUM** - discoverability / render gate - confidence high (rendered) - check `RND-001`

**Evidence.** On 1 of 3 rendered pages the raw HTML contains less text than the browser DOM; worst case https://bombas.com/ ships 801 words against 1589 after JavaScript (50% coverage).

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
- https://bombas.com/

### F-004 - Facts appear to be locked inside images with no text equivalent

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 90 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. /_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fsock-1.20b4654a.webp&w=2048&q=75 on https://beebetter.bombas.com/.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (medium priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://beebetter.bombas.com/
- https://beebetter.bombas.com/impact
- https://beebetter.bombas.com/partners
- https://bombas.com/collections/baby-socks
- https://bombas.com/collections/bralette

### F-005 - Most images have no alt text

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-007`

**Evidence.** 424 of 552 images across 30 sampled pages (77%) have a missing or empty alt attribute.

**Why it matters.** Alt text is the only description of an image available to a text reader, and it is one of the few places where an image's meaning enters the page's extractable content. Its absence also makes the page unusable with a screen reader, which is an engagement failure as much as a discoverability one.

**Fix (medium priority, medium effort, content).** Add descriptive alt text to meaningful images and empty alt to decorative ones.

- Describe what the image conveys in context, in a sentence fragment.
- Use alt="" for decoration so readers skip it rather than announcing a filename.
- Add an alt field to the CMS image component so authors cannot omit it silently.

**Verify.** Re-run check RND-007 and confirm it no longer fires.

### F-006 - Much of the page text is hidden behind tabs or accordions at load time

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-011`

**Evidence.** 9 sampled pages hide more than 40% of their body text in collapsed regions, e.g. https://bombas.com/help?a=How-do-I-track-my-order---id--2CJttFHETPGTkQZcEzNOlQ keeps 169 of 289 words in {'hidden_block': 1}.

**Why it matters.** The text is in the HTML, so this is milder than a render gap - but content hidden at load time is weighted down or dropped by some extractors, and a visitor who does not click never reads it. Specifications, FAQs and shipping terms are the usual casualties, and they are exactly the facts people ask assistants about.

**Fix (high priority, low effort, design).** Show the highest-value content expanded by default and keep collapsing for genuine overflow.

- Expand the first panel of each accordion or tab group by default.
- Move facts people search for - price, dimensions, delivery, compatibility, hours - into always-visible text.
- Where an FAQ is collapsed for layout, add FAQPage structured data so the pairs remain machine-readable.

**Verify.** Re-run check RND-011 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/help?a=How-do-I-track-my-order---id--2CJttFHETPGTkQZcEzNOlQ
- https://bombas.com/help?a=What%27s-your-returnexchange-policy---id--99ZcZXU7SpepjRHgO0yu6w
- https://bombas.com/help?g=Account+%26+Checkout
- https://bombas.com/help?g=Gifting
- https://bombas.com/help?g=Shipping

### F-007 - Pages have no H1 heading

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-012`

**Evidence.** 20 of 30 sampled pages contain no <h1> element, e.g. https://bombas.com/.

**Why it matters.** The H1 is the most reliable statement of what a page is about, and extractive systems lean on it heavily when deciding whether a page answers a question and what to call it in a citation. Without one, the page's topic has to be inferred from body text, which is less reliable.

**Fix (high priority, low effort, content).** Give every page exactly one H1 that states the page's subject in plain words.

- Add a single <h1> per page containing the page's real subject, not a slogan or the site name.
- Style it freely - the level is a structural statement, not a visual one.

*On Shopify:*
- Make the change in `theme.liquid` so it applies to every template.

**Verify.** Re-run check RND-012 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/
- https://bombas.com/pages/about-us
- https://bombas.com/help?a=How-do-I-track-my-order---id--2CJttFHETPGTkQZcEzNOlQ
- https://bombas.com/help?a=What%27s-your-returnexchange-policy---id--99ZcZXU7SpepjRHgO0yu6w
- https://bombas.com/help?g=Account+%26+Checkout

### F-008 - Different pages share the same title

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 8 of 30 sampled pages share 2 repeated title(s), e.g. "Bombas 200 Million Items Donated: BeeBetter".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (high priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On Shopify:*
- Edit the title and description templates in `theme.liquid` and set per-product values in the admin's search-listing preview.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://beebetter.bombas.com/
- https://bombas.com/help?a=How-do-I-track-my-order---id--2CJttFHETPGTkQZcEzNOlQ
- https://bombas.com/help?a=What%27s-your-returnexchange-policy---id--99ZcZXU7SpepjRHgO0yu6w
- https://bombas.com/help?g=Account+%26+Checkout
- https://bombas.com/help?g=Gifting

### F-009 - Pricing pages contain no readable price

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 7 of 7 sampled pricing/product pages contain no numeric price in their text, e.g. https://bombas.com/products/gift-card.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (medium priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/products/gift-card
- https://bombas.com/products/mens-medical-grade-compression-knee-high-socks-20-30mmhg?variant=sea-blue
- https://bombas.com/products/mens-merino-wool-sock-4-pack?variant=grey-olive-mix
- https://bombas.com/products/mens-running-ankle-sock-3-pack?variant=sapphire-grey-mix
- https://bombas.com/products/mens-suede-moccasin-slipper?variant=golden-camel

### F-010 - Home pages have no Organization/WebSite structured data

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-006`

**Evidence.** 1 of 1 sampled home pages carry no Organization or WebSite markup, e.g. https://bombas.com/.

**Why it matters.** The Organization type is how a machine learns who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (medium priority, medium effort, engineering).** Add Organization JSON-LD to the home page template.

- Add a `Organization` JSON-LD block to the home template, populated from the same data the page already renders.
- Include the fields that make it answerable: name, url, logo, description, sameAs.
- Emit it once per page from the template so new pages inherit it automatically.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/

### F-011 - Product markup carries no price

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-008`

**Evidence.** 1 of 7 sampled product/pricing pages declare Product-family markup with no populated Offer price, e.g. https://bombas.com/products/gift-card.

**Why it matters.** 'How much does it cost' is among the most common questions asked of an assistant about a commercial brand. A Product node without a price cannot answer it, so the assistant falls back to a reseller, a directory or a review site - all of which are more likely to quote an out-of-date figure than the brand's own page would.

**Fix (medium priority, medium effort, engineering).** Add Offer price, priceCurrency and availability to product markup.

- Nest an `offers` object with `price`, `priceCurrency` and `availability` in every Product node.
- Use `AggregateOffer` with `lowPrice`/`highPrice` where a product spans variants.
- Populate it from live pricing data so the markup cannot drift from the page.
- For quote-based pricing, publish an indicative range rather than nothing - an absent price is treated as an absent product.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-008 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/products/gift-card

### F-012 - Question-and-answer content is not marked up as an FAQ

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-009`

**Evidence.** 2 pages contain 10+ question-shaped headings with no FAQPage markup, e.g. https://beebetter.bombas.com/impact asks "What is a Giving Partner Organization?".

**Why it matters.** Question-and-answer pairs are the most directly quotable content a site can publish, because the question already matches the shape of what users ask. Marking them up hands a retrieval system a pre-matched pair instead of asking it to locate the answer inside a page of prose.

**Fix (high priority, low effort, content).** Add FAQPage structured data wrapping the existing questions and answers.

- Emit `FAQPage` with a `mainEntity` array of `Question`/`acceptedAnswer` pairs built from the headings and body already on the page.
- Keep the answers self-contained: each should make sense quoted on its own, without the question above it or the paragraph before it.
- Only mark up genuine questions the page answers - inventing pairs for markup's sake is treated as spam by consumers.

*On Shopify:*
- Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` and `collection` Liquid objects.
- Use `product.selected_or_first_available_variant.price | money_without_currency` and `product.available` so price and availability follow the variant the customer is viewing.

**Verify.** Re-run check SDA-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://beebetter.bombas.com/impact
- https://bombas.com/pages/affiliates

### F-013 - Some pages ship a very large HTML document

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-004`

**Evidence.** 3 of 30 sampled pages return more than 1.2 MB of HTML alone, e.g. https://bombas.com/ at 1206 KB (before images, scripts and stylesheets).

**Why it matters.** The HTML document blocks everything else: nothing renders until it has arrived and been parsed. On a mobile connection a document this size costs seconds before the first pixel, and abandonment climbs steeply with every second of delay.

**Fix (medium priority, medium effort, engineering).** Reduce document size by paginating, deferring and trimming inlined data.

- Move large inlined JSON, base64 images and repeated markup out of the document.
- Paginate or lazy-load long lists rather than emitting every item.
- Serve compressed responses (gzip or brotli) and confirm the header is present.

**Verify.** Re-run check ENG-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/
- https://bombas.com/pages/about-us
- https://bombas.com/collections/bralette

### F-014 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 27 of 30 sampled pages, and 9 of those pages carry under 120 words of body text, e.g. https://beebetter.bombas.com/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://beebetter.bombas.com/
- https://bombas.com/products/gift-card
- https://bombas.com/products/mens-medical-grade-compression-knee-high-socks-20-30mmhg?variant=sea-blue
- https://bombas.com/products/mens-merino-wool-sock-4-pack?variant=grey-olive-mix
- https://bombas.com/products/mens-running-ankle-sock-3-pack?variant=sapphire-grey-mix

### F-015 - Pages have no <main> or <article> landmark

**LOW** - discoverability / render gate - confidence high (static) - check `RND-013`

**Evidence.** 22 of 30 sampled pages wrap their content in generic containers with no <main> or <article> element.

**Why it matters.** Content extractors use landmarks to separate the article from the navigation, header and footer that repeat on every page. Without them the boundary is guessed, and boilerplate is regularly quoted as though it were page content.

**Fix (medium priority, low effort, engineering).** Wrap the unique content of each page in <main>, and each self-contained item in <article>.

- Add one <main> per page around the content that is unique to it.
- Use <article> for individually meaningful items - posts, products, listings.
- Keep navigation in <nav>, site header in <header>, site footer in <footer>.

*On Shopify:*
- Make the change in `theme.liquid` so it applies to every template.

**Verify.** Re-run check RND-013 and confirm it no longer fires.

**Affected URLs (sample).**
- https://bombas.com/
- https://beebetter.bombas.com/
- https://bombas.com/pages/about-us
- https://bombas.com/help?a=How-do-I-track-my-order---id--2CJttFHETPGTkQZcEzNOlQ
- https://bombas.com/help?a=What%27s-your-returnexchange-policy---id--99ZcZXU7SpepjRHgO0yu6w

### F-016 - The site does not answer comparison, use-case or how-to questions

**LOW** - discoverability / extract gate - confidence medium (static) - check `ANS-009`

**Evidence.** Across 30 known URLs there are no pages matching comparison, faq, how_to, use_case patterns; only none present.

**Why it matters.** A large share of the questions put to assistants are comparative or qualifying - which tool for this job, how does this compare to that, is this suitable for my situation. A site that only describes its own products in its own vocabulary has no passage that matches those questions, so the answer is assembled from review sites and competitors' comparison pages instead.

**Fix (low priority, high effort, marketing).** Publish comparison, use-case and how-to pages in the customer's own words.

- Write honest comparison pages against the alternatives buyers genuinely evaluate, including where the alternative is the better fit - even-handed pages are cited more often than promotional ones.
- Publish `for <audience>` or `for <industry>` pages describing the specific situation each serves.
- Add how-to and getting-started content answering the questions that precede a purchase decision.
- Title and phrase each page as the question it answers.

**Verify.** Re-run check ANS-009 and confirm it no longer fires.

### F-017 - The site never declares which external profiles belong to this brand

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-002`

**Evidence.** 0 sameAs links are declared across 0 Organization-family node(s) on the homepage, although 2 external profile link(s) appear on the page (https://www.facebook.com/bombassocks, https://www.instagram.com/bombas).

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
- https://bombas.com/

### F-018 - The site publishes few verifiable facts about the organisation itself

**LOW** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 1 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (low priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-019 - No skip-to-content link is provided

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-015`

**Evidence.** None of the 30 sampled pages offers a skip-to-content link.

**Why it matters.** Keyboard and screen-reader users must otherwise traverse the entire navigation on every page before reaching the content. It is a small omission with a disproportionate cost for the visitors it affects.

**Fix (medium priority, low effort, engineering).** Add a skip link as the first focusable element on every page.

- Add `<a class="skip-link" href="#main">Skip to main content</a>` as the first element in <body>.
- Give the main content container the matching id and make the link visible on focus.

*On Shopify:*
- Make the change in `theme.liquid` so it applies to every template.

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

## What this audit could not determine

- The site returned no usable response to this auditor's own user agent but did to a browser user agent, so the crawl was performed with a browser user agent in order to audit the content at all. See finding ACC-008: every non-browser client, including AI retrieval fetchers, receives the same block. Run with --no-ua-fallback to disable this substitution.

## Checks skipped (and why)

- `ANS-002` - no H1 on the homepage; covered by RND-012
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-011` - the site declares no external profiles to verify
- `ENT-012` - only 0 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-005` - thin text is already explained by the render-gap finding
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 about page(s) lacked expected markup - too few to conclude a pattern
- `SDA-005` - only 1 careers page(s) lacked expected markup - too few to conclude a pattern
