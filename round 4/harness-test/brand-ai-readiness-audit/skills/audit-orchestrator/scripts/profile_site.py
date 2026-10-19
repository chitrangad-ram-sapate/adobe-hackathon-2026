#!/usr/bin/env python3
"""Classify the site before anything is checked against it.

This step exists for one reason: **false-positive control**. Nearly every bad
audit in this problem space comes from applying a checklist written for one
kind of site to a different kind - demanding Product/Offer markup from a
charity, a pricing CTA from a documentation site, or opening hours from a SaaS
company. Detectors consult this profile and skip inapplicable checks, recording
the skip so the report says what was *not* tested rather than silently passing.

It also fingerprints the platform, which the remediation planner uses to turn
"add JSON-LD" into an instruction someone can actually follow in their CMS.

Writes the result into the cache manifest under `profile`.

Usage:
    python profile_site.py --cache ./cache [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
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

from auditlib import force_utf8_stdout  # noqa: E402
from auditlib import cache as cache_mod  # noqa: E402
from auditlib import schema as schema_mod  # noqa: E402

# --- platform fingerprints ----------------------------------------------------
#
# (label, weight, where, pattern). `where` is one of html / header / generator.
# Weights let several weak signals combine without any single one being able to
# assert a platform on its own.
PLATFORM_SIGNATURES = [
    ("Adobe Experience Manager", 5, "html", r"/etc\.clientlibs/|/etc/designs/|cq:template|/content/dam/|granite\.csrf"),
    ("Adobe Experience Manager", 5, "generator", r"adobe experience manager|\bAEM\b"),
    ("Adobe Edge Delivery Services", 5, "html", r"/scripts/aem\.js|lib-franklin|aem\.live|hlx\.page|hlx\.live|/scripts/scripts\.js\"[^>]*type=\"module\""),
    ("Adobe Commerce (Magento)", 5, "html", r"/static/version\d+|Magento_|mage/cookies|/pub/static/frontend/"),
    ("Shopify", 5, "html", r"cdn\.shopify\.com|Shopify\.theme|/cdn/shop/|shopify-section"),
    ("Shopify", 5, "header", r"x-shopify"),
    ("WordPress", 5, "html", r"/wp-content/|/wp-includes/|wp-json"),
    ("WordPress", 5, "generator", r"wordpress"),
    ("WooCommerce", 4, "html", r"/plugins/woocommerce|woocommerce-page|wc-block|/woocommerce/assets/"),
    ("Drupal", 5, "html", r"/sites/default/files/|drupal-settings-json|/core/misc/drupal\.js"),
    ("Drupal", 5, "generator", r"drupal"),
    ("Wix", 5, "html", r"static\.wixstatic\.com|wix-code|_wixCIDX"),
    ("Squarespace", 5, "html", r"squarespace\.com/universal|static1\.squarespace\.com|Static\.SQUARESPACE_CONTEXT"),
    ("Webflow", 5, "html", r"webflow\.js|w-webflow-badge|data-wf-page"),
    ("HubSpot CMS", 5, "html", r"hs-scripts\.com|hsforms\.net|/hubfs/"),
    ("Ghost", 4, "generator", r"ghost"),
    ("Contentful", 3, "html", r"ctfassets\.net"),
    ("Sanity", 3, "html", r"cdn\.sanity\.io"),
    ("Next.js", 4, "html", r"/_next/static/|__NEXT_DATA__|self\.__next_f"),
    ("Nuxt", 4, "html", r"/_nuxt/|__NUXT__|__NUXT_DATA__"),
    ("SvelteKit", 4, "html", r"__sveltekit_|/_app/immutable/"),
    ("Gatsby", 4, "html", r"___gatsby|/page-data/"),
    ("Astro", 3, "html", r"astro-island|data-astro-"),
    ("Angular", 4, "html", r"ng-version=|<app-root"),
    ("React (client-rendered)", 2, "html", r"data-reactroot|__REACT_DEVTOOLS|react\.production\.min\.js"),
    ("Vue", 2, "html", r"data-v-[0-9a-f]{8}|vue\.runtime"),
    ("Hugo", 3, "generator", r"hugo"),
    ("Jekyll", 3, "generator", r"jekyll"),
    ("Eleventy", 3, "generator", r"eleventy"),
    ("Framer", 4, "html", r"framerusercontent\.com|__framer"),
    ("BigCommerce", 4, "html", r"cdn\d*\.bigcommerce\.com"),
    ("Salesforce Commerce", 4, "html", r"demandware\.static|/on/demandware\.store"),
]

HOST_SIGNATURES = [
    ("Vercel", r"^vercel"),
    ("Netlify", r"^netlify"),
    ("Cloudflare", r"cloudflare"),
    ("Akamai", r"akamai|akamaighost"),
    ("Fastly", r"fastly"),
    ("AWS CloudFront", r"cloudfront"),
    ("Nginx", r"^nginx"),
    ("Apache", r"^apache"),
    ("Microsoft-IIS", r"^microsoft-iis"),
]

# Analytics / experience tooling. Not a defect either way - it tells the
# remediation planner what the team already owns, and flags the case where a
# site has no measurement at all (you cannot improve engagement blind).
ANALYTICS_SIGNATURES = [
    ("Adobe Analytics / Experience Platform", r"assets\.adobedtm\.com|adobedc\.demdex\.net|alloy\.js|s_code\.js|/b/ss/"),
    ("Adobe Target", r"at\.js|/rest/v1/delivery|adobe\.target"),
    ("Google Analytics 4", r"gtag/js|googletagmanager\.com/gtag|G-[A-Z0-9]{8,}"),
    ("Google Tag Manager", r"googletagmanager\.com/gtm\.js|GTM-[A-Z0-9]+"),
    ("Plausible", r"plausible\.io/js"),
    ("Fathom", r"cdn\.usefathom\.com"),
    ("Matomo", r"matomo\.js|piwik\.js"),
    ("Segment", r"cdn\.segment\.com"),
    ("Hotjar", r"static\.hotjar\.com"),
    ("Amplitude", r"amplitude\.com/libs|cdn\.amplitude\.com"),
    ("Mixpanel", r"cdn\.mxpnl\.com"),
]

COMMERCE_TEXT = re.compile(
    r"\b(add to (cart|bag|basket)|buy now|checkout|shopping (cart|bag)|free shipping|in stock|out of stock)\b", re.I
)
SAAS_TEXT = re.compile(
    r"\b(free trial|start free|book a demo|request a demo|sign up free|per (user|seat|month)|/mo\b|api key|integrations?)\b", re.I
)
INSTITUTIONAL_TEXT = re.compile(
    r"(donate|donation|volunteer|charity|registered charity|fundraising|our mission|"
    r"admissions|undergraduate|postgraduate|prospectus|faculty|campus|enrol|enroll|"
    r"public services|citizens|taxpayer|department for|ministry of|council|constituency|"
    r"nonprofit|non-profit|501\(c\)|beneficiaries)", re.I
)
DOCS_TEXT = re.compile(
    r"(installation|getting started|api reference|parameters?|returns?|deprecated|"
    r"changelog|command line|configuration|syntax|example usage|see also)", re.I
)
LOCAL_TEXT = re.compile(
    r"\b(opening hours|business hours|mon(day)?\s*[-–]\s*fri|our (address|location|store)|directions|walk-?ins?|appointment)\b", re.I
)
PHONE_RE = re.compile(r"(\+\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}")
ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Z][a-zA-Z]+\s+(street|st|road|rd|avenue|ave|lane|ln|drive|dr|boulevard|blvd|way|court|ct)\b", re.I
)
PRICE_RE = re.compile(r"[$£€¥₹]\s?\d[\d,]*(\.\d{2})?|\b\d[\d,]*\s?(USD|EUR|GBP|INR|AUD|CAD)\b")


def _attribute_blob(doc, limit=400000):
    """Every attribute value in the document, plus inline script sources.

    This is where a platform actually reveals itself - asset paths, class name
    prefixes, data attributes - as opposed to body text, where its name may
    appear for entirely unrelated reasons.
    """
    parts = []
    total = 0
    for nodes in doc._by_tag.values():
        for node in nodes:
            for key, value in node.attrs.items():
                if not value:
                    continue
                parts.append(value)
                total += len(value)
                if total > limit:
                    return " ".join(parts)
    return " ".join(parts)


def fingerprint_platform(pages, extras):
    """Identify the platform serving the *audited origin*, not its subdomains.

    A blog or docs subdomain very often runs on something else entirely, and
    letting it vote produces a confident, wrong answer - which would then tell
    the team to edit files in a CMS they do not use. Restricting the sample to
    the primary host costs a little coverage and prevents that.
    """
    origin_host = ""
    for page in pages:
        if page.is_home:
            origin_host = urlsplit(page.url).netloc.lower()
            break
    primary = [p for p in pages if not origin_host
               or urlsplit(p.url).netloc.lower() == origin_host] or pages
    pages = primary

    scores, evidence = {}, {}

    def add(label, weight, why):
        scores[label] = scores.get(label, 0) + weight
        evidence.setdefault(label, []).append(why)

    for page in pages[:8]:
        # Match against attribute values (src, href, class, id, content) rather
        # than the whole document. Platform names are ordinary words in prose -
        # a payments company documenting its WooCommerce integration is not
        # running WooCommerce - and a confident wrong platform produces
        # remediation steps for a CMS the team does not have, which is worse
        # than offering none.
        markup = _attribute_blob(page.doc)
        generator = page.doc.meta().get("generator", "")
        headers_blob = " ".join(f"{k}: {v}" for k, v in page.headers.items())
        for label, weight, where, pattern in PLATFORM_SIGNATURES:
            blob = {"html": markup, "header": headers_blob, "generator": generator}[where]
            if blob and re.search(pattern, blob, re.I):
                add(label, weight, f"{where} matched /{pattern[:40]}/ on {page.url}")

    platform, confidence = "unknown", "low"
    if scores:
        # Deterministic tie-break by name so repeat runs agree.
        platform = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        top = scores[platform]
        # The bar for "medium" is set so a single weak marker on one page can
        # never reach the level at which platform-specific advice is emitted.
        confidence = "high" if top >= 12 else "medium" if top >= 8 else "low"

    host_stack = []
    server_blob = " ".join(
        (p.header("server", "") + " " + p.header("x-powered-by", "") + " " + p.header("x-served-by", ""))
        for p in pages[:5]
    )
    for label, pattern in HOST_SIGNATURES:
        if re.search(pattern, server_blob, re.I):
            host_stack.append(label)

    analytics = []
    blob = " ".join(p.html for p in pages[:5])
    for label, pattern in ANALYTICS_SIGNATURES:
        if re.search(pattern, blob, re.I):
            analytics.append(label)

    return {
        "platform": platform,
        "platform_confidence": confidence,
        "platform_scores": dict(sorted(scores.items(), key=lambda kv: -kv[1])[:6]),
        "platform_evidence": evidence.get(platform, [])[:3],
        "hosting_stack": sorted(set(host_stack)),
        "analytics": sorted(set(analytics)),
    }


def classify_site(cache, pages):
    """Weighted vote over URL shapes, schema types and page text.

    Deliberately returns "unknown" when no type clears the bar. A wrong site
    type is worse than no site type: it turns on the wrong checks.
    """
    votes = {k: 0.0 for k in
             ("ecommerce", "saas", "local_business", "media_publisher", "documentation",
              "brochure", "marketplace", "institutional")}
    signals = []
    types_seen = cache.page_types()
    text_blob = " ".join(p.doc.main_text[:6000] for p in pages[:8])
    schema_types = set()
    for page in pages[:12]:
        for obj in schema_mod.extract_objects(page.doc):
            schema_types.update(schema_mod.types_of(obj))

    def vote(kind, amount, why):
        votes[kind] += amount
        signals.append(f"{kind} +{amount}: {why}")

    # Structured data is the strongest single signal when it is present.
    if {"Product", "Offer", "AggregateOffer"} & schema_types:
        vote("ecommerce", 3, "Product/Offer schema present")
    if {"LocalBusiness", "Restaurant", "Store", "Dentist", "MedicalBusiness", "ProfessionalService"} & schema_types:
        vote("local_business", 3, "LocalBusiness-family schema present")
    if {"NewsArticle", "BlogPosting", "Article"} & schema_types:
        vote("media_publisher", 2.5, "Article-family schema present")
    if {"NewsMediaOrganization"} & schema_types:
        vote("media_publisher", 2, "NewsMediaOrganization schema present")
    if {"EducationalOrganization", "CollegeOrUniversity", "School", "GovernmentOrganization",
        "NGO", "Course"} & schema_types:
        vote("institutional", 3, "educational/government/NGO schema present")
    if {"SoftwareApplication", "WebApplication", "Service"} & schema_types:
        vote("saas", 2, "SoftwareApplication/Service schema present")

    # URL shape.
    if types_seen.get("product", 0) >= 2:
        vote("ecommerce", 2, f"{types_seen['product']} product URLs sampled")
    if types_seen.get("category", 0) >= 2:
        vote("ecommerce", 1, f"{types_seen['category']} category URLs sampled")
    if types_seen.get("docs", 0) >= 4:
        vote("documentation", 3, f"{types_seen['docs']} documentation URLs sampled")
    elif types_seen.get("docs", 0) >= 2:
        vote("documentation", 2, f"{types_seen['docs']} documentation URLs sampled")
    if types_seen.get("article", 0) >= 2:
        vote("media_publisher", 2, f"{types_seen['article']} article URLs sampled")
    # A date in the path is the strongest single indicator of a publishing site.
    dated = sum(1 for p in pages if re.search(r"/(19|20)\d{2}/(\d{1,2}/)?", p.url))
    if dated >= 2:
        vote("media_publisher", 2.5, f"{dated} URLs contain a date path segment")
    if types_seen.get("pricing", 0) >= 1:
        vote("saas", 1.5, "a pricing page exists")

    # Page text.
    commerce_hits = len(COMMERCE_TEXT.findall(text_blob))
    saas_hits = len(SAAS_TEXT.findall(text_blob))
    local_hits = len(LOCAL_TEXT.findall(text_blob))
    if commerce_hits >= 3:
        vote("ecommerce", 2, f"{commerce_hits} commerce phrases in body text")
    if saas_hits >= 3:
        vote("saas", 2, f"{saas_hits} SaaS phrases in body text")
    if local_hits >= 2 or (ADDRESS_RE.search(text_blob) and PHONE_RE.search(text_blob)):
        vote("local_business", 2, "address/hours/phone patterns in body text")

    # Institutional signals: the registrable domain is often decisive, and this
    # class of site (government, education, charity) otherwise falls through to
    # "unknown", which reads as the profiler failing rather than as caution.
    host = (cache.site or "").lower()
    # A registry-controlled domain is decisive, not merely heavy. These suffixes
    # cannot be registered without being the kind of body they denote, so they
    # outrank content-shape signals: an institution that also publishes news is
    # still an institution, and "has articles" must not outvote "is a
    # government". Set authoritatively instead of raising the weight, which
    # would only start a vote arms race with the next generic signal.
    authoritative = ""
    if re.search(r"(^|\.)(gov|mil)(\.[a-z]{2})?$", host) or host.endswith(".gov.uk"):
        vote("institutional", 4, f"government domain ({host})")
        authoritative = f"government domain ({host})"
    elif re.search(r"(^|\.)(edu|ac\.[a-z]{2})$", host) or host.endswith(".ac.uk"):
        vote("institutional", 4, f"academic domain ({host})")
        authoritative = f"academic domain ({host})"
    institutional_hits = len(INSTITUTIONAL_TEXT.findall(text_blob))
    if institutional_hits >= 3:
        vote("institutional", 2, f"{institutional_hits} institutional phrases in body text")
    if host.endswith(".org") and institutional_hits >= 3:
        vote("institutional", 2.5, f".org domain with {institutional_hits} mission/donation phrases")
    elif host.endswith(".org") and institutional_hits >= 1:
        vote("institutional", 1.5, ".org domain with mission/donation language")

    # Text and code-block signals only corroborate a structural one. On their
    # own they elect "documentation" for any site that happens to use technical
    # vocabulary, which is how a news site ends up misclassified - and a wrong
    # site type turns on the wrong checks, which is worse than no type at all.
    if types_seen.get("docs", 0) >= 1:
        docs_hits = len(DOCS_TEXT.findall(text_blob))
        code_blocks = sum(p.doc.count("pre") for p in pages[:8])
        if docs_hits >= 4:
            vote("documentation", 1.5, f"{docs_hits} documentation phrases in body text")
        if code_blocks >= 5:
            vote("documentation", 1.5, f"{code_blocks} code blocks across sampled pages")

    total_pages = len(cache.html_pages())
    if total_pages <= 6 and votes["ecommerce"] < 2 and votes["documentation"] < 2:
        vote("brochure", 1.5, f"only {total_pages} crawlable HTML pages found")

    ranked = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))
    best, best_score = ranked[0]
    site_type = best if best_score >= 2.5 else "unknown"
    confidence = "high" if best_score >= 5 else "medium" if best_score >= 2.5 else "low"
    if authoritative:
        if site_type != "institutional":
            signals.append(
                f"institutional overrides {site_type or 'unknown'}: {authoritative} "
                f"is registry-controlled and outranks content-shape signals")
        site_type, confidence = "institutional", "high"
    return {
        "site_type": site_type,
        "site_type_confidence": confidence,
        "site_type_votes": {k: round(v, 1) for k, v in ranked if v > 0},
        "site_type_signals": signals[:10],
        "schema_types_seen": sorted(schema_types)[:25],
        "has_pricing_page": types_seen.get("pricing", 0) > 0,
        "has_blog": types_seen.get("article", 0) > 0,
        "has_contact_page": types_seen.get("contact", 0) > 0,
        "has_about_page": types_seen.get("about", 0) > 0,
        "prices_in_text": bool(PRICE_RE.search(text_blob)),
    }


def main():
    ap = argparse.ArgumentParser(description="Profile the audited site")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--json", action="store_true", help="print the profile to stdout")
    args = ap.parse_args()
    force_utf8_stdout()

    cache = cache_mod.load(args.cache)
    pages = cache.html_pages()
    if not pages:
        profile = {"site_type": "unknown", "site_type_confidence": "low",
                   "platform": "unknown", "platform_confidence": "low",
                   "note": "no HTML pages were fetched; every page-level check will be skipped"}
    else:
        profile = {}
        profile.update(classify_site(cache, pages))
        profile.update(fingerprint_platform(pages, cache.extras))
        langs = [p.doc.lang for p in pages if p.doc.lang]
        profile["primary_language"] = (max(set(langs), key=langs.count) if langs else "")
        profile["page_types_seen"] = sorted(cache.page_types())
        profile["pages_analyzed"] = len(pages)

    manifest_path = os.path.join(args.cache, "manifest.json")
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["profile"] = profile
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    if args.json:
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
