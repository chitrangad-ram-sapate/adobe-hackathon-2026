#!/usr/bin/env python3
"""Offline regression suite for every detector in the marketplace.

Runs with no network access, against hand-written HTML fixtures. Each detector
is asserted in **both** directions:

* a broken fixture must produce specific `check_id`s - proving the detector
  actually detects;
* a clean fixture must produce **nothing** - proving it stays silent on a
  healthy site.

The second assertion is the one that matters most here. The rubric this
marketplace is built against penalises false positives as heavily as misses,
and "it found lots of problems" is easy while "it correctly found none" is
not. A detector that cannot stay quiet on the clean fixtures is broken.

Usage:
    python tests/run_tests.py [-v]
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness as H  # noqa: E402

VERBOSE = "-v" in sys.argv or "--verbose" in sys.argv
RESULTS = []


def case(name, detector, pages, expect=(), forbid=(), exclude_info=False, **kwargs):
    """Run one detector against one fixture and assert on the check ids."""
    cache = H.build_cache(pages, **kwargs)
    try:
        output = H.run_detector(detector, cache)
        found = H.check_ids(output, exclude_info=exclude_info)
        missing = set(expect) - found
        unexpected = found & set(forbid)
        ok = not missing and not unexpected
        detail = ""
        if missing:
            detail += f" missing={sorted(missing)}"
        if unexpected:
            detail += f" unexpected={sorted(unexpected)}"
        if VERBOSE or not ok:
            detail += f" (all: {sorted(found) or 'none'})"
        RESULTS.append((ok, name, detail))
        return output
    except AssertionError as e:
        RESULTS.append((False, name, f" {e}"))
        return None
    finally:
        H.cleanup(cache)


def clean_pages(site_type="saas"):
    """A well-built four-page site. Every detector must be silent on it."""
    org = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "name": "Northwind Robotics",
             "url": "https://example.com/", "logo": "https://example.com/logo.png",
             "description": "Northwind Robotics is a robotics company that builds autonomous mobile "
                            "robots for warehouse automation in mid-size distribution centres.",
             "sameAs": ["https://www.linkedin.com/company/northwind-robotics",
                        "https://www.wikidata.org/wiki/Q000000"],
             "address": {"@type": "PostalAddress", "streetAddress": "12 Wellington Street",
                         "addressLocality": "Leeds", "postalCode": "LS1 4HW"},
             "contactPoint": {"@type": "ContactPoint", "telephone": "+44 113 496 0000",
                              "email": "hello@example.com", "contactType": "sales"},
             "foundingDate": "2014-03-01"},
            {"@type": "WebSite", "name": "Northwind Robotics", "url": "https://example.com/",
             "inLanguage": "en"},
        ],
    }
    extra = ('<meta property="og:description" content="Northwind Robotics is a robotics company that '
             'builds autonomous mobile robots for warehouse automation in mid-size distribution centres.">')
    pages = []
    for url, ptype, title in [
        ("https://example.com/", "home", "Northwind Robotics - warehouse automation robots for distributors"),
        ("https://example.com/about", "about", "About Northwind Robotics - robotics company in Leeds"),
        ("https://example.com/pricing", "pricing", "Pricing - Northwind Robotics warehouse robots"),
        ("https://example.com/contact", "contact", "Contact Northwind Robotics - Leeds, United Kingdom"),
    ]:
        pages.append({
            "url": url, "page_type": ptype, "is_home": ptype == "home",
            "html": H.good_page(title=title, canonical=url, jsonld=org, extra_head=extra),
        })
    return pages


# =============================================================================
# Clean-site control: every detector must be silent.
# =============================================================================

for detector in ("access", "render", "schema", "answer", "entity", "engagement"):
    case(
        f"clean site -> {detector} detector reports nothing",
        detector, clean_pages(),
        forbid=[f"{p}-{n:03d}" for p in ("ACC", "RND", "SDA", "ANS", "ENT", "ENG") for n in range(1, 30)],
        exclude_info=True,
        robots_txt="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
        profile={"site_type": "saas", "site_type_confidence": "high", "platform": "unknown",
                 "platform_confidence": "low", "primary_language": "en"},
    )


# =============================================================================
# Gate 1 - access
# =============================================================================

case(
    "robots.txt disallowing everything -> ACC-002",
    "access", clean_pages(), expect=["ACC-002"],
    robots_txt="User-agent: *\nDisallow: /\n",
)

case(
    "AI retrieval crawlers blocked -> ACC-003, and training-only block is NOT a defect",
    "access", clean_pages(), expect=["ACC-003"], forbid=["ACC-004"],
    robots_txt=("User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n\n"
                "User-agent: OAI-SearchBot\nDisallow: /\n\n"
                "User-agent: PerplexityBot\nDisallow: /\n"),
)

case(
    "training crawlers blocked alone -> ACC-004 at info only, never ACC-003",
    "access", clean_pages(), expect=["ACC-004"], forbid=["ACC-003", "ACC-002"],
    robots_txt=("User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n\n"
                "User-agent: GPTBot\nDisallow: /\n\nUser-agent: CCBot\nDisallow: /\n"),
)

case(
    "WAF serves 200 to browsers and 403 to plain clients -> ACC-008",
    "access", clean_pages(), expect=["ACC-008"],
    robots_txt="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
    extras={"probes": {"user_agent_differential": {
        "default_ua": {"status": 403, "words": 0, "bytes": 0, "error": None, "server": "cloudflare"},
        "browser_ua": {"status": 200, "words": 900, "bytes": 40000, "error": None, "server": "cloudflare"}}}},
)

case(
    "missing robots.txt is NOT a finding",
    "access", clean_pages(), forbid=["ACC-001", "ACC-002", "ACC-006"],
    robots_txt=None,
    extras={"robots": {"status": 404}},
)

case(
    "noindex on the homepage -> ACC-016 at critical",
    "access",
    [dict(p, html=p["html"].replace("<head>", '<head><meta name="robots" content="noindex,nofollow">'))
     for p in clean_pages()],
    expect=["ACC-016"],
    robots_txt="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
)

case(
    "soft 404 -> ACC-026",
    "access", clean_pages(), expect=["ACC-026"],
    robots_txt="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
    extras={"probes": {"not_found": {"url": "https://example.com/nope", "status": 200, "words": 300,
                                     "final_url": "https://example.com/nope", "redirected": False}}},
)


# =============================================================================
# Gate 2 - render
# =============================================================================

SHELL = ('<!doctype html><html><head><title>App</title></head><body>'
         '<div id="root"></div><script src="/_next/static/chunks/main.js"></script>'
         + "<!--" + ("padding " * 4000) + "-->" + '</body></html>')

case(
    "empty SPA shell without a renderer -> RND-002 at medium confidence",
    "render",
    [{"url": "https://example.com/", "html": SHELL, "page_type": "home", "is_home": True},
     {"url": "https://example.com/pricing", "html": SHELL, "page_type": "pricing"},
     {"url": "https://example.com/about", "html": SHELL, "page_type": "about"}],
    expect=["RND-002"], forbid=["RND-001"],
    robots_txt="User-agent: *\n",
)

case(
    "measured render gap when a renderer ran -> RND-001, and RND-002 is suppressed",
    "render",
    [{"url": "https://example.com/", "html": SHELL, "page_type": "home", "is_home": True,
      "rendered_html": H.good_page(canonical="https://example.com/")},
     {"url": "https://example.com/about", "html": SHELL, "page_type": "about",
      "rendered_html": H.good_page(canonical="https://example.com/about")}],
    expect=["RND-001"], forbid=["RND-002"],
    robots_txt="User-agent: *\n",
    capabilities={"javascript_rendering": True, "web_search": False},
)

# Regression: a fully server-rendered page whose JavaScript only expands site
# furniture - a mega-menu and an extended footer - must NOT be reported as a
# render gap. Measuring whole-page text instead of main content read python.org
# as "assembled by JavaScript" at 73% coverage when its main content was
# byte-identical before and after rendering.
_MEGA_MENU = "<nav>" + "".join(
    f'<a href="/s/{i}">Solutions for sector number {i} including logistics '
    f'and distribution services</a>' for i in range(40)
) + "</nav>"

case(
    "JavaScript that only expands navigation furniture is not a render gap",
    "render",
    [{"url": "https://example.com/", "html": H.good_page(canonical="https://example.com/"),
      "page_type": "home", "is_home": True,
      "rendered_html": H.good_page(canonical="https://example.com/",
                                   extra_body=_MEGA_MENU)},
     {"url": "https://example.com/about", "html": H.good_page(canonical="https://example.com/about"),
      "page_type": "about",
      "rendered_html": H.good_page(canonical="https://example.com/about",
                                   extra_body=_MEGA_MENU)}],
    forbid=["RND-001", "RND-002"],
    robots_txt="User-agent: *\n",
    capabilities={"javascript_rendering": True, "web_search": False},
)

case(
    "price list locked in an image with no alt -> RND-006",
    "render",
    [dict(p, html=p["html"].replace("</main>", '<img src="/img/2026-price-list-chart.png"></main>'))
     for p in clean_pages()],
    expect=["RND-006"],
    robots_txt="User-agent: *\n",
)

case(
    "a short page that is NOT a shell is not flagged",
    "render",
    [{"url": "https://example.com/", "html": '<!doctype html><html lang="en"><head><title>Ada Fen, potter</title>'
      '</head><body><main><h1>Ada Fen</h1><p>I am a potter working in Leeds. I sell studio pottery at the '
      'Kirkgate market on Saturdays. Email ada@example.com to commission a piece.</p></main></body></html>',
      "page_type": "home", "is_home": True}],
    forbid=["RND-002", "RND-003"],
    robots_txt="User-agent: *\n",
)


# =============================================================================
# Gate 3a - structured data
# =============================================================================

case(
    "malformed JSON-LD -> SDA-001",
    "schema",
    [dict(p, html=p["html"].replace(
        "</head>", '<script type="application/ld+json">{"@type":"Product","name":"X",}</script></head>'))
     for p in clean_pages()],
    expect=["SDA-001"],
    robots_txt="User-agent: *\n",
)

PRODUCT_NO_PRICE = {"@context": "https://schema.org", "@type": "Product", "name": "AMR-200", "image": "a.png"}

case(
    "Product markup with no price -> SDA-008, and SDA-007 defers to it",
    "schema",
    [{"url": "https://example.com/", "html": H.good_page(canonical="https://example.com/"),
      "page_type": "home", "is_home": True},
     {"url": "https://example.com/products/a", "html": H.good_page(canonical="https://example.com/products/a",
      jsonld=PRODUCT_NO_PRICE), "page_type": "product", "depth": 2},
     {"url": "https://example.com/products/b", "html": H.good_page(canonical="https://example.com/products/b",
      jsonld=PRODUCT_NO_PRICE), "page_type": "product", "depth": 2}],
    expect=["SDA-008"], forbid=["SDA-007"],
    robots_txt="User-agent: *\n",
    profile={"site_type": "ecommerce", "site_type_confidence": "high", "primary_language": "en"},
)

case(
    "a blog is NOT asked for Product or Offer markup",
    "schema",
    [{"url": "https://example.com/", "html": H.good_page(canonical="https://example.com/"),
      "page_type": "home", "is_home": True}]
    + [{"url": f"https://example.com/blog/post-{i}", "page_type": "article", "depth": 2,
        "html": H.good_page(title=f"Post {i}", canonical=f"https://example.com/blog/post-{i}",
                            jsonld={"@context": "https://schema.org", "@type": "BlogPosting",
                                    "headline": f"Post {i}", "datePublished": "2026-01-0%d" % (i + 1),
                                    "dateModified": "2026-02-01", "author": {"@type": "Person", "name": "Ada Fen"},
                                    "image": "a.png", "publisher": {"@type": "Organization", "name": "N"}})}
       for i in range(1, 4)],
    forbid=["SDA-008", "SDA-005"],
    robots_txt="User-agent: *\n",
    profile={"site_type": "media_publisher", "site_type_confidence": "high", "primary_language": "en"},
)


# =============================================================================
# Gate 3b - answer readiness
# =============================================================================

FLUFF_BODY = ("<p>We believe in a better tomorrow. Our journey began with a simple idea: the "
              "possibilities are endless when you dare to look beyond.</p>"
              "<p>Join us as we transform what comes next. Contact us to request a quote.</p>")
FLUFF = ('<!doctype html><html lang="en"><head><title>Home</title>'
         '<link rel="canonical" href="{u}"></head><body><main>'
         "<h1>Reimagine what's possible</h1>" + FLUFF_BODY + "</main></body></html>")

case(
    "abstract hero with no identity statement -> ANS-001 and ANS-002",
    "answer",
    [{"url": u, "html": FLUFF.format(u=u), "page_type": t, "is_home": t == "home"}
     for u, t in [("https://example.com/", "home"), ("https://example.com/about", "about"),
                  ("https://example.com/pricing", "pricing"), ("https://example.com/contact", "contact")]],
    expect=["ANS-001", "ANS-002", "ANS-004", "ANS-006", "ANS-007"],
    robots_txt="User-agent: *\n",
    profile={"site_type": "saas", "site_type_confidence": "high", "primary_language": "en"},
)

case(
    "documentation site is NOT asked for a published price",
    "answer", clean_pages(),
    forbid=["ANS-006", "ANS-009"],
    robots_txt="User-agent: *\n",
    profile={"site_type": "documentation", "site_type_confidence": "high", "primary_language": "en"},
)


# =============================================================================
# Gate 4 - entity and trust
# =============================================================================

case(
    "no sameAs and an unqualified short brand name -> ENT-002 and ENT-005",
    "entity",
    [{"url": u, "page_type": t, "is_home": t == "home",
      "html": '<!doctype html><html lang="en"><head><title>Acme</title></head><body><main><h1>Acme</h1>'
              "<p>Acme is a company. We do things well and we have done so for a long time.</p>"
              "</main></body></html>"}
     for u, t in [("https://acme.com/", "home"), ("https://acme.com/about", "about")]],
    expect=["ENT-002", "ENT-005"],
    robots_txt="User-agent: *\n", site="acme.com", origin="https://acme.com/",
)

case(
    "contradictory self-descriptions -> ENT-001",
    "entity",
    [dict(p, html=p["html"].replace(
        '<meta name="description"',
        '<meta property="og:description" content="Bespoke handmade ceramic tableware fired in small batches '
        'by artisans in rural Portugal, shipped worldwide."><meta name="description"'))
     for p in clean_pages()],
    expect=["ENT-001"],
    robots_txt="User-agent: *\n",
)


# =============================================================================
# Engagement
# =============================================================================

ORPHAN = ('<!doctype html><html lang="en"><head><title>Spec sheet</title></head><body><main>'
          "<h2>Technical specification</h2><p>Payload 1200 kg. Runtime 9 hours. Charge time 45 minutes. "
          "Operating temperature minus 10 to plus 40 degrees Celsius. Navigation by lidar and wheel odometry. "
          "Communication over 802.11ax. Safety rated to the relevant machinery standards for shared floors."
          "</p></main></body></html>")

case(
    "interior pages with no brand context or onward links -> ENG-001",
    "engagement",
    [{"url": "https://example.com/", "html": H.good_page(canonical="https://example.com/"),
      "page_type": "home", "is_home": True}]
    + [{"url": f"https://example.com/specs/{n}", "html": ORPHAN, "page_type": "other", "depth": 2}
       for n in ("amr-200", "amr-400", "amr-800")],
    expect=["ENG-001"],
    robots_txt="User-agent: *\n",
)

case(
    "no viewport meta -> ENG-007",
    "engagement",
    [dict(p, html=p["html"].replace('<meta name="viewport" content="width=device-width, initial-scale=1">', ""))
     for p in clean_pages()],
    expect=["ENG-007"],
    robots_txt="User-agent: *\n",
)

case(
    "a consent banner ALONE is not flagged as gating content",
    "engagement",
    [dict(p, html=p["html"].replace(
        "</body>", '<div class="cookie-consent-banner">We use cookies. '
                   '<button>Accept</button></div></body>'))
     for p in clean_pages()],
    forbid=["ENG-010"],
    robots_txt="User-agent: *\n",
)


# =============================================================================
# Composition: determinism and contract conformance
# =============================================================================

def _offsite(profiles, attempted=True):
    return {"offsite": {"attempted": attempted, "reason": None, "profiles": profiles,
                        "declared_sameas": len(profiles), "candidates_found": len(profiles)}}


_HOME = [{"url": "https://example.com/", "html": H.good_page(canonical="https://example.com/"),
          "page_type": "home", "is_home": True}]

case(
    "a declared sameAs profile that 404s -> ENT-011",
    "entity", _HOME,
    expect=["ENT-011"],
    robots_txt="User-agent: *\n",
    extras=_offsite([
        {"url": "https://github.com/acme", "status": 200, "state": "ok",
         "links_back": True, "mentions_domain": True, "text_sample": "Acme robots warehouse " * 12},
        {"url": "https://www.crunchbase.com/organization/acme", "status": 404, "state": "dead"},
    ]),
)

case(
    "a blocked profile is a limitation, never a dead link -> no ENT-011",
    "entity", _HOME,
    forbid=["ENT-011", "ENT-012"],
    robots_txt="User-agent: *\n",
    extras=_offsite([
        {"url": "https://www.linkedin.com/company/acme", "status": 403, "state": "blocked"},
        {"url": "https://x.com/acme", "status": None, "state": "robots_disallowed"},
    ]),
)

case(
    "reachable profiles that never link back -> ENT-012",
    "entity", _HOME,
    expect=["ENT-012"],
    robots_txt="User-agent: *\n",
    extras=_offsite([
        {"url": "https://github.com/acme", "status": 200, "state": "ok",
         "links_back": False, "mentions_domain": False, "text_sample": "unrelated page text " * 12},
        {"url": "https://medium.com/@acme", "status": 200, "state": "ok",
         "links_back": False, "mentions_domain": False, "text_sample": "unrelated page text " * 12},
    ]),
)

case(
    "profiles that do link back are not a reciprocity defect -> no ENT-012",
    "entity", _HOME,
    forbid=["ENT-012"],
    robots_txt="User-agent: *\n",
    extras=_offsite([
        {"url": "https://github.com/acme", "status": 200, "state": "ok",
         "links_back": True, "mentions_domain": True, "text_sample": "Northwind Robotics robots " * 12},
        {"url": "https://en.wikipedia.org/wiki/Acme", "status": 200, "state": "ok",
         "links_back": True, "mentions_domain": True, "text_sample": "Northwind Robotics robots " * 12},
    ]),
)

case(
    "off-site checks stay silent when verification never ran",
    "entity", _HOME,
    forbid=["ENT-011", "ENT-012", "ENT-013"],
    robots_txt="User-agent: *\n",
    extras={"offsite": {"attempted": False, "reason": "disabled by flag", "profiles": []}},
)


def test_end_to_end_composition():
    """Compose a report from a broken fixture twice; assert identical output
    and schema conformance."""
    import subprocess
    import tempfile

    pages = [{"url": "https://example.com/", "html": SHELL, "page_type": "home", "is_home": True},
             {"url": "https://example.com/pricing", "html": SHELL, "page_type": "pricing"},
             {"url": "https://example.com/about", "html": SHELL, "page_type": "about"}]
    cache = H.build_cache(pages, robots_txt="User-agent: *\nDisallow: /\n")
    work = os.path.join(cache, "_findings")
    os.makedirs(work, exist_ok=True)
    try:
        for name in ("access", "render", "schema", "answer", "entity", "engagement"):
            output = H.run_detector(name, cache)
            with open(os.path.join(work, f"{name}.json"), "w", encoding="utf-8") as fh:
                json.dump(output, fh)

        reports = []
        for run in range(2):
            out_path = os.path.join(tempfile.mkdtemp(), f"report-{run}.json")
            result = subprocess.run(
                [sys.executable, os.path.join(H.ROOT, "skills/audit-orchestrator/scripts/compose_report.py"),
                 "--cache", cache, "--findings-dir", work, "--out", out_path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if result.returncode != 0:
                RESULTS.append((False, "end-to-end composition", f" compose failed: {result.stderr[-400:]}"))
                return
            with open(out_path, encoding="utf-8") as fh:
                reports.append(json.load(fh))
            last_path = out_path

        a, b = reports
        for report in (a, b):
            report.pop("audited_at", None)
            report.get("audit", {}).pop("duration_seconds", None)
        RESULTS.append((a == b, "composition is deterministic across runs",
                        "" if a == b else " two runs produced different reports"))

        # Gate precedence: a site-wide robots block must demote later gates.
        demoted = [f for f in reports[0]["findings"]
                   if f.get("gate") != "access"
                   and "severity_adjustment" in (f.get("evidence_detail") or {})]
        RESULTS.append((bool(demoted), "gate precedence demotes later gates behind a site-wide block",
                        "" if demoted else " no finding was demoted despite ACC-002"))

        # Contract conformance.
        result = subprocess.run(
            [sys.executable, os.path.join(H.ROOT, "skills/audit-orchestrator/scripts/validate_report.py"),
             last_path],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        RESULTS.append((result.returncode == 0, "composed report satisfies the output contract",
                        "" if result.returncode == 0 else " " + result.stdout.strip()[-500:]))
    finally:
        H.cleanup(cache)


test_end_to_end_composition()


# =============================================================================

def main():
    passed = sum(1 for ok, _n, _d in RESULTS if ok)
    failed = len(RESULTS) - passed
    for ok, name, detail in RESULTS:
        if not ok or VERBOSE:
            print(f"{'PASS' if ok else 'FAIL'}  {name}{detail}")
    print(f"\n{passed}/{len(RESULTS)} passed" + (f", {failed} FAILED" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
