"""Build synthetic audit caches so detectors can be tested with no network.

Every test in this suite runs offline against hand-written HTML. That matters
for two reasons:

1. Detectors can be asserted in both directions - a broken fixture must produce
   a specific check_id, and a clean fixture must produce nothing. The second
   assertion is the only real evidence that a detector does not fire on healthy
   sites, which is the failure mode this marketplace is most concerned with.
2. The suite is deterministic and fast, so it can gate changes without
   depending on a live site that may change under it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))

from auditlib import cache as cache_mod  # noqa: E402


class FakeResponse:
    """Duck-types auditlib.http.Response for the cache writer."""

    def __init__(self, url, body="", status=200, headers=None, content_type="text/html",
                 error=None, tls_error=None, redirect_chain=None, elapsed=0.12):
        self.url = url
        self.final_url = url
        self.status = status
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.headers.setdefault("content-type", content_type)
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.elapsed = elapsed
        self.redirect_chain = redirect_chain or []
        self.error = error
        self.tls_error = tls_error
        self.truncated = False

    @property
    def content_type(self):
        return self.headers.get("content-type", "").split(";")[0].strip().lower()

    @property
    def bytes_len(self):
        return len(self.body)


def build_cache(pages, robots_txt=None, extras=None, capabilities=None,
                profile=None, site="example.com", origin="https://example.com/",
                cache_dir=None):
    """Create a cache directory from a list of page dicts.

    page dict keys: url, html, status, headers, content_type, page_type,
    is_home, discovered_via, rendered_html.
    """
    cache_dir = cache_dir or tempfile.mkdtemp(prefix="audit-fixture-")
    writer = cache_mod.Writer(cache_dir, site, origin, {"max_pages": len(pages)})

    for spec in pages:
        response = FakeResponse(
            spec["url"],
            body=spec.get("html", ""),
            status=spec.get("status", 200),
            headers=spec.get("headers"),
            content_type=spec.get("content_type", "text/html"),
            error=spec.get("error"),
            tls_error=spec.get("tls_error"),
            redirect_chain=spec.get("redirect_chain"),
            elapsed=spec.get("elapsed", 0.12),
        )
        writer.add_page(
            response,
            page_type=spec.get("page_type", "other"),
            is_home=spec.get("is_home", False),
            discovered_via=spec.get("discovered_via", "homepage-link"),
            depth=spec.get("depth", 1),
        )
        if spec.get("rendered_html"):
            writer.add_rendered(spec["url"], spec["rendered_html"])

    writer.set_robots_body(robots_txt or "")
    base_extras = {
        "origin": origin,
        "host_variants": {origin: {"status": 200, "final_url": origin, "redirects": 0, "elapsed": 0.1}},
        "robots": {"url": origin + "robots.txt", "status": 200 if robots_txt is not None else 404,
                   "error": None, "bytes": len(robots_txt or "")},
        "sitemaps": [{"url": origin + "sitemap.xml", "status": 200, "declared_in_robots": True,
                      "url_count": 20, "with_lastmod": 20,
                      "lastmod_values": ["2026-01-0%d" % i for i in range(1, 9)]}],
        "sitemap_url_count": 20,
        "sitemap_sample": [],
        "sitemap_lastmods": [],
        "probes": {
            "user_agent_differential": {
                "default_ua": {"status": 200, "words": 500, "bytes": 20000, "error": None, "server": "nginx"},
                "browser_ua": {"status": 200, "words": 500, "bytes": 20000, "error": None, "server": "nginx"},
            },
            "not_found": {"url": origin + "missing", "status": 404, "words": 20,
                          "final_url": origin + "missing", "redirected": False},
            "llms_txt": {"status": 404, "bytes": 0},
        },
        "robots_blocked_urls": [],
        "notes": [],
        "limitations": [],
    }
    if extras:
        for key, value in extras.items():
            if isinstance(value, dict) and isinstance(base_extras.get(key), dict):
                base_extras[key].update(value)
            else:
                base_extras[key] = value
    writer.set_extras(base_extras)
    writer.set_capabilities(capabilities or {"javascript_rendering": False, "web_search": False})
    writer.set_profile(profile or {"site_type": "saas", "site_type_confidence": "high",
                                   "platform": "unknown", "platform_confidence": "low",
                                   "primary_language": "en"})
    writer.save(started_at="2026-01-01T00:00:00Z", crawl_seconds=1.0, pages_requested=len(pages))
    return cache_dir


DETECTORS = {
    "access": "skills/site-access-audit/scripts/check_access.py",
    "render": "skills/render-extractability-audit/scripts/check_render.py",
    "schema": "skills/structured-data-audit/scripts/check_schema.py",
    "answer": "skills/answer-readiness-audit/scripts/check_answer_readiness.py",
    "entity": "skills/entity-corroboration-audit/scripts/check_identity.py",
    "engagement": "skills/engagement-audit/scripts/check_engagement.py",
}


def run_detector(name, cache_dir):
    """Run one detector against a cache and return its parsed output."""
    script = os.path.join(ROOT, DETECTORS[name])
    result = subprocess.run(
        [sys.executable, script, "--cache", cache_dir],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    if result.returncode != 0:
        raise AssertionError(f"{name} detector exited {result.returncode}:\n{result.stderr[-2000:]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"{name} detector did not emit valid JSON ({e}):\n{result.stdout[:1000]}")


def check_ids(output, exclude_info=False) -> set:
    """Check ids present in a detector's output.

    `exclude_info` drops info-severity findings, which the severity rubric
    defines as observations rather than defects. The clean-site control uses it
    so that recording, say, the absence of analytics does not count as a false
    positive.
    """
    return {f["check_id"] for f in output["findings"]
            if not (exclude_info and f.get("severity") == "info")}


def cleanup(path):
    shutil.rmtree(path, ignore_errors=True)


# --- reusable HTML building blocks --------------------------------------------

def good_page(title="Northwind Robotics - warehouse automation for mid-size distributors",
              h1="Warehouse automation for mid-size distributors",
              body=None, extra_head="", extra_body="", jsonld=None,
              canonical="https://example.com/"):
    body = body or (
        "<p>Northwind Robotics builds autonomous mobile robots that move pallets inside "
        "distribution centres. We are a robotics company based in Leeds, United Kingdom, founded "
        "in 2014, and we serve mid-size distributors across Europe.</p>"
        "<p>Our robots install in under two weeks and integrate with existing warehouse "
        "management systems. Pricing starts at 4,500 GBP per robot per year, billed annually, "
        "with no minimum fleet size.</p>"
        "<h2>How the robots navigate</h2>"
        "<p>Each unit maps the floor with lidar and shares that map with the fleet, so a new "
        "robot is productive within an hour of arriving on site. Typical deployments recover "
        "their cost within fourteen months.</p>"
        "<h2>What it costs</h2>"
        "<p>A single robot costs 4,500 GBP per year on an annual contract, which includes "
        "installation, remote monitoring, spare parts and software updates. There is no "
        "separate licence fee and no charge per pallet moved. Most customers start with three "
        "robots and add capacity each quarter as throughput grows.</p>"
        "<h2>Who we work with</h2>"
        "<p>We work with distributors handling between two thousand and forty thousand pallets "
        "a week, in food, pharmaceutical and general merchandise supply chains. Our largest "
        "installation runs sixty robots across two sites in the Netherlands.</p>"
    )
    ld = ""
    if jsonld:
        ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>'
    return f"""<!doctype html><html lang="en"><head>
<title>{title}</title>
<meta name="description" content="Northwind Robotics builds autonomous mobile robots for warehouse automation in mid-size distribution centres across Europe.">
<link rel="canonical" href="{canonical}">
<meta name="viewport" content="width=device-width, initial-scale=1">
{ld}{extra_head}</head><body>
<a class="skip-link" href="#main">Skip to main content</a>
<header><nav><a href="/">Home</a> <a href="/about">About</a> <a href="/pricing">Pricing</a> <a href="/contact">Contact</a></nav></header>
<main id="main"><h1>{h1}</h1>{body}
<p><a href="/pricing">See pricing</a> or <a href="/contact">book a site survey</a>.</p>
</main>
<footer><p>Northwind Robotics Ltd, 12 Wellington Street, Leeds LS1 4HW, United Kingdom. Telephone +44 113 496 0000. Copyright 2026.</p></footer>
{extra_body}</body></html>"""
