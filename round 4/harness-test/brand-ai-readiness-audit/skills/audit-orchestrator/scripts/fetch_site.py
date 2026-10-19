#!/usr/bin/env python3
"""Crawl a site once into the shared cache that every detector reads.

Read-only by construction: GET and HEAD only, no forms, no authenticated
areas, robots.txt obeyed for every crawled URL. The only requests that
deliberately ignore a Disallow are the diagnostic probes of robots.txt itself
and of the site root, which are single requests needed to report *why* a
crawler would be blocked.

Bounded by construction: a page budget, a wall-clock deadline, a per-request
timeout and a response size cap. The crawl degrades - fewer pages, recorded as
a limitation - rather than overrunning.

Usage:
    python fetch_site.py https://example.com --cache ./cache [--max-pages 30]
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
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

from auditlib import force_utf8_stdout  # noqa: E402
from auditlib import BROWSER_UA, USER_AGENT, MARKETPLACE_VERSION  # noqa: E402
from auditlib import cache as cache_mod, htmlx, http, robots as robots_mod, schema as schema_mod, urls  # noqa: E402

# A path that should never exist. Fixed rather than random so two runs of the
# audit produce identical evidence.
NONEXISTENT_PATH = "/audit-probe-404-do-not-create-b7f2c1"

# Sampling priority. The crawler spends its budget on the page classes that
# carry brand facts and answer real questions, not on whatever the homepage
# happens to link to first.
TYPE_PRIORITY = {
    "home": 0, "about": 1, "pricing": 2, "product": 3, "contact": 4,
    "faq": 5, "article": 6, "docs": 7, "category": 8, "case_study": 9,
    "section_home": 10, "careers": 11, "other": 12, "legal": 15,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Budget:
    """Wall-clock guard. Every phase asks before starting more work."""

    def __init__(self, seconds: float):
        self.deadline = time.time() + seconds
        self.overrun = False

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.time())

    def ok(self, need: float = 1.0) -> bool:
        if self.remaining() < need:
            self.overrun = True
            return False
        return True


# --- target resolution --------------------------------------------------------

def resolve_target(raw: str, budget: Budget, allow_ua_fallback: bool = True):
    """Find the canonical live origin, and record the host variants.

    Which of http/https and apex/www actually answer - and whether they
    redirect to one another - is itself audit evidence: a site reachable on
    four distinct origins that do not converge splits its own authority.

    If no origin answers the auditor's own user agent but one answers a browser
    user agent, the site is behind a bot-management rule. That is the single
    most valuable thing this audit can tell an owner, so the run must not end
    here: the origin is resolved with the browser agent, the crawl continues
    with it, and the substitution is disclosed in the finding, in
    `audit.limitations`, and in the returned metadata. Returning nothing would
    hide exactly the defect the owner most needs to see.
    """
    raw = raw.strip()
    if "://" not in raw:
        raw = "https://" + raw
    host = urls.host_of(raw)
    apex = urls.registrable(host)
    variants, resolved = {}, None

    candidates = [
        f"https://{apex}/", f"https://www.{apex}/",
        f"http://{apex}/", f"http://www.{apex}/",
    ]
    # Try the URL as given first so a site living on a subdomain still works.
    given = urls.normalize(raw)
    if given and given not in candidates:
        candidates.insert(0, given)

    def sweep(ua, tag):
        found = None
        for candidate in candidates:
            if not budget.ok(4):
                break
            resp = http.fetch(candidate, ua=ua, timeout=10, max_bytes=512 * 1024)
            variants.setdefault(candidate, {})[tag] = {
                "status": resp.status,
                "final_url": resp.final_url,
                "error": resp.error,
                "tls_error": resp.tls_error,
                "redirects": len(resp.redirect_chain),
                "elapsed": round(resp.elapsed, 3),
            }
            if tag == "default_ua":
                variants[candidate].update(variants[candidate]["default_ua"])
            if found is None and resp.ok and resp.is_html:
                found = resp.final_url
        return found

    resolved = sweep(USER_AGENT, "default_ua")
    crawl_ua, blocked = USER_AGENT, False
    if resolved is None and allow_ua_fallback and budget.ok(6):
        fallback = sweep(BROWSER_UA, "browser_ua")
        if fallback:
            resolved, crawl_ua, blocked = fallback, BROWSER_UA, True
    return resolved, variants, crawl_ua, blocked


# --- sitemap discovery --------------------------------------------------------

def _read_xml(resp) -> bytes:
    body = resp.body
    if resp.url.endswith(".gz") or resp.header("content-type").startswith("application/gzip"):
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    return body


def parse_sitemap(resp, budget: Budget, depth=0, seen=None):
    """Return (urls_with_lastmod, notes). Follows sitemap indexes one level."""
    seen = seen if seen is not None else set()
    out, notes = [], []
    body = _read_xml(resp)
    if not body:
        return out, ["sitemap body was empty"]
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        return out, [f"sitemap XML did not parse: {e}"]

    tag = root.tag.rsplit("}", 1)[-1].lower()

    def find_text(node, name):
        for child in node:
            if child.tag.rsplit("}", 1)[-1].lower() == name:
                return (child.text or "").strip()
        return ""

    if tag == "sitemapindex":
        children = [find_text(node, "loc") for node in root]
        children = [c for c in children if c][:10]
        notes.append(f"sitemap index listing {len(children)} child sitemaps")
        if depth == 0:
            for child_url in children:
                if not budget.ok(6) or child_url in seen:
                    break
                seen.add(child_url)
                child_resp = http.fetch(child_url, timeout=10, max_bytes=8 * 1024 * 1024)
                if child_resp.ok:
                    child_urls, child_notes = parse_sitemap(child_resp, budget, depth + 1, seen)
                    out.extend(child_urls)
                    notes.extend(child_notes)
    elif tag == "urlset":
        for node in root:
            loc = find_text(node, "loc")
            if loc:
                out.append({"url": loc, "lastmod": find_text(node, "lastmod")})
    else:
        notes.append(f"unexpected sitemap root element <{tag}>")
    return out, notes


def discover_sitemaps(origin: str, robots: robots_mod.Robots, budget: Budget):
    """Sitemaps declared in robots.txt plus the conventional locations."""
    tried, entries, notes = [], [], []
    candidates = list(dict.fromkeys(
        [u for u in robots.sitemaps if u]
        + [origin.rstrip("/") + p for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")]
    ))
    found_any = False
    for candidate in candidates[:6]:
        if not budget.ok(8):
            break
        resp = http.fetch(candidate, timeout=10, max_bytes=8 * 1024 * 1024)
        record = {
            "url": candidate,
            "status": resp.status,
            "declared_in_robots": candidate in robots.sitemaps,
            "error": resp.error,
            "url_count": 0,
            "with_lastmod": 0,
        }
        if resp.ok:
            found, sitemap_notes = parse_sitemap(resp, budget)
            record["url_count"] = len(found)
            record["with_lastmod"] = sum(1 for e in found if e["lastmod"])
            record["lastmod_values"] = sorted({e["lastmod"][:10] for e in found if e["lastmod"]})[:20]
            notes.extend(sitemap_notes)
            entries.extend(found)
            if found:
                found_any = True
        tried.append(record)
        if found_any and record["url_count"]:
            break
    return tried, entries, notes


# --- link discovery -----------------------------------------------------------

def links_from(page_html: str, page_url: str, origin: str) -> list:
    doc = htmlx.parse(page_html, page_url)
    out = []
    for href, _text, _rel, _node in doc.links():
        target = urls.normalize(href, base=page_url)
        if target and urls.same_site(target, origin):
            out.append(target)
    return out


def build_frontier(origin, sitemap_entries, home_html, budget):
    """Choose which URLs to spend the page budget on.

    Stratified, not first-come: one candidate per interesting page type before
    a second of any type, so a 3000-page blog cannot crowd out the pricing and
    contact pages that carry the facts assistants are asked for.
    """
    candidates = {}

    def consider(url, via):
        norm = urls.normalize(url)
        if not norm or not urls.same_site(norm, origin):
            return
        if not urls.is_probably_html(norm) and not urls.is_document(norm):
            return
        if urls.is_excluded_from_audit(norm):
            return
        candidates.setdefault(norm, via)

    for entry in sitemap_entries:
        consider(entry["url"], "sitemap")
    for link in links_from(home_html, origin, origin):
        consider(link, "homepage-link")

    scored = []
    for url, via in candidates.items():
        ptype = urls.classify_page(url, is_home=(urls.path_of(url) in ("/", "")))
        if urls.is_document(url):
            ptype = "document"
            rank = 10
        else:
            rank = TYPE_PRIORITY.get(ptype, 12)
        scored.append((rank, urls.depth(url), url, ptype, via))
    scored.sort()

    # Round-robin across page types for breadth, then fill by rank.
    by_type = {}
    for item in scored:
        by_type.setdefault(item[3], []).append(item)
    ordered, added = [], True
    while added:
        added = False
        for ptype in sorted(by_type, key=lambda t: TYPE_PRIORITY.get(t, 12)):
            if by_type[ptype]:
                ordered.append(by_type[ptype].pop(0))
                added = True
    return ordered


# --- access probes ------------------------------------------------------------

def run_probes(origin: str, budget: Budget) -> dict:
    """Differential and well-known-path probes.

    The user-agent probe is the important one: a CDN or WAF rule that serves
    200 to a browser string and 403 to everything else makes a site invisible
    to every AI fetcher while looking perfectly healthy to its owner.
    """
    probes = {}

    if budget.ok(6):
        as_bot = http.fetch(origin, ua=USER_AGENT, timeout=10, max_bytes=1024 * 1024)
        as_browser = http.fetch(origin, ua=BROWSER_UA, timeout=10, max_bytes=1024 * 1024)
        bot_words = len(htmlx.strip_tags(as_bot.text).split()) if as_bot.body else 0
        browser_words = len(htmlx.strip_tags(as_browser.text).split()) if as_browser.body else 0
        probes["user_agent_differential"] = {
            "default_ua": {"status": as_bot.status, "words": bot_words, "bytes": as_bot.bytes_len,
                           "error": as_bot.error, "server": as_bot.header("server")},
            "browser_ua": {"status": as_browser.status, "words": browser_words, "bytes": as_browser.bytes_len,
                           "error": as_browser.error, "server": as_browser.header("server")},
        }

    if budget.ok(4):
        missing = http.fetch(origin.rstrip("/") + NONEXISTENT_PATH, timeout=10, max_bytes=512 * 1024)
        probes["not_found"] = {
            "url": missing.url,
            "status": missing.status,
            "words": len(htmlx.strip_tags(missing.text).split()) if missing.body else 0,
            "final_url": missing.final_url,
            "redirected": bool(missing.redirect_chain),
        }

    for name, path in (("llms_txt", "/llms.txt"), ("llms_full_txt", "/llms-full.txt")):
        if not budget.ok(3):
            break
        resp = http.head_or_get(origin.rstrip("/") + path, timeout=8, max_bytes=256 * 1024)
        probes[name] = {"status": resp.status, "bytes": resp.bytes_len}

    return probes


# --- off-site corroboration ---------------------------------------------------

OFFSITE_MAX = 8
OFFSITE_BLOCKED_STATUSES = (401, 402, 403, 405, 406, 429, 451, 999)

def collect_profile_urls(home_html, home_url, limit=OFFSITE_MAX):
    """The external profiles the site explicitly claims as its own identity.

    Only `sameAs` entries are verified. `sameAs` is by definition the assertion
    "this profile is the same entity as this brand", so following it verifies a
    claim the site actually made.

    Ordinary homepage links are deliberately NOT followed. A site links to
    plenty of third-party pages it does not own - an issue tracker, a Wikipedia
    article about a technology it uses - and treating those as identity claims
    would fault a brand for a profile that was never theirs. That also keeps
    this step free of any host-pattern heuristic to maintain.
    """
    doc = htmlx.parse(home_html)
    ordered, seen = [], set()

    for raw in schema_mod.sameas_of(schema_mod.extract_objects(doc)):
        resolved = urls.normalize(raw, base=home_url)
        if not resolved or not resolved.startswith("http"):
            continue
        resolved = resolved.split("#")[0]
        if urls.same_site(resolved, home_url):
            continue
        key = resolved.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(resolved)

    return ordered[:limit], len(ordered)


def verify_profiles(profile_urls, origin, crawl_ua, budget, timeout=8.0):
    """Fetch each declared profile and record whether it resolves and links back.

    Read-only GETs to public URLs the site advertises, one per profile, with
    each third-party host's own robots.txt consulted first. A host that blocks
    or rate-limits automated clients yields "blocked" - an unverified profile,
    never a defect charged to the audited site.
    """
    results = []
    robots_by_host = {}
    brand_domain = urls.registrable(urls.host_of(origin))

    for url in profile_urls:
        if not budget.ok(8):
            results.append({"url": url, "state": "skipped_budget", "status": None})
            continue
        host = urls.host_of(url)
        if host not in robots_by_host:
            r = http.fetch("https://" + host + "/robots.txt", ua=crawl_ua,
                           timeout=6, max_bytes=512 * 1024)
            robots_by_host[host] = robots_mod.Robots(
                r.text if r.ok else "", r.status, "https://" + host + "/robots.txt")
        if not robots_by_host[host].allows(crawl_ua, url):
            results.append({"url": url, "state": "robots_disallowed", "status": None})
            continue

        resp = http.fetch(url, ua=crawl_ua, timeout=timeout, max_bytes=768 * 1024)
        rec = {"url": url, "status": resp.status, "final_url": resp.final_url}
        if resp.ok and resp.is_html:
            pdoc = htmlx.parse(resp.text)
            links_back = False
            for href, _t, _r, _n in pdoc.links():
                target = urls.normalize(href, base=resp.final_url)
                if target and urls.registrable(urls.host_of(target)) == brand_domain:
                    links_back = True
                    break
            rec["state"] = "ok"
            rec["links_back"] = links_back
            rec["mentions_domain"] = brand_domain.lower() in resp.text.lower()
            rec["text_sample"] = pdoc.visible_text[:600]
        elif resp.status in (404, 410):
            rec["state"] = "dead"
        elif resp.status in OFFSITE_BLOCKED_STATUSES:
            rec["state"] = "blocked"
        elif resp.tls_error:
            rec["state"] = "tls_error"
        else:
            rec["state"] = "error"
            rec["error"] = resp.error
        results.append(rec)
    return results


# --- optional JavaScript rendering -------------------------------------------

def try_render(page_urls, timeout_ms=15000):
    """Render pages with Playwright if it is installed.

    Absence is expected and handled: the render detector falls back to
    heuristics and labels its findings accordingly. It never pretends a DOM was
    executed when it was not.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return {}, "playwright not installed"
    rendered = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--disable-dev-shm-usage"])
            context = browser.new_context(user_agent=BROWSER_UA)
            for url in page_urls:
                page = None
                try:
                    page = context.new_page()
                    try:
                        page.goto(url, timeout=timeout_ms, wait_until="networkidle")
                    except Exception:
                        # Heavy single-page applications poll continuously and
                        # may never reach network idle - and those are exactly
                        # the pages with the largest render gap. Dropping them
                        # would hide the defect on the sites that have it worst,
                        # so settle for a parsed DOM plus a short settle delay.
                        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                        page.wait_for_timeout(2500)
                    rendered[url] = page.content()
                except Exception:
                    continue
                finally:
                    if page is not None:
                        try:
                            page.close()
                        except Exception:
                            pass
            browser.close()
    except Exception as e:
        return rendered, f"playwright failed to launch: {type(e).__name__}"
    return rendered, None


# --- main ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Crawl a site into the shared audit cache")
    ap.add_argument("target", help="URL or bare domain")
    ap.add_argument("--cache", required=True)
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=12.0)
    ap.add_argument("--budget", type=float, default=180.0, help="wall-clock seconds for the crawl phase")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--render-pages", type=int, default=3)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-offsite", action="store_true",
                    help="do not verify the external profiles the site declares; "
                         "the audit then stays strictly within the audited origin")
    ap.add_argument("--no-ua-fallback", action="store_true",
                    help="do not retry with a browser user agent when the site blocks the auditor; "
                         "the run then reports the site as unreachable instead of auditing it")
    args = ap.parse_args()
    force_utf8_stdout()

    started = time.time()
    budget = Budget(args.budget)
    notes, limitations = [], []

    origin, variants, crawl_ua, ua_blocked = resolve_target(
        args.target, budget, allow_ua_fallback=not args.no_ua_fallback)
    if not origin:
        os.makedirs(args.cache, exist_ok=True)
        writer = cache_mod.Writer(args.cache, urls.registrable(urls.host_of(args.target)), args.target, vars(args))
        writer.set_extras({
            "host_variants": variants,
            "fatal": "no origin responded with HTML to either the auditor or a browser user agent",
            "limitations": ["The site did not return HTML on http or https, apex or www, with either the "
                            "auditor's user agent or a browser user agent. No page-level check could run."],
            "probes": {}, "sitemaps": [], "notes": [],
        })
        writer.save(started_at=now_iso(), unreachable=True, crawl_seconds=round(time.time() - started, 2),
                    pages_requested=0)
        # A cache is still written, so the pipeline continues and emits a valid
        # report saying the site was unreachable - more useful than no output.
        print(json.dumps({"ok": False, "unreachable": True,
                          "error": "site did not respond on http/https, apex or www",
                          "cache": args.cache}, indent=2))
        return 0

    site = urls.registrable(urls.host_of(origin))
    os.makedirs(args.cache, exist_ok=True)
    writer = cache_mod.Writer(args.cache, site, origin, {
        "max_pages": args.max_pages, "timeout": args.timeout,
        "budget": args.budget, "marketplace_version": MARKETPLACE_VERSION,
    })

    # 1. robots.txt - fetched before anything is crawled, and obeyed after.
    robots_url = origin.rstrip("/") + "/robots.txt"
    robots_resp = http.fetch(robots_url, ua=crawl_ua, timeout=10, max_bytes=1024 * 1024)
    robots_text = robots_resp.text if robots_resp.ok else ""
    rules = robots_mod.Robots(robots_text, robots_resp.status, robots_url)
    writer.set_robots_body(robots_text)

    # 2. Homepage.
    #
    # Resolution can succeed and still land on a blocked origin: an apex that
    # returns 200 may redirect to a www host that rejects non-browser clients.
    # Verify the resolved origin actually yields content before spending the
    # page budget crawling 403s, and fall back the same way (disclosed) if not.
    home_resp = http.fetch(origin, ua=crawl_ua, timeout=args.timeout)
    if (not home_resp.ok or not home_resp.is_html) and not args.no_ua_fallback and crawl_ua != BROWSER_UA:
        retry = http.fetch(origin, ua=BROWSER_UA, timeout=args.timeout)
        if retry.ok and retry.is_html:
            notes.append(
                f"the resolved origin returned {home_resp.status or home_resp.error} to the auditor's user agent "
                "but 200 to a browser user agent; the crawl continued with a browser user agent"
            )
            home_resp, crawl_ua, ua_blocked = retry, BROWSER_UA, True
    writer.add_page(home_resp, page_type="home", is_home=True, discovered_via="origin", depth=0)
    home_html = home_resp.text

    # 3. Sitemaps and the crawl frontier.
    sitemaps, sitemap_entries, sitemap_notes = discover_sitemaps(origin, rules, budget)
    notes.extend(sitemap_notes)
    frontier = build_frontier(origin, sitemap_entries, home_html, budget)

    # 4. Crawl, obeying robots for every URL we choose to fetch.
    group = rules.group_for(USER_AGENT)
    delay = (group.crawl_delay if group and group.crawl_delay else 0.0)
    if delay > 2.0:
        notes.append(f"robots.txt requests Crawl-delay: {delay}s; capping page budget to stay polite and within the time budget")
        delay = min(delay, 2.0)

    to_fetch, blocked = [], []
    for _rank, depth, url, ptype, via in frontier:
        if len(to_fetch) >= args.max_pages - 1:
            break
        if url == origin:
            continue
        if not rules.allows(USER_AGENT, url):
            blocked.append(url)
            continue
        to_fetch.append((url, ptype, via, depth))

    fetched_pages = []

    def fetch_one(item):
        url, ptype, via, depth = item
        max_bytes = 3 * 1024 * 1024 if not urls.is_document(url) else 512 * 1024
        return item, http.fetch(url, ua=crawl_ua, timeout=args.timeout, max_bytes=max_bytes)

    if delay > 0:
        for item in to_fetch:
            if not budget.ok(args.timeout + 2):
                break
            fetched_pages.append(fetch_one(item))
            time.sleep(delay)
    else:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = []
            for item in to_fetch:
                if not budget.ok(args.timeout + 2):
                    break
                futures.append(pool.submit(fetch_one, item))
            for future in futures:
                try:
                    fetched_pages.append(future.result(timeout=args.timeout + 10))
                except Exception as e:
                    notes.append(f"fetch worker failed: {type(e).__name__}")

    # Deterministic page order regardless of thread completion order.
    fetched_pages.sort(key=lambda pair: (TYPE_PRIORITY.get(pair[0][1], 12), pair[0][3], pair[0][0]))
    for (url, ptype, via, depth), resp in fetched_pages:
        title = ""
        if resp.ok and resp.is_html and resp.body:
            title = htmlx.parse(resp.text, url).title
        writer.add_page(
            resp,
            page_type=("document" if urls.is_document(url) else urls.classify_page(url, title)),
            discovered_via=via, depth=depth,
        )

    if budget.overrun:
        limitations.append(
            f"Crawl stopped early at the {args.budget:.0f}s time budget; "
            f"{len(fetched_pages) + 1} of {len(to_fetch) + 1} selected pages were fetched. "
            "Coverage-based findings are computed over what was fetched."
        )
    if blocked:
        notes.append(f"{len(blocked)} discovered URLs were not crawled because robots.txt disallows them")

    # 5. Probes.
    probes = run_probes(origin, budget)

    # 6. Optional rendering, on the pages where a render gap matters most.
    capabilities = {"javascript_rendering": False, "web_search": False, "pdf_text_extraction": False}
    render_note = "rendering skipped by flag"
    if not args.no_render and args.render_pages > 0 and budget.ok(30):
        html_pages = [origin] + [
            url for (url, ptype, _via, _d), resp in fetched_pages
            if resp.ok and resp.is_html and ptype in ("product", "pricing", "article", "about", "docs", "other")
        ]
        rendered, render_note = try_render(html_pages[: args.render_pages])
        for url, html in rendered.items():
            writer.add_rendered(url, html)
        capabilities["javascript_rendering"] = bool(rendered)
    if not capabilities["javascript_rendering"]:
        limitations.append(
            "JavaScript rendering was unavailable (" + (render_note or "unknown") + "), so the render gap was "
            "estimated from static signals (framework shells, hydration payloads, text volume) rather than "
            "measured against an executed DOM. Render-gap findings carry method=heuristic and reduced confidence."
        )

    # 7. Off-site corroboration: verify the identity claims the site publishes.
    #    Run here, in the crawl phase, so the results live in the cache and a
    #    re-analysis of one crawl stays deterministic.
    offsite = {"attempted": False, "reason": "disabled by flag", "profiles": []}
    if not args.no_offsite and home_html:
        candidates, declared_count = collect_profile_urls(home_html, origin)
        if candidates:
            profiles = verify_profiles(candidates, origin, crawl_ua, budget)
            offsite = {"attempted": True, "reason": None, "profiles": profiles,
                       "declared_sameas": declared_count,
                       "candidates_found": len(candidates)}
            unverified = [p for p in profiles if p.get("state") in
                          ("blocked", "robots_disallowed", "skipped_budget")]
            if unverified:
                limitations.append(
                    f"{len(unverified)} of {len(profiles)} declared external profile(s) could not be "
                    "verified because the host blocked the request, disallows it in robots.txt, or the "
                    "time budget ran out. Those profiles are reported as unverified, never as defects. "
                    "Run with --no-offsite to skip off-site verification entirely."
                )
        else:
            offsite = {"attempted": True, "reason": "the site declares no sameAs profiles to verify",
                       "profiles": [], "declared_sameas": declared_count,
                       "candidates_found": 0}
    elif args.no_offsite:
        limitations.append(
            "Off-site verification was disabled (--no-offsite), so the external profiles this site "
            "declares were not checked for reachability or reciprocity."
        )
    else:
        offsite = {"attempted": False, "reason": "no homepage HTML was captured", "profiles": []}
    capabilities["offsite_verification"] = bool(offsite.get("attempted"))

    writer.set_capabilities(capabilities)
    if ua_blocked:
        limitations.append(
            "The site returned no usable response to this auditor's own user agent but did to a browser "
            "user agent, so the crawl was performed with a browser user agent in order to audit the "
            "content at all. See finding ACC-008: every non-browser client, including AI retrieval "
            "fetchers, receives the same block. Run with --no-ua-fallback to disable this substitution."
        )

    writer.set_extras({
        "origin": origin,
        "crawl_user_agent": crawl_ua,
        "user_agent_blocked": ua_blocked,
        "host_variants": variants,
        "robots": {"url": robots_url, "status": robots_resp.status, "error": robots_resp.error,
                   "bytes": robots_resp.bytes_len, "content_type": robots_resp.content_type},
        "sitemaps": sitemaps,
        "sitemap_url_count": len(sitemap_entries),
        "sitemap_sample": [e["url"] for e in sitemap_entries[:200]],
        "sitemap_lastmods": [e["lastmod"] for e in sitemap_entries[:500] if e["lastmod"]],
        "probes": probes,
        "offsite": offsite,
        "robots_blocked_urls": blocked[:25],
        "notes": notes,
        "limitations": limitations,
    })
    writer.save(started_at=now_iso(), crawl_seconds=round(time.time() - started, 2),
                pages_requested=len(to_fetch) + 1)

    print(json.dumps({
        "ok": True, "site": site, "origin": origin,
        "pages_fetched": len(writer.manifest["pages"]),
        "sitemap_urls": len(sitemap_entries),
        "rendered": capabilities["javascript_rendering"],
        "seconds": round(time.time() - started, 2),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
