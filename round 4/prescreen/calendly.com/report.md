# AI-readiness audit: calendly.com

*2026-09-24T19:01:17Z - 30 pages analysed*

**12 findings on calendly.com: the most severe is high and sits at the render gate - machines cannot read what visitors can see. Start with "Facts appear to be locked inside images with no text equivalent".**

## Readiness score: 82.2/100

| Gate | Score | What it means |
| --- | --- | --- |
| Access | 92 | Can a machine reach the content |
| Render | 60 | Can a machine read what visitors see |
| Extract | 86 | Can a machine quote a specific fact |
| Trust | 94 | Will the fact be believed and repeated |
| Engagement | 81 | Do arriving visitors orient and act |

## Findings (12)

critical 0 - high 2 - medium 4 - low 5 - info 1

### F-001 - Facts appear to be locked inside images with no text equivalent

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-006`

**Evidence.** 93 images whose filename or position indicates they carry words (charts, price lists, banners, heading graphics) have no alt text, e.g. /_astro/timeline-background.UWFBJqGi.svg on https://calendly.com/.

**Why it matters.** Text drawn inside an image is invisible to every text-based reader. When a price list, an opening-hours table or a specification chart exists only as a picture, the facts on it cannot be extracted, cited, or read by assistive technology - the information is published and simultaneously unavailable.

**Fix (high priority, medium effort, content).** Publish the facts these images carry as real text, and give every image meaningful alt text.

- For each image carrying data - prices, hours, specifications, comparisons - add the same content as HTML text or a table next to it. The image becomes the illustration, not the source.
- Write alt text that states what the image communicates, not what it depicts.
- Where an image is purely decorative, use alt="" so readers skip it deliberately.

**Verify.** Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.

**Affected URLs (sample).**
- https://calendly.com/
- https://calendly.com/about
- https://calendly.com/contact-us
- https://calendly.com/customers
- https://calendly.com/leadership

### F-002 - Most images have no alt text

**HIGH** - discoverability / render gate - confidence high (static) - check `RND-007`

**Evidence.** 580 of 685 images across 30 sampled pages (85%) have a missing or empty alt attribute.

**Why it matters.** Alt text is the only description of an image available to a text reader, and it is one of the few places where an image's meaning enters the page's extractable content. Its absence also makes the page unusable with a screen reader, which is an engagement failure as much as a discoverability one.

**Fix (high priority, medium effort, content).** Add descriptive alt text to meaningful images and empty alt to decorative ones.

- Describe what the image conveys in context, in a sentence fragment.
- Use alt="" for decoration so readers skip it rather than announcing a filename.
- Add an alt field to the CMS image component so authors cannot omit it silently.

**Verify.** Re-run check RND-007 and confirm it no longer fires.

### F-003 - Pages that should be findable are marked noindex

**MEDIUM** - discoverability / access gate - confidence high (static) - check `ACC-016`

**Evidence.** 1 of 30 sampled pages carry a noindex directive, e.g. https://calendly.com/contact.

**Why it matters.** noindex tells indexing systems to discard the page after fetching it. Content behind it can never be surfaced or cited, and because the page still renders normally for visitors, the exclusion is invisible from inside the organisation.

**Fix (high priority, low effort, engineering).** Remove noindex from pages that are meant to be found.

- Remove `<meta name="robots" content="noindex">` and any `X-Robots-Tag: noindex` header from these pages.
- Check whether the directive is applied by a template or an edge rule rather than by the page itself.
- A staging-environment configuration reaching production is the usual cause - verify the deploy pipeline.

**Verify.** Fetch each URL and confirm no noindex appears in the meta robots tag or the X-Robots-Tag header.

**Affected URLs (sample).**
- https://calendly.com/contact

### F-004 - No contact details appear as text

**MEDIUM** - discoverability / extract gate - confidence high (static) - check `ANS-007`

**Evidence.** Neither an email address nor a phone number appears in the text of 4 sampled contact/home page(s) (https://calendly.com/contact).

**Why it matters.** "How do I contact them" is one of the most common questions asked about any organisation. Details that exist only inside a contact form, an image, or a script-rendered widget cannot be extracted, so the answer is either absent or taken from a third-party directory listing that the brand does not control and may not have updated.

**Fix (high priority, low effort, content).** Publish a phone number, an email address and a postal address as selectable text.

- Put the details in HTML text, using `tel:` and `mailto:` links.
- Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).
- Keep a contact form if preferred - but alongside the details, not instead of them.

**Verify.** Re-run check ANS-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://calendly.com/contact
- https://calendly.com/contact-us
- https://calendly.com/partners/contact
- https://calendly.com/contacts

### F-005 - Pages load many render-blocking or third-party scripts

**MEDIUM** - engagement / engagement gate - confidence medium (static) - check `ENG-005`

**Evidence.** 1 of 30 sampled pages load 9 render-blocking scripts from up to 3 third-party hosts, e.g. https://community.calendly.com/.

**Why it matters.** A render-blocking script stops the page being displayed until it has downloaded and executed, and each additional third-party host adds a DNS lookup and TLS handshake before that can even begin. The visitor sees nothing while this happens, and any one of those third parties being slow makes the brand's own site feel slow.

**Fix (medium priority, medium effort, engineering).** Defer non-essential scripts and cut the number of third-party origins.

- Add `defer` or `async` to every script that is not required for first paint.
- Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.
- Load remaining third-party scripts through a single tag manager, after first paint.
- Self-host small critical dependencies to remove a connection setup from the critical path.

**Verify.** Re-run check ENG-005 and confirm it no longer fires.

**Affected URLs (sample).**
- https://community.calendly.com/

### F-006 - A consent or subscription overlay may be gating the page content

**MEDIUM** - engagement / engagement gate - confidence low (heuristic) - check `ENG-010`

**Evidence.** Overlay markup appears on 30 of 30 sampled pages, and 2 of those pages carry under 120 words of body text, e.g. https://community.calendly.com/.

**Why it matters.** When content is only assembled after a consent choice, both the visitor and any machine reader see the overlay rather than the page. Visitors who decline or ignore the prompt get nothing, and the page's real content never enters the crawl.

**Fix (medium priority, medium effort, engineering).** Render page content beneath the consent layer rather than after it.

- Serve the full page content regardless of consent state, and gate only the tracking that genuinely requires consent.
- Never block the document behind the banner for non-browser clients.
- Delay newsletter and subscription prompts until the visitor has engaged, and never show them on first paint.

**Verify.** Re-run check ENG-010 and confirm it no longer fires.

**Affected URLs (sample).**
- https://community.calendly.com/
- https://calendly.com/partners/contact

### F-007 - Different pages share the same title

**LOW** - discoverability / extract gate - confidence high (static) - check `ANS-003`

**Evidence.** 2 of 30 sampled pages share 1 repeated title(s), e.g. "About Us | Calendly".

**Why it matters.** The title is how a page is named in a citation and is one of the strongest topic signals a retrieval system has. Identical titles make pages indistinguishable to it, so they compete with one another and the most relevant one is not reliably chosen.

**Fix (medium priority, low effort, content).** Give every page a unique title describing that page's specific subject.

- Template titles as `<specific page subject> - <brand>`.
- Derive the first part from the page's own H1 or product/article name, never from the site name alone.

*On unknown:*
- Set the values in the shared layout with a per-page override, so a new page cannot ship without them.

**Verify.** Re-run check ANS-003 and confirm it no longer fires.

**Affected URLs (sample).**
- https://calendly.com/about
- https://calendly.com/leadership

### F-008 - Article structured data is missing required fields

**LOW** - discoverability / extract gate - confidence high (static) - check `SDA-007`

**Evidence.** 12 Article nodes omit datePublished (12x), e.g. on https://calendly.com/customers.

**Why it matters.** The block is present and parses, so it appears to be working - but without datePublished it cannot answer what does this say, when was it said, and who said it. Consumers that require these fields discard the node entirely, leaving the page in the same position as one with no markup at all.

**Fix (medium priority, low effort, engineering).** Populate the required Article fields: datePublished.

- Add datePublished to the Article block, sourced from the same data the page renders.
- Leave a field out entirely rather than emitting an empty string or a placeholder - an empty value is treated as an assertion that the value is empty.
- Validate the output against the type's requirements as part of the build.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check SDA-007 and confirm it no longer fires.

**Affected URLs (sample).**
- https://calendly.com/customers
- https://calendly.com/customers
- https://calendly.com/customers
- https://calendly.com/customers
- https://calendly.com/customers

### F-009 - Some brand profiles linked on the site are missing from sameAs

**LOW** - discoverability / trust gate - confidence high (static) - check `ENT-004`

**Evidence.** 3 external profile(s) linked from the homepage are not declared in sameAs: https://facebook.com/calendly, https://instagram.com/calendly, https://linkedin.com/company/calendly.

**Why it matters.** A link in the footer is a hint; a sameAs entry is an assertion. Profiles left out of the declaration are not connected to the entity, so whatever they corroborate is not counted.

**Fix (medium priority, low effort, marketing).** Add the remaining profiles to the sameAs array.

- Add https://facebook.com/calendly, https://instagram.com/calendly, https://linkedin.com/company/calendly to the Organization sameAs list.
- Keep the two in sync whenever a profile is added or retired.

*On unknown:*
- Emit the markup from the shared page template so every page of that class inherits it, and build it from the same data the page renders.

**Verify.** Re-run check ENT-004 and confirm it no longer fires.

### F-010 - The site publishes few verifiable facts about the organisation itself

**LOW** - discoverability / trust gate - confidence medium (static) - check `ENT-006`

**Evidence.** Across 2 sampled page(s): no founding date, headquarters or 'based in' statement appears in the text.

**Why it matters.** A claim repeated consistently across many independent sources is treated as reliable; a claim that exists in one place is fragile. Before the wider web can repeat anything about an organisation, the organisation has to state it somewhere quotable. With no founding date, location, scale or named figures published, there is nothing for journalists, directories or assistants to corroborate - so the brand has no verifiable substance to attach to its name.

**Fix (low priority, medium effort, marketing).** Publish a facts page: what the organisation is, when and where it was founded, its scale, and who leads it.

- Create or expand an About page stating founding year, headquarters location, legal entity name, leadership and size, in plain sentences.
- Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - and keep them current.
- Add a press or newsroom page carrying the same facts in a form journalists can lift.
- Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they are machine-readable as well as readable.

**Verify.** Re-run check ENT-006 and confirm it no longer fires.

### F-011 - Navigation relies on repeated, undescriptive link text

**LOW** - engagement / engagement gate - confidence high (static) - check `ENG-003`

**Evidence.** The link text "learn more" appears 4 times across the sampled pages, alongside 1 such repeated labels in total.

**Why it matters.** Identical undescriptive labels force the visitor to work out where each one goes from its surroundings, which is slow on a screen and impossible for anyone navigating by links alone with a screen reader. The same text also gives search and retrieval systems no signal about what the linked page contains.

**Fix (medium priority, low effort, content).** Replace repeated generic labels with text naming the destination.

- Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.
- Where the visual design requires a short label, add an aria-label carrying the full description.

**Verify.** Re-run check ENG-003 and confirm it no longer fires.

### F-012 - AI training crawlers are blocked (recorded, not flagged as a defect)

**INFO** - discoverability / access gate - confidence high (static) - check `ACC-004`

**Evidence.** 1 training-corpus agents are disallowed: ccbot.

**Why it matters.** Training crawlers build the corpus a model learns from. Blocking them reduces the chance the brand is known from model memory, but does not affect live retrieval or citation. This is a policy choice with a known cost, not a misconfiguration.

**Fix (low priority, low effort, marketing).** No action required unless the brand wants to be recalled from model memory as well as cited.

- Keep this block if opting out of training is deliberate.
- If it was not deliberate, allow GPTBot, ClaudeBot, Google-Extended and CCBot to be learned from.

**Verify.** No verification needed; this is an observation.

## Proactive recommendations

*Improvements where no defect was detected - these strengthen discoverability and engagement rather than repairing something broken.*

### P-001 - Publish answers to the questions customers actually ask, in their words

**MEDIUM priority, medium effort.** Retrieval matches a user's question against candidate passages. Content already written as a question with a self-contained answer matches directly, while the same information as narrative prose has to be located inside a longer passage first. The wording matters as much as the format: customers ask in their own vocabulary, not the brand's product names.

- Collect the real questions from sales calls, support tickets and site search logs.
- Publish each with an answer that stands alone when quoted out of context.
- Use the customer's phrasing in the question; introduce internal product vocabulary in the answer.
- Mark the block up as FAQPage.

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
- `ANS-006` - site type is media_publisher; a published price is not expected
- `ANS-009` - site type is media_publisher; comparison and use-case pages are not expected
- `ENT-010` - site is not a local business; NAP consistency is not applicable
- `ENT-012` - only 1 declared profile(s) could be fetched; a reciprocity rate needs at least two
- `ENT-013` - no fetched profile carried enough text to compare against the site's own description
- `RND-002` - superseded by the measured render-gap comparison (RND-001)
- `RND-008` - no PDF documents were linked from the sampled pages
- `SDA-005` - only 1 careers page(s) lacked expected markup - too few to conclude a pattern
- `SDA-008` - site type is media_publisher; offer markup is not expected
