#!/usr/bin/env python3
"""Turn findings into fixes someone can actually carry out, and add the
improvements worth making where nothing is broken.

Two jobs, both of which need every detector's output plus the site profile, and
neither of which belongs inside a detector:

1. **Platform-specific remediation.** "Add Product JSON-LD" is correct and
   unhelpful. Where the site's CMS or framework has been identified, each
   suggested action gains steps naming the actual place to make the change.
   Detection stays generic; prescription becomes specific.

2. **Proactive recommendations.** Improvements that strengthen discoverability
   and engagement where no defect was found. They are kept strictly separate
   from findings - a finding has evidence of a problem, a recommendation does
   not - and are suppressed when the related defect is already reported, so the
   report never asks for the same thing twice.

Usage:
    python plan_remediation.py --cache ./cache --findings-dir ./work \
        --proactive-out ./proactive.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
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

from auditlib import force_utf8_stdout  # noqa: E402
from auditlib import cache as cache_mod, findings as F  # noqa: E402

# Each finding is mapped to a remediation topic; playbooks are written per
# topic per platform. This keeps the matrix small and means a new detector
# check inherits platform guidance by declaring its topic, not by editing every
# playbook.
CHECK_TOPIC = {
    "ACC-001": "robots", "ACC-002": "robots", "ACC-003": "robots", "ACC-005": "robots", "ACC-006": "robots",
    "ACC-008": "edge", "ACC-009": "edge", "ACC-010": "edge",
    "ACC-011": "sitemap", "ACC-012": "sitemap", "ACC-013": "sitemap", "ACC-014": "sitemap", "ACC-015": "sitemap",
    "ACC-016": "noindex", "ACC-018": "canonical", "ACC-019": "canonical", "ACC-020": "canonical",
    "ACC-021": "redirects", "ACC-022": "redirects", "ACC-025": "redirects", "ACC-026": "notfound",
    "RND-001": "ssr", "RND-002": "ssr", "RND-003": "ssr", "RND-004": "ssr",
    "RND-006": "media", "RND-007": "media", "RND-008": "media", "RND-009": "media",
    "RND-012": "template", "RND-013": "template", "RND-014": "template", "RND-015": "template",
    "SDA-001": "jsonld", "SDA-002": "jsonld", "SDA-003": "jsonld", "SDA-004": "jsonld",
    "SDA-005": "jsonld", "SDA-006": "jsonld", "SDA-007": "jsonld", "SDA-008": "jsonld",
    "SDA-009": "jsonld", "SDA-010": "jsonld",
    "ANS-003": "meta", "ANS-004": "meta", "ANS-005": "meta",
    "ENT-002": "jsonld", "ENT-003": "jsonld", "ENT-004": "jsonld",
    "ENG-007": "template", "ENG-008": "media", "ENG-012": "template", "ENG-015": "template",
}

# Platform playbooks. Written from the perspective of someone who has to open
# the right file or screen - that is the whole point of this skill.
PLAYBOOKS = {
    "Adobe Experience Manager": {
        "jsonld": [
            "Add the JSON-LD to the page component's HTL template (typically `/apps/<project>/components/page/customheaderlibs.html`), "
            "populated from the page properties or the content fragment model rather than hard-coded.",
            "Expose the fields through a Sling Model so authors edit them in the page properties dialog and cannot leave them blank.",
            "For Content Fragment-driven pages, map fragment fields to schema properties once in the model so every fragment inherits it.",
        ],
        "ssr": [
            "AEM renders server-side by default - a render gap here usually means a client-side SPA component is "
            "assembling the content. Check the SPA Editor components and move content into HTL-rendered components "
            "or supply server-rendered fallback markup.",
        ],
        "meta": [
            "Set page title and description in the page properties dialog; expose them as required fields so authors "
            "cannot publish without them.",
            "Verify the template's `customheaderlibs.html` emits them rather than falling back to the page name.",
        ],
        "sitemap": [
            "Enable the AEM sitemap servlet (`/content/<site>.sitemap.xml`) or the ACS Commons sitemap, and map it "
            "to `/sitemap.xml` at the dispatcher.",
            "Add the `Sitemap:` line to the robots.txt served by the dispatcher.",
        ],
        "robots": [
            "robots.txt is normally served through the dispatcher - edit it there rather than in the repository, and "
            "confirm the dispatcher is not serving a cached staging copy.",
        ],
        "canonical": [
            "Emit the canonical link in the page template from the externalised page path, using the Externalizer "
            "service so the published domain is used rather than the author instance host.",
        ],
        "template": [
            "Fix this once in the base page component template so every page inherits it.",
        ],
        "edge": [
            "Check the dispatcher filter rules and any CDN in front of it - dispatcher `/filter` sections are a "
            "common place for crawler requests to be rejected.",
        ],
    },
    "Adobe Edge Delivery Services": {
        "jsonld": [
            "Add the JSON-LD in `scripts/scripts.js` during page decoration, or emit it from the document's metadata "
            "table so authors control it from the source document.",
            "Use the metadata table in the authoring source (Word or Google Docs) for per-page values so the markup "
            "stays author-editable.",
        ],
        "ssr": [
            "Edge Delivery serves static HTML, so a render gap usually means a block is fetching content client-side. "
            "Move the content into the authored document, or have the block render server-fetched content into the "
            "DOM before the page is considered loaded.",
        ],
        "meta": [
            "Set Title and Description in the document's metadata table; they are published straight into the head.",
        ],
        "sitemap": [
            "Configure the sitemap in `helix-sitemap.yaml` (or the project's equivalent) and confirm it publishes.",
        ],
        "template": [
            "Apply the change in `scripts/scripts.js` or the relevant block so every page inherits it.",
        ],
    },
    "Adobe Commerce (Magento)": {
        "jsonld": [
            "Product and Offer markup is emitted by the theme - override the relevant template in your theme "
            "(`Magento_Catalog::product/view.phtml` and related) rather than editing the core module.",
            "Populate price and availability from the product's final price and stock status so the markup tracks "
            "live data.",
        ],
        "meta": ["Set meta title and description per product and category in the admin, and configure the "
                 "store-level templates so new products inherit a sensible default."],
        "sitemap": ["Configure the sitemap under Marketing > SEO & Search > Site Map and schedule its regeneration; "
                    "confirm the cron job that regenerates it is actually running."],
        "robots": ["Edit robots.txt under Content > Design > Configuration > Search Engine Robots."],
    },
    "Shopify": {
        "jsonld": [
            "Add the JSON-LD to `snippets/` and include it from `theme.liquid`, populated from the `product`, `shop` "
            "and `collection` Liquid objects.",
            "Use `product.selected_or_first_available_variant.price | money_without_currency` and "
            "`product.available` so price and availability follow the variant the customer is viewing.",
        ],
        "meta": ["Edit the title and description templates in `theme.liquid` and set per-product values in the admin's "
                 "search-listing preview."],
        "robots": ["Customise robots.txt through the `robots.txt.liquid` template - the file cannot be edited directly."],
        "sitemap": ["Shopify generates /sitemap.xml automatically; if pages are missing, check they are published and "
                    "not excluded from the sales channel."],
        "template": ["Make the change in `theme.liquid` so it applies to every template."],
    },
    "WordPress": {
        "jsonld": [
            "If an SEO plugin is active, configure its schema settings rather than adding a second, conflicting "
            "block - duplicated disagreeing markup is worse than none.",
            "Otherwise add the JSON-LD via a `wp_head` action in the theme's `functions.php`, built from post meta.",
        ],
        "meta": ["Set titles and descriptions through the active SEO plugin's per-post fields, and fix the site-wide "
                 "title template so new posts inherit a good default."],
        "sitemap": ["Use the SEO plugin's sitemap, or WordPress core's `/wp-sitemap.xml`; make sure only one is "
                    "active and that it is the one declared in robots.txt."],
        "robots": ["Check Settings > Reading for the 'Discourage search engines' option, which silently adds a "
                   "site-wide noindex - it is the most common cause of an accidentally invisible WordPress site."],
        "noindex": ["Check Settings > Reading > 'Discourage search engines from indexing this site' first; then the "
                    "SEO plugin's per-post and taxonomy-level indexing settings."],
        "template": ["Apply the change in the theme's `header.php` or via a `wp_head` hook in a child theme so "
                     "updates do not overwrite it."],
    },
    "Next.js": {
        "jsonld": [
            "Emit the JSON-LD from the route's server component (or `generateMetadata` for metadata fields), so it is "
            "present in the server-rendered HTML rather than added on the client.",
            "Build the object from the same data the page fetches, so the markup cannot drift from what is displayed.",
        ],
        "ssr": [
            "Move the affected routes off client-only rendering: use server components, `generateStaticParams` for "
            "static routes, or `getServerSideProps` in the pages router.",
            "Confirm the fix at the transport layer - `curl -s <url>` must contain the page's text, not just the "
            "hydration payload in `__NEXT_DATA__` or the flight stream.",
        ],
        "meta": ["Export `metadata` or `generateMetadata` per route so each page has its own title and description."],
        "sitemap": ["Add `app/sitemap.ts` (or `next-sitemap`) and ensure it enumerates dynamic routes."],
        "canonical": ["Set `alternates.canonical` in each route's metadata to the page's own absolute URL."],
        "robots": ["Add `app/robots.ts` or a static `public/robots.txt`."],
    },
    "Nuxt": {
        "jsonld": ["Use `useHead` / `useSeoMeta` in the page component to emit the JSON-LD script server-side."],
        "ssr": ["Ensure the route is not `ssr: false`; check `nuxt.config` route rules and any `<ClientOnly>` wrapper "
                "around the primary content."],
        "meta": ["Set title and description per page with `useSeoMeta`."],
        "sitemap": ["Add the sitemap module and confirm dynamic routes are enumerated."],
    },
    "Webflow": {
        "jsonld": ["Add the JSON-LD in Page Settings > Custom Code > Head, using CMS field bindings so collection "
                   "pages populate per item."],
        "meta": ["Set the SEO title and description per page, and use field bindings on collection templates."],
        "template": ["Change the collection page template so every item inherits it."],
    },
    "Squarespace": {
        "jsonld": ["Add the JSON-LD under Settings > Advanced > Code Injection, or per page in Page Settings > "
                   "Advanced > Page Header Code Injection."],
        "meta": ["Set the SEO title and description per page under Page Settings > SEO."],
    },
    "Wix": {
        "jsonld": ["Use the SEO settings panel's structured data markup section, per page and per dynamic page "
                   "template."],
        "meta": ["Set title and description per page in the SEO panel; use dynamic patterns for collection pages."],
    },
    "Drupal": {
        "jsonld": ["Use the Schema.org Metatag module and map fields per content type rather than hard-coding markup "
                   "in templates."],
        "meta": ["Configure the Metatag module's per-content-type token patterns."],
        "sitemap": ["Use the Simple XML Sitemap module and confirm the relevant entity types are enabled."],
    },
    "HubSpot CMS": {
        "jsonld": ["Add the JSON-LD to the template's head via a HubL module so it can be populated from page or "
                   "HubDB fields."],
        "meta": ["Set page title and description in the page editor's settings tab."],
    },
}

# Generic fallbacks so an unknown platform still gets something more concrete
# than the base action.
GENERIC = {
    "jsonld": ["Emit the markup from the shared page template so every page of that class inherits it, and build it "
               "from the same data the page renders."],
    "ssr": ["Render the content on the server for the affected routes and verify with `curl -s <url>` that the text "
            "is in the response body."],
    "meta": ["Set the values in the shared layout with a per-page override, so a new page cannot ship without them."],
    "edge": ["Make this change in the CDN or WAF configuration rather than in application code."],
}


def platform_steps(platform, topic):
    book = PLAYBOOKS.get(platform, {})
    steps = book.get(topic)
    if steps:
        return steps
    return GENERIC.get(topic)


def annotate(findings_dir, profile):
    """Attach platform-specific steps to each finding, in place."""
    platform = profile.get("platform", "unknown")
    confidence = profile.get("platform_confidence", "low")
    annotated = 0
    # A low-confidence platform guess is not a basis for telling someone to
    # edit a specific file. Fall back to the generic guidance instead.
    trust_platform = platform != "unknown" and confidence in ("high", "medium")

    for path in sorted(glob.glob(os.path.join(findings_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        changed = False
        for finding in payload.get("findings", []):
            topic = CHECK_TOPIC.get(finding.get("check_id"))
            if not topic:
                continue
            steps = platform_steps(platform if trust_platform else "", topic)
            if not steps:
                continue
            label = platform if trust_platform else "this stack"
            finding["suggested_action"]["platform_specific"] = list(steps)
            finding["suggested_action"]["platform"] = label
            annotated += 1
            changed = True
        if changed:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
    return annotated, platform, trust_platform


def existing_check_ids(findings_dir):
    ids = set()
    for path in glob.glob(os.path.join(findings_dir, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                for finding in json.load(fh).get("findings", []):
                    ids.add(finding.get("check_id"))
        except (OSError, json.JSONDecodeError):
            continue
    return ids


def build_recommendations(cache, present_checks):
    """Improvements worth making where no defect was detected.

    Each is gated: on site type, on what the crawl actually found, and on
    whether the matching defect is already reported as a finding. A
    recommendation that repeats a finding is noise.
    """
    profile = cache.profile
    site_type = profile.get("site_type", "unknown")
    extras = cache.extras
    recs, index = [], [0]

    # Nothing was observed, so nothing can be recommended. Suggesting content
    # strategy for a site that did not respond is noise that undermines the one
    # finding that matters.
    if cache.manifest.get("unreachable") or not cache.html_pages():
        return recs


    def add(title, rationale, priority, how, applies=None, effort="medium"):
        index[0] += 1
        recs.append(F.recommendation(f"P-{index[0]:03d}", title, rationale, priority, how, applies, effort))

    # 1. llms.txt - absence is never a defect, so it belongs here rather than
    #    in a detector.
    if extras.get("probes", {}).get("llms_txt", {}).get("status") != 200:
        add(
            "Publish an /llms.txt index of the site's most quotable pages",
            "Assistants that fetch pages live have to guess which URLs carry the facts they need. An llms.txt file "
            "is an emerging convention for stating that explicitly - a short, plain-text map of the pages a machine "
            "should read first. It costs almost nothing, and where it is honoured it puts the brand in control of "
            "which pages represent it.",
            "medium",
            [
                "Create `/llms.txt`: an H1 with the organisation's name, a blockquote with the one-line description, "
                "then linked sections for the pages that answer real questions - what the company does, products, "
                "pricing, contact, documentation.",
                "Keep it to the pages a machine should read first, not a mirror of the sitemap.",
                "Optionally publish clean Markdown mirrors of those pages and link them from it.",
                "Keep it current: a stale index is worse than none, because it directs readers to the wrong pages.",
            ],
            effort="low",
        )

    # 2. A citable-facts page - the supply side of corroboration.
    if "ENT-006" not in present_checks:
        add(
            "Publish a facts-and-figures page that other sources can cite",
            "A claim repeated across many independent sources is treated as reliable; one that exists in a single "
            "place is fragile. Journalists, directories, analysts and assistants can only repeat facts that are "
            "stated somewhere quotable, in a stable location, with a date attached. Most organisations never publish "
            "this, and then wonder why the web describes them inaccurately.",
            "medium",
            [
                "Create a page carrying the organisation's canonical facts: legal name, founding year, headquarters, "
                "leadership, size, key figures - each as a short declarative sentence.",
                "Date every figure and update them on a fixed schedule.",
                "Give it a stable URL and link it from the About page, the footer and any press materials.",
                "Mirror the same values in Organization structured data so they are machine-readable too.",
            ],
        )

    # 3. Question-shaped content from real customer questions.
    if "ANS-008" not in present_checks and "SDA-009" not in present_checks:
        add(
            "Publish answers to the questions customers actually ask, in their words",
            "Retrieval matches a user's question against candidate passages. Content already written as a question "
            "with a self-contained answer matches directly, while the same information as narrative prose has to be "
            "located inside a longer passage first. The wording matters as much as the format: customers ask in "
            "their own vocabulary, not the brand's product names.",
            "medium",
            [
                "Collect the real questions from sales calls, support tickets and site search logs.",
                "Publish each with an answer that stands alone when quoted out of context.",
                "Use the customer's phrasing in the question; introduce internal product vocabulary in the answer.",
                "Mark the block up as FAQPage.",
            ],
        )

    # 4. Comparison and qualification coverage.
    if site_type in ("saas", "ecommerce", "marketplace") and "ANS-009" not in present_checks:
        add(
            "Publish honest comparison and 'is this right for me' pages",
            "A large share of the questions put to assistants are comparative or qualifying. If the brand does not "
            "answer them, review sites and competitors' comparison pages do - and those are the sources that get "
            "cited. Even-handed pages that say where an alternative is the better fit are cited more often than "
            "promotional ones, because they read as reliable.",
            "medium",
            [
                "Write comparisons against the alternatives buyers genuinely evaluate, including the cases where the "
                "alternative wins.",
                "Publish `for <industry>` or `for <role>` pages describing the specific situation each serves.",
                "Title each page as the question it answers.",
                "Keep them current - a comparison against an outdated competitor version damages credibility.",
            ],
            effort="high",
        )

    # 5. Redundancy for non-text assets.
    add(
        "Make every fact that appears in an image, video or PDF also available as text",
        "Facts carried only by non-textual media are invisible to text-based readers, and this is systematically "
        "true of the highest-value facts - price lists, specifications, opening hours, menus - because those are the "
        "ones designers most often set as graphics. Publishing the text alongside costs little and removes an entire "
        "class of invisibility.",
        "medium",
        [
            "Adopt a rule that no fact may exist only in a non-text asset: if it is in an image, a diagram, a video "
            "or a PDF, it is also in HTML text on the same page.",
            "Give data-bearing images alt text that states what they communicate, and put the underlying data in a "
            "table beside them.",
            "Publish transcripts and summaries for video and audio.",
            "Where a PDF is the canonical document, publish an HTML summary of its key facts as well.",
        ],
    )

    # 6. Identity graph.
    if "ENT-002" not in present_checks and "ENT-003" not in present_checks:
        add(
            "Strengthen the brand's identity graph across authoritative sources",
            "Entity confusion is one of the main causes of an assistant describing a brand inaccurately. The defence "
            "is a consistent, mutually linked set of identity records: the same canonical description, the same "
            "legal name, the same location, asserted in several places that reference one another.",
            "medium",
            [
                "Create or claim a Wikidata item; it is openly editable and widely consumed as an identity reference.",
                "Align the description on LinkedIn, Crunchbase, GitHub and industry directories with the site's "
                "canonical sentence, word for word.",
                "Declare each of them in the site's Organization `sameAs`, and link back where the platform allows.",
                "Use the qualified brand name consistently - `<Brand>, the <category> for <audience>` - so the "
                "distinguishing phrase is what gets repeated.",
            ],
        )

    # 7. Make interior pages self-sufficient.
    if "ENG-001" not in present_checks:
        add(
            "Design interior pages for visitors who arrive without context",
            "Assistant referrals land deep in a site rather than on the homepage, and they arrive with no idea whose "
            "site they are on. Pages built on the assumption that the visitor came through the front door lose them "
            "immediately - so the more successful the discoverability work, the more traffic this wastes.",
            "medium",
            [
                "Ensure every page states the organisation's name and what it does, in text.",
                "Add breadcrumbs so a visitor can see where they have landed.",
                "End each page with a next step chosen for that page's subject.",
                "Review the pages assistants most often cite and treat each as a potential first impression.",
            ],
            effort="low",
        )

    # 8. Measurement of the traffic these fixes produce.
    if "ENG-016" not in present_checks:
        add(
            "Segment assistant-referred traffic so this work can be evaluated",
            "AI-referred visits behave differently from search visits: they land deeper, arrive with more context, "
            "and convert on different pages. Without a separate segment they are averaged into search traffic and "
            "the effect of any discoverability work is invisible.",
            "low",
            [
                "Create an analytics segment for known assistant referrers and review it separately.",
                "Report on landing page, onward navigation and conversion for that segment specifically.",
                "Watch server logs for the AI crawler user agents to confirm the site is actually being fetched.",
            ],
            effort="low",
        )

    return recs


def main():
    ap = argparse.ArgumentParser(description="Platform-specific remediation and proactive recommendations")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--findings-dir", required=True)
    ap.add_argument("--proactive-out", required=True)
    args = ap.parse_args()
    force_utf8_stdout()

    cache = cache_mod.load(args.cache)
    annotated, platform, trusted = annotate(args.findings_dir, cache.profile)
    recommendations = build_recommendations(cache, existing_check_ids(args.findings_dir))

    with open(args.proactive_out, "w", encoding="utf-8") as fh:
        json.dump({"proactive_recommendations": recommendations}, fh, indent=2, ensure_ascii=False)

    print(json.dumps({
        "ok": True,
        "platform": platform,
        "platform_guidance_applied": trusted,
        "findings_annotated": annotated,
        "recommendations": len(recommendations),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
