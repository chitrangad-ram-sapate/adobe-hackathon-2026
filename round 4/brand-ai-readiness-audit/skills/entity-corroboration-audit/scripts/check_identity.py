#!/usr/bin/env python3
"""Gate 4 - Trust. Will an extracted fact be believed and repeated?

Reaching, reading and quoting a page is not enough. A system deciding what to
say about a brand weighs whether the claim is corroborated, whether the entity
is unambiguous, and whether the content is current. Three failure modes matter:

* **Self-inconsistency.** The brand describes itself differently in its title,
  its meta description, its social tags and its structured data. A system with
  four conflicting descriptions hedges, or picks the least useful one.
* **Entity ambiguity.** Nothing distinguishes this brand from the other things
  sharing its name, so facts about one get attached to another.
* **Staleness.** Nothing indicates the content is current, so it is discounted
  against a fresher source that may be less accurate.

This detector works only from the site itself. Genuine off-site corroboration
would need external sources; where that is unavailable, the checks measure
whether the site does the things that *enable* corroboration - publishing
identity links, citable facts, and dates - and the report says so rather than
implying the wider web was consulted.

Usage:
    python check_identity.py --cache ./cache
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone


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

CURRENT_YEAR = datetime.now(timezone.utc).year

COPYRIGHT = re.compile(r"(?:©|\(c\)|copyright)\s*(?:\d{4}\s*[-–—]\s*)?(\d{4})", re.I)
CATEGORY_NOUN = re.compile(
    r"\b(platform|software|app|tool|service|agency|studio|company|firm|consultancy|marketplace|"
    r"shop|store|retailer|manufacturer|supplier|distributor|clinic|restaurant|hotel|school|"
    r"university|charity|bank|solution|system|robots?|equipment|products?|services?|for)\b", re.I
)
FOUNDING_FACT = re.compile(
    r"\b(founded in|established in|since \d{4}|incorporated in|started in|we were founded|"
    r"headquartered in|based in|our headquarters)\b", re.I
)
CITABLE_STAT = re.compile(
    r"\b(\d[\d,]*\+?\s*(customers|clients|users|employees|staff|countries|locations|stores|"
    r"projects|installations|patients|students|members)|\d+(\.\d+)?\s*(million|billion|thousand))\b", re.I
)
SOCIAL_HOST = re.compile(
    r"(linkedin\.com|twitter\.com|x\.com|facebook\.com|instagram\.com|youtube\.com|github\.com|"
    r"crunchbase\.com|wikipedia\.org|wikidata\.org|tiktok\.com|threads\.net|mastodon)", re.I
)
PHONE = re.compile(r"(\+\d{1,3}[\s.\-()]{0,3})?(\(?\d{2,5}\)?[\s.\-]{0,2}){2,4}\d{2,5}")


def _tokens(text):
    return {t for t in re.findall(r"[a-z]{4,}", (text or "").lower())}


def _jaccard(a, b):
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 1.0  # nothing to disagree about
    return len(ta & tb) / len(ta | tb)


def _org_objects(cache):
    home = cache.home
    if not home:
        return []
    return [o for o in schema.extract_objects(home.doc) if set(schema.types_of(o)) & schema.ORG_TYPES]


def check_description_consistency(cache, out, skipped):
    home = cache.home
    if not home:
        skipped.append(F.skip("ENT-001", "no homepage was fetched"))
        return

    meta = home.doc.meta()
    candidates = {
        "meta description": meta.get("description", "").strip(),
        "og:description": meta.get("og:description", "").strip(),
        "twitter:description": meta.get("twitter:description", "").strip(),
    }
    for obj in _org_objects(cache):
        description = obj.get("description")
        if isinstance(description, str) and description.strip():
            candidates["Organization schema description"] = description.strip()
            break

    present = {k: v for k, v in candidates.items() if len(v) > 30}
    if len(present) < 2:
        skipped.append(F.skip("ENT-001", "fewer than two self-descriptions present to compare"))
        return

    keys = sorted(present)
    divergent = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            similarity = _jaccard(present[a], present[b])
            if similarity < 0.35:
                divergent.append({"a": a, "b": b, "similarity": round(similarity, 2)})

    if not divergent:
        return
    worst = min(divergent, key=lambda d: d["similarity"])
    out.append(F.finding(
        "ENT-001", "The brand describes itself differently in different places on the same page",
        "medium", "discoverability", "trust",
        evidence=f"{len(divergent)} pair(s) of self-descriptions on the homepage share little vocabulary; the "
                 f"{worst['a']} and the {worst['b']} overlap by only {int(worst['similarity'] * 100)}% "
                 f"(\"{present[worst['a']][:70]}\" vs \"{present[worst['b']][:70]}\").",
        mechanism="These fields are read by different consumers, and together they form the brand's self-description. "
                  "When they disagree, a system has no single authoritative account of what the brand is; it either "
                  "hedges, blends them into something the brand never said, or prefers a third-party description that "
                  "at least appears consistently.",
        action_summary="Write one canonical description of the organisation and use it in every one of these fields.",
        how=[
            "Agree a single sentence describing what the organisation is, who it serves and where.",
            "Use it verbatim in the meta description, og:description, twitter:description and the Organization "
            "schema `description`.",
            "Use the same sentence in off-site profiles - LinkedIn, Crunchbase, directories - so the description "
            "the wider web repeats matches the site.",
        ],
        effort="low", owner="marketing", method="static",
        affected_urls=[home.url], affected_count=1, sampled_count=1,
        evidence_detail={"descriptions": {k: v[:200] for k, v in present.items()}, "divergent_pairs": divergent},
    ))


def check_identity_graph(cache, out, skipped):
    """sameAs links are how a brand asserts it is the same entity as elsewhere."""
    home = cache.home
    if not home:
        return
    objects = _org_objects(cache)
    links = schema.sameas_of(objects)
    classified = schema.classify_sameas(links)

    # Social links visible in the page but never declared as sameAs.
    page_social = set()
    for href, _text, _rel, _node in home.doc.links():
        resolved = urls.normalize(href, base=home.url)
        if resolved and SOCIAL_HOST.search(resolved) and not urls.same_site(resolved, home.url):
            page_social.add(resolved.split("?")[0])

    if not links:
        severity = "medium" if objects else "low"
        out.append(F.finding(
            "ENT-002", "The site never declares which external profiles belong to this brand",
            severity, "discoverability", "trust",
            evidence=(f"0 sameAs links are declared across {len(objects)} Organization-family node(s) on the "
                      "homepage"
                      + (f", although {len(page_social)} external profile link(s) appear on the page "
                         f"({', '.join(sorted(page_social)[:3])})" if page_social else
                         ", and 0 external brand profile links appear on the page") + "."),
            mechanism="sameAs is the machine-readable claim that this site, this company registry entry, this "
                      "LinkedIn page and this Wikipedia article are one entity. Without it, corroborating facts "
                      "scattered across those sources are not recognised as being about the same organisation, so "
                      "each one stands alone and is weaker - and a similarly named organisation can be confused "
                      "with this one.",
            action_summary="Declare sameAs links from Organization schema to every profile the brand controls.",
            how=[
                "Add a `sameAs` array to the Organization block listing the brand's authoritative profiles.",
                "Prioritise identity authorities over social reach: Wikidata, Wikipedia, LinkedIn, Crunchbase, "
                "a company register entry, GitHub - these disambiguate; a follower count does not.",
                "Make the links reciprocal where possible: the profile should link back to the site.",
            ],
            effort="low", owner="marketing", method="static",
            affected_urls=[home.url], affected_count=1, sampled_count=1,
            evidence_detail={"social_links_on_page": sorted(page_social)[:10]},
        ))
        return

    undeclared = sorted(page_social - {l.split("?")[0] for l in links})
    if not classified["authorities"]:
        out.append(F.finding(
            "ENT-003", "Identity links point only at social accounts, not at identity authorities",
            "low", "discoverability", "trust",
            evidence=f"{len(links)} sameAs links are declared, all social "
                     f"({', '.join(sorted(classified['social'])[:4]) or 'unclassified'}), with no link to Wikidata, "
                     "Wikipedia, LinkedIn, a company register or an industry authority.",
            mechanism="Social profiles establish presence but are weak at establishing identity - they are easy to "
                      "create and rarely used as a reference point. Authority records are what a system uses to "
                      "decide that two mentions refer to the same organisation.",
            action_summary="Add authority profiles to sameAs, and create the ones that do not exist.",
            how=["Add LinkedIn company page, Crunchbase, a company register entry and, where the brand qualifies, "
                 "Wikidata and Wikipedia.",
                 "Create a Wikidata item if none exists - it is openly editable and widely consumed as an identity "
                 "reference.",
                 "Ensure each profile describes the brand with the same canonical sentence used on the site."],
            effort="medium", owner="marketing", method="static",
            affected_count=1, sampled_count=1,
            evidence_detail={"declared": links[:10], "classified": classified},
        ))

    if undeclared:
        out.append(F.finding(
            "ENT-004", "Some brand profiles linked on the site are missing from sameAs",
            "low", "discoverability", "trust",
            evidence=f"{len(undeclared)} external profile(s) linked from the homepage are not declared in sameAs: "
                     f"{', '.join(undeclared[:4])}.",
            mechanism="A link in the footer is a hint; a sameAs entry is an assertion. Profiles left out of the "
                      "declaration are not connected to the entity, so whatever they corroborate is not counted.",
            action_summary="Add the remaining profiles to the sameAs array.",
            how=[f"Add {', '.join(undeclared[:5])} to the Organization sameAs list.",
                 "Keep the two in sync whenever a profile is added or retired."],
            effort="low", owner="marketing", method="static",
            affected_count=len(undeclared), sampled_count=1,
            evidence_detail={"undeclared": undeclared[:10]},
        ))


def check_entity_ambiguity(cache, out, skipped):
    """Does anything distinguish this brand from others sharing its name?"""
    home = cache.home
    if not home:
        return
    objects = _org_objects(cache)
    has_authority = bool(schema.classify_sameas(schema.sameas_of(objects))["authorities"])
    title = home.doc.title.strip()
    brand = cache.site.split(".")[0]

    # A title that is only the brand name, with no category and no qualifier.
    title_words = [w for w in re.split(r"[\s\-|–—:,]+", title) if w]
    qualified = bool(CATEGORY_NOUN.search(title)) or len(title_words) > 4
    if qualified or has_authority:
        return
    # Long, distinctive brand names are unlikely to collide; short generic ones are.
    if len(brand) > 12:
        skipped.append(F.skip("ENT-005", f"brand token '{brand}' is long and distinctive; name collision unlikely"))
        return

    out.append(F.finding(
        "ENT-005", "Nothing on the site distinguishes this brand from others with the same name",
        "medium", "discoverability", "trust",
        evidence=f"The homepage title is \"{title or '(none)'}\" - {len(title_words)} word(s) with no category "
                 f"qualifier - and no identity-authority sameAs link is declared for the name \"{brand}\".",
        mechanism="Several organisations, products and places routinely share a name. With no category in the title "
                  "and no link to an identity authority, a system has nothing to tell them apart, so facts about a "
                  "similarly named entity get attributed to this brand and vice versa. This is the mechanism behind "
                  "most cases of an assistant describing a company as something it is not.",
        action_summary="Qualify the brand everywhere it is named, and link to an identity authority.",
        how=[
            f"Change the homepage title to `{brand.title()} - <what it is> for <who>` so the name never appears "
            "unqualified.",
            "Add Organization schema with `description`, `address` and `sameAs` links to Wikidata, LinkedIn and a "
            "company register.",
            "Use the qualified form consistently in off-site profiles and press mentions, so the distinguishing "
            "phrase is what the wider web repeats.",
        ],
        effort="low", owner="marketing", method="heuristic", confidence="medium",
        affected_urls=[home.url], affected_count=1, sampled_count=1,
        evidence_detail={"title": title, "brand_token": brand, "has_authority_link": has_authority},
    ))


def check_corroboration_surface(cache, out, skipped):
    """Does the site publish anything the wider web could repeat about it?"""
    pages = cache.html_pages()
    if not pages:
        return
    about_pages = cache.pages_of_type("about")
    combined = " ".join(p.doc.main_text for p in (about_pages or pages)[:6])

    has_founding = bool(FOUNDING_FACT.search(combined))
    has_stats = bool(CITABLE_STAT.search(combined))
    has_about = bool(about_pages)

    if has_founding and (has_stats or has_about):
        return
    if has_about and has_founding:
        return

    missing = []
    if not has_about:
        missing.append("no About page was found")
    if not has_founding:
        missing.append("no founding date, headquarters or 'based in' statement appears in the text")
    if not has_stats:
        missing.append("no named, quantified fact (customers, employees, locations) appears in the text")

    # Severity scales with how much is absent: one gap is a thin About page,
    # all three is an organisation with no published substance at all.
    severity = "medium" if len(missing) >= 2 else "low"
    out.append(F.finding(
        "ENT-006", "The site publishes few verifiable facts about the organisation itself",
        severity, "discoverability", "trust",
        evidence=f"Across {len(about_pages or pages[:6])} sampled page(s): " + "; ".join(missing) + ".",
        mechanism="A claim repeated consistently across many independent sources is treated as reliable; a claim that "
                  "exists in one place is fragile. Before the wider web can repeat anything about an organisation, "
                  "the organisation has to state it somewhere quotable. With no founding date, location, scale or "
                  "named figures published, there is nothing for journalists, directories or assistants to corroborate "
                  "- so the brand has no verifiable substance to attach to its name.",
        action_summary="Publish a facts page: what the organisation is, when and where it was founded, its scale, and "
                       "who leads it.",
        how=[
            "Create or expand an About page stating founding year, headquarters location, legal entity name, "
            "leadership and size, in plain sentences.",
            "Publish named, dated figures the press and analysts can cite - customers served, locations, headcount - "
            "and keep them current.",
            "Add a press or newsroom page carrying the same facts in a form journalists can lift.",
            "Mirror the same facts in Organization schema (foundingDate, address, numberOfEmployees, founder) so they "
            "are machine-readable as well as readable.",
        ],
        effort="medium", owner="marketing", method="static", confidence="medium",
        affected_count=1, sampled_count=len(pages),
        evidence_detail={"has_about_page": has_about, "has_founding_fact": has_founding, "has_citable_stat": has_stats},
    ))


def check_freshness(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        return

    stale_years = []
    for page in pages:
        for match in COPYRIGHT.finditer(page.doc.visible_text[-3000:] or page.doc.visible_text):
            try:
                year = int(match.group(1))
            except ValueError:
                continue
            if 2000 <= year <= CURRENT_YEAR and year <= CURRENT_YEAR - 2:
                stale_years.append({"url": page.url, "year": year})
            break

    if stale_years and len(stale_years) >= max(2, len(pages) * 0.4):
        oldest = min(s["year"] for s in stale_years)
        out.append(F.finding(
            "ENT-007", "The site's copyright year suggests it has not been updated for years",
            "low", "discoverability", "trust",
            evidence=f"{len(stale_years)} of {len(pages)} sampled pages show a copyright year of "
                     f"{oldest} or similar, against the current year {CURRENT_YEAR}.",
            mechanism="A visibly stale date is read as evidence the content is unmaintained, by visitors deciding "
                      "whether to trust the page and by systems choosing between competing sources. It is a cheap "
                      "signal to fix and a costly one to leave.",
            action_summary="Generate the copyright year dynamically and keep genuinely dated content current.",
            how=["Render the year from the server or build date rather than hard-coding it.",
                 "Review pages carrying old dates in their body copy; update or date-stamp them explicitly."],
            effort="low", owner="engineering", method="static",
            affected_urls=[s["url"] for s in stale_years][:10],
            affected_count=len(stale_years), sampled_count=len(pages),
            evidence_detail={"years": sorted({s["year"] for s in stale_years})},
        ))

    articles = cache.pages_of_type("article")
    if len(articles) >= 3:
        undated, unattributed = [], []
        for page in articles:
            objects = schema.find(schema.extract_objects(page.doc), *schema.ARTICLE_TYPES)
            has_date = any(schema.has_value(o, "datePublished") or schema.has_value(o, "dateModified")
                           for o in objects)
            has_author = any(schema.has_value(o, "author") for o in objects)
            if not has_date and not re.search(r"\b(20\d{2})\b", page.doc.main_text[:1200]):
                undated.append(page.url)
            if not has_author:
                unattributed.append(page.url)

        if len(undated) >= max(2, len(articles) * 0.5):
            out.append(F.finding(
                "ENT-008", "Articles carry no visible or machine-readable publication date",
                "medium", "discoverability", "trust",
                evidence=f"{len(undated)} of {len(articles)} sampled articles have no datePublished/dateModified in "
                         "structured data and no year in their opening text.",
                mechanism="Recency is one of the main criteria for choosing between sources that say different "
                          "things. Undated content cannot be shown to be current, so it loses to dated content even "
                          "when it is newer and better - and a reader cannot tell whether advice from years ago "
                          "still applies.",
                action_summary="Publish and mark up a publication date, and a modification date, on every article.",
                how=["Show the date visibly on the page.",
                     "Add `datePublished` and `dateModified` to Article structured data.",
                     "Update `dateModified` when the content genuinely changes - not on every deploy, which "
                     "consumers learn to discount."],
                effort="low", owner="content", method="static",
                affected_urls=undated[:10], affected_count=len(undated), sampled_count=len(articles),
            ))

        if len(unattributed) >= max(2, len(articles) * 0.6):
            out.append(F.finding(
                "ENT-009", "Articles have no named author in structured data",
                "low", "discoverability", "trust",
                evidence=f"{len(unattributed)} of {len(articles)} sampled articles declare no author.",
                mechanism="Attribution is part of how a claim's weight is assessed. Named, described authors connect "
                          "content to a person whose expertise can be established elsewhere; anonymous content has "
                          "only the domain behind it.",
                action_summary="Attribute articles to named authors with linked profiles.",
                how=["Add `author` as a Person object with `name`, `url` and `sameAs` to the article's structured data.",
                     "Publish author profile pages describing relevant expertise.",
                     "Show the byline visibly as well as in markup."],
                effort="medium", owner="content", method="static",
                affected_urls=unattributed[:10], affected_count=len(unattributed), sampled_count=len(articles),
            ))


def check_nap_consistency(cache, out, skipped):
    """Local businesses: does the phone number agree with itself across the site?"""
    if cache.profile.get("site_type") != "local_business":
        skipped.append(F.skip("ENT-010", "site is not a local business; NAP consistency is not applicable"))
        return

    numbers = {}
    for page in cache.html_pages():
        for match in PHONE.finditer(page.doc.visible_text):
            digits = re.sub(r"\D", "", match.group(0))
            if 9 <= len(digits) <= 15:
                numbers.setdefault(digits, set()).add(page.url)
    if len(numbers) <= 1:
        return

    out.append(F.finding(
        "ENT-010", "Different phone numbers appear across the site",
        "medium", "discoverability", "trust",
        evidence=f"{len(numbers)} distinct phone numbers appear across the sampled pages: "
                 + ", ".join(sorted(numbers)[:4]) + ".",
        mechanism="Name, address and phone consistency is how directories, maps and assistants confirm that listings "
                  "for a business refer to the same place. Conflicting numbers on the business's own site weaken "
                  "every listing derived from it, and can split one business into several in downstream data.",
        action_summary="Publish one canonical phone number and use it everywhere, including structured data.",
        how=["Decide the primary number and use it consistently in the header, footer, contact page and schema.",
             "If separate numbers are genuinely needed per location or department, mark each one up on its own "
             "LocalBusiness or ContactPoint node with a stated purpose.",
             "Align the same details across Google Business Profile, Apple Business Connect and major directories."],
        effort="low", owner="marketing", method="static", confidence="medium",
        affected_count=len(numbers), sampled_count=len(cache.html_pages()),
        evidence_detail={"numbers": {k: sorted(v)[:3] for k, v in list(numbers.items())[:5]}},
    ))


def _offsite(cache):
    return (cache.extras.get("offsite") or {})


def check_offsite_reachable(cache, out, skipped):
    """ENT-011 - a declared profile that does not resolve.

    Robust to bot-blocking: a 404 is a confirmed dead link, while a 403 is only
    an unverified one, and the two are never conflated.
    """
    info = _offsite(cache)
    if not info.get("attempted"):
        skipped.append(F.skip("ENT-011", info.get("reason") or "off-site verification did not run"))
        return
    profiles = info.get("profiles") or []
    if not profiles:
        skipped.append(F.skip("ENT-011", "the site declares no external profiles to verify"))
        return

    dead = [p for p in profiles if p.get("state") == "dead"]
    if not dead:
        return

    checked = [p for p in profiles if p.get("state") in ("ok", "dead")]
    severity = F.apply_blast_radius("medium", len(dead), max(len(checked), 1))
    out.append(F.finding(
        "ENT-011", "Some external profiles the site claims as its own do not exist",
        severity, "discoverability", "trust",
        evidence=(f"{len(dead)} of {len(checked)} verifiable declared profile(s) returned 404 or 410: "
                  + ", ".join(f"{p['url']} ({p['status']})" for p in dead[:3]) + "."),
        mechanism="A sameAs entry is a machine-readable assertion that this profile is the same entity as "
                  "this brand. When the target does not exist, the assertion cannot be corroborated and the "
                  "identity graph a retrieval system would follow terminates at a dead end - which weakens "
                  "every other claim the graph was supposed to support.",
        action_summary="Remove or correct the dead profile URLs the site declares.",
        how=["Fetch each URL in the Organization sameAs array and confirm it returns 200.",
             "Update entries whose handle or slug changed; delete entries for profiles that no longer exist.",
             "Re-check after any rebrand - renamed social handles are the usual cause."],
        effort="low", owner="marketing", method="external", confidence="high",
        verify="Re-run the audit; ENT-011 should not fire once every declared profile resolves.",
        affected_urls=[p["url"] for p in dead[:5]],
        affected_count=len(dead), sampled_count=len(checked),
        evidence_detail={"dead": [{"url": p["url"], "status": p["status"]} for p in dead[:8]]},
    ))


def check_offsite_reciprocity(cache, out, skipped):
    """ENT-012 - a profile that resolves but never points back."""
    info = _offsite(cache)
    if not info.get("attempted"):
        skipped.append(F.skip("ENT-012", info.get("reason") or "off-site verification did not run"))
        return
    reachable = [p for p in (info.get("profiles") or []) if p.get("state") == "ok"]
    if len(reachable) < 2:
        skipped.append(F.skip(
            "ENT-012", f"only {len(reachable)} declared profile(s) could be fetched; "
                       "a reciprocity rate needs at least two"))
        return

    oneway = [p for p in reachable if not p.get("links_back") and not p.get("mentions_domain")]
    if not oneway:
        return
    # Two independent one-way profiles, and at least half of them. One
    # unreciprocated profile out of two is not "the profiles do not point
    # back" - half of them do, and the title would overstate the evidence.
    if len(oneway) < 2 or len(oneway) / len(reachable) < 0.5:
        skipped.append(F.skip(
            "ENT-012", f"{len(oneway)} of {len(reachable)} reachable profiles do not link back; "
                       "the check needs at least two, and at least half, before reporting"))
        return

    out.append(F.finding(
        "ENT-012", "The external profiles this brand claims do not point back to the site",
        "low", "discoverability", "trust",
        evidence=(f"{len(oneway)} of {len(reachable)} reachable declared profile(s) contain no link to "
                  f"{cache.site} and no mention of the domain: "
                  + ", ".join(p["url"] for p in oneway[:3]) + "."),
        mechanism="Corroboration is strongest when the link is mutual: the site claims the profile and the "
                  "profile claims the site. A one-way claim can be made by anyone about anyone, so it is "
                  "weaker evidence that the two identities are the same entity.",
        action_summary="Add the website URL to each external profile the brand controls.",
        how=["Set the website field on each profile to the canonical https origin.",
             "Where a profile has no website field, put the domain in the bio or description text.",
             "Prioritise the identity authorities (LinkedIn, Crunchbase, Wikidata) over social profiles."],
        effort="low", owner="marketing", method="external", confidence="medium",
        verify="Re-run the audit; each profile should link to or name the site's domain.",
        affected_urls=[p["url"] for p in oneway[:5]],
        affected_count=len(oneway), sampled_count=len(reachable),
        evidence_detail={"one_way": [p["url"] for p in oneway[:8]]},
    ))


def check_offsite_description(cache, out, skipped):
    """ENT-013 - the off-site description of the brand disagrees with the site's."""
    info = _offsite(cache)
    if not info.get("attempted"):
        skipped.append(F.skip("ENT-013", info.get("reason") or "off-site verification did not run"))
        return
    home = cache.home
    samples = [p for p in (info.get("profiles") or [])
               if p.get("state") == "ok" and len((p.get("text_sample") or "").split()) >= 30]
    if not home or not samples:
        skipped.append(F.skip(
            "ENT-013", "no fetched profile carried enough text to compare against the site's own description"))
        return

    onsite = " ".join(home.doc.main_text.split()[:120])
    if len(onsite.split()) < 20:
        skipped.append(F.skip("ENT-013", "the homepage carries too little text to compare"))
        return

    divergent = []
    for p in samples:
        overlap = _jaccard(_tokens(onsite), _tokens(p["text_sample"]))
        if overlap < 0.06:
            divergent.append((p["url"], round(overlap, 3)))

    if not divergent or len(divergent) < len(samples):
        if not divergent:
            return
        skipped.append(F.skip(
            "ENT-013", f"{len(divergent)} of {len(samples)} profiles diverge; "
                       "the check needs every fetched profile to disagree before reporting"))
        return

    out.append(F.finding(
        "ENT-013", "How the brand is described off-site shares almost no vocabulary with the site",
        "low", "discoverability", "trust",
        evidence=(f"All {len(samples)} fetched profile(s) share under 6% of their vocabulary with the "
                  f"homepage's own description; lowest is {divergent[0][0]} at "
                  f"{round(divergent[0][1] * 100)}%."),
        mechanism="Assistants assemble an answer from whatever sources they reach. When the site and its own "
                  "profiles describe the brand in unrelated language, there is no repeated phrasing for a "
                  "model to converge on, so the description it repeats is whichever source it happened to "
                  "read - not the one the brand controls.",
        action_summary="Use one consistent description sentence on the site and on every profile.",
        how=["Write a single sentence naming what the company does and who it serves.",
             "Use it verbatim in the Organization schema description and on each external profile.",
             "Keep the wording stable; consistency across sources is the signal, not the phrasing itself."],
        effort="low", owner="marketing", method="external", confidence="low",
        verify="Re-run the audit; vocabulary overlap between site and profiles should rise above 6%.",
        affected_urls=[u for u, _ in divergent[:5]],
        affected_count=len(divergent), sampled_count=len(samples),
        evidence_detail={"overlap": {u: v for u, v in divergent[:8]}},
    ))


def main():
    ap = argparse.ArgumentParser(description="Gate 4 - entity, corroboration and freshness checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    # The note has to match what actually happened on this run: the detector
    # verifies the profiles the site declares when that step ran, and stays
    # entirely on-site when it did not.
    if (cache.extras.get("offsite") or {}).get("attempted"):
        notes = ["entity-corroboration-audit verified the external profiles this site declares as its own "
                 "(sameAs and homepage profile links) for reachability and reciprocity; it never searched "
                 "for the brand elsewhere, so corroboration beyond those declared profiles is still "
                 "assessed by whether the site enables it, not by observing it"]
    else:
        notes = ["entity-corroboration-audit measures only what the site publishes about itself; "
                 "no external source was consulted, so off-site corroboration is assessed by whether the site "
                 "enables it, not by observing it"]
    for check in (check_description_consistency, check_identity_graph, check_entity_ambiguity,
                  check_corroboration_surface, check_freshness, check_nap_consistency,
                  check_offsite_reachable, check_offsite_reciprocity, check_offsite_description):
        try:
            check(cache, out, skipped)
        except Exception as e:
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped, notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
