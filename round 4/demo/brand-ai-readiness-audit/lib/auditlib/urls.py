"""URL normalisation and classification helpers."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit, urljoin, parse_qsl, urlencode

# Query parameters that never change the content served, only the attribution.
# Stripping them prevents the crawler from spending its page budget fetching the
# same page five times under different campaign tags.
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "gclid", "fbclid", "msclkid", "mc_cid", "mc_eid", "ref",
    "referrer", "source", "_ga", "_gl", "igshid", "yclid", "dclid",
    "campaignid", "adgroupid", "hsa_acc", "hsa_cam", "hsa_grp", "hsa_ad",
}

NON_HTML_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp",
    ".mp4", ".webm", ".mov", ".avi", ".mp3", ".wav", ".ogg", ".m4a",
    ".zip", ".gz", ".tar", ".rar", ".7z", ".dmg", ".exe", ".pkg", ".msi",
    ".css", ".js", ".map", ".json", ".xml", ".rss", ".atom",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv",
}

DOCUMENT_EXTENSIONS = {".pdf"}


def normalize(url: str, base: str | None = None) -> str | None:
    """Absolutise, strip tracking noise and fragments, and canonicalise case.

    Returns None for anything that is not a fetchable http(s) URL - mailto:,
    tel:, javascript:, data: and malformed values all collapse to None so
    callers never have to special-case them.
    """
    if not url:
        return None
    url = url.strip()
    if not url or url.startswith("#"):
        return None
    low = url.lower()
    for bad in ("javascript:", "mailto:", "tel:", "data:", "sms:", "callto:", "about:"):
        if low.startswith(bad):
            return None
    if base:
        url = urljoin(base, url)
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    if not parts.netloc:
        return None

    host = parts.netloc.lower()
    # Drop the default port; :80 and :443 are the same origin as no port.
    if host.endswith(":80") and parts.scheme == "http":
        host = host[:-3]
    elif host.endswith(":443") and parts.scheme == "https":
        host = host[:-4]

    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(query_pairs)

    path = parts.path or "/"
    # Collapse duplicate slashes, which otherwise produce duplicate crawl entries.
    path = re.sub(r"/{2,}", "/", path)

    return urlunsplit((parts.scheme, host, path, query, ""))


def host_of(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower()
    except ValueError:
        return ""


def registrable(host: str) -> str:
    """Strip a leading www. so that www and apex are treated as one site.

    Deliberately not a full public-suffix implementation: the audit only needs
    to know whether two URLs belong to the same site, and a PSL would be a
    third-party dependency for a marginal gain.
    """
    host = (host or "").lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def same_site(a: str, b: str) -> bool:
    ra, rb = registrable(host_of(a)), registrable(host_of(b))
    if not ra or not rb:
        return False
    # Treat a subdomain as the same site (blog.example.com belongs to example.com)
    # so that a site whose content lives on a subdomain is still audited.
    return ra == rb or ra.endswith("." + rb) or rb.endswith("." + ra)


def path_of(url: str) -> str:
    try:
        return urlsplit(url).path or "/"
    except ValueError:
        return "/"


def extension(url: str) -> str:
    path = path_of(url).lower()
    dot = path.rfind(".")
    slash = path.rfind("/")
    return path[dot:] if dot > slash and dot != -1 else ""


def is_probably_html(url: str) -> bool:
    return extension(url) not in NON_HTML_EXTENSIONS | DOCUMENT_EXTENSIONS


def is_document(url: str) -> bool:
    """A PDF or similar: not HTML, but a real carrier of brand facts."""
    return extension(url) in DOCUMENT_EXTENSIONS


def depth(url: str) -> int:
    """Number of path segments. Used for click-depth and sampling breadth."""
    return len([s for s in path_of(url).split("/") if s])


# --- Page-type classification -------------------------------------------------
#
# Page type gates which checks are allowed to fire. Asking a blog post for
# Product/Offer markup, or a docs page for a pricing CTA, is the single most
# common source of false positives in this problem space.

PAGE_TYPE_PATTERNS = [
    ("product",     r"/(product|products|item|items|p|shop|store|dp|sku)(/|$)"),
    ("category",    r"/(category|categories|collection|collections|catalog|c)(/|$)"),
    ("pricing",     r"/(pricing|price|plans|plan|subscribe|packages|tariff)(/|$)"),
    ("article",     r"/(blog|news|article|articles|post|posts|insights|stories|press-release)(/|$)"),
    ("docs",        r"/(docs|documentation|developer|developers|api|reference|guide|guides|manual|kb|knowledge-?base|help)(/|$)"),
    ("about",       r"/(about|about-us|company|who-we-are|our-story|team|leadership|mission)(/|$)"),
    ("contact",     r"/(contact|contact-us|get-in-touch|support|locations|find-us|stores)(/|$)"),
    ("faq",         r"/(faq|faqs|frequently-asked|questions|q-and-a)(/|$)"),
    ("legal",       r"/(privacy|terms|legal|cookie|cookies|gdpr|imprint|impressum|accessibility|disclaimer)(/|$)"),
    ("careers",     r"/(careers|jobs|join-us|vacancies|hiring|work-with-us)(/|$)"),
    ("case_study",  r"/(case-stud|customers|customer-stories|success-stor|testimonial)"),
    ("account",     r"/(login|signin|sign-in|register|signup|sign-up|account|cart|checkout|basket|my-)(/|$)"),
    ("search",      r"/(search|s|find)(/|\?|$)"),
]


def classify_page(url: str, title: str = "", is_home: bool = False) -> str:
    """Classify a page from its URL, falling back to its title.

    Conservative by design: returns "other" rather than guessing. Checks that
    need a specific page type simply do not fire on "other", which costs a
    little recall and buys a lot of precision.
    """
    if is_home:
        return "home"
    path = path_of(url).lower()
    if path in ("/", ""):
        # A root path that is not the audited origin is a section front (a blog
        # or docs subdomain), not the site home. Conflating them would make
        # home-only checks fire several times per site.
        return "section_home"
    for name, pattern in PAGE_TYPE_PATTERNS:
        if re.search(pattern, path):
            return name
    t = (title or "").lower()
    if re.search(r"\b(pricing|plans?)\b", t):
        return "pricing"
    if re.search(r"\b(about us|our story|who we are)\b", t):
        return "about"
    if re.search(r"\b(contact|get in touch)\b", t):
        return "contact"
    if re.search(r"\b(faq|frequently asked)\b", t):
        return "faq"
    return "other"


TRANSACTIONAL_HOST = re.compile(
    r"^(checkout|secure|account|accounts|login|signin|my|shop-?admin|payments?|billing)\.", re.I
)


def is_transactional_host(url: str) -> bool:
    """Hosts that exist to carry a logged-in or in-progress transaction.

    Everything served from these is legitimately excluded from indexing, so a
    noindex directive there is correct behaviour rather than a defect. Treating
    it as one is a false positive on a site that is doing the right thing.
    """
    return bool(TRANSACTIONAL_HOST.match(host_of(url)))


def is_excluded_from_audit(url: str) -> bool:
    """Pages that exist for humans mid-transaction and are legitimately thin.

    Auditing a checkout page for structured data or a value proposition
    produces noise, not findings, so they are kept out of the sample entirely.
    """
    return classify_page(url) in ("account", "search") or is_transactional_host(url)
