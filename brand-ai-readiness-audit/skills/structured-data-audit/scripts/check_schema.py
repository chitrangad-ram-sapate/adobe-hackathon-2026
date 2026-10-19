#!/usr/bin/env python3
"""Gate 3a - Extract. Are the page's facts available as typed, machine-readable data?

Structured data is the difference between a machine inferring a price from
prose and a machine *knowing* the price, its currency and whether the item is
in stock. Retrieval systems prefer facts they do not have to guess at, and
typed facts survive summarisation intact.

The checks here are organised around **field completeness for the type**, not
around whether markup exists. A `Product` node with no `offers`, or an
`Organization` with nothing but a name, validates cleanly and answers no
question - which is why "has schema markup" is a near-useless signal on its own.

Applicability is gated by page type and site type throughout: this detector
will not ask a charity for Offer markup, or a documentation page for a price.

Usage:
    python check_schema.py --cache ./cache
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

from auditlib import cache as cache_mod, findings as F, schema  # noqa: E402

FAQ_HEADING = re.compile(
    r"^(what|how|why|when|where|who|can|do|does|is|are|will|should|which)\b.*\?$", re.I
)
PRICE_IN_TEXT = re.compile(r"[$£€¥₹]\s?\d[\d,]*(\.\d{2})?|\b\d[\d,]*\s?(USD|EUR|GBP|INR|AUD|CAD)\b")


def _objects_for(page):
    return schema.extract_objects(page.doc)


def check_parse_errors(cache, out, skipped):
    """Invalid JSON-LD is worse than none: it looks present and is discarded."""
    broken, escaped = [], []
    for page in cache.html_pages():
        for _raw, parsed, error in page.doc.jsonld_blocks():
            if parsed is None and error:
                broken.append({"url": page.url, "error": error})
            elif parsed is not None and error:
                escaped.append({"url": page.url, "error": error})

    if broken:
        out.append(F.finding(
            "SDA-001", "Structured data blocks contain invalid JSON and are discarded",
            "high", "discoverability", "extract",
            evidence=f"{len(broken)} JSON-LD blocks failed to parse, e.g. on {broken[0]['url']}: {broken[0]['error']}.",
            mechanism="A JSON-LD block that does not parse is dropped in full, silently. The team believes the page "
                      "publishes structured data, consumers see none, and the failure is invisible without "
                      "deliberately validating the output.",
            action_summary="Fix the JSON syntax so the blocks parse, and validate structured data in the build.",
            how=[
                "Correct the reported syntax errors - trailing commas, unescaped quotes inside string values and "
                "unquoted keys account for most of them.",
                "Serialise JSON-LD with a real JSON serialiser rather than string templating in the view layer.",
                "Add a build-time or CI validation step so a malformed block fails the build instead of shipping.",
            ],
            effort="low", owner="engineering", method="static",
            affected_urls=[b["url"] for b in broken][:10], affected_count=len(broken),
            sampled_count=len(cache.html_pages()),
            evidence_detail={"errors": broken[:8]},
            verify="Re-run check SDA-001; every ld+json block should parse without modification.",
        ))

    if escaped:
        out.append(F.finding(
            "SDA-002", "Structured data is HTML-escaped inside its script block",
            "medium", "discoverability", "extract",
            evidence=f"{len(escaped)} JSON-LD blocks only parse after HTML entity unescaping, e.g. on "
                     f"{escaped[0]['url']}.",
            mechanism="The template is escaping the JSON body as though it were HTML text. Strict consumers parse "
                      "the block as-is, fail, and discard it; lenient ones recover it. The result is markup that "
                      "works in some validators and not in the systems that matter.",
            action_summary="Emit JSON-LD raw inside the script element, without HTML escaping.",
            how=["Mark the JSON-LD output as safe/raw in the templating layer so entities are not encoded.",
                 "Escape only the sequence `</` inside string values, which is the one case that needs it."],
            effort="low", owner="engineering", method="static",
            affected_urls=[e["url"] for e in escaped][:10], affected_count=len(escaped),
            sampled_count=len(cache.html_pages()),
        ))


def check_presence(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        skipped.append(F.skip("SDA-003", "no HTML pages were fetched"))
        return

    with_jsonld, with_micro = [], []
    for page in pages:
        if _objects_for(page):
            with_jsonld.append(page)
        elif page.doc.microdata_types() or page.doc.has_rdfa():
            with_micro.append(page)

    if not with_jsonld and not with_micro:
        out.append(F.finding(
            "SDA-003", "The site publishes no structured data at all",
            "high", "discoverability", "extract",
            evidence=f"None of the {len(pages)} sampled pages contain JSON-LD, microdata or RDFa markup.",
            mechanism="Without structured data, every fact on the site has to be inferred from prose. Inference is "
                      "lossy and unattributed: a system that is unsure what the company is, what it sells, or what "
                      "something costs will prefer a source that states those facts explicitly - typically a "
                      "directory or a competitor - and cite that instead.",
            action_summary="Add JSON-LD for the site's core entities, starting with Organization and WebSite on the homepage.",
            how=[
                "Add an `Organization` (or `LocalBusiness`) block on the homepage with name, url, logo, description "
                "and sameAs links to the brand's authoritative profiles.",
                "Add a `WebSite` block naming the site as a whole.",
                "Then add the type that matches each page class: Product/Offer on product pages, Article on posts, "
                "FAQPage on question-and-answer content, BreadcrumbList on nested pages.",
                "Generate the markup from the same data the page renders, so the two can never disagree.",
            ],
            effort="medium", owner="engineering", method="static",
            sampled_count=len(pages),
            verify="Re-run check SDA-003; the homepage should expose at least Organization and WebSite.",
        ))
        return

    if with_micro and not with_jsonld:
        out.append(F.finding(
            "SDA-004", "Structured data uses only the older microdata format",
            "low", "discoverability", "extract",
            evidence=f"{len(with_micro)} of {len(pages)} sampled pages carry microdata/RDFa attributes and none "
                     "carry JSON-LD.",
            mechanism="Microdata is still read by major consumers, so this is not a failure - but JSON-LD is the "
                      "form most retrieval pipelines parse first and most reliably, because it is a self-contained "
                      "block rather than attributes interleaved with presentation markup.",
            action_summary="Add equivalent JSON-LD alongside the existing microdata.",
            how=["Emit a JSON-LD block carrying the same entities the microdata describes.",
                 "Keep both during migration; duplicated agreeing markup is harmless."],
            effort="medium", owner="engineering", method="static",
            affected_count=len(with_micro), sampled_count=len(pages),
        ))


def check_expected_types(cache, out, skipped):
    """Per page class, is the type that class exists to express actually present?"""
    profile = cache.profile
    site_type = profile.get("site_type", "unknown")
    pages = cache.html_pages()
    if not pages:
        return

    missing_by_type = {}
    for page in pages:
        expected = schema.EXPECTED_BY_PAGE_TYPE.get(page.page_type)
        if not expected:
            continue
        # Applicability gates that prevent the classic false positives.
        if page.page_type == "pricing" and site_type not in ("saas", "ecommerce", "marketplace", "unknown"):
            continue
        if page.page_type == "contact" and site_type != "local_business":
            expected = ["Organization"]
        present = {t for obj in _objects_for(page) for t in schema.types_of(obj)}
        # Credit any organisation subtype where Organization is expected.
        if "Organization" in expected and (present & schema.ORG_TYPES):
            continue
        if any(t in present for t in expected):
            continue
        if "Article" in expected and (present & schema.ARTICLE_TYPES):
            continue
        missing_by_type.setdefault(page.page_type, []).append((page, expected))

    for page_type, entries in sorted(missing_by_type.items()):
        pages_of_type = [p for p in pages if p.page_type == page_type]
        # Require a real sample before generalising. One unmarked page is not a
        # site-wide defect, and reporting it as one is a false positive.
        if page_type != "home" and len(entries) < 2:
            skipped.append(F.skip(
                "SDA-005",
                f"only {len(entries)} {page_type} page(s) lacked expected markup - too few to conclude a pattern",
            ))
            continue

        expected = entries[0][1]
        severity = {"home": "high", "product": "high", "article": "medium",
                    "faq": "medium", "contact": "medium", "about": "low",
                    "pricing": "medium", "careers": "low"}.get(page_type, "medium")
        severity = F.apply_blast_radius(severity, len(entries), max(1, len(pages_of_type)))
        primary = expected[0]
        spec = schema.TYPE_SPECS.get(primary, {})
        # The homepage case gets its own id because its fix and its severity
        # differ from the rest. Both ids are written literally rather than
        # assembled at runtime, so every check id in this marketplace can be
        # found by searching for it - by a reader tracing a finding in a report
        # back to the code, and by the consistency checker.
        detail = dict(
            title=f"{page_type.replace('_', ' ').title()} pages have no "
                  f"{'/'.join(expected)} structured data",
            severity=severity, category="discoverability", gate="extract",
            evidence=f"{len(entries)} of {len(pages_of_type)} sampled {page_type} pages carry no "
                     f"{' or '.join(expected)} markup, e.g. {entries[0][0].url}.",
            mechanism=f"The {primary} type is how a machine learns {spec.get('answers', 'what this page is about')}. "
                      "Without it the page competes on prose alone against sources that state the same facts in a "
                      "form that needs no interpretation.",
            action_summary=f"Add {primary} JSON-LD to the {page_type} page template.",
            how=[
                f"Add a `{primary}` JSON-LD block to the {page_type} template, populated from the same data the page "
                "already renders.",
                "Include the fields that make it answerable: "
                + ", ".join(spec.get("required", []) + spec.get("recommended", [])[:3]) + ".",
                "Emit it once per page from the template so new pages inherit it automatically.",
            ],
            effort="medium", owner="engineering", method="static",
            affected_urls=[p.url for p, _ in entries][:10],
            affected_count=len(entries), sampled_count=len(pages_of_type),
            evidence_detail={"page_type": page_type, "expected": expected, "site_type": site_type},
        )
        if page_type == "home":
            out.append(F.finding("SDA-006", **detail))
        else:
            out.append(F.finding("SDA-005", **detail))


def check_completeness(cache, out, skipped):
    """Present but hollow: typed nodes missing the fields that answer questions."""
    # SDA-008 reports a missing price with more precision and a better fix, so
    # the generic completeness check yields that field to it rather than
    # reporting one root cause twice.
    price_reported = any(f["check_id"] == "SDA-008" for f in out)
    incomplete = {}
    counted = 0
    for page in cache.html_pages():
        for obj in _objects_for(page):
            report = schema.check_completeness(obj)
            if not report["known"]:
                continue
            counted += 1
            missing_required = report["missing_required"]
            if price_reported and report["type"] == "Product":
                missing_required = [f for f in missing_required if f != "offers"]
            if missing_required:
                key = report["type"]
                incomplete.setdefault(key, {"pages": [], "missing": {}, "answers": report.get("answers", "")})
                incomplete[key]["pages"].append(page.url)
                for field in missing_required:
                    incomplete[key]["missing"][field] = incomplete[key]["missing"].get(field, 0) + 1

    if not counted:
        return

    for type_name, detail in sorted(incomplete.items()):
        fields = sorted(detail["missing"], key=lambda f: -detail["missing"][f])
        severity = "high" if type_name in ("Product", "Offer", "LocalBusiness") else "medium"
        severity = F.apply_blast_radius(severity, len(detail["pages"]), max(1, counted))
        out.append(F.finding(
            "SDA-007", f"{type_name} structured data is missing required fields",
            severity, "discoverability", "extract",
            evidence=f"{len(detail['pages'])} {type_name} nodes omit " +
                     ", ".join(f"{f} ({detail['missing'][f]}x)" for f in fields[:4]) +
                     f", e.g. on {detail['pages'][0]}.",
            mechanism=f"The block is present and parses, so it appears to be working - but without "
                      f"{', '.join(fields[:3])} it cannot answer {detail['answers'] or 'the question it exists for'}. "
                      "Consumers that require these fields discard the node entirely, leaving the page in the same "
                      "position as one with no markup at all.",
            action_summary=f"Populate the required {type_name} fields: {', '.join(fields[:5])}.",
            how=[
                f"Add {', '.join(fields[:5])} to the {type_name} block, sourced from the same data the page renders.",
                "Leave a field out entirely rather than emitting an empty string or a placeholder - an empty value "
                "is treated as an assertion that the value is empty.",
                "Validate the output against the type's requirements as part of the build.",
            ],
            effort="low", owner="engineering", method="static",
            affected_urls=detail["pages"][:10], affected_count=len(detail["pages"]), sampled_count=counted,
            evidence_detail={"type": type_name, "missing_counts": detail["missing"]},
        ))


def check_offers(cache, out, skipped):
    """Price is the single most-asked commercial fact. Treat it specially."""
    profile = cache.profile
    if profile.get("site_type") not in ("ecommerce", "marketplace", "saas", "unknown"):
        skipped.append(F.skip("SDA-008", f"site type is {profile.get('site_type')}; offer markup is not expected"))
        return

    product_pages = cache.pages_of_type("product", "pricing")
    if not product_pages:
        skipped.append(F.skip("SDA-008", "no product or pricing pages were sampled"))
        return

    priceless = []
    for page in product_pages:
        products = schema.find(_objects_for(page), "Product", "SoftwareApplication", "Service")
        if not products:
            continue
        for product in products:
            offers = schema.offers_of(product)
            if not offers or not any(schema.has_value(o, "price") or schema.has_value(o, "lowPrice") for o in offers):
                priceless.append({"url": page.url, "name": str(product.get("name", ""))[:60]})
                break

    if priceless:
        out.append(F.finding(
            "SDA-008", "Product markup carries no price",
            F.apply_blast_radius("high", len(priceless), len(product_pages)),
            "discoverability", "extract",
            evidence=f"{len(priceless)} of {len(product_pages)} sampled product/pricing pages declare Product-family "
                     f"markup with no populated Offer price, e.g. {priceless[0]['url']}.",
            mechanism="'How much does it cost' is among the most common questions asked of an assistant about a "
                      "commercial brand. A Product node without a price cannot answer it, so the assistant falls back "
                      "to a reseller, a directory or a review site - all of which are more likely to quote an "
                      "out-of-date figure than the brand's own page would.",
            action_summary="Add Offer price, priceCurrency and availability to product markup.",
            how=[
                "Nest an `offers` object with `price`, `priceCurrency` and `availability` in every Product node.",
                "Use `AggregateOffer` with `lowPrice`/`highPrice` where a product spans variants.",
                "Populate it from live pricing data so the markup cannot drift from the page.",
                "For quote-based pricing, publish an indicative range rather than nothing - an absent price is "
                "treated as an absent product.",
            ],
            effort="medium", owner="engineering", method="static",
            affected_urls=[p["url"] for p in priceless][:10],
            affected_count=len(priceless), sampled_count=len(product_pages),
        ))


def check_faq_opportunity(cache, out, skipped):
    """Question-shaped content already on the page, not marked up as such."""
    candidates = []
    for page in cache.html_pages():
        if schema.find(_objects_for(page), "FAQPage", "QAPage"):
            continue
        questions = [text for level, text in page.doc.headings() if FAQ_HEADING.match(text.strip())]
        if len(questions) >= 3:
            candidates.append({"url": page.url, "questions": questions[:4], "count": len(questions)})

    if candidates:
        out.append(F.finding(
            "SDA-009", "Question-and-answer content is not marked up as an FAQ",
            "medium", "discoverability", "extract",
            evidence=f"{len(candidates)} pages contain {candidates[0]['count']}+ question-shaped headings with no "
                     f"FAQPage markup, e.g. {candidates[0]['url']} asks \"{candidates[0]['questions'][0][:70]}\".",
            mechanism="Question-and-answer pairs are the most directly quotable content a site can publish, because "
                      "the question already matches the shape of what users ask. Marking them up hands a retrieval "
                      "system a pre-matched pair instead of asking it to locate the answer inside a page of prose.",
            action_summary="Add FAQPage structured data wrapping the existing questions and answers.",
            how=[
                "Emit `FAQPage` with a `mainEntity` array of `Question`/`acceptedAnswer` pairs built from the "
                "headings and body already on the page.",
                "Keep the answers self-contained: each should make sense quoted on its own, without the question "
                "above it or the paragraph before it.",
                "Only mark up genuine questions the page answers - inventing pairs for markup's sake is treated as "
                "spam by consumers.",
            ],
            effort="low", owner="content", method="static",
            affected_urls=[c["url"] for c in candidates][:10],
            affected_count=len(candidates), sampled_count=len(cache.html_pages()),
            evidence_detail={"examples": candidates[:5]},
        ))


def check_breadcrumbs(cache, out, skipped):
    deep = [p for p in cache.html_pages() if p.depth >= 2]
    if len(deep) < 3:
        skipped.append(F.skip("SDA-010", "fewer than 3 nested pages sampled"))
        return
    without = [p for p in deep if not schema.find(_objects_for(p), "BreadcrumbList")]
    if len(without) >= max(3, len(deep) * 0.8):
        out.append(F.finding(
            "SDA-010", "Nested pages carry no breadcrumb structured data",
            "low", "discoverability", "extract",
            evidence=f"{len(without)} of {len(deep)} sampled nested pages have no BreadcrumbList markup.",
            mechanism="Breadcrumbs tell a machine where a page sits in the site, which is how an isolated page - the "
                      "kind an assistant links someone straight into - acquires context about what it is part of. "
                      "They also give the brand a labelled path in results rather than a bare URL.",
            action_summary="Add BreadcrumbList markup, and a visible breadcrumb trail, to nested page templates.",
            how=["Emit `BreadcrumbList` with an ordered `itemListElement` from the site root to the current page.",
                 "Render a matching visible trail; it serves the same orientation purpose for the reader.",
                 "Keep the markup and the visible trail identical."],
            effort="low", owner="engineering", method="static",
            affected_count=len(without), sampled_count=len(deep),
        ))


def main():
    ap = argparse.ArgumentParser(description="Gate 3a - structured data checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    # check_offers runs before check_completeness so the latter can defer the
    # price field to it. Order is otherwise the gate's own reading order.
    for check in (check_parse_errors, check_presence, check_expected_types,
                  check_offers, check_completeness, check_faq_opportunity, check_breadcrumbs):
        try:
            check(cache, out, skipped)
        except Exception as e:
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
