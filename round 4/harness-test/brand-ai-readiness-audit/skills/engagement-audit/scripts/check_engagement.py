#!/usr/bin/env python3
"""On-site engagement: why visitors who do arrive fail to orient, act or stay.

The framing that matters here: a visitor sent by an assistant does not arrive
on the homepage. They are deep-linked into whichever page answered their
question, they arrive with no brand context, and they have already had part of
their answer given to them elsewhere. A page that only makes sense to someone
who navigated in from the front door will lose them.

That makes several of these checks dual-purpose - the same defect that costs
engagement also costs discoverability - which is why the report links them to
their gate rather than treating engagement as a separate concern bolted on.

Measurement honesty: no browser was used to measure paint timings, so this
detector reports transport-level and markup-level proxies (response size,
blocking scripts, third-party count, server response time) and says so. It
never reports a Core Web Vitals figure it did not measure.

Usage:
    python check_engagement.py --cache ./cache
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from urllib.parse import urlsplit


def _bootstrap():
    here = os.path.dirname(os.path.abspath(__file__))
    while here != os.path.dirname(here):
        candidate = os.path.join(here, "lib")
        if os.path.isdir(os.path.join(candidate, "auditlib")):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            return
        here = os.path.dirname(here)
    sys.exit("auditlib not found: run this script from inside the marketplace directory")


_bootstrap()

from auditlib import cache as cache_mod, findings as F, schema, urls  # noqa: E402

CTA_TEXT = re.compile(
    r"\b(buy|order|add to (cart|bag|basket)|shop|subscribe|sign up|signup|get started|start (free|now)|"
    r"try (it |for )?free|book|reserve|schedule|request|contact|call|email|enquire|inquire|apply|"
    r"download|get (a )?quote|talk to|demo|join|donate|register)\b", re.I
)
VAGUE_CTA = re.compile(r"^\s*(learn more|read more|more|find out more|see more|click here|here|details|explore|discover|view)\s*[>»→]?\s*$", re.I)

MODAL_MARKER = re.compile(
    r"(cookie-?(banner|consent|notice|wall)|onetrust|cookiebot|klaro|didomi|usercentrics|quantcast|"
    r"trustarc|newsletter-?(popup|modal)|exit-?intent|subscribe-?modal|paywall|"
    r"\bmodal--?open\b|overlay--?active)", re.I
)
AUTOPLAY = re.compile(r"<(video|audio)[^>]*\bautoplay\b", re.I)
CHAT_WIDGET = re.compile(r"(intercom|drift\.com|tawk\.to|livechatinc|zendesk|crisp\.chat|hubspot.*conversations|tidio)", re.I)

SKIP_LINK = re.compile(r"skip (to|to the) (main|content|navigation)", re.I)

# Pages a visitor commonly needs to reach from anywhere.
KEY_DESTINATIONS = {
    "contact": re.compile(r"/(contact|get-in-touch|support)", re.I),
    "about": re.compile(r"/(about|company|who-we-are)", re.I),
    "pricing": re.compile(r"/(pricing|plans|price)", re.I),
}


def _internal_links(page):
    seen = set()
    for href, text, _rel, _node in page.doc.links():
        resolved = urls.normalize(href, base=page.url)
        if resolved and urls.same_site(resolved, page.url):
            seen.add((resolved, text.strip()))
    return seen


def _brand_tokens(cache):
    """Words that identify the brand, from its own declarations first.

    Deriving the brand name from the domain alone is wrong often enough to
    matter: plenty of organisations trade under a name their domain abbreviates
    or omits entirely. Missing the real name would make every page look
    context-free, which is a false positive on exactly the check this skill
    leads with.
    """
    names = []
    home = cache.home
    if home:
        for obj in schema.extract_objects(home.doc):
            if set(schema.types_of(obj)) & (schema.ORG_TYPES | {"WebSite"}):
                name = obj.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name)
        # The trailing segment of a title is nearly always the site name.
        title = home.doc.title
        if "|" in title or " - " in title:
            names.append(re.split(r"\s[|\-]\s", title)[-1])
    names.append(cache.site.split(".")[0])
    tokens = set()
    for name in names:
        for token in re.findall(r"[A-Za-z]{3,}", name):
            tokens.add(token.lower())
    # Words too generic to identify anything.
    return tokens - {"the", "and", "ltd", "inc", "llc", "gmbh", "limited", "company", "group", "www", "com"}


def check_standalone_context(cache, out, skipped):
    """The signature check for AI-referred traffic: does a deep page stand alone?

    An assistant links a visitor straight into an interior page. If that page
    never names the organisation, never says what it is, and offers no route
    onward, the visitor has landed somewhere with no context and typically
    leaves - so the discoverability win is thrown away at the door.
    """
    deep = [p for p in cache.html_pages() if not p.is_home and p.depth >= 1
            and p.page_type not in ("legal", "section_home")]
    if len(deep) < 3:
        skipped.append(F.skip("ENG-001", "fewer than 3 interior pages sampled"))
        return

    brand_tokens = _brand_tokens(cache)
    orphaned = []
    for page in deep:
        text = page.doc.main_text.lower()
        header_text = " ".join(n.text() for n in page.doc.all("header")).lower()
        names_brand = any(token in (text + " " + header_text + " " + page.doc.title.lower())
                          for token in brand_tokens)
        links = _internal_links(page)
        links_home = any(urls.path_of(u) in ("/", "") for u, _t in links)
        has_onward = len([1 for u, _t in links if u != page.url]) >= 3
        if not names_brand or not (links_home or has_onward):
            orphaned.append({
                "url": page.url, "names_brand": names_brand,
                "links_home": links_home, "onward_links": len(links),
            })

    if len(orphaned) < max(2, len(deep) * 0.3):
        return

    out.append(F.finding(
        "ENG-001", "Interior pages give a visitor arriving from outside no context",
        # Capped at high: "critical" is reserved for a defect that closes a
        # gate site-wide and removes the brand from AI answers entirely. A
        # context-free interior page loses visitors; it does not do that.
        min(F.apply_blast_radius("high", len(orphaned), len(deep)), "high",
            key=lambda s: -F.SEVERITY_RANK[s]), "engagement", "engagement",
        evidence=f"{len(orphaned)} of {len(deep)} sampled interior pages fail to name the organisation in their "
                 f"content or offer a clear route onward, e.g. {orphaned[0]['url']} "
                 f"(names brand: {orphaned[0]['names_brand']}, links home: {orphaned[0]['links_home']}, "
                 f"internal links: {orphaned[0]['onward_links']}).",
        mechanism="Visitors referred by an assistant land on the page that answered their question, not on the "
                  "homepage, and they arrive with no idea who the site belongs to. A page that assumes the visitor "
                  "has already seen the homepage gives them nothing to orient against and no next step, so the "
                  "session ends there. Every improvement to discoverability sends more traffic into this failure.",
        action_summary="Make every interior page self-contained: say who this is, and offer an obvious next step.",
        how=[
            "Ensure the organisation's name and a one-line description of what it does appear on every page, in "
            "content or a persistent header - not only in the logo image.",
            "Add a visible breadcrumb trail so the visitor can see where they have landed.",
            "End each page with a relevant next step: related pages, the product it belongs to, or a way to get in "
            "touch - chosen for that page's subject, not a generic footer.",
            "Test by opening an interior page in a fresh window: is it obvious whose site this is and what to do next?",
        ],
        effort="medium", owner="design", method="static",
        affected_urls=[o["url"] for o in orphaned][:10], affected_count=len(orphaned), sampled_count=len(deep),
        evidence_detail={"pages": orphaned[:8]},
        verify="Re-run check ENG-001; each interior page should name the brand and offer onward routes.",
    ))


def check_calls_to_action(cache, out, skipped):
    pages = [p for p in cache.html_pages() if p.page_type in
             ("home", "product", "pricing", "about", "case_study", "section_home")]
    if len(pages) < 2:
        skipped.append(F.skip("ENG-002", "too few conversion-relevant pages sampled"))
        return

    without_cta, vague_counts = [], Counter()
    for page in pages:
        link_texts = [t for _u, t in _internal_links(page)]
        button_texts = [n.text() for n in page.doc.all("button")]
        all_texts = [t for t in link_texts + button_texts if t]
        if not any(CTA_TEXT.search(t) for t in all_texts):
            without_cta.append(page.url)
        for text in all_texts:
            if VAGUE_CTA.match(text):
                vague_counts[text.strip().lower()] += 1

    if len(without_cta) >= max(2, len(pages) * 0.5):
        out.append(F.finding(
            "ENG-002", "Key pages offer no clear action to take",
            "high", "engagement", "engagement",
            evidence=f"{len(without_cta)} of {len(pages)} sampled conversion-relevant pages contain no link or "
                     f"button whose text describes an action, e.g. {without_cta[0]}.",
            mechanism="A visitor who has just read the answer to their question is at the point of highest intent. "
                      "If the page offers nothing to do next, that intent expires - and because assistant-referred "
                      "visitors arrive mid-journey rather than at the start, they are unusually likely to leave "
                      "rather than go looking for the next step themselves.",
            action_summary="Give each key page one obvious primary action, described by what it does.",
            how=[
                "Add a single visually primary action per page: 'Book a site survey', 'See pricing', 'Start a trial'.",
                "Label it with the outcome, not the mechanism - 'Get a quote' rather than 'Submit'.",
                "Place one instance within the first screen and repeat it at the end of longer pages.",
            ],
            effort="low", owner="design", method="static",
            affected_urls=without_cta[:10], affected_count=len(without_cta), sampled_count=len(pages),
        ))

    repeated_vague = [text for text, count in vague_counts.items() if count >= 4]
    if repeated_vague:
        worst = max(vague_counts.items(), key=lambda kv: kv[1])
        out.append(F.finding(
            "ENG-003", "Navigation relies on repeated, undescriptive link text",
            "low", "engagement", "engagement",
            evidence=f"The link text \"{worst[0]}\" appears {worst[1]} times across the sampled pages, alongside "
                     f"{len(repeated_vague)} such repeated labels in total.",
            mechanism="Identical undescriptive labels force the visitor to work out where each one goes from its "
                      "surroundings, which is slow on a screen and impossible for anyone navigating by links alone "
                      "with a screen reader. The same text also gives search and retrieval systems no signal about "
                      "what the linked page contains.",
            action_summary="Replace repeated generic labels with text naming the destination.",
            how=["Rewrite as the destination: 'Read the AMR-200 specification' rather than 'Learn more'.",
                 "Where the visual design requires a short label, add an aria-label carrying the full description."],
            effort="low", owner="content", method="static",
            affected_count=sum(vague_counts.values()), sampled_count=len(pages),
            evidence_detail={"labels": dict(vague_counts.most_common(6))},
        ))


def check_weight_and_speed(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return

    heavy, slow, third_party_heavy = [], [], []
    for page in pages:
        scripts = page.doc.scripts()
        blocking = [s for s in scripts if s["src"] and not s["async"] and not s["defer"] and not s["module"]]
        hosts = set()
        for script in scripts:
            if script["src"].startswith("http"):
                host = urlsplit(script["src"]).netloc.lower()
                if host and not urls.same_site(script["src"], page.url):
                    hosts.add(host)
        if page.bytes > 1_200_000:
            heavy.append({"url": page.url, "kb": page.bytes // 1024})
        if len(blocking) >= 8:
            third_party_heavy.append({"url": page.url, "blocking": len(blocking), "third_party_hosts": len(hosts)})
        elif len(hosts) >= 12:
            third_party_heavy.append({"url": page.url, "blocking": len(blocking), "third_party_hosts": len(hosts)})
        if page.elapsed > 2.5:
            slow.append({"url": page.url, "seconds": round(page.elapsed, 2)})

    if heavy:
        out.append(F.finding(
            "ENG-004", "Some pages ship a very large HTML document",
            "medium", "engagement", "engagement",
            evidence=f"{len(heavy)} of {len(pages)} sampled pages return more than 1.2 MB of HTML alone, e.g. "
                     f"{heavy[0]['url']} at {heavy[0]['kb']} KB (before images, scripts and stylesheets).",
            mechanism="The HTML document blocks everything else: nothing renders until it has arrived and been "
                      "parsed. On a mobile connection a document this size costs seconds before the first pixel, and "
                      "abandonment climbs steeply with every second of delay.",
            action_summary="Reduce document size by paginating, deferring and trimming inlined data.",
            how=["Move large inlined JSON, base64 images and repeated markup out of the document.",
                 "Paginate or lazy-load long lists rather than emitting every item.",
                 "Serve compressed responses (gzip or brotli) and confirm the header is present."],
            effort="medium", owner="engineering", method="static", confidence="medium",
            affected_urls=[h["url"] for h in heavy][:10], affected_count=len(heavy), sampled_count=len(pages),
            evidence_detail={"pages": heavy[:8],
                             "method_note": "Measured from the HTML response only; sub-resources were not fetched."},
        ))

    if third_party_heavy:
        worst = max(third_party_heavy, key=lambda t: (t["blocking"], t["third_party_hosts"]))
        out.append(F.finding(
            "ENG-005", "Pages load many render-blocking or third-party scripts",
            "medium", "engagement", "engagement",
            evidence=f"{len(third_party_heavy)} of {len(pages)} sampled pages load {worst['blocking']} "
                     f"render-blocking scripts from up to {worst['third_party_hosts']} third-party hosts, e.g. "
                     f"{worst['url']}.",
            mechanism="A render-blocking script stops the page being displayed until it has downloaded and executed, "
                      "and each additional third-party host adds a DNS lookup and TLS handshake before that can even "
                      "begin. The visitor sees nothing while this happens, and any one of those third parties being "
                      "slow makes the brand's own site feel slow.",
            action_summary="Defer non-essential scripts and cut the number of third-party origins.",
            how=["Add `defer` or `async` to every script that is not required for first paint.",
                 "Audit the tag list and remove anything nobody is acting on - marketing tags accumulate silently.",
                 "Load remaining third-party scripts through a single tag manager, after first paint.",
                 "Self-host small critical dependencies to remove a connection setup from the critical path."],
            effort="medium", owner="engineering", method="static", confidence="medium",
            affected_urls=[t["url"] for t in third_party_heavy][:10],
            affected_count=len(third_party_heavy), sampled_count=len(pages),
        ))

    if len(slow) >= max(2, len(pages) * 0.3):
        out.append(F.finding(
            "ENG-006", "The server is slow to return pages",
            "medium", "engagement", "engagement",
            evidence=f"{len(slow)} of {len(pages)} sampled pages took over 2.5s to return, e.g. "
                     f"{slow[0]['url']} at {slow[0]['seconds']}s.",
            mechanism="Server response time precedes everything the browser can do, so it is added to every visitor's "
                      "wait regardless of how well the front end is built. Slow responses also reduce how much of a "
                      "site a crawler fetches in a session, which quietly shrinks how much of it is discoverable.",
            action_summary="Reduce server response time with caching at the edge.",
            how=["Serve cacheable pages from a CDN so most requests never reach the origin.",
                 "Profile the slowest templates; uncached database queries in page rendering are the usual cause.",
                 "Set explicit Cache-Control headers so intermediaries can cache."],
            effort="medium", owner="engineering", method="static", confidence="medium",
            affected_urls=[s["url"] for s in slow][:10], affected_count=len(slow), sampled_count=len(pages),
            evidence_detail={"pages": slow[:8],
                             "method_note": "Wall-clock time for the full HTTP response from this auditor's network "
                                            "location; not a substitute for field measurement."},
        ))


def check_mobile(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return
    no_viewport = [p.url for p in pages if not p.doc.meta().get("viewport")]
    if len(no_viewport) >= max(2, len(pages) * 0.5):
        out.append(F.finding(
            "ENG-007", "Pages do not declare a mobile viewport",
            "high", "engagement", "engagement",
            evidence=f"{len(no_viewport)} of {len(pages)} sampled pages have no viewport meta tag.",
            mechanism="Without a viewport declaration, mobile browsers render the page at desktop width and scale it "
                      "down, so text is unreadable and controls are too small to hit. Most assistant-referred traffic "
                      "arrives on mobile, which makes this the first experience many visitors have of the brand.",
            action_summary="Add a responsive viewport meta tag and verify the layout adapts.",
            how=["Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">` to the base template.",
                 "Confirm the layout reflows rather than requiring horizontal scrolling.",
                 "Check that tap targets are large enough and body text is at least 16px."],
            effort="low", owner="engineering", method="static",
            affected_urls=no_viewport[:10], affected_count=len(no_viewport), sampled_count=len(pages),
        ))

    images = [(p, img) for p in pages for img in p.doc.images() if img["src"]]
    if len(images) >= 10:
        undimensioned = [i for _p, i in images if not i["width"] or not i["height"]]
        not_lazy = [i for _p, i in images if i["loading"] != "lazy"]
        if len(undimensioned) / len(images) > 0.7 and len(not_lazy) / len(images) > 0.7:
            out.append(F.finding(
                "ENG-008", "Images have no dimensions and are not lazy-loaded",
                "low", "engagement", "engagement",
                evidence=f"{len(undimensioned)} of {len(images)} sampled images declare no width/height and "
                         f"{len(not_lazy)} do not use loading=\"lazy\".",
                mechanism="Without declared dimensions the browser cannot reserve space, so content jumps as images "
                          "arrive and visitors tap the wrong thing. Without lazy loading, images far below the fold "
                          "compete for bandwidth with content the visitor is waiting to read.",
                action_summary="Declare intrinsic width and height on images and lazy-load those below the fold.",
                how=["Set width and height attributes matching the image's intrinsic aspect ratio.",
                     "Add `loading=\"lazy\"` to images below the fold, and leave it off the main hero image.",
                     "Serve modern formats with responsive `srcset` sizes."],
                effort="low", owner="engineering", method="static",
                affected_count=len(undimensioned), sampled_count=len(images),
            ))


def check_interruptions(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return
    modal_pages, autoplay_pages, chat_pages = [], [], []
    for page in pages:
        html = page.html
        if MODAL_MARKER.search(html):
            modal_pages.append(page.url)
        if AUTOPLAY.search(html):
            autoplay_pages.append(page.url)
        if CHAT_WIDGET.search(html):
            chat_pages.append(page.url)

    if autoplay_pages:
        out.append(F.finding(
            "ENG-009", "Media is set to play automatically",
            "medium", "engagement", "engagement",
            evidence=f"{len(autoplay_pages)} of {len(pages)} sampled pages contain a video or audio element with the "
                     f"autoplay attribute, e.g. {autoplay_pages[0]}.",
            mechanism="Autoplaying media consumes bandwidth before the visitor has decided to watch anything, delays "
                      "the content they came for, and - where sound is involved - is a common reason for closing a "
                      "tab immediately.",
            action_summary="Require an explicit play action, or at minimum keep autoplay muted and deferred.",
            how=["Remove autoplay and show a poster image with a visible play control.",
                 "If a background video is essential to the design, keep it muted, short, and loaded after the "
                 "primary content.",
                 "Respect prefers-reduced-motion."],
            effort="low", owner="design", method="static",
            affected_urls=autoplay_pages[:10], affected_count=len(autoplay_pages), sampled_count=len(pages),
        ))

    # A consent banner is a legal requirement in many jurisdictions, so its mere
    # presence is never a finding. It only becomes one when it is paired with
    # evidence that content is withheld behind it.
    if modal_pages and len(modal_pages) >= len(pages) * 0.8:
        thin_behind = [p for p in pages if p.doc.main_word_count < 120]
        if thin_behind:
            out.append(F.finding(
                "ENG-010", "A consent or subscription overlay may be gating the page content",
                "medium", "engagement", "engagement",
                evidence=f"Overlay markup appears on {len(modal_pages)} of {len(pages)} sampled pages, and "
                         f"{len(thin_behind)} of those pages carry under 120 words of body text, e.g. "
                         f"{thin_behind[0].url}.",
                mechanism="When content is only assembled after a consent choice, both the visitor and any machine "
                          "reader see the overlay rather than the page. Visitors who decline or ignore the prompt "
                          "get nothing, and the page's real content never enters the crawl.",
                action_summary="Render page content beneath the consent layer rather than after it.",
                how=["Serve the full page content regardless of consent state, and gate only the tracking that "
                     "genuinely requires consent.",
                     "Never block the document behind the banner for non-browser clients.",
                     "Delay newsletter and subscription prompts until the visitor has engaged, and never show them "
                     "on first paint."],
                effort="medium", owner="engineering", method="heuristic", confidence="low",
                affected_urls=[p.url for p in thin_behind][:10],
                affected_count=len(thin_behind), sampled_count=len(pages),
            ))


def check_dead_ends(cache, out, skipped):
    pages = [p for p in cache.html_pages() if p.page_type not in ("legal",)]
    if len(pages) < 4:
        skipped.append(F.skip("ENG-011", "too few pages sampled to assess internal linking"))
        return
    dead_ends = []
    for page in pages:
        onward = {u for u, _t in _internal_links(page) if u != page.url}
        if len(onward) <= 2:
            dead_ends.append({"url": page.url, "links": len(onward)})
    if len(dead_ends) >= max(2, len(pages) * 0.3):
        out.append(F.finding(
            "ENG-011", "Pages are dead ends with almost no onward links",
            "medium", "engagement", "engagement",
            evidence=f"{len(dead_ends)} of {len(pages)} sampled pages contain 2 or fewer links to other pages on "
                     f"the site, e.g. {dead_ends[0]['url']} has {dead_ends[0]['links']}.",
            mechanism="A visitor who finishes a page with nowhere to go leaves. Internal links are also how "
                      "discovery propagates: pages that nothing links onward from are crawled less and understood as "
                      "less connected to the rest of the site, so the deeper content stays invisible.",
            action_summary="Add contextual internal links and a relevant next step to every page.",
            how=["Link from body text to the related products, articles or documentation the page mentions.",
                 "Add a 'related' block chosen by subject rather than by recency.",
                 "Ensure the primary navigation is present in the HTML of every page, not injected by script."],
            effort="medium", owner="content", method="static",
            affected_urls=[d["url"] for d in dead_ends][:10], affected_count=len(dead_ends), sampled_count=len(pages),
        ))


def check_navigation_reach(cache, out, skipped):
    home = cache.home
    if not home:
        return
    home_links = {u for u, _t in _internal_links(home)}
    if len(home_links) < 3:
        skipped.append(F.skip("ENG-012", "homepage exposes too few links to assess navigation reach"))
        return
    known = {p.url for p in cache.html_pages()} | set(cache.extras.get("sitemap_sample", []))
    missing = []
    for name, pattern in KEY_DESTINATIONS.items():
        exists = any(pattern.search(u) for u in known)
        linked = any(pattern.search(u) for u in home_links)
        if exists and not linked:
            missing.append(name)
    if missing:
        out.append(F.finding(
            "ENG-013", "Key pages exist but are not linked from the homepage",
            "medium", "engagement", "engagement",
            evidence=f"The site has {', '.join(missing)} page(s) that the homepage does not link to, among "
                     f"{len(home_links)} homepage links.",
            mechanism="A page that exists but is not reachable from the front door is effectively hidden from "
                      "visitors browsing the site, and receives little of the internal linking that signals its "
                      "importance. The pages this most often affects - contact, pricing - are the ones visitors go "
                      "looking for first.",
            action_summary="Link the key destinations from the primary navigation or footer.",
            how=[f"Add links to the {', '.join(missing)} page(s) in the header navigation or footer.",
                 "Make sure the navigation is present in the served HTML, not added by script after load."],
            effort="low", owner="design", method="static",
            affected_count=len(missing), sampled_count=1,
            evidence_detail={"missing_from_nav": missing},
        ))


def check_forms_and_accessibility(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return

    unlabelled_total, field_total, long_forms = 0, 0, []
    for page in pages:
        for form in page.doc.forms():
            if form["is_search"] or form["visible_fields"] == 0:
                continue
            field_total += form["visible_fields"]
            unlabelled_total += max(0, form["visible_fields"] - form["labelled_fields"])
            if form["required_fields"] >= 7:
                long_forms.append({"url": page.url, "required": form["required_fields"],
                                   "fields": form["visible_fields"]})

    if field_total and unlabelled_total / field_total > 0.4 and unlabelled_total >= 3:
        out.append(F.finding(
            "ENG-012", "Form fields have no programmatic labels",
            "medium", "engagement", "engagement",
            evidence=f"{unlabelled_total} of {field_total} visible form fields across the sampled pages have no "
                     "associated <label>, aria-label or aria-labelledby.",
            mechanism="An unlabelled field is unusable with a screen reader and ambiguous with autofill, so the "
                      "visitors most likely to abandon are the ones who most need the form to work. Placeholder text "
                      "is not a label: it disappears as soon as typing begins.",
            action_summary="Give every form control a persistent, programmatically associated label.",
            how=["Associate a visible <label for=\"...\"> with each input, select and textarea.",
                 "Keep the label visible while the field is being filled - do not rely on placeholder text.",
                 "Where the design has no room for a label, use aria-label carrying the same text."],
            effort="low", owner="engineering", method="static",
            affected_count=unlabelled_total, sampled_count=field_total,
        ))

    if long_forms:
        out.append(F.finding(
            "ENG-014", "Forms demand a large number of required fields",
            "medium", "engagement", "engagement",
            evidence=f"{len(long_forms)} form(s) require {long_forms[0]['required']} or more fields, e.g. on "
                     f"{long_forms[0]['url']} ({long_forms[0]['required']} required of "
                     f"{long_forms[0]['fields']} fields).",
            mechanism="Every required field is a reason to stop. A visitor arriving from an assistant is early in "
                      "their relationship with the brand and has the least tolerance for being asked for information "
                      "before receiving anything - completion falls sharply with each additional mandatory field.",
            action_summary="Ask only for what is needed now, and collect the rest later.",
            how=["Reduce required fields to the minimum that lets someone respond - often name and email.",
                 "Make the remainder optional, or gather them in a follow-up once there is a relationship.",
                 "Never require a phone number to start a conversation unless the response is by phone."],
            effort="low", owner="marketing", method="static",
            affected_urls=[f["url"] for f in long_forms][:10],
            affected_count=len(long_forms), sampled_count=len(pages),
        ))

    no_skip = [p.url for p in pages
               if not any(SKIP_LINK.search(t) for _u, t in _internal_links(p))
               and not any(SKIP_LINK.search(a.text()) for a in p.doc.all("a"))]
    if len(no_skip) == len(pages) and len(pages) >= 4:
        out.append(F.finding(
            "ENG-015", "No skip-to-content link is provided",
            "low", "engagement", "engagement",
            evidence=f"None of the {len(pages)} sampled pages offers a skip-to-content link.",
            mechanism="Keyboard and screen-reader users must otherwise traverse the entire navigation on every page "
                      "before reaching the content. It is a small omission with a disproportionate cost for the "
                      "visitors it affects.",
            action_summary="Add a skip link as the first focusable element on every page.",
            how=["Add `<a class=\"skip-link\" href=\"#main\">Skip to main content</a>` as the first element in <body>.",
                 "Give the main content container the matching id and make the link visible on focus."],
            effort="low", owner="engineering", method="static",
            affected_count=len(no_skip), sampled_count=len(pages),
        ))


def check_measurement(cache, out, skipped):
    """You cannot improve engagement you are not measuring."""
    if cache.profile.get("analytics"):
        return
    if len(cache.html_pages()) < 3:
        skipped.append(F.skip("ENG-016", "too few pages sampled to conclude analytics are absent"))
        return
    out.append(F.finding(
        "ENG-016", "No analytics instrumentation was detected",
        "info", "engagement", "engagement",
        evidence=f"No recognised analytics or tag-management script was found across "
                 f"{len(cache.html_pages())} sampled pages.",
        mechanism="Without measurement there is no way to tell whether any engagement change helped, and no way to "
                  "see assistant-referred traffic arriving on deep pages - which is the traffic this audit's "
                  "discoverability fixes are intended to produce.",
        action_summary="Add privacy-respecting analytics and segment traffic by referrer so AI referrals are visible.",
        how=[
            "Install an analytics tool appropriate to the site's privacy posture and consent obligations.",
            "Create a segment for assistant referrers so the effect of discoverability work can be observed "
            "separately from search.",
            "Track landing page and onward navigation, since deep-linked arrivals are the population these "
            "engagement findings concern.",
        ],
        effort="low", owner="marketing", method="static", confidence="medium",
        sampled_count=len(cache.html_pages()),
    ))


def main():
    ap = argparse.ArgumentParser(description="On-site engagement checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    notes = ["engagement timings are transport-level proxies measured from the audit's network location; "
             "no browser paint or field measurement was performed"]
    for check in (check_standalone_context, check_calls_to_action, check_weight_and_speed,
                  check_mobile, check_interruptions, check_dead_ends,
                  check_navigation_reach, check_forms_and_accessibility, check_measurement):
        try:
            check(cache, out, skipped)
        except Exception as e:
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped, notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
