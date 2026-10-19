# AI-readiness audit: typeform.com

*2026-09-24T19:02:01Z - 30 pages analysed*

**16 findings on typeform.com: the most severe is high and sits at the render gate - machines cannot read what visitors can see. Start with "Facts appear to be locked inside images with no text equivalent".**

## Readiness score: 67.7/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 100 | Can a machine reach the content |
| Render | 72 | Can a machine read what visitors see |
| Extract | 23 | Can a machine quote a specific fact |
| Trust | 86 | Will the fact be believed and repeated |
| Engagement | 73 | Do arriving visitors orient and act |

## Findings (16)

critical 0 - high 4 - medium 6 - low 6 - info 0

### F-001 - Facts appear to be locked inside images with no text equivalent

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 9 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. https://cdn.prod.website-files.com/66ffe2174aa8e8d5661c2708/69fc834d25dca9f26a7de418_Chart-Line.svg on https://www.typeform.com/.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (high priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://www.typeform.com/
- https://www.typeform.com/blog
- https://www.typeform.com/blog-category/news
- https://www.typeform.com/blog-category/product
- https://www.typeform.com/contact-us

### F-002 - The homepage never states in plain words what the organisation is

**HIGH** - discoverability / extract gate - confidence medium (heuristic) - check `ANS-001`

**Evidence.** None of the first 6 sentences on the homepage, the meta description, or any Organization description combines the brand name with a descriptive verb and a category noun. Opening line: "AI forms & automation Your favorite forms.".

**Why it matters.** When an assistant is asked what a company does, it looks for a sentence that says so. If the page communicates identity through imagery, layout and implication instead, there is nothing to lift - so the assistant either declines to describe the brand or reconstructs a description from third parties, which is where misrepresentation begins.

**Fix (high priority, low effort, content).** Add one plain declarative sentence near the top of the homepage stating what the organisation is, who it serves, and where.

- Write a sentence of the form: "Typeform is a <category> that <does what> for <who>, based in <where>."
- Place it in the first screen of the homepage as body text - not inside an image, a video, or a carousel.
- Mirror the same sentence in the meta description and in the Organization schema `description` field so all three agree.
- Keep it literal. A slogan can sit above it; the literal sentence is what gets quoted.

**Verify.** Re-run check ANS-001; a sentence naming the brand, a verb and a category noun should appear in the homepage's opening text.

**Affected URLs (sample).**
- https://www.typeform.com/

### F-003 - Pricing pages contain no readable price

**HIGH** - discoverability / extract gate - confidence high (static) - check `ANS-006`

**Evidence.** 3 of 5 sampled pricing/product pages contain no numeric price in their text, e.g. https://www.typeform.com/blog-category/product.

**Why it matters.** Cost is among the most common things asked about any commercial brand. With no number on the page, an assistant cannot answer from the brand's own site and turns to resellers, review sites and forums - sources that are often out of date and never in the brand's control. Publishing a figure is what makes the brand's own page the citable one.

**Fix (high priority, medium effort, marketing).** Publish a real figure or an indicative range, even where final pricing is negotiated.

- State a starting price, a typical range, or a worked example: "from 4,500 GBP per unit per year".
- Put it in body text, not in an image or a downloadable PDF.
- Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.
- If pricing genuinely cannot be published, state what it depends on in plain text - that is still an extractable, quotable answer, where silence is not.

**Verify.** Re-run check ANS-006 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/blog-category/product
- https://www.typeform.com/blog-tag/product
- https://www.typeform.com/careers/product

### F-004 - Article pages have no Article/BlogPosting/NewsArticle structured data

**HIGH** - discoverability / extract gate - confidence high (static) - check `SDA-005`

**Evidence.** 3 of 3 sampled article pages carry no Article or BlogPosting or NewsArticle markup, e.g. https://www.typeform.com/blog.

**Why it matters.** The Article type is how a machine learns what does this say, when was it said, and who said it. Without it the page competes on prose alone against sources that state the same facts in a form that needs no interpretation.

**Fix (high priority, medium effort, engineering).** Add Article JSON-LD to the article page template.

- Add a `Article` JSON-LD block to the article template, populated from the same data the page already renders.
- Include the fields that make it answerable: headline, datePublished, author, dateModified, image.
- Emit it once per page from the template so new pages inherit it automatically.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/blog
- https://www.typeform.com/blog-category/news
- https://www.typeform.com/blog-tag/press-release

### F-005 - The site tells non-JavaScript clients that it will not work

**MEDIUM** - discoverability / render gate - confidence high (static) - check `RND-004`

**Evidence.** 2 of 30 sampled pages contain a <noscript> block stating JavaScript is required, e.g. "You need to enable JavaScript to run Typeform.".

**Why it matters.** This message is the fallback a non-JavaScript client actually receives. Where it appears, it confirms the page's real content is unavailable without script execution - and for a text extractor, this sentence may be the most prominent text on the page.

**Fix (medium priority, medium effort, engineering).** Provide real content in <noscript>, or server-render the page so the fallback is unnecessary.

- Server-render the primary content (see RND-001/RND-002).
- Until then, put the page's core text - headline, description, key facts, links - inside <noscript> so something meaningful is readable.

*On unknown:*
- Render the content on the server for the affected routes and verify with `curl -s <url>` that the text is in the response body.

**Verify.** Re-run check RND-004 and confirm it no longer fires.

**Affected URLs (sample).**
- https://admin.typeform.com/
- https://admin.typeform.com/?cello-open=true

### F-006 - Question-and-answer content is not marked up as an FAQ

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `SDA-009`

**Evidence.** 4 pages contain 9+ question-shaped headings with no FAQPage markup, e.g. https://www.typeform.com/pricing asks "What are the benefits of a paid vs free plan?".

**Why it matters.** Question-and-answer pairs are the most directly quotable content a site can publish, because the question already matches the shape of what users ask. Marking them up hands a retrieval system a pre-matched pair instead of asking it to locate the answer inside a page of prose.

**Fix (high priority, low effort, content).** Add FAQPage structured data wrapping the existing questions and answers.

- Emit `FAQPage` with a `mainEntity` array of `Question`/`acceptedAnswer` pairs built from the headings and body already on the page.
- Keep the answers self-contained: each should make sense quoted on its own, without the question above it or the paragraph before it.
- Only mark up genuine questions the page answers - inventing pairs for markup's sake is treated as spam by consumers.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/pricing
- https://www.typeform.com/pricing/talent
- https://www.typeform.com/templates/faq
- https://www.typeform.com/templates/testimonial-form-template

### F-007 - The brand describes itself differently in different places on the same page

**MEDIUM** - discoverability / trust gate - confidence high (static) - check `ENT-001`

**Evidence.** 3 pair(s) of self-descriptions on the homepage share little vocabulary; the Organization schema description and the meta description overlap by only 13% ("Build beautiful, interactive forms — get more responses. No coding nee" vs "Build AI-powered forms that get 3.5x more data — then trigger automate").

**Why it matters.** These fields are read by different consumers, and together they form the brand's self-description. When they disagree, a system has no single authoritative account of what the brand is; it either hedges, blends them into something the brand never said, or prefers a third-party description that at least appears consistently.

**Fix (high priority, low effort, marketing).** Write one canonical description of the organisation and use it in every one of these fields.

- Agree a single sentence describing what the organisation is, who it serves and where.
- Use it verbatim in the meta description, og:description, twitter:description and the Organization schema `description`.
- Use the same sentence in off-site profiles - LinkedIn, Crunchbase, directories - so the description the wider web repeats matches the site.

**Verify.** Re-run check ENT-001 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/

### F-008 - Pages load many render-blocking or third-party scripts

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-005`

**Evidence.** 26 of 30 sampled pages load 17 render-blocking scripts from up to 7 third-party hosts, e.g. https://www.typeform.com/templates-sub-category/contact.

**Why it matters.** A render-blocking script stops the page being displayed until it has downloaded and executed, and each additional third-party host adds a DNS lookup and TLS handshake before that can even begin. The visitor sees nothing while this happens, and any one of those third parties being slow makes the brand's own site feel slow.

**Fix (medium priority, medium effort, engineering).** Defer non-essential scripts and cut the number of third-party origins.

- Add `defer` or `async` to every script that is not required for first paint.
- Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.
- Load remaining third-party scripts through a single tag manager, after first paint.
- Self-host small critical dependencies to remove a connection setup from the critical path.

**Verify.** Re-run check ENG-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/
- https://community.typeform.com/
- https://www.typeform.com/about-us
- https://www.typeform.com/pricing
- https://www.typeform.com/pricing/talent

### F-009 - Media is set to play automatically

**MEDIUM** - engagement / engagement gate - confidence high (static) - check `ENG-009`

**Evidence.** 2 of 30 sampled pages contain a video or audio element with the autoplay attribute, e.g. https://www.typeform.com/.

**Why it matters.** Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays the content they came for, and - where sound is involved - is a common reason for closing a tab immediately.

**Fix (high priority, low effort, design).** Require an explicit play action, or at minimum keep autoplay muted and deferred.

- Remove autoplay and show a poster image with a visible play control.
- If a background video is essential to the design, keep it muted, short, and loaded after the primary content.
- Respect prefers-reduced-motion.

**Verify.** Re-run check ENG-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/
- https://www.typeform.com/ai

### F-010 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 27 of 30 sampled pages, and 5 of those pages carry under 120 words of body text, e.g. https://admin.typeform.com/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://admin.typeform.com/
- https://admin.typeform.com/?cello-open=true
- https://community.typeform.com/
- https://www.typeform.com/agencies
- https://www.typeform.com/legal

### F-011 - Different pages share the same title

**LOW** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 4 of 30 sampled pages share 2 repeated title(s), e.g. "Typeform".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (medium priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On unknown:*
- Set the values in the shared layout with a per-page override, so a new page cannot ship without them.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://admin.typeform.com/
- https://admin.typeform.com/?cello-open=true
- https://www.typeform.com/pricing
- https://www.typeform.com/pricing/talent

### F-012 - Organization structured data is missing required fields

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-007`

**Evidence.** 1 Organization nodes omit url (1x), e.g. on https://www.typeform.com/ai.

**Why it matters.** The block is present and parses, so it appears to be working - but without url it cannot answer who is this company, and is it the same entity as the one on Wikipedia/LinkedIn. Consumers that require these fields discard the node entirely, leaving the page in the same position as one with no markup at all.

**Fix (medium priority, low effort, engineering).** Populate the required Organization fields: url.

- Add url to the Organization block, sourced from the same data the page renders.
- Leave a field out entirely rather than emitting an empty string or a placeholder - an empty value is treated as an assertion that the value is empty.
- Validate the output against the type's requirements as part of the build.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/ai

### F-013 - Nested pages carry no breadcrumb structured data

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-010`

**Evidence.** 16 of 16 sampled nested pages have no BreadcrumbList markup.

**Why it matters.** Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the kind an assistant links someone straight into - acquires context about what it is part of. They also give the brand a labelled path in results rather than a bare URL.

**Fix (medium priority, low effort, engineering).** Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.

- Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.
- Render a matching visible trail; it serves the same orientation purpose for the reader.
- Keep the markup and the visible trail identical.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-010 and confirm it no longer fires.

### F-014 - Some brand profiles linked on the site are missing from sameAs

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-004`

**Evidence.** 1 external profile(s) linked from the homepage are not declared in sameAs: https://www.linkedin.com/company/typeform-com/.

**Why it matters.** A link in the footer is a hint; a sameAs entry is an assertion. Profiles left out of the declaration are not connected to the entity, so whatever they corroborate is not counted.

**Fix (medium priority, low effort, marketing).** Add the remaining profiles to the sameAs array.

- Add https://www.linkedin.com/company/typeform-com/ to the Organization sameAs list.
- Keep the two in sync whenever a profile is added or retired.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check ENT-004 and confirm it no longer fires.

### F-015 - Articles have no named author in structured data

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-009`

**Evidence.** 3 of 3 sampled articles declare no author.

**Why it matters.** Attribution is part of how a claim's weight is assessed. Named, described authors connect content to a person whose expertise can be established elsewhere; anonymous content has only the domain behind it.

**Fix (low priority, medium effort, content).** Attribute articles to named authors with linked profiles.

- Add `author` as a Person object with `name`, `url` and `sameAs` to the article's structured data.
- Publish author profile pages describing relevant expertise.
- Show the byline visibly as well as in markup.

**Verify.** Re-run check ENT-009 and confirm it no longer fires.

**Affected URLs (sample).**
- https://www.typeform.com/blog
- https://www.typeform.com/blog-category/news
- https://www.typeform.com/blog-tag/press-release

### F-016 - Navigation relies on repeated, undescriptive link text

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-003`

**Evidence.** The link text "learn more →" appears 10 times across the sampled pages, alongside 2 such repeated labels in total.

**Why it matters.** Identical undescriptive labels force the visitor to work out where each one goes from its surroundings, which is slow on a screen and impossible for anyone navigating by links alone with a screen reader. The same text also gives search and retrieval systems no signal about what the linked page contains.

**Fix (medium priority, low effort, content).** Replace repeated generic labels with text naming the destination.

- Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.
- Where the visual design requires a short label, add an aria-label carrying the full description.

**Verify.** Re-run check ENG-003 and confirm it no longer fires.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish a facts-and-figures page that other sources can cite

**MEDIUM priority, medium effort.** A claim repeated across many independent sources is treated as reliable; one that exists in a single place is fragile. Journalists, directories, analysts and assistants can only repeat facts that are stated somewhere quotable, in a stable location, with a date attached. Most organisations never publish this, and then wonder why the web describes them inaccurately.

- Create a page carrying the organisation's canonical facts: legal name, founding year, headquarters, leadership, size, key figures - each as a short declarative sentence.
- Date every figure and update them on a fixed schedule.
- Give it a stable URL and link it from the About page, the footer and any press materials.
- Mirror the same values in Organization structured data so they are machine-readable too.

### P-002 - Publish honest comparison and 'is this right for me' pages

**MEDIUM priority, high effort.** A large share of the questions put to assistants are comparative or qualifying. If the brand does not answer them, review sites and competitors' comparison pages do - and those are the sources that get cited. Even-handed pages that say where an alternative is the better fit are cited more often than promotional ones, because they read as reliable.

- Write comparisons against the alternatives buyers genuinely evaluate, including the cases where the alternative wins.
- Publish `for <industry>` or `for <role>` pages describing the specific situation each serves.
- Title each page as the question it answers.
- Keep them current - a comparison against an outdated competitor version damages credibility.

### P-003 - Make every fact that appears in an image, video or PDF also available as text

**MEDIUM priority, medium effort.** Facts carried only by non-textual media are invisible to text-based readers, and this is systematically true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire class of invisibility.

- Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video or a PDF, it is also in HTML text on the same page.
- Give data-bearing images alt text that states what they communicate, and put the underlying data in a table beside them.
- Publish transcripts and summaries for video and audio.
- Where a PDF is the canonical document, publish an HTML summary of its key facts as well.

### P-004 - Strengthen the brand's identity graph across authoritative sources

**MEDIUM priority, medium effort.** Entity confusion is one of the main causes of an assistant describing a brand inaccurately. The defence is a consistent, mutually linked set of identity records: the same canonical description, the same legal name, the same location, asserted in several places that reference one another.

- Create or claim a Wikidata item; it is openly editable and widely consumed as an identity reference.
- Align the description on LinkedIn, Crunchbase, GitHub and industry directories with the site's canonical sentence, word for word.
- Declare each of them in the site's Organization `sameAs`, and link back where the platform allows.
- Use the qualified brand name consistently - `<Brand>, the <category> for <audience>` - so the distinguishing phrase is what gets repeated.

### P-005 - Design interior pages for visitors who arrive without context

**MEDIUM priority, low effort.** Assistant referrals land deep in a site rather than on the homepage, and they arrive with no idea whose site they are on. Pages built on the assumption that the visitor came through the front door lose them immediately - so the more successful the discoverability work, the more traffic this wastes.

- Ensure every page states the organisation's name and what it does, in text.
- Add breadcrumbs so a visitor can see where they have landed.
- End each page with a next step chosen for that page's subject.
- Review the pages assistants most often cite and treat each as a potential first impression.

### P-006 - Segment assistant-referred traffic so this work can be evaluated

**LOW priority, low effort.** AI-referred visits behave differently from search visits: they land deeper, arrive with more context, and convert on different pages. Without a separate segment they are averaged into search traffic and the effect of any discoverability work is invisible.

- Create an analytics segment for known assistant referrers and review it separately.
- Report on landing page, onward navigation and conversion for that segment specifically.
- Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.

## What this audit could not determine

- 4 of 5 declared external profile(s) could not be verified because the host blocked the request, disallows it in robots.txt, or the time budget ran out. Those profiles are reported as unverified, never as defects. Run with --no-offsite to skip off-site verification entirely.

## Checks skipped (and why)

- `ANS-002` - no H1 on the homepage; covered by RND-012
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-012` - only 1 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 faq page(s) lacked expected markup - too few to conclude a pattern
