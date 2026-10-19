#!/usr/bin/env python3
"""Gate 2 - Render. Can a machine read what a human sees?

A page that looks complete in a browser is frequently near-empty to the systems
that decide what gets cited, because most AI retrieval fetchers take the raw
HTTP response and do not execute JavaScript. The same is true of facts drawn as
images, embedded in iframes, or shipped only inside a PDF.

Every measurement here is made against the *raw response body* - the bytes a
fetcher actually receives - and, where a browser engine was available, compared
against the executed DOM. When no engine was available the comparison degrades
to static signals and every affected finding is labelled `method: heuristic`
with reduced confidence, never presented as a measurement that did not happen.

Usage:
    python check_render.py --cache ./cache
"""

from __future__ import annotations

import argparse
import os
import re
import sys


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

from auditlib import cache as cache_mod, findings as F, htmlx, urls  # noqa: E402

# Markup that only ships with a client-rendering framework.
SPA_SHELL = re.compile(
    r"<div[^>]+id=[\"'](root|app|__next|__nuxt|q-app|main-app)[\"'][^>]*>\s*</div>|"
    r"<app-root\s*>\s*</app-root>|<div[^>]+data-reactroot[^>]*>\s*</div>",
    re.I,
)
FRAMEWORK_MARKER = re.compile(
    r"/_next/static/|__NEXT_DATA__|self\.__next_f|/_nuxt/|__NUXT|ng-version=|"
    r"data-reactroot|__sveltekit_|___gatsby|/_app/immutable/|vue\.runtime|"
    r"webpackChunk|requirejs|systemjs",
    re.I,
)
JS_REQUIRED_TEXT = re.compile(
    r"(enable javascript|javascript is (required|disabled)|turn on javascript|"
    r"requires javascript|doesn'?t work (properly )?without javascript|"
    r"you need to enable javascript)",
    re.I,
)

# Filenames that usually carry words rather than decoration. A missing alt on
# one of these means the words are simply gone for a text reader.
TEXTY_IMAGE = re.compile(
    r"(banner|infographic|chart|graph|diagram|table|price|pricing|menu|poster|flyer|"
    r"screenshot|quote|testimonial|stat|figure|slide|comparison|spec|leaflet|brochure|"
    r"timeline|roadmap|schedule|hours)",
    re.I,
)

# Types where a thin page is a real defect rather than a design choice.
CONTENT_TYPES = {"home", "about", "pricing", "product", "article", "docs", "faq", "case_study", "section_home"}

# Floors are deliberately low. They mark pages with essentially nothing to
# quote, not pages that could be longer - a concise page that states its facts
# clearly is a good page, and flagging it would be a false positive.
MIN_WORDS_BY_TYPE = {
    "home": 90, "about": 90, "pricing": 70, "product": 70,
    "article": 200, "docs": 120, "faq": 80, "case_study": 120, "section_home": 80,
}


def _raw_words(page) -> int:
    return len(htmlx.strip_tags(page.html).split())


def check_render_gap(cache, out, skipped):
    """The measured comparison, when a browser engine was available."""
    if not cache.has_capability("javascript_rendering"):
        skipped.append(F.skip("RND-001", "no JavaScript engine available; render gap estimated statically by RND-002"))
        return

    compared, gaps = 0, []
    for page in cache.html_pages():
        rendered_doc = page.rendered_doc
        if rendered_doc is None:
            continue
        compared += 1
        # Compare like with like: the same extractor on both sides, over main
        # content only. Whole-page text measured furniture instead - JavaScript
        # routinely expands nav menus and injects banners without adding a
        # single quotable word, which reads as a render gap on a fully
        # server-rendered page. main_text is also what an extractive system
        # would actually quote, which is what this check claims to be about.
        raw_words = page.doc.main_word_count
        rendered_words = rendered_doc.main_word_count
        if rendered_words < 80:
            # Nothing meaningful on the page either way - not a render gap.
            # Application shells with almost no prose are left to RND-003.
            continue
        coverage = raw_words / rendered_words
        if coverage < 0.75:
            gaps.append({"url": page.url, "raw_words": raw_words,
                         "rendered_words": rendered_words, "coverage": round(coverage, 3)})

    if not compared:
        skipped.append(F.skip("RND-001", "renderer produced no comparable pages"))
        return
    if not gaps:
        return

    worst = min(g["coverage"] for g in gaps)
    severity = "critical" if worst < 0.3 else "high" if worst < 0.6 else "medium"
    severity = F.apply_blast_radius(severity, len(gaps), compared)
    example = sorted(gaps, key=lambda g: g["coverage"])[0]
    out.append(F.finding(
        "RND-001", "Page content is assembled by JavaScript and is missing from the server response",
        severity, "discoverability", "render",
        evidence=f"On {len(gaps)} of {compared} rendered pages the raw HTML contains less text than the browser DOM; "
                 f"worst case {example['url']} ships {example['raw_words']} words against "
                 f"{example['rendered_words']} after JavaScript ({round(example['coverage'] * 100)}% coverage).",
        mechanism="Most AI retrieval fetchers and many crawlers read the HTTP response without running JavaScript. "
                  "Whatever the client assembles afterwards does not exist for them, so the page is fetched "
                  "successfully and found to contain almost nothing worth quoting - the site is reachable and still "
                  "uncitable.",
        action_summary="Server-render or pre-render the content that currently only appears after JavaScript runs.",
        how=[
            "Move the primary content - headings, body copy, prices, specifications, contact details - into the "
            "server-rendered HTML so it is present in the first response.",
            "Use the framework's server-side rendering or static generation mode for these routes rather than "
            "client-only rendering.",
            "Where full SSR is impractical, pre-render the top templates to static HTML and hydrate afterwards.",
            "Verify with `curl -s <url> | wc -w`: the raw response should contain the page's real text.",
        ],
        effort="high", owner="engineering", method="rendered", confidence="high",
        affected_urls=[g["url"] for g in gaps], affected_count=len(gaps), sampled_count=compared,
        evidence_detail={"gaps": gaps[:10]},
        verify="Re-run check RND-001; raw-to-rendered word coverage should exceed 0.75 on every content page.",
    ))


def check_static_shell(cache, out, skipped):
    """Static-signal estimate of the same defect, for runs with no engine.

    Deliberately conservative: it fires only when the response is large enough
    to be carrying content but contains almost no text, which is the signature
    of a shipped application shell rather than of a genuinely short page.
    """
    if cache.has_capability("javascript_rendering"):
        skipped.append(F.skip("RND-002", "superseded by the measured render-gap comparison (RND-001)"))
        return

    pages = [p for p in cache.html_pages() if p.page_type in CONTENT_TYPES]
    if not pages:
        skipped.append(F.skip("RND-002", "no content-bearing pages were sampled"))
        return

    shells, payload_only = [], []
    for page in pages:
        raw_words = _raw_words(page)
        html = page.html
        has_framework = bool(FRAMEWORK_MARKER.search(html))
        has_shell = bool(SPA_SHELL.search(html))
        payloads = page.doc.inline_json_payloads()
        payload_bytes = sum(payloads.values())

        # A big response carrying almost no prose is the tell. The byte floor
        # keeps genuinely small pages (a one-line contact page) out of it.
        if raw_words < 60 and page.bytes > 15000 and (has_framework or has_shell):
            shells.append({"url": page.url, "raw_words": raw_words, "bytes": page.bytes,
                           "shell_element": has_shell, "payload_bytes": payload_bytes})
        elif payload_bytes > 20000 and raw_words < 250 and payload_bytes > page.bytes * 0.25:
            payload_only.append({"url": page.url, "raw_words": raw_words,
                                 "payload_bytes": payload_bytes, "keys": sorted(payloads)})

    if shells:
        severity = F.apply_blast_radius("critical", len(shells), len(pages))
        example = shells[0]
        out.append(F.finding(
            "RND-002", "Pages are served as an empty JavaScript application shell",
            severity, "discoverability", "render",
            evidence=f"{len(shells)} of {len(pages)} sampled content pages return a {example['bytes'] // 1024} KB "
                     f"response containing only {example['raw_words']} words of text alongside client-framework "
                     f"markers, e.g. {example['url']}.",
            mechanism="The server sends an application shell and the content is fetched and assembled in the browser. "
                      "A fetcher that does not execute JavaScript receives the shell - a page that is technically "
                      "200 OK and effectively blank - so nothing on it can be indexed, retrieved or quoted.",
            action_summary="Server-render the content routes, or pre-render them to static HTML.",
            how=[
                "Switch these routes to server-side rendering or static generation in the framework already in use.",
                "Confirm the fix at the transport layer, not in the browser: `curl -s <url>` must contain the page text.",
                "If the application cannot be server-rendered, publish a pre-rendered static copy of the highest-value "
                "pages and serve it to non-browser clients from the edge.",
            ],
            effort="high", owner="engineering",
            method="heuristic", confidence="medium",
            affected_urls=[s["url"] for s in shells], affected_count=len(shells), sampled_count=len(pages),
            evidence_detail={"shells": shells[:10],
                             "note": "No browser engine was available, so this is inferred from response size, "
                                     "text volume and framework markers rather than measured against an executed DOM."},
            verify="Install a browser engine and re-run; RND-001 will measure the gap exactly.",
        ))

    if payload_only:
        out.append(F.finding(
            "RND-003", "Page content ships as a JSON payload rather than as readable HTML",
            "high", "discoverability", "render",
            evidence=f"{len(payload_only)} sampled pages carry "
                     f"{payload_only[0]['payload_bytes'] // 1024} KB of inline JSON hydration data "
                     f"({', '.join(payload_only[0]['keys'][:3])}) but only {payload_only[0]['raw_words']} words "
                     f"of readable text, e.g. {payload_only[0]['url']}.",
            mechanism="The content is genuinely present in the response, but as serialised application state rather "
                      "than as prose. Text extractors read the visible document, not the framework's data island, so "
                      "the facts are shipped and still unreadable. This is a better position than an empty shell - "
                      "the data is already there - and usually only needs the template to render it.",
            action_summary="Render the data that is already in the payload into the HTML body.",
            how=[
                "Render the fields the payload already contains - headings, descriptions, prices, dates - into "
                "server-side HTML instead of leaving them for client hydration.",
                "Add the corresponding JSON-LD block from the same data, so the facts are both readable and typed.",
            ],
            effort="medium", owner="engineering", method="static", confidence="medium",
            affected_urls=[p["url"] for p in payload_only], affected_count=len(payload_only),
            sampled_count=len(pages),
            evidence_detail={"pages": payload_only[:8]},
        ))


def check_noscript_dependency(cache, out, skipped):
    pages = cache.html_pages()
    hits = []
    for page in pages:
        for node in page.doc.all("noscript"):
            text = node.text(skip_invisible=False)
            if JS_REQUIRED_TEXT.search(text):
                hits.append({"url": page.url, "text": text[:160]})
                break
    if hits:
        out.append(F.finding(
            "RND-004", "The site tells non-JavaScript clients that it will not work",
            "medium", "discoverability", "render",
            evidence=f"{len(hits)} of {len(pages)} sampled pages contain a <noscript> block stating JavaScript is "
                     f"required, e.g. \"{hits[0]['text'][:90]}\".",
            mechanism="This message is the fallback a non-JavaScript client actually receives. Where it appears, it "
                      "confirms the page's real content is unavailable without script execution - and for a text "
                      "extractor, this sentence may be the most prominent text on the page.",
            action_summary="Provide real content in <noscript>, or server-render the page so the fallback is unnecessary.",
            how=["Server-render the primary content (see RND-001/RND-002).",
                 "Until then, put the page's core text - headline, description, key facts, links - inside <noscript> "
                 "so something meaningful is readable."],
            effort="medium", owner="engineering", method="static",
            affected_urls=[h["url"] for h in hits], affected_count=len(hits), sampled_count=len(pages),
        ))


def check_thin_content(cache, out, skipped):
    pages = [p for p in cache.html_pages() if p.page_type in CONTENT_TYPES]
    if not pages:
        skipped.append(F.skip("RND-005", "no content-bearing pages were sampled"))
        return
    # Suppressed when a shell/render-gap finding already explains the emptiness:
    # reporting both would double-count one root cause.
    if any(f["check_id"] in ("RND-001", "RND-002") for f in out):
        skipped.append(F.skip("RND-005", "thin text is already explained by the render-gap finding"))
        return

    thin = []
    for page in pages:
        words = page.doc.main_word_count
        floor = MIN_WORDS_BY_TYPE.get(page.page_type, 100)
        if words < floor:
            thin.append({"url": page.url, "type": page.page_type, "words": words, "floor": floor})
    if len(thin) < max(2, len(pages) * 0.3):
        return
    out.append(F.finding(
        "RND-005", "Key pages contain very little extractable text",
        F.apply_blast_radius("medium", len(thin), len(pages)), "discoverability", "render",
        evidence=f"{len(thin)} of {len(pages)} content pages fall below the expected body-text volume for their "
                 f"type, e.g. {thin[0]['url']} has {thin[0]['words']} words of body text "
                 f"(expected at least {thin[0]['floor']} for a {thin[0]['type']} page).",
        mechanism="Retrieval systems select passages, and a passage has to exist to be selected. Pages that carry "
                  "their meaning in imagery, layout and implication give an extractor nothing to lift, so a "
                  "competitor's more explicit page is quoted instead - even when this brand is the better answer.",
        action_summary="State the page's substance in body text, not only in visuals and layout.",
        how=["Write out what the page communicates: what this is, who it is for, what it costs, what happens next.",
             "Convert facts currently carried by images or diagrams into text or a table alongside them.",
             "Aim for explicit declarative sentences - an extractor quotes sentences, not impressions."],
        effort="medium", owner="content", method="static",
        affected_urls=[t["url"] for t in thin], affected_count=len(thin), sampled_count=len(pages),
        evidence_detail={"pages": thin[:10]},
    ))


def check_images(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return

    total, missing_alt, texty_missing, heading_images = 0, [], [], []
    for page in pages:
        for image in page.doc.images():
            if not image["src"]:
                continue
            total += 1
            alt = (image["alt"] or "").strip()
            has_text = bool(alt)
            if not has_text:
                missing_alt.append({"url": page.url, "src": image["src"][:120]})
                if TEXTY_IMAGE.search(image["src"]):
                    texty_missing.append({"url": page.url, "src": image["src"][:120]})
                if image["in_heading"]:
                    heading_images.append({"url": page.url, "src": image["src"][:120]})

    if not total:
        skipped.append(F.skip("RND-006", "no images found on the sampled pages"))
        return

    if texty_missing or heading_images:
        cases = texty_missing + [h for h in heading_images if h not in texty_missing]
        out.append(F.finding(
            "RND-006", "Facts appear to be locked inside images with no text equivalent",
            "high", "discoverability", "render",
            evidence=f"{len(cases)} images whose filename or position indicates they carry words "
                     f"(charts, price lists, banners, heading graphics) have no alt text, e.g. "
                     f"{cases[0]['src']} on {cases[0]['url']}.",
            mechanism="Text drawn inside an image is invisible to every text-based reader. When a price list, an "
                      "opening-hours table or a specification chart exists only as a picture, the facts on it cannot "
                      "be extracted, cited, or read by assistive technology - the information is published and "
                      "simultaneously unavailable.",
            action_summary="Publish the facts these images carry as real text, and give every image meaningful alt text.",
            how=[
                "For each image carrying data - prices, hours, specifications, comparisons - add the same content as "
                "HTML text or a table next to it. The image becomes the illustration, not the source.",
                "Write alt text that states what the image communicates, not what it depicts.",
                "Where an image is purely decorative, use alt=\"\" so readers skip it deliberately.",
            ],
            effort="medium", owner="content", method="static",
            affected_urls=sorted({c["url"] for c in cases}), affected_count=len(cases), sampled_count=total,
            evidence_detail={"examples": cases[:10]},
            verify="Re-run check RND-006; data-bearing images should have alt text and an HTML equivalent.",
        ))

    share = len(missing_alt) / total
    if share > 0.3 and len(missing_alt) >= 5:
        out.append(F.finding(
            "RND-007", "Most images have no alt text",
            "medium" if share < 0.7 else "high", "discoverability", "render",
            evidence=f"{len(missing_alt)} of {total} images across {len(pages)} sampled pages "
                     f"({round(share * 100)}%) have a missing or empty alt attribute.",
            mechanism="Alt text is the only description of an image available to a text reader, and it is one of the "
                      "few places where an image's meaning enters the page's extractable content. Its absence also "
                      "makes the page unusable with a screen reader, which is an engagement failure as much as a "
                      "discoverability one.",
            action_summary="Add descriptive alt text to meaningful images and empty alt to decorative ones.",
            how=["Describe what the image conveys in context, in a sentence fragment.",
                 "Use alt=\"\" for decoration so readers skip it rather than announcing a filename.",
                 "Add an alt field to the CMS image component so authors cannot omit it silently."],
            effort="medium", owner="content", method="static",
            affected_count=len(missing_alt), sampled_count=total,
            evidence_detail={"examples": missing_alt[:10]},
        ))


def check_documents(cache, out, skipped):
    """PDFs: linked, fetched, and inspected for a text layer.

    A PDF is a legitimate way to publish. A *scanned* PDF is a way to publish
    facts that no machine can read at all - and it is common for exactly the
    documents that carry the most valuable facts: price lists, menus, spec
    sheets, annual reports.
    """
    docs = cache.documents()
    if not docs:
        skipped.append(F.skip("RND-008", "no PDF documents were linked from the sampled pages"))
        return

    scanned, untitled = [], []
    for doc in docs:
        raw = doc.raw_bytes
        if not raw.startswith(b"%PDF"):
            continue
        has_fonts = b"/Font" in raw
        has_text_ops = b"Tj" in raw or b"TJ" in raw or b"/Text" in raw
        has_images = b"/Image" in raw or b"/DCTDecode" in raw
        if not (has_fonts and has_text_ops) and has_images:
            scanned.append({"url": doc.url, "bytes": doc.bytes})
        if b"/Title" not in raw:
            untitled.append(doc.url)

    if scanned:
        out.append(F.finding(
            "RND-008", "Published PDFs contain no text layer (scanned images of pages)",
            "high", "discoverability", "render",
            evidence=f"{len(scanned)} of {len(docs)} linked PDFs contain image data but no font or text-drawing "
                     f"operators, indicating scanned pages rather than text, e.g. {scanned[0]['url']}.",
            mechanism="A scanned PDF is a picture of a document. Text extractors recover nothing from it, so every "
                      "fact it contains - prices, specifications, terms, dates - is invisible to search and to "
                      "assistants, while looking entirely normal to a person who opens it.",
            action_summary="Republish these PDFs with a real text layer, and put their key facts on an HTML page.",
            how=[
                "Regenerate the PDF from its source document rather than from a scan; if only the scan exists, run OCR "
                "and embed the recovered text layer.",
                "Publish the facts that matter - prices, hours, specifications - as an HTML page as well. HTML is "
                "indexed more reliably than PDF even when the PDF is readable.",
                "Set the PDF's Title metadata so it has a usable name in results.",
            ],
            effort="medium", owner="content", method="static", confidence="medium",
            affected_urls=[s["url"] for s in scanned], affected_count=len(scanned), sampled_count=len(docs),
            evidence_detail={"scanned": scanned[:10],
                             "method_note": "Detected from PDF object structure (absence of /Font plus text operators "
                                            "with image XObjects present), not by running OCR."},
        ))

    if untitled and len(untitled) >= max(2, len(docs) * 0.5):
        out.append(F.finding(
            "RND-009", "Linked PDFs carry no Title metadata",
            "low", "discoverability", "extract",
            evidence=f"{len(untitled)} of {len(docs)} linked PDFs have no /Title entry in their document metadata.",
            mechanism="Without embedded title metadata, a PDF is listed by its filename. A result labelled "
                      "`final_v3_web.pdf` is rarely chosen, and gives an assistant nothing to describe it with.",
            action_summary="Set descriptive Title metadata on every published PDF.",
            how=["Populate the document Title property before export.",
                 "Use human-readable filenames as well: `2026-price-list.pdf`, not `doc_final_v3.pdf`."],
            effort="low", owner="content", method="static",
            affected_urls=untitled[:10], affected_count=len(untitled), sampled_count=len(docs),
        ))


def check_iframes(cache, out, skipped):
    pages = cache.html_pages()
    heavy = []
    for page in pages:
        frames = [f for f in page.doc.iframes() if f["src"]]
        # Ignore the ubiquitous embeds that are never the page's own content.
        substantive = [
            f for f in frames
            if not re.search(r"(youtube|vimeo|google\.com/maps|googletagmanager|doubleclick|"
                             r"facebook\.com/plugins|twitter\.com|player\.|recaptcha|hcaptcha|"
                             r"consent|cookiebot|onetrust)", f["src"], re.I)
        ]
        if substantive and page.doc.main_word_count < 200:
            heavy.append({"url": page.url, "iframes": [f["src"][:100] for f in substantive][:3],
                          "words": page.doc.main_word_count})
    if heavy:
        out.append(F.finding(
            "RND-010", "Primary content appears to live inside an iframe",
            "high", "discoverability", "render",
            evidence=f"{len(heavy)} sampled pages have under 200 words of their own body text while embedding "
                     f"third-party frames, e.g. {heavy[0]['url']} ({heavy[0]['words']} words, embeds "
                     f"{heavy[0]['iframes'][0]}).",
            mechanism="An iframe's content belongs to the framed document, not to the page that embeds it. Indexing "
                      "and retrieval attribute that content to the other URL, so the brand's page is treated as an "
                      "empty container and the substance is credited elsewhere - or, when the frame is blocked from "
                      "crawling, to nobody.",
            action_summary="Move the primary content into the page itself and keep iframes for supporting media.",
            how=["Render the content server-side in the host page instead of embedding it.",
                 "Where the source is a third-party system (booking, listings, documentation), use its API or feed to "
                 "render the same data as HTML on this domain.",
                 "Keep at minimum a text summary of the framed content in the host page."],
            effort="high", owner="engineering", method="static",
            affected_urls=[h["url"] for h in heavy], affected_count=len(heavy), sampled_count=len(pages),
            evidence_detail={"pages": heavy[:8]},
        ))


def check_gated_content(cache, out, skipped):
    pages = cache.html_pages()
    gated = []
    for page in pages:
        regions = page.doc.gated_regions()
        total_words = page.doc.main_word_count
        hidden = regions.get("hidden_words", 0)
        if total_words > 100 and hidden > total_words * 0.4 and hidden > 150:
            gated.append({"url": page.url, "hidden_words": hidden, "total_words": total_words,
                          "regions": {k: v for k, v in regions.items() if v and k != "hidden_words"}})
    if gated:
        out.append(F.finding(
            "RND-011", "Much of the page text is hidden behind tabs or accordions at load time",
            "medium", "discoverability", "render",
            evidence=f"{len(gated)} sampled pages hide more than 40% of their body text in collapsed regions, e.g. "
                     f"{gated[0]['url']} keeps {gated[0]['hidden_words']} of {gated[0]['total_words']} words in "
                     f"{gated[0]['regions']}.",
            mechanism="The text is in the HTML, so this is milder than a render gap - but content hidden at load "
                      "time is weighted down or dropped by some extractors, and a visitor who does not click never "
                      "reads it. Specifications, FAQs and shipping terms are the usual casualties, and they are "
                      "exactly the facts people ask assistants about.",
            action_summary="Show the highest-value content expanded by default and keep collapsing for genuine overflow.",
            how=["Expand the first panel of each accordion or tab group by default.",
                 "Move facts people search for - price, dimensions, delivery, compatibility, hours - into always-visible text.",
                 "Where an FAQ is collapsed for layout, add FAQPage structured data so the pairs remain machine-readable."],
            effort="low", owner="design", method="static",
            affected_urls=[g["url"] for g in gated], affected_count=len(gated), sampled_count=len(pages),
            evidence_detail={"pages": gated[:8]},
        ))


def check_structure(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return

    no_h1, multi_h1, skipped_levels, no_landmark, no_lang = [], [], [], [], []
    for page in pages:
        headings = page.doc.headings()
        h1s = [h for h in headings if h[0] == 1]
        if not h1s:
            no_h1.append(page.url)
        elif len(h1s) > 2:
            multi_h1.append({"url": page.url, "count": len(h1s)})
        levels = [level for level, _text in headings]
        for previous, current in zip(levels, levels[1:]):
            if current - previous > 1:
                skipped_levels.append({"url": page.url, "from": previous, "to": current})
                break
        if not page.doc.first("main") and not page.doc.first("article"):
            no_landmark.append(page.url)
        if not page.doc.lang:
            no_lang.append(page.url)

    total = len(pages)
    if len(no_h1) >= max(2, total * 0.4):
        out.append(F.finding(
            "RND-012", "Pages have no H1 heading",
            "medium", "discoverability", "render",
            evidence=f"{len(no_h1)} of {total} sampled pages contain no <h1> element, e.g. {no_h1[0]}.",
            mechanism="The H1 is the most reliable statement of what a page is about, and extractive systems lean on "
                      "it heavily when deciding whether a page answers a question and what to call it in a citation. "
                      "Without one, the page's topic has to be inferred from body text, which is less reliable.",
            action_summary="Give every page exactly one H1 that states the page's subject in plain words.",
            how=["Add a single <h1> per page containing the page's real subject, not a slogan or the site name.",
                 "Style it freely - the level is a structural statement, not a visual one."],
            effort="low", owner="content", method="static",
            affected_urls=no_h1[:10], affected_count=len(no_h1), sampled_count=total,
        ))

    if len(no_landmark) >= max(2, total * 0.6):
        out.append(F.finding(
            "RND-013", "Pages have no <main> or <article> landmark",
            "low", "discoverability", "render",
            evidence=f"{len(no_landmark)} of {total} sampled pages wrap their content in generic containers with no "
                     "<main> or <article> element.",
            mechanism="Content extractors use landmarks to separate the article from the navigation, header and "
                      "footer that repeat on every page. Without them the boundary is guessed, and boilerplate is "
                      "regularly quoted as though it were page content.",
            action_summary="Wrap the unique content of each page in <main>, and each self-contained item in <article>.",
            how=["Add one <main> per page around the content that is unique to it.",
                 "Use <article> for individually meaningful items - posts, products, listings.",
                 "Keep navigation in <nav>, site header in <header>, site footer in <footer>."],
            effort="low", owner="engineering", method="static",
            affected_urls=no_landmark[:10], affected_count=len(no_landmark), sampled_count=total,
        ))

    if len(no_lang) >= max(2, total * 0.5):
        out.append(F.finding(
            "RND-014", "The document language is not declared",
            "low", "discoverability", "render",
            evidence=f"{len(no_lang)} of {total} sampled pages have no lang attribute on <html>.",
            mechanism="The language declaration tells retrieval systems which language queries this page can answer, "
                      "and tells screen readers which voice to use. Undeclared pages are sometimes assigned the wrong "
                      "language and dropped from results in their real one.",
            action_summary="Declare the page language on the <html> element.",
            how=["Add `lang=\"<language code>\"` to <html> in the base template.",
                 "For multilingual sites, emit the correct code per locale and add rel=alternate hreflang links."],
            effort="low", owner="engineering", method="static",
            affected_count=len(no_lang), sampled_count=total,
        ))

    if len(multi_h1) >= max(2, total * 0.4):
        out.append(F.finding(
            "RND-015", "Pages contain several competing H1 headings",
            "low", "discoverability", "render",
            evidence=f"{len(multi_h1)} of {total} sampled pages have 3 or more <h1> elements, e.g. "
                     f"{multi_h1[0]['url']} has {multi_h1[0]['count']}.",
            mechanism="Several top-level headings leave no single statement of what the page is about, so the "
                      "document outline conveys less than it appears to and the page's topic becomes ambiguous.",
            action_summary="Use one H1 per page and demote the rest to H2/H3 by their real hierarchy.",
            how=["Keep the page's subject as the only H1.",
                 "Convert section titles to H2 and their subsections to H3, without skipping levels."],
            effort="low", owner="content", method="static",
            affected_urls=[m["url"] for m in multi_h1][:10], affected_count=len(multi_h1), sampled_count=total,
        ))


def main():
    ap = argparse.ArgumentParser(description="Gate 2 - render and extractability checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    for check in (check_render_gap, check_static_shell, check_noscript_dependency,
                  check_thin_content, check_images, check_documents,
                  check_iframes, check_gated_content, check_structure):
        try:
            check(cache, out, skipped)
        except Exception as e:
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
