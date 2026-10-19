#!/usr/bin/env python3
"""Gate 3b - Extract. Is there a sentence worth quoting?

Structured data is not the only way a fact becomes usable. When an assistant
composes an answer it lifts *passages*: short, self-contained statements that
answer the question directly. A page can be perfectly crawlable, perfectly
rendered and still contribute nothing, because it never states in plain words
what the company is, who it is for, or what anything costs.

This is the most common failure among sites that are otherwise well built.
Brand copy is written to impress a reader who already knows the context; an
extractive system has no context and cannot infer a category from a slogan.

These checks are linguistic, so several carry `confidence: medium` by design -
they are reported as signals for a human to confirm, never as measurements.

Usage:
    python check_answer_readiness.py --cache ./cache
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter


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

# A definitional sentence: the subject, a copular or descriptive verb, then a
# category. This is the shape an extractor can lift to answer "what is X".
IDENTITY_VERB = re.compile(
    r"\b(is|are|was|provides?|offers?|builds?|makes?|sells?|delivers?|creates?|develops?|"
    r"helps?|enables?|supplies|specialis[ez]es?|manufactures?|operates?|runs?|serves?)\b", re.I
)
# Concrete category nouns. A hero line containing none of these is describing a
# feeling rather than a business.
CATEGORY_NOUN = re.compile(
    r"\b(platform|software|app|application|tool|service|agency|studio|company|firm|brand|"
    r"consultancy|marketplace|shop|store|retailer|manufacturer|supplier|distributor|clinic|"
    r"restaurant|cafe|hotel|school|college|university|charity|nonprofit|foundation|bank|"
    r"insurer|broker|solution|system|network|community|magazine|newspaper|publisher|"
    r"institute|laboratory|practice|team|robots?|hardware|equipment|products?|services?)\b", re.I
)
# Aspirational vocabulary that carries no extractable fact on its own.
FLUFF = re.compile(
    r"\b(reimagine|unleash|unlock|empower|transform|revolution(ise|ize|ary)?|elevate|"
    r"redefine|reinvent|next[- ]generation|world[- ]class|cutting[- ]edge|best[- ]in[- ]class|"
    r"seamless|innovative|synerg|disrupt|game[- ]chang|beyond|possibilities|journey|"
    r"experience the|welcome to)\b", re.I
)
GENERIC_TITLE = re.compile(
    r"^(home|homepage|welcome|index|untitled|new page|home page|main|start)\b", re.I
)
PRICE_IN_TEXT = re.compile(r"[$£€¥₹]\s?\d[\d,]*(\.\d{2})?|\b\d[\d,]*(\.\d{2})?\s?(USD|EUR|GBP|INR|AUD|CAD|per month|/mo|a month|per year|/yr)\b", re.I)
QUOTE_PRICE = re.compile(r"\b(contact (us|sales)|request a quote|get a quote|talk to sales|pricing on request|bespoke pricing|custom pricing)\b", re.I)
EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE = re.compile(r"(\+\d{1,3}[\s.\-()]{0,3})?(\(?\d{2,5}\)?[\s.\-]{0,2}){2,4}\d{2,5}")
QUESTION_HEADING = re.compile(r"^(what|how|why|when|where|who|can|do|does|is|are|will|should|which)\b.*\?\s*$", re.I)

# Page shapes that answer the comparison and qualification questions people
# actually put to assistants. Their absence is an opportunity, not a defect.
QUERY_SURFACE = {
    "comparison": re.compile(r"/(vs|versus|compare|comparison|alternatives?)(/|-|$)", re.I),
    "use_case": re.compile(r"/(for|solutions?|industries|use-cases?|by-industry)(/|-|$)", re.I),
    "how_to": re.compile(r"/(how-to|guide|tutorial|getting-started|learn)(/|-|$)", re.I),
    "faq": re.compile(r"/(faq|faqs|questions|help)(/|$)", re.I),
}


def _brand_tokens(cache):
    """Best guess at the brand's own name, from schema then title then host."""
    home = cache.home
    names = []
    if home:
        for obj in schema.extract_objects(home.doc):
            if set(schema.types_of(obj)) & (schema.ORG_TYPES | {"WebSite"}):
                name = obj.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
    host_name = cache.site.split(".")[0]
    names.append(host_name)
    tokens = set()
    for name in names:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9&'-]{2,}", name):
            tokens.add(token.lower())
    return tokens, (names[0] if names else host_name)


def check_identity_statement(cache, out, skipped):
    """Does the homepage say, in one sentence, what this organisation is?"""
    home = cache.home
    if not home:
        skipped.append(F.skip("ANS-001", "no homepage was fetched"))
        return

    tokens, brand = _brand_tokens(cache)
    doc = home.doc
    opening = doc.sentences()[:6]
    headline_text = " ".join([doc.title] + [t for _l, t in doc.headings()[:3]])
    meta_description = doc.meta().get("description", "")

    def is_identity(sentence):
        has_brand = any(token in sentence.lower() for token in tokens)
        return bool(has_brand and IDENTITY_VERB.search(sentence) and CATEGORY_NOUN.search(sentence))

    identity_sentences = [s for s in opening if is_identity(s)]
    # A description meta tag or an Organization description counts too - the
    # fact only has to be extractable somewhere prominent, not in one place.
    if not identity_sentences:
        for candidate in (meta_description,):
            if candidate and IDENTITY_VERB.search(candidate) and CATEGORY_NOUN.search(candidate):
                identity_sentences.append(candidate)
    if not identity_sentences:
        for obj in schema.extract_objects(doc):
            if set(schema.types_of(obj)) & schema.ORG_TYPES:
                description = obj.get("description")
                if isinstance(description, str) and CATEGORY_NOUN.search(description):
                    identity_sentences.append(description)

    if identity_sentences:
        return

    out.append(F.finding(
        "ANS-001", "The homepage never states in plain words what the organisation is",
        "high", "discoverability", "extract",
        evidence=f"None of the first {len(opening)} sentences on the homepage, the meta description, or any "
                 f"Organization description combines the brand name with a descriptive verb and a category noun. "
                 f"Opening line: \"{(opening[0][:110] if opening else '(no body text)')}\".",
        mechanism="When an assistant is asked what a company does, it looks for a sentence that says so. If the page "
                  "communicates identity through imagery, layout and implication instead, there is nothing to lift - "
                  "so the assistant either declines to describe the brand or reconstructs a description from third "
                  "parties, which is where misrepresentation begins.",
        action_summary="Add one plain declarative sentence near the top of the homepage stating what the organisation "
                       "is, who it serves, and where.",
        how=[
            f"Write a sentence of the form: \"{brand} is a <category> that <does what> for <who>, based in <where>.\"",
            "Place it in the first screen of the homepage as body text - not inside an image, a video, or a carousel.",
            "Mirror the same sentence in the meta description and in the Organization schema `description` field so "
            "all three agree.",
            "Keep it literal. A slogan can sit above it; the literal sentence is what gets quoted.",
        ],
        effort="low", owner="content", method="heuristic", confidence="medium",
        affected_urls=[home.url], affected_count=1, sampled_count=1,
        evidence_detail={"opening_sentences": opening[:3], "headline_text": headline_text[:200],
                         "meta_description": meta_description[:200]},
        verify="Re-run check ANS-001; a sentence naming the brand, a verb and a category noun should appear in the "
               "homepage's opening text.",
    ))


def check_hero_clarity(cache, out, skipped):
    """Aspirational headline with no concrete category is a real, common defect."""
    home = cache.home
    if not home:
        return
    headings = home.doc.headings()
    h1 = next((text for level, text in headings if level == 1), "")
    if not h1:
        skipped.append(F.skip("ANS-002", "no H1 on the homepage; covered by RND-012"))
        return
    if CATEGORY_NOUN.search(h1):
        return
    if not FLUFF.search(h1) and len(h1.split()) > 3:
        # Concrete-sounding but unmatched vocabulary: too uncertain to flag.
        skipped.append(F.skip("ANS-002", "homepage H1 is unrecognised vocabulary rather than identifiable marketing "
                                         "abstraction; not flagged to avoid a false positive"))
        return

    out.append(F.finding(
        "ANS-002", "The homepage headline is abstract and names no category",
        "medium", "discoverability", "extract",
        evidence=f"The homepage H1 is \"{h1[:120]}\", which contains no concrete category noun"
                 + (" and uses aspirational marketing vocabulary" if FLUFF.search(h1) else "") + ".",
        mechanism="The H1 is one of the strongest signals a retrieval system has for what a page is about. A headline "
                  "that describes an ambition rather than a business gives it nothing to match a question against, so "
                  "the page is not retrieved for the queries the brand most wants to appear in.",
        action_summary="Rewrite the headline so it names what the organisation actually does, and keep the slogan as a subhead.",
        how=[
            "Put the concrete statement in the H1: what it is, for whom.",
            "Move the aspirational line to a subheading, where it still sets tone but is not doing the identifying.",
            "Test the headline in isolation: if someone who has never heard of the brand cannot say what it sells "
            "from the H1 alone, neither can a machine.",
        ],
        effort="low", owner="content", method="heuristic", confidence="medium",
        affected_urls=[home.url], affected_count=1, sampled_count=1,
        evidence_detail={"h1": h1[:200]},
    ))


def check_titles_and_descriptions(cache, out, skipped):
    pages = cache.html_pages()
    if len(pages) < 3:
        skipped.append(F.skip("ANS-003", "fewer than 3 pages sampled"))
        return

    titles, descriptions = [], []
    missing_title, generic_title, missing_description = [], [], []
    for page in pages:
        title = page.doc.title.strip()
        description = page.doc.meta().get("description", "").strip()
        if not title:
            missing_title.append(page.url)
        else:
            titles.append((title, page.url))
            if GENERIC_TITLE.match(title) or len(title) < 12:
                generic_title.append({"url": page.url, "title": title})
        if not description:
            missing_description.append(page.url)
        else:
            descriptions.append((description, page.url))

    duplicate_titles = [t for t, count in Counter(t for t, _u in titles).items() if count > 1]
    if duplicate_titles and len(titles) >= 4:
        affected = [u for t, u in titles if t in duplicate_titles]
        out.append(F.finding(
            "ANS-003", "Different pages share the same title",
            F.apply_blast_radius("medium", len(affected), len(pages)), "discoverability", "extract",
            evidence=f"{len(affected)} of {len(pages)} sampled pages share {len(duplicate_titles)} repeated "
                     f"title(s), e.g. \"{duplicate_titles[0][:80]}\".",
            mechanism="The title is how a page is named in a citation and is one of the strongest topic signals a "
                      "retrieval system has. Identical titles make pages indistinguishable to it, so they compete "
                      "with one another and the most relevant one is not reliably chosen.",
            action_summary="Give every page a unique title describing that page's specific subject.",
            how=["Template titles as `<specific page subject> - <brand>`.",
                 "Derive the first part from the page's own H1 or product/article name, never from the site name alone."],
            effort="low", owner="content", method="static",
            affected_urls=affected[:10], affected_count=len(affected), sampled_count=len(pages),
            evidence_detail={"duplicates": duplicate_titles[:5]},
        ))

    if generic_title or missing_title:
        cases = generic_title + [{"url": u, "title": ""} for u in missing_title]
        if len(cases) >= max(2, len(pages) * 0.25):
            out.append(F.finding(
                "ANS-004", "Pages have missing or placeholder titles",
                "medium", "discoverability", "extract",
                evidence=f"{len(cases)} of {len(pages)} sampled pages have no title or a generic one, e.g. "
                         f"{cases[0]['url']} is titled \"{cases[0]['title'] or '(none)'}\".",
                mechanism="A page titled \"Home\" tells a retrieval system nothing about the brand or the subject, and "
                          "produces a citation nobody clicks. It is also the label the page carries in every system "
                          "that ever references it.",
                action_summary="Write a descriptive, unique title for every page.",
                how=["Name the subject and the brand: `Warehouse robots for distributors - Northwind Robotics`.",
                     "Keep it under about 60 characters so it is not truncated in results."],
                effort="low", owner="content", method="static",
                affected_urls=[c["url"] for c in cases][:10], affected_count=len(cases), sampled_count=len(pages),
            ))

    if len(missing_description) >= max(3, len(pages) * 0.5):
        out.append(F.finding(
            "ANS-005", "Most pages have no meta description",
            "low", "discoverability", "extract",
            evidence=f"{len(missing_description)} of {len(pages)} sampled pages have no meta description.",
            mechanism="The meta description is a pre-written, self-contained summary of the page. Where it is absent "
                      "a summary is generated from whatever text happens to be near the top - often navigation or a "
                      "cookie notice - so the brand loses control of how the page is described.",
            action_summary="Write a one-sentence meta description for every page.",
            how=["Summarise what the page answers in 120-155 characters, as a complete sentence.",
                 "Write it as a standalone statement - it is frequently read without the page around it."],
            effort="medium", owner="content", method="static",
            affected_count=len(missing_description), sampled_count=len(pages),
        ))


def check_price_extractability(cache, out, skipped):
    site_type = cache.profile.get("site_type", "unknown")
    if site_type not in ("saas", "ecommerce", "marketplace"):
        skipped.append(F.skip("ANS-006", f"site type is {site_type}; a published price is not expected"))
        return
    pricing_pages = cache.pages_of_type("pricing", "product")
    if not pricing_pages:
        skipped.append(F.skip("ANS-006", "no pricing or product pages were sampled"))
        return

    quote_only = []
    for page in pricing_pages:
        text = page.doc.main_text
        if PRICE_IN_TEXT.search(text):
            continue
        quote_only.append({"url": page.url, "quote_language": bool(QUOTE_PRICE.search(text))})

    if len(quote_only) < max(1, len(pricing_pages) * 0.6):
        return

    all_quote = all(q["quote_language"] for q in quote_only)
    out.append(F.finding(
        "ANS-006", "Pricing pages contain no readable price",
        "high" if not all_quote else "medium", "discoverability", "extract",
        evidence=f"{len(quote_only)} of {len(pricing_pages)} sampled pricing/product pages contain no numeric price "
                 f"in their text"
                 + (" and instead direct the reader to contact sales" if all_quote else "")
                 + f", e.g. {quote_only[0]['url']}.",
        mechanism="Cost is among the most common things asked about any commercial brand. With no number on the page, "
                  "an assistant cannot answer from the brand's own site and turns to resellers, review sites and "
                  "forums - sources that are often out of date and never in the brand's control. Publishing a figure "
                  "is what makes the brand's own page the citable one.",
        action_summary="Publish a real figure or an indicative range, even where final pricing is negotiated.",
        how=[
            "State a starting price, a typical range, or a worked example: \"from 4,500 GBP per unit per year\".",
            "Put it in body text, not in an image or a downloadable PDF.",
            "Mirror it in Offer/AggregateOffer structured data with price and priceCurrency.",
            "If pricing genuinely cannot be published, state what it depends on in plain text - that is still an "
            "extractable, quotable answer, where silence is not.",
        ],
        effort="medium", owner="marketing", method="static", confidence="high",
        affected_urls=[q["url"] for q in quote_only][:10],
        affected_count=len(quote_only), sampled_count=len(pricing_pages),
        evidence_detail={"pages": quote_only[:8]},
    ))


def check_contact_extractability(cache, out, skipped):
    contact_pages = cache.pages_of_type("contact")
    home = cache.home
    candidates = contact_pages or ([home] if home else [])
    if not candidates:
        skipped.append(F.skip("ANS-007", "no contact or home page was sampled"))
        return

    combined = " ".join(p.doc.visible_text for p in candidates)
    has_email = bool(EMAIL.search(combined))
    has_phone = bool(PHONE.search(combined))
    is_local = cache.profile.get("site_type") == "local_business"

    if has_email or has_phone:
        return
    # A form-only contact route is a legitimate choice for many businesses, so
    # this is medium at most - except for a local business, where the phone
    # number is the single most-asked fact.
    out.append(F.finding(
        "ANS-007", "No contact details appear as text",
        "high" if is_local else "medium", "discoverability", "extract",
        evidence=f"Neither an email address nor a phone number appears in the text of "
                 f"{len(candidates)} sampled contact/home page(s) ({candidates[0].url}).",
        mechanism="\"How do I contact them\" is one of the most common questions asked about any organisation. "
                  "Details that exist only inside a contact form, an image, or a script-rendered widget cannot be "
                  "extracted, so the answer is either absent or taken from a third-party directory listing that the "
                  "brand does not control and may not have updated.",
        action_summary="Publish a phone number, an email address and a postal address as selectable text.",
        how=[
            "Put the details in HTML text, using `tel:` and `mailto:` links.",
            "Add them to Organization or LocalBusiness structured data (telephone, email, address, contactPoint).",
            "Keep a contact form if preferred - but alongside the details, not instead of them.",
        ],
        effort="low", owner="content", method="static",
        affected_urls=[p.url for p in candidates][:5], affected_count=len(candidates), sampled_count=len(candidates),
        evidence_detail={"has_email": has_email, "has_phone": has_phone, "site_type": cache.profile.get("site_type")},
    ))


def check_answer_formats(cache, out, skipped):
    """Does the site publish anything in a directly quotable question/answer shape?"""
    pages = cache.html_pages()
    # A small brochure site with no FAQ section is not defective - it is small.
    # The threshold keeps this check to sites large enough that the absence of
    # any question-shaped content is a genuine content-strategy gap.
    if len(pages) < 8:
        skipped.append(F.skip("ANS-008", f"only {len(pages)} pages sampled; too small a site for the absence of "
                                         "question-and-answer content to indicate a gap"))
        return

    question_headings = 0
    for page in pages:
        question_headings += sum(1 for _level, text in page.doc.headings() if QUESTION_HEADING.match(text.strip()))
    has_faq_page = bool(cache.pages_of_type("faq"))
    has_faq_schema = any(schema.find(schema.extract_objects(p.doc), "FAQPage", "QAPage") for p in pages)

    if question_headings >= 3 or has_faq_page or has_faq_schema:
        return

    out.append(F.finding(
        "ANS-008", "The site publishes nothing in a question-and-answer shape",
        "medium", "discoverability", "extract",
        evidence=f"Across {len(pages)} sampled pages there are {question_headings} question-shaped headings, no FAQ "
                 "page and no FAQPage markup.",
        mechanism="Retrieval works by matching a user's question against candidate passages. Content already written "
                  "as a question with a self-contained answer matches directly; the same information written as "
                  "narrative prose has to be located inside a longer passage first, which is less reliable and often "
                  "loses to a competitor who wrote it the other way.",
        action_summary="Publish the questions customers actually ask, each with a self-contained answer.",
        how=[
            "Collect the real questions from sales calls, support tickets and site search logs.",
            "Write each answer to stand alone - it should make sense quoted without the question or the page around it.",
            "Use the customer's wording for the question, not internal product vocabulary.",
            "Mark the block up as FAQPage so the pairing is explicit.",
        ],
        effort="medium", owner="content", method="static",
        sampled_count=len(pages),
        evidence_detail={"question_headings": question_headings},
    ))


def check_query_surface(cache, out, skipped):
    """Coverage of the question shapes people actually bring to assistants."""
    site_type = cache.profile.get("site_type", "unknown")
    if site_type not in ("saas", "ecommerce", "marketplace", "documentation"):
        skipped.append(F.skip("ANS-009", f"site type is {site_type}; comparison and use-case pages are not expected"))
        return

    known_urls = [p.url for p in cache.html_pages()] + cache.extras.get("sitemap_sample", [])
    if len(known_urls) < 10:
        skipped.append(F.skip("ANS-009", "too few known URLs to judge content coverage"))
        return

    present = {name for name, pattern in QUERY_SURFACE.items() if any(pattern.search(u) for u in known_urls)}
    missing = sorted(set(QUERY_SURFACE) - present)
    if len(missing) < 3:
        return

    out.append(F.finding(
        "ANS-009", "The site does not answer comparison, use-case or how-to questions",
        "low", "discoverability", "extract",
        evidence=f"Across {len(known_urls)} known URLs there are no pages matching {', '.join(missing)} patterns; "
                 f"only {', '.join(sorted(present)) or 'none'} present.",
        mechanism="A large share of the questions put to assistants are comparative or qualifying - which tool for "
                  "this job, how does this compare to that, is this suitable for my situation. A site that only "
                  "describes its own products in its own vocabulary has no passage that matches those questions, so "
                  "the answer is assembled from review sites and competitors' comparison pages instead.",
        action_summary="Publish comparison, use-case and how-to pages in the customer's own words.",
        how=[
            "Write honest comparison pages against the alternatives buyers genuinely evaluate, including where the "
            "alternative is the better fit - even-handed pages are cited more often than promotional ones.",
            "Publish `for <audience>` or `for <industry>` pages describing the specific situation each serves.",
            "Add how-to and getting-started content answering the questions that precede a purchase decision.",
            "Title and phrase each page as the question it answers.",
        ],
        effort="high", owner="marketing", method="static", confidence="medium",
        sampled_count=len(known_urls),
        evidence_detail={"missing_surfaces": missing, "present_surfaces": sorted(present)},
    ))


def main():
    ap = argparse.ArgumentParser(description="Gate 3b - answer readiness checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    for check in (check_identity_statement, check_hero_clarity, check_titles_and_descriptions,
                  check_price_extractability, check_contact_extractability,
                  check_answer_formats, check_query_surface):
        try:
            check(cache, out, skipped)
        except Exception as e:
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
