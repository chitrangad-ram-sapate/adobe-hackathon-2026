#!/usr/bin/env python3
"""Gate 1 - Access. Can a machine reach the content at all?

This is the first gate for a reason: nothing downstream matters if the fetch
never succeeds. A site with immaculate structured data that returns 403 to
every non-browser user agent is invisible, and its owner will never see the
problem, because it looks perfect in their browser.

Reads the shared cache; performs no network requests of its own.

Usage:
    python check_access.py --cache ./cache
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

from auditlib import cache as cache_mod, findings as F, urls  # noqa: E402
from auditlib.robots import AI_CRAWLERS  # noqa: E402

CHALLENGE_MARKERS = re.compile(
    r"(just a moment|checking your browser|cf-browser-verification|cf_chl_opt|"
    r"attention required|access denied|enable javascript and cookies|ddos protection|"
    r"pardon our interruption|are you a robot|incapsula|请开启|verifying you are human)",
    re.I,
)

IMPORTANT_TYPES = {"home", "about", "pricing", "product", "contact", "faq", "article", "docs", "section_home"}


def check_reachable(cache, out, skipped):
    """The site answered nothing at all - report it rather than staying silent."""
    if not cache.manifest.get("unreachable"):
        return
    variants = cache.extras.get("host_variants", {})
    statuses = []
    for url, info in list(variants.items())[:4]:
        default = info.get("default_ua", info)
        statuses.append(f"{url} -> {default.get('status') or default.get('error') or 'no response'}")
    out.append(F.finding(
        "ACC-000", "The site did not respond to any request",
        "critical", "discoverability", "access",
        evidence=f"{len(variants)} origin variant(s) were tried with both an auditor and a browser user agent, "
                 f"and none returned HTML: {'; '.join(statuses)}.",
        mechanism="Nothing can index, retrieve or cite a site it cannot fetch. Every other check in this audit "
                  "depends on a successful response, so none of them could run - this is the only finding, and "
                  "the absence of others is not evidence that the rest of the site is sound.",
        action_summary="Restore a working HTTP response on the canonical hostname.",
        how=[
            "Confirm DNS resolves for both the apex and www hostnames.",
            "Confirm the origin server is running and reachable from outside your network.",
            "Check whether a CDN, WAF or firewall rule is rejecting the request before it reaches the origin.",
            "Verify the certificate is valid and serves the full chain.",
            "Re-run this audit once a browser can load the site from an external network.",
        ],
        effort="medium", owner="ops", method="probe",
        evidence_detail={"variants": variants},
        verify="Re-run the audit; ACC-000 should not fire.",
    ))
    # Nothing downstream in this gate can be measured.
    raise StopIteration


def check_robots(cache, out, skipped):
    robots = cache.robots
    extras = cache.extras
    info = extras.get("robots", {})

    if robots.fetch_failed:
        out.append(F.finding(
            "ACC-001", "robots.txt could not be fetched",
            "high", "discoverability", "access",
            evidence=f"GET {info.get('url','/robots.txt')} returned status {info.get('status', 0)}"
                     f"{' (' + str(info.get('error')) + ')' if info.get('error') else ''}.",
            mechanism="Several major crawlers treat an unreachable or 5xx robots.txt as disallow-all "
                      "rather than allow-all, because they cannot prove they are permitted. A server error "
                      "on this one file can therefore suppress crawling of the entire site.",
            action_summary="Make /robots.txt return 200 with a plain-text body, or 404 if you do not need one.",
            how=[
                "Serve /robots.txt as text/plain with a 200 status; a 404 is also safe and means 'no restrictions'.",
                "Ensure the file is served from the same origin as the site and is not behind the CDN's bot challenge.",
                "Never let this path return 5xx: fix the origin error or serve a static file at the edge.",
            ],
            effort="low", owner="engineering", method="static",
            evidence_detail=info,
            verify="curl -sI https://<site>/robots.txt returns 200 or 404, never 5xx.",
        ))
        return

    if not robots.exists:
        # A 404 robots.txt is correct behaviour, not a defect. Say nothing.
        skipped.append(F.skip("ACC-002", "no robots.txt served (404), which correctly means no crawl restrictions"))
        return

    # --- blanket block --------------------------------------------------
    star = robots.group_for("*")
    if star and star.blocks_everything():
        out.append(F.finding(
            "ACC-002", "robots.txt blocks all crawlers from the entire site",
            "critical", "discoverability", "access",
            evidence=f"The User-agent: * group contains '{star.match('/')[3]}', which disallows every path for every "
                     "crawler that has no more specific group.",
            mechanism="Every compliant crawler - search engines and AI retrieval fetchers alike - stops here. "
                      "The site cannot be indexed, retrieved, or cited by anything that respects the standard, "
                      "no matter how good its content is.",
            action_summary="Remove the site-wide Disallow: / and restrict only the paths that genuinely must stay private.",
            how=[
                "Delete or narrow the `Disallow: /` line in the `User-agent: *` group.",
                "Replace it with specific paths that should not be crawled (for example /cart, /account, /search).",
                "If this was inherited from a staging configuration, check the deployment pipeline: staging robots.txt "
                "reaching production is the single most common cause of this.",
            ],
            effort="low", owner="engineering", method="static",
            evidence_detail={"rule": star.match("/")[3], "line": star.match("/")[4], "agents": star.agents},
            verify="Re-run check ACC-002; the * group should no longer disallow /.",
        ))

    # --- AI crawler blocks ----------------------------------------------
    status = robots.ai_crawler_status("/")
    retrieval_blocked, training_blocked = [], []
    for agent, detail in status["ai"].items():
        if not detail.get("blocked"):
            continue
        (retrieval_blocked if detail["purpose"] in ("retrieval", "both") else training_blocked).append(
            {"agent": agent, "vendor": detail["vendor"], "rule": detail.get("rule", ""), "line": detail.get("line")}
        )

    if retrieval_blocked:
        vendors = sorted({b["vendor"] for b in retrieval_blocked})
        named = [b for b in retrieval_blocked if b.get("rule")]
        out.append(F.finding(
            "ACC-003", "AI assistant retrieval crawlers are blocked in robots.txt",
            "critical", "discoverability", "access",
            evidence=f"{len(retrieval_blocked)} retrieval agents are disallowed from /: "
                     + ", ".join(f"{b['agent']} ({b['vendor']})" for b in retrieval_blocked[:6])
                     + (f"; e.g. rule '{named[0]['rule']}' at line {named[0]['line']}." if named else "."),
            mechanism="These are the agents that fetch a page live while composing an answer and then cite it. "
                      "Blocking them is different from blocking training crawlers: it removes the brand from "
                      "answers that would have linked back to the site, so it costs referral traffic directly "
                      "and immediately. It is very often set by accident, by copying a blocklist intended to "
                      "opt out of model training.",
            action_summary=f"Allow retrieval agents ({', '.join(vendors)}) while keeping any training opt-out you intend.",
            how=[
                "Separate the two decisions: keep `Disallow: /` for training crawlers if that is a deliberate policy, "
                "but allow the retrieval agents (OAI-SearchBot, ChatGPT-User, Claude-User, Claude-SearchBot, "
                "PerplexityBot, Meta-ExternalFetcher).",
                "Give each retrieval agent its own `User-agent` group with `Disallow:` left empty, since the most "
                "specific matching group wins and a broad block would otherwise still apply.",
                "Confirm the same agents are not also blocked at the CDN or WAF layer - robots.txt is advisory and "
                "an edge rule will override your intent (see ACC-008).",
            ],
            effort="low", owner="engineering", method="static",
            evidence_detail={"blocked": retrieval_blocked},
            verify="Re-run check ACC-003; no agent with purpose=retrieval should be disallowed from /.",
        ))

    if training_blocked and not retrieval_blocked:
        # Reported at info: opting out of training corpora is a legitimate,
        # common business decision and is not a defect. The reader is told what
        # it costs so the decision can be made knowingly.
        out.append(F.finding(
            "ACC-004", "AI training crawlers are blocked (recorded, not flagged as a defect)",
            "info", "discoverability", "access",
            evidence=f"{len(training_blocked)} training-corpus agents are disallowed: "
                     + ", ".join(b["agent"] for b in training_blocked[:8]) + ".",
            mechanism="Training crawlers build the corpus a model learns from. Blocking them reduces the chance "
                      "the brand is known from model memory, but does not affect live retrieval or citation. "
                      "This is a policy choice with a known cost, not a misconfiguration.",
            action_summary="No action required unless the brand wants to be recalled from model memory as well as cited.",
            how=[
                "Keep this block if opting out of training is deliberate.",
                "If it was not deliberate, allow GPTBot, ClaudeBot, Google-Extended and CCBot to be learned from.",
            ],
            effort="low", owner="marketing", method="static",
            evidence_detail={"blocked": training_blocked},
            verify="No verification needed; this is an observation.",
        ))

    # --- classic search crawler blocks ----------------------------------
    search_blocked = [a for a, d in status["search"].items() if d.get("blocked")]
    if search_blocked and not (star and star.blocks_everything()):
        out.append(F.finding(
            "ACC-005", "Conventional search crawlers are blocked in robots.txt",
            "critical" if "googlebot" in search_blocked else "high",
            "discoverability", "access",
            evidence=f"{len(search_blocked)} of {len(status['search'])} major search crawlers are disallowed "
                     f"from /: {', '.join(sorted(search_blocked))}.",
            mechanism="Several assistants ground their answers on a conventional web index rather than crawling "
                      "directly. Excluding the search crawlers therefore removes the brand from AI answers "
                      "indirectly, through a path most teams do not think to check.",
            action_summary="Allow the major search crawlers unless there is a specific reason to exclude them.",
            how=["Remove the Disallow rules targeting Googlebot, Bingbot and equivalents.",
                 "Restrict only genuinely private paths."],
            effort="low", owner="engineering", method="static",
            evidence_detail={"blocked": sorted(search_blocked)},
        ))

    # --- malformed directives -------------------------------------------
    if robots.parse_notes:
        out.append(F.finding(
            "ACC-006", "robots.txt contains directives that crawlers will silently ignore",
            "medium", "discoverability", "access",
            evidence=f"{len(robots.parse_notes)} malformed or misplaced line(s): " + "; ".join(robots.parse_notes[:3]) + ".",
            mechanism="robots.txt has no error reporting. A rule placed before any User-agent line, or written with "
                      "the wrong separator, is discarded without warning - so the file appears to express an intent "
                      "that no crawler is acting on. This cuts both ways: intended blocks are not applied, and "
                      "intended allowances do not override a broader block.",
            action_summary="Fix the malformed lines so the file expresses what it appears to express.",
            how=["Ensure every Allow/Disallow line follows a User-agent line within the same group.",
                 "Use `Field: value` syntax on every line; blank-line separated groups.",
                 "Re-test the file against the paths you intend to control."],
            effort="low", owner="engineering", method="static",
            evidence_detail={"notes": robots.parse_notes[:10]},
        ))


def check_bot_gating(cache, out, skipped):
    """The differential user-agent probe - the highest-yield check in the gate."""
    probe = cache.extras.get("probes", {}).get("user_agent_differential")
    if not probe:
        skipped.append(F.skip("ACC-008", "user-agent differential probe did not run (time budget)"))
        return

    bot, browser = probe["default_ua"], probe["browser_ua"]
    home = cache.home
    body_blob = home.html[:20000] if home else ""

    bot_blocked = bot["status"] in (401, 403, 405, 406, 429, 503) or bot.get("error")
    browser_ok = 200 <= browser["status"] < 300

    if bot_blocked and browser_ok:
        out.append(F.finding(
            "ACC-008", "The site serves content to browsers but blocks non-browser clients",
            "critical", "discoverability", "access",
            evidence=f"The same URL returned {browser['status']} with {browser['words']} words to a browser "
                     f"user-agent, and {bot['status'] or 'a connection failure'} to a plain client"
                     f"{' (server: ' + bot.get('server', '') + ')' if bot.get('server') else ''}.",
            mechanism="A CDN, WAF or bot-management rule is filtering by user-agent or TLS fingerprint. Every AI "
                      "retrieval fetcher and most search crawlers arrive as non-browser clients, so they receive the "
                      "challenge page instead of the content. The site looks perfectly healthy to its owners, who "
                      "only ever visit it in a browser, which is why this failure can persist for years unnoticed.",
            action_summary="Allow verified search and AI crawler traffic through the bot-management rules at the edge.",
            how=[
                "In the CDN/WAF bot-management configuration, add an allow rule for verified search and AI crawlers "
                "rather than relying on user-agent strings alone.",
                "Verify by reverse-DNS or the vendors' published IP ranges so the allowance cannot be spoofed.",
                "Re-test with `curl -A 'GPTBot' https://<site>/` and confirm a 200 with real content, not a challenge page.",
                "Check rate-limit thresholds separately: a 429 to crawlers has the same effect as a block.",
            ],
            effort="medium", owner="ops", method="probe", confidence="high",
            evidence_detail=probe,
            verify="Re-run check ACC-008; both user agents should return 200 with comparable word counts.",
        ))
        return

    # Same status, very different content: soft gating (a challenge page or an
    # interstitial served with a 200).
    if browser_ok and 200 <= bot["status"] < 300:
        bot_words, browser_words = bot["words"], browser["words"]
        if browser_words >= 100 and bot_words < browser_words * 0.4:
            out.append(F.finding(
                "ACC-009", "Non-browser clients receive substantially less content than browsers",
                "high", "discoverability", "access",
                evidence=f"Both requests returned 200, but the browser user-agent received {browser_words} words "
                         f"and a plain client received {bot_words} "
                         f"({round(100 * bot_words / max(1, browser_words))}% of the content).",
                mechanism="The edge is serving a reduced page - typically a JavaScript challenge or an interstitial - "
                          "under a 200 status. Crawlers cannot tell they were served a placeholder, so they index the "
                          "placeholder, and the brand is represented in AI answers by a page that says nothing.",
                action_summary="Stop serving challenge or placeholder content to non-browser clients.",
                how=["Identify the edge rule producing the reduced response (bot management, geo/consent gating, A/B split).",
                     "Exempt verified crawler traffic from it.",
                     "If a challenge is required, return 503 with Retry-After rather than a 200, so crawlers do not "
                     "cache the placeholder as the page's content."],
                effort="medium", owner="ops", method="probe", confidence="high",
                evidence_detail=probe,
            ))
            return
        if CHALLENGE_MARKERS.search(body_blob):
            out.append(F.finding(
                "ACC-010", "The crawled homepage looks like a bot-challenge page, not the real site",
                "critical", "discoverability", "access",
                evidence="The fetched homepage body matches a bot-challenge signature "
                         f"({CHALLENGE_MARKERS.search(body_blob).group(0)!r}), so the audited content is the "
                         "interstitial rather than the site.",
                mechanism="Interstitial challenge pages are what an AI fetcher sees and, in some pipelines, what it "
                          "stores. Everything downstream of this - structured data, copy, engagement - is being "
                          "measured against a page the brand did not write.",
                action_summary="Exempt verified crawlers from the interstitial so they receive the real page.",
                how=["Allow verified search/AI crawler traffic through bot management.",
                     "Re-run this audit afterwards: all other findings in this report were measured against the "
                     "challenge page and must be re-established."],
                effort="medium", owner="ops", method="probe", confidence="high",
                evidence_detail={"marker": CHALLENGE_MARKERS.search(body_blob).group(0)},
            ))


def check_sitemaps(cache, out, skipped):
    extras = cache.extras
    sitemaps = extras.get("sitemaps", [])
    working = [s for s in sitemaps if s.get("url_count", 0) > 0]
    declared = [s for s in sitemaps if s.get("declared_in_robots")]
    total_urls = extras.get("sitemap_url_count", 0)

    if not working:
        broken_declared = [s for s in declared if s.get("url_count", 0) == 0]
        if broken_declared:
            out.append(F.finding(
                "ACC-011", "The sitemap declared in robots.txt does not work",
                "high", "discoverability", "access",
                evidence="; ".join(
                    f"{s['url']} returned status {s['status']}"
                    + (f" ({s['error']})" if s.get("error") else "")
                    + (" and contained no URLs" if s["status"] == 200 else "")
                    for s in broken_declared[:3]) + ".",
                mechanism="robots.txt advertises a sitemap that crawlers then fail to retrieve or parse. Discovery "
                          "falls back to link-following, so any page not linked from a crawled page - which on most "
                          "sites means deep product, location and article pages - is never found.",
                action_summary="Fix or remove the broken sitemap reference and publish a valid XML sitemap.",
                how=["Serve the declared sitemap URL with a 200 and a valid <urlset> or <sitemapindex> body.",
                     "Validate it parses as XML and every <loc> is an absolute URL on this site.",
                     "If the sitemap no longer exists, remove its Sitemap: line from robots.txt."],
                effort="low", owner="engineering", method="static",
                evidence_detail={"sitemaps": broken_declared},
            ))
        else:
            severity = "medium" if len(cache.html_pages()) <= 8 else "high"
            out.append(F.finding(
                "ACC-012", "No XML sitemap was found",
                severity, "discoverability", "access",
                evidence=f"No sitemap was declared in robots.txt and {len(sitemaps)} conventional location(s) "
                         f"({', '.join(urls.path_of(s['url']) for s in sitemaps) or 'none reachable'}) returned "
                         f"0 parseable sitemap URLs across {len(cache.html_pages())} crawled pages.",
                mechanism="Without a sitemap, a crawler can only find pages by following links from pages it has "
                          "already fetched. Pages that are linked only from JavaScript menus, paginated archives, or "
                          "nowhere at all are never discovered, and cannot be cited.",
                action_summary="Publish an XML sitemap and declare it in robots.txt.",
                how=["Generate a sitemap listing every canonical, indexable URL, with an accurate <lastmod> per URL.",
                     "Add `Sitemap: https://<site>/sitemap.xml` to robots.txt.",
                     "Split into a sitemap index if the site exceeds 50,000 URLs or 50 MB uncompressed.",
                     "Regenerate it automatically on publish, so <lastmod> stays truthful."],
                effort="low", owner="engineering", method="static",
                evidence_detail={"tried": [s["url"] for s in sitemaps]},
            ))
        return

    if not declared:
        out.append(F.finding(
            "ACC-013", "A sitemap exists but is not declared in robots.txt",
            "low", "discoverability", "access",
            evidence=f"{working[0]['url']} contains {working[0]['url_count']} URLs, but robots.txt has no "
                     "Sitemap: directive.",
            mechanism="Crawlers that do not guess conventional filenames rely on the robots.txt declaration to find "
                      "the sitemap. Declaring it is the only portable way to advertise a sitemap that is not at the "
                      "default path.",
            action_summary="Add a Sitemap: line to robots.txt.",
            how=[f"Add `Sitemap: {working[0]['url']}` to robots.txt."],
            effort="low", owner="engineering", method="static",
        ))

    primary = working[0]
    with_lastmod = primary.get("with_lastmod", 0)
    count = primary.get("url_count", 0)
    if count and with_lastmod / count < 0.5:
        out.append(F.finding(
            "ACC-014", "Sitemap entries mostly lack <lastmod> dates",
            "low", "discoverability", "access",
            evidence=f"{with_lastmod} of {count} sitemap URLs carry a <lastmod> value.",
            mechanism="Crawlers use <lastmod> to decide what to re-fetch. Without it they re-crawl on their own "
                      "schedule, so updated pages can be represented in answers by a stale copy for far longer "
                      "than necessary.",
            action_summary="Emit an accurate <lastmod> for every sitemap URL.",
            how=["Populate <lastmod> from the content's real last-modified time, not the build time.",
                 "Do not set every URL to the same timestamp on each deploy - crawlers learn to distrust it."],
            effort="low", owner="engineering", method="static",
            evidence_detail={"url_count": count, "with_lastmod": with_lastmod},
        ))
    elif count and with_lastmod == count:
        values = primary.get("lastmod_values", [])
        if len(values) == 1 and count >= 20:
            out.append(F.finding(
                "ACC-015", "Every sitemap URL shares one identical <lastmod> date",
                "low", "discoverability", "trust",
                evidence=f"All {count} sitemap URLs report <lastmod> {values[0]}.",
                mechanism="A single build timestamp stamped across every URL tells a crawler nothing about which "
                          "pages actually changed. Crawlers detect this pattern and discount the signal, which "
                          "removes the benefit of having it at all.",
                action_summary="Derive <lastmod> per URL from real content modification times.",
                how=["Emit each URL's own last content change date.",
                     "If the CMS cannot supply it, omit <lastmod> rather than stamping the build time."],
                effort="medium", owner="engineering", method="static",
                evidence_detail={"lastmod_values": values, "url_count": count},
            ))


def check_indexability(cache, out, skipped):
    pages = cache.html_pages()
    if not pages:
        skipped.append(F.skip("ACC-016", "no HTML pages were fetched"))
        return

    noindex_pages, header_noindex = [], []
    for page in pages:
        meta_robots = page.doc.robots_meta
        header = page.header("x-robots-tag", "").lower()
        if "noindex" in meta_robots or "none" in meta_robots:
            noindex_pages.append(page)
        if "noindex" in header or "none" in header:
            header_noindex.append(page)

    important_noindex = [
        p for p in noindex_pages + header_noindex
        if p.page_type in IMPORTANT_TYPES and not urls.is_transactional_host(p.url)
    ]
    if important_noindex:
        home_affected = any(p.is_home for p in important_noindex)
        severity = "critical" if home_affected else "high"
        severity = F.apply_blast_radius(severity, len(important_noindex), len(pages)) if not home_affected else severity
        out.append(F.finding(
            "ACC-016", "Pages that should be findable are marked noindex",
            severity, "discoverability", "access",
            evidence=f"{len(important_noindex)} of {len(pages)} sampled pages carry a noindex directive"
                     + (" including the homepage" if home_affected else "")
                     + f", e.g. {important_noindex[0].url}.",
            mechanism="noindex tells indexing systems to discard the page after fetching it. Content behind it can "
                      "never be surfaced or cited, and because the page still renders normally for visitors, the "
                      "exclusion is invisible from inside the organisation.",
            action_summary="Remove noindex from pages that are meant to be found.",
            how=["Remove `<meta name=\"robots\" content=\"noindex\">` and any `X-Robots-Tag: noindex` header from these pages.",
                 "Check whether the directive is applied by a template or an edge rule rather than by the page itself.",
                 "A staging-environment configuration reaching production is the usual cause - verify the deploy pipeline."],
            effort="low", owner="engineering", method="static",
            affected_urls=[p.url for p in important_noindex],
            affected_count=len(important_noindex), sampled_count=len(pages),
            evidence_detail={"meta_noindex": [p.url for p in noindex_pages][:10],
                             "header_noindex": [p.url for p in header_noindex][:10]},
            verify="Fetch each URL and confirm no noindex appears in the meta robots tag or the X-Robots-Tag header.",
        ))


def check_canonicals(cache, out, skipped):
    pages = [p for p in cache.html_pages() if p.page_type != "section_home"]
    if len(pages) < 3:
        skipped.append(F.skip("ACC-017", "fewer than 3 comparable HTML pages sampled"))
        return

    missing, offsite, collapsed = [], [], []
    home_url = cache.home.url if cache.home else ""
    for page in pages:
        canonical = page.doc.canonical
        if not canonical:
            missing.append(page)
            continue
        resolved = urls.normalize(canonical, base=page.url)
        if not resolved:
            continue
        if not urls.same_site(resolved, page.url):
            offsite.append((page, resolved))
        elif home_url and urls.normalize(resolved) == urls.normalize(home_url) and not page.is_home:
            collapsed.append((page, resolved))

    if offsite:
        out.append(F.finding(
            "ACC-018", "Canonical tags point to a different domain",
            "critical", "discoverability", "access",
            evidence=f"{len(offsite)} of {len(pages)} sampled pages declare a canonical URL on another host, "
                     f"e.g. {offsite[0][0].url} -> {offsite[0][1]}.",
            mechanism="A cross-domain canonical instructs indexing systems to attribute the content to the other "
                      "domain entirely. The brand's own pages are then treated as duplicates, and any citation goes "
                      "to the other site.",
            action_summary="Point canonical tags at the page's own URL on this domain.",
            how=["Set a self-referencing canonical on every indexable page.",
                 "If the content is genuinely syndicated from elsewhere, keep the cross-domain canonical only on the "
                 "syndicated copies, never on original pages."],
            effort="low", owner="engineering", method="static",
            affected_urls=[p.url for p, _ in offsite], affected_count=len(offsite), sampled_count=len(pages),
            evidence_detail={"examples": [{"page": p.url, "canonical": c} for p, c in offsite[:5]]},
        ))

    if len(collapsed) >= max(2, len(pages) * 0.25):
        out.append(F.finding(
            "ACC-019", "Multiple distinct pages canonicalise to the homepage",
            "high", "discoverability", "access",
            evidence=f"{len(collapsed)} of {len(pages)} sampled pages declare the homepage as their canonical URL, "
                     f"e.g. {collapsed[0][0].url}.",
            mechanism="Every page carrying this tag asks to be collapsed into the homepage. Their content is dropped "
                      "from the index, so none of it can be retrieved or quoted - only the homepage survives, and it "
                      "rarely contains the specific fact a question is about.",
            action_summary="Give each page a self-referencing canonical URL.",
            how=["Emit `<link rel=\"canonical\" href=\"<this page's own absolute URL>\">` per page.",
                 "This is usually a template defect where a hard-coded site URL was used; fix it once in the layout."],
            effort="low", owner="engineering", method="static",
            affected_urls=[p.url for p, _ in collapsed], affected_count=len(collapsed), sampled_count=len(pages),
        ))

    if len(missing) >= max(3, len(pages) * 0.6) and not offsite:
        out.append(F.finding(
            "ACC-020", "Most pages have no canonical URL declared",
            "low", "discoverability", "access",
            evidence=f"{len(missing)} of {len(pages)} sampled pages have no rel=canonical link.",
            mechanism="Without a canonical, the same content reachable through tracking parameters, trailing-slash "
                      "variants or both host names is treated as several competing pages. Authority is split across "
                      "the duplicates and none of them is a clear best answer.",
            action_summary="Add a self-referencing canonical to every indexable page.",
            how=["Add `<link rel=\"canonical\">` to the base template, populated with the page's own absolute URL.",
                 "Normalise it: one host, one scheme, consistent trailing slash, no tracking parameters."],
            effort="low", owner="engineering", method="static",
            affected_count=len(missing), sampled_count=len(pages),
        ))


def check_origins(cache, out, skipped):
    variants = cache.extras.get("host_variants", {})
    if not variants:
        skipped.append(F.skip("ACC-021", "host variant probe did not run"))
        return

    live_https = {
        url: info for url, info in variants.items()
        if url.startswith("https://") and 200 <= info.get("status", 0) < 300
    }
    # Two https origins that both answer 200 and do not converge on one
    # final_url are serving the site twice.
    finals = {info.get("final_url", "") for info in live_https.values()}
    if len(live_https) > 1 and len({urls.normalize(f) or f for f in finals}) > 1:
        out.append(F.finding(
            "ACC-021", "The site answers on both apex and www without redirecting to one",
            "medium", "discoverability", "access",
            evidence="Distinct 200 responses on " + ", ".join(sorted(live_https)) +
                     " resolving to different final URLs: " + ", ".join(sorted(f for f in finals if f)) + ".",
            mechanism="Two hostnames serving the same content are two sites as far as an indexing system is "
                      "concerned. Links, citations and authority accumulated by the brand are split between them, "
                      "and neither version is as strong a candidate to cite as the combined site would be.",
            action_summary="Pick one canonical hostname and 301-redirect the other to it.",
            how=["Choose apex or www and redirect the other with a permanent 301 at the edge.",
                 "Make canonical tags, sitemap URLs and internal links all use the chosen host.",
                 "Keep the redirect to a single hop - chains lose crawlers."],
            effort="low", owner="engineering", method="probe",
            evidence_detail={"variants": variants},
        ))

    http_live = {
        url: info for url, info in variants.items()
        if url.startswith("http://") and 200 <= info.get("status", 0) < 300
        and str(info.get("final_url", "")).startswith("http://")
    }
    if http_live:
        out.append(F.finding(
            "ACC-022", "Plain HTTP serves content without redirecting to HTTPS",
            "medium", "discoverability", "access",
            evidence=", ".join(sorted(http_live)) + " returned 200 over plain HTTP without redirecting to HTTPS.",
            mechanism="An insecure duplicate of the site exists at a second set of URLs. Browsers warn visitors, "
                      "which costs engagement, and the duplicate splits the site's authority the same way a second "
                      "hostname does.",
            action_summary="Redirect all HTTP traffic to HTTPS with a permanent 301 and enable HSTS.",
            how=["Return `301 https://<canonical-host><path>` for every http:// request.",
                 "Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` once the redirect is verified."],
            effort="low", owner="engineering", method="probe",
        ))

    tls_failures = {url: info for url, info in variants.items() if info.get("tls_error")}
    if tls_failures:
        out.append(F.finding(
            "ACC-023", "TLS certificate validation failed",
            "critical", "discoverability", "access",
            evidence="; ".join(f"{url}: {str(info['tls_error'])[:120]}" for url, info in list(tls_failures.items())[:2]) + ".",
            mechanism="Crawlers and AI fetchers abandon a request whose certificate does not validate; there is no "
                      "interstitial to click through. Browsers show a full-page warning, which ends most visits. "
                      "The site is effectively offline for both audiences.",
            action_summary="Install a valid certificate covering every hostname the site answers on.",
            how=["Renew or reissue the certificate; confirm it covers both apex and www.",
                 "Serve the full chain including intermediates - a missing intermediate validates in some browsers "
                 "and fails in most automated clients.",
                 "Automate renewal so expiry cannot recur."],
            effort="low", owner="ops", method="probe",
            evidence_detail={"failures": {k: str(v.get("tls_error"))[:200] for k, v in tls_failures.items()}},
        ))


def check_status_health(cache, out, skipped):
    pages = cache.pages
    broken = [p for p in pages if p.status >= 400 or (p.error and not p.ok)]
    linked_broken = [p for p in broken if p.discovered_via in ("homepage-link", "sitemap")]
    if linked_broken:
        sampled = len(pages)
        severity = F.apply_blast_radius("medium", len(linked_broken), sampled)
        out.append(F.finding(
            "ACC-024", "Internal links and sitemap entries point at pages that fail to load",
            severity, "discoverability", "access",
            evidence=f"{len(linked_broken)} of {sampled} crawled URLs returned an error, e.g. "
                     + ", ".join(f"{p.url} ({p.status or p.error})" for p in linked_broken[:3]) + ".",
            mechanism="Every dead link is a discovery path that terminates, and a visitor who reaches one usually "
                      "leaves rather than navigating back. Dead entries in a sitemap additionally teach crawlers to "
                      "trust the sitemap less.",
            action_summary="Fix or remove the broken URLs from links and from the sitemap.",
            how=["Repair the links, or redirect the old URLs to their current equivalents with a 301.",
                 "Remove URLs that no longer exist from the sitemap.",
                 "Add a build-time link check so this does not regress."],
            effort="medium", owner="engineering", method="static",
            affected_urls=[p.url for p in linked_broken], affected_count=len(linked_broken), sampled_count=sampled,
        ))

    long_chains = [p for p in pages if len(p.redirect_chain) >= 3]
    if long_chains:
        out.append(F.finding(
            "ACC-025", "Some URLs redirect through long chains",
            "low", "discoverability", "access",
            evidence=f"{len(long_chains)} crawled URLs required 3 or more redirect hops, e.g. {long_chains[0].url} "
                     f"({len(long_chains[0].redirect_chain)} hops).",
            mechanism="Some fetchers follow only one or two hops before giving up, and every hop adds latency for the "
                      "visitor. Long chains usually accumulate from stacked rules - http to https, apex to www, old "
                      "path to new - each added separately.",
            action_summary="Collapse redirect chains to a single hop.",
            how=["Rewrite the rules so the original URL redirects straight to the final destination.",
                 "Order edge rules so scheme, host and path normalisation happen in one response."],
            effort="low", owner="engineering", method="static",
            affected_urls=[p.url for p in long_chains], affected_count=len(long_chains), sampled_count=len(pages),
        ))

    soft404 = cache.extras.get("probes", {}).get("not_found")
    if soft404 and soft404.get("status") == 200 and soft404.get("words", 0) > 30:
        out.append(F.finding(
            "ACC-026", "Missing pages return 200 instead of 404 (soft 404)",
            "medium", "discoverability", "access",
            evidence=f"A URL that cannot exist ({soft404['url']}) returned status 200 with "
                     f"{soft404['words']} words of content.",
            mechanism="When every URL returns success, a crawler cannot tell real pages from mistakes. Nonexistent "
                      "URLs enter the index as thin duplicates, budget is spent fetching them, and the signal that a "
                      "page has been removed never reaches the systems that need it.",
            action_summary="Return a real 404 status for URLs that do not exist.",
            how=["Serve HTTP 404 (or 410 for permanently removed pages) with the error page body.",
                 "In client-rendered apps, ensure the server - not just the router - returns the 404 status.",
                 "Keep the error page useful: search, top links, and a route back into the site."],
            effort="medium", owner="engineering", method="probe",
            evidence_detail=soft404,
        ))


def main():
    ap = argparse.ArgumentParser(description="Gate 1 - access checks")
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()

    cache = cache_mod.load(args.cache)
    out, skipped = [], []
    for check in (check_reachable, check_robots, check_bot_gating, check_sitemaps,
                  check_indexability, check_canonicals, check_origins, check_status_health):
        try:
            check(cache, out, skipped)
        except StopIteration:
            # The site was unreachable; every later check in this gate would be
            # measuring nothing. Recorded, not silently dropped.
            skipped.append(F.skip("ACC-*", "site was unreachable, so no further access check could be measured"))
            break
        except Exception as e:  # a detector bug must not lose the whole audit
            skipped.append(F.skip(check.__name__, f"check raised {type(e).__name__}: {e}"))
    F.emit(out, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
