"""schema.org extraction and completeness checking.

Presence of structured data is close to worthless as a signal on its own - a
`Product` node with no price, or an `Organization` with nothing but a name, is
markup that validates and answers no question. What matters to a retrieval
system is whether the specific field it needs is populated, so this module is
organised around **required and recommended fields per type**, not around
whether a block exists.

Supports JSON-LD (the form every consumer prefers) and a light microdata
reader, so a site that marked up its content the older way is not reported as
having none.
"""

from __future__ import annotations

import re

# Fields that make a type actually answer questions.
#
# `required`    - without these the node cannot answer the question its type
#                 exists to answer, and consumers routinely discard it.
# `recommended` - materially improves what an assistant can say about it.
#
# Kept deliberately tighter than the full schema.org vocabulary: this is a list
# of what a machine needs to produce a correct answer, not a completeness audit
# against the specification.
TYPE_SPECS = {
    "Organization": {
        "required": ["name", "url"],
        "recommended": ["logo", "description", "sameAs", "address", "contactPoint", "foundingDate"],
        "answers": "who is this company, and is it the same entity as the one on Wikipedia/LinkedIn",
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHours", "openingHoursSpecification", "geo", "priceRange", "url", "sameAs"],
        "answers": "where is it, when is it open, how do I contact it",
    },
    "Product": {
        "required": ["name", "offers"],
        "recommended": ["image", "description", "brand", "sku", "aggregateRating", "review", "gtin"],
        "answers": "what is this product and what does it cost",
    },
    "Offer": {
        "required": ["price", "priceCurrency"],
        "recommended": ["availability", "url", "priceValidUntil", "shippingDetails"],
        "answers": "what does it cost and can I buy it right now",
    },
    "Article": {
        "required": ["headline", "datePublished"],
        "recommended": ["author", "dateModified", "image", "publisher", "description"],
        "answers": "what does this say, when was it said, and who said it",
    },
    "BlogPosting": {
        "required": ["headline", "datePublished"],
        "recommended": ["author", "dateModified", "image", "publisher"],
        "answers": "what does this say, when was it said, and who said it",
    },
    "NewsArticle": {
        "required": ["headline", "datePublished"],
        "recommended": ["author", "dateModified", "image", "publisher"],
        "answers": "what does this say, when was it said, and who said it",
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
        "answers": "direct question-and-answer pairs an assistant can quote verbatim",
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
        "answers": "where this page sits in the site, which gives an isolated page its context",
    },
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["publisher", "potentialAction", "inLanguage"],
        "answers": "what this site is called as a whole",
    },
    "Person": {
        "required": ["name"],
        "recommended": ["jobTitle", "sameAs", "worksFor", "image"],
        "answers": "who this person is and whether they are the same person as elsewhere",
    },
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": ["endDate", "offers", "eventStatus", "description"],
        "answers": "what is happening, when, and where",
    },
    "Recipe": {
        "required": ["name", "recipeIngredient", "recipeInstructions"],
        "recommended": ["cookTime", "prepTime", "nutrition", "image"],
        "answers": "how do I make this",
    },
    "JobPosting": {
        "required": ["title", "datePosted", "hiringOrganization"],
        "recommended": ["jobLocation", "baseSalary", "employmentType", "validThrough"],
        "answers": "what is the role, where, and for how much",
    },
    "Service": {
        "required": ["name"],
        "recommended": ["provider", "areaServed", "description", "offers"],
        "answers": "what service is offered and to whom",
    },
    "SoftwareApplication": {
        "required": ["name"],
        "recommended": ["applicationCategory", "operatingSystem", "offers", "aggregateRating"],
        "answers": "what the software does and what it costs",
    },
}

# Which page types are expected to carry which types. Used as the applicability
# gate so a check never demands Product markup from an About page.
EXPECTED_BY_PAGE_TYPE = {
    "home": ["Organization", "WebSite"],
    "product": ["Product"],
    "article": ["Article", "BlogPosting", "NewsArticle"],
    "faq": ["FAQPage"],
    "contact": ["Organization", "LocalBusiness"],
    "about": ["Organization"],
    "pricing": ["Product", "Offer", "Service", "SoftwareApplication"],
    "careers": ["JobPosting"],
}

ORG_TYPES = {
    "Organization", "Corporation", "LocalBusiness", "NGO", "EducationalOrganization",
    "GovernmentOrganization", "NewsMediaOrganization", "OnlineBusiness", "Store",
    "Restaurant", "Hotel", "ProfessionalService", "MedicalBusiness", "SportsOrganization",
}

ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "ScholarlyArticle", "Report"}


def types_of(obj) -> list:
    """@type as a list, namespace-stripped. Handles the multi-type form."""
    if not isinstance(obj, dict):
        return []
    raw = obj.get("@type") or obj.get("type") or []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for item in raw:
        if isinstance(item, str):
            out.append(item.rstrip("/").rsplit("/", 1)[-1].split("#")[-1])
    return out


def walk(obj, depth=0, max_depth=6):
    """Yield every dict with an @type anywhere in a JSON-LD structure.

    Handles the three shapes real sites emit: a bare object, an array of
    objects, and a @graph wrapper - plus arbitrary nesting inside them.
    """
    if depth > max_depth:
        return
    if isinstance(obj, list):
        for item in obj:
            yield from walk(item, depth + 1, max_depth)
        return
    if not isinstance(obj, dict):
        return
    if "@graph" in obj:
        yield from walk(obj["@graph"], depth + 1, max_depth)
    if types_of(obj):
        yield obj
    for key, value in obj.items():
        if key in ("@graph", "@context", "@type"):
            continue
        if isinstance(value, (dict, list)):
            yield from walk(value, depth + 1, max_depth)


def extract_objects(doc) -> list:
    """Every typed node from every valid JSON-LD block on the page."""
    out = []
    for _raw, parsed, _err in doc.jsonld_blocks():
        if parsed is not None:
            out.extend(walk(parsed))
    return out


def extract_microdata(doc) -> list:
    """Light microdata reader: itemtype plus its immediate itemprops.

    Not a full microdata implementation - enough to establish that a site has
    marked its content up the older way, so it is credited rather than reported
    as having no structured data at all.
    """
    out = []
    for nodes in doc._by_tag.values():
        for node in nodes:
            itemtype = node.get("itemtype", "")
            if not itemtype:
                continue
            props = {}
            stack = [c for c in node.children if not isinstance(c, str)]
            while stack:
                child = stack.pop()
                name = child.get("itemprop", "")
                if name and name not in props:
                    props[name] = (
                        child.get("content") or child.get("datetime")
                        or child.get("href") or child.get("src") or child.text()[:200]
                    )
                if not child.get("itemtype"):
                    stack.extend(c for c in child.children if not isinstance(c, str))
            out.append({
                "@type": itemtype.rstrip("/").rsplit("/", 1)[-1],
                "_source": "microdata",
                **props,
            })
    return out


def find(objects, *wanted) -> list:
    wanted_set = set(wanted)
    return [o for o in objects if wanted_set & set(types_of(o))]


def has_value(obj, field) -> bool:
    """Is a field populated with something a consumer could actually use?

    Empty strings, empty lists, and placeholder values left in by a template
    all count as absent - they validate and answer nothing.
    """
    if field not in obj:
        return False
    value = obj[field]
    if value is None:
        return False
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return False
        return cleaned.lower() not in (
            "n/a", "na", "none", "null", "undefined", "tbd", "todo",
            "your company name", "example", "lorem ipsum", "0",
        )
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def check_completeness(obj) -> dict:
    """Missing required/recommended fields for the best-known type on a node."""
    node_types = types_of(obj)
    spec, matched = None, None
    for t in node_types:
        if t in TYPE_SPECS:
            spec, matched = TYPE_SPECS[t], t
            break
    if spec is None:
        # Unknown types are not defects - schema.org is large and sites use
        # legitimate types this module does not model.
        return {"type": node_types[0] if node_types else "", "known": False,
                "missing_required": [], "missing_recommended": []}
    return {
        "type": matched,
        "known": True,
        "answers": spec["answers"],
        "missing_required": [f for f in spec["required"] if not has_value(obj, f)],
        "missing_recommended": [f for f in spec["recommended"] if not has_value(obj, f)],
    }


def offers_of(product: dict) -> list:
    offers = product.get("offers")
    if offers is None:
        return []
    return [o for o in walk(offers) if "Offer" in types_of(o) or "AggregateOffer" in types_of(o)] or (
        [offers] if isinstance(offers, dict) else []
    )


SAMEAS_AUTHORITIES = {
    "wikipedia.org": "Wikipedia",
    "wikidata.org": "Wikidata",
    "linkedin.com": "LinkedIn",
    "crunchbase.com": "Crunchbase",
    "github.com": "GitHub",
    "bloomberg.com": "Bloomberg",
    "sec.gov": "SEC",
    "companieshouse.gov.uk": "Companies House",
    "opencorporates.com": "OpenCorporates",
    "g2.com": "G2",
    "capterra.com": "Capterra",
    "trustpilot.com": "Trustpilot",
}

SOCIAL_HOSTS = {
    "twitter.com": "X/Twitter", "x.com": "X/Twitter", "facebook.com": "Facebook",
    "instagram.com": "Instagram", "youtube.com": "YouTube", "tiktok.com": "TikTok",
    "pinterest.com": "Pinterest", "threads.net": "Threads", "mastodon.social": "Mastodon",
}


def sameas_of(objects) -> list:
    out = []
    for obj in objects:
        value = obj.get("sameAs")
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(v for v in value if isinstance(v, str))
    return sorted(set(out))


def classify_sameas(links) -> dict:
    """Split identity links into authority profiles and social profiles.

    The distinction matters: a link to Wikidata or Wikipedia disambiguates an
    entity, while a link to Instagram mostly does not.
    """
    authorities, social, other = {}, {}, []
    for link in links:
        host = re.sub(r"^https?://", "", link.lower()).split("/")[0]
        host = host[4:] if host.startswith("www.") else host
        for domain, label in SAMEAS_AUTHORITIES.items():
            if host.endswith(domain):
                authorities[label] = link
                break
        else:
            for domain, label in SOCIAL_HOSTS.items():
                if host.endswith(domain):
                    social[label] = link
                    break
            else:
                other.append(link)
    return {"authorities": authorities, "social": social, "other": other}
