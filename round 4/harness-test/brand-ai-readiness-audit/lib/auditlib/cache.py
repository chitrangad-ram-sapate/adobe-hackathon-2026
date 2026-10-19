"""The shared crawl cache: fetched once by the orchestrator, read by every detector.

This is the composition backbone of the marketplace. Because the cache is a
plain directory of files with a documented layout, each detector is a pure,
independently runnable function from cache to findings - no detector re-crawls
the site, no detector depends on another detector, and any one of them can be
run alone against a saved cache for debugging or for a regression test.

Layout:

    <cache>/manifest.json          run config, profile, and the page index
    <cache>/robots.txt             verbatim body, if one was served
    <cache>/extras.json            robots status, sitemap data, access probes
    <cache>/pages/<key>.html       raw HTTP response body, as fetched
    <cache>/pages/<key>.rendered   post-JavaScript DOM, only if a renderer ran
    <cache>/pages/<key>.json       status, headers, timing, classification
"""

from __future__ import annotations

import hashlib
import json
import os

from . import htmlx, robots as robots_mod


def key_for(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8", errors="ignore")).hexdigest()[:16]


class Page:
    """One fetched URL. HTML and the parsed document are loaded lazily."""

    def __init__(self, cache_dir: str, record: dict):
        self._dir = cache_dir
        self.record = record
        self.url = record.get("url", "")
        self.final_url = record.get("final_url", self.url)
        self.status = record.get("status", 0)
        self.headers = record.get("headers", {})
        self.content_type = record.get("content_type", "")
        self.elapsed = record.get("elapsed", 0.0)
        self.bytes = record.get("bytes", 0)
        self.page_type = record.get("page_type", "other")
        self.is_home = record.get("is_home", False)
        self.error = record.get("error")
        self.tls_error = record.get("tls_error")
        self.redirect_chain = record.get("redirect_chain", [])
        self.discovered_via = record.get("discovered_via", "")
        self.depth = record.get("depth", 0)
        self.rendered = record.get("rendered", False)
        self._html = None
        self._rendered_html = None
        self._doc = None
        self._rendered_doc = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and not self.error

    @property
    def is_html(self) -> bool:
        return self.ok and self.content_type in ("text/html", "application/xhtml+xml", "")

    def _path(self, suffix: str) -> str:
        return os.path.join(self._dir, "pages", key_for(self.url) + suffix)

    @property
    def html(self) -> str:
        if self._html is None:
            path = self._path(".html")
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    self._html = fh.read()
            except OSError:
                self._html = ""
        return self._html

    @property
    def raw_bytes(self) -> bytes:
        """Undecoded response body. Needed for binary formats such as PDF,
        where decoding as text would destroy the structure being inspected."""
        try:
            with open(self._path(".html"), "rb") as fh:
                return fh.read()
        except OSError:
            return b""

    @property
    def rendered_html(self) -> str:
        """Post-JavaScript DOM, or "" when no renderer was available."""
        if self._rendered_html is None:
            path = self._path(".rendered")
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    self._rendered_html = fh.read()
            except OSError:
                self._rendered_html = ""
        return self._rendered_html

    @property
    def doc(self) -> htmlx.Doc:
        if self._doc is None:
            self._doc = htmlx.parse(self.html, self.url)
        return self._doc

    @property
    def rendered_doc(self):
        if not self.rendered_html:
            return None
        if self._rendered_doc is None:
            self._rendered_doc = htmlx.parse(self.rendered_html, self.url)
        return self._rendered_doc

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    def __repr__(self):
        return f"<Page {self.status} {self.page_type} {self.url}>"


class Cache:
    def __init__(self, cache_dir: str):
        self.dir = cache_dir
        with open(os.path.join(cache_dir, "manifest.json"), encoding="utf-8") as fh:
            self.manifest = json.load(fh)
        self.site = self.manifest.get("site", "")
        self.site_url = self.manifest.get("site_url", "")
        self.config = self.manifest.get("config", {})
        self.profile = self.manifest.get("profile", {})
        self.capabilities = self.manifest.get("capabilities", {})
        self.started_at = self.manifest.get("started_at", "")
        self.pages = [Page(cache_dir, r) for r in self.manifest.get("pages", [])]
        self._extras = None
        self._robots = None

    # --- accessors used by detectors ------------------------------------

    @property
    def extras(self) -> dict:
        if self._extras is None:
            try:
                with open(os.path.join(self.dir, "extras.json"), encoding="utf-8") as fh:
                    self._extras = json.load(fh)
            except OSError:
                self._extras = {}
        return self._extras

    @property
    def robots(self) -> robots_mod.Robots:
        if self._robots is None:
            info = self.extras.get("robots", {})
            text = ""
            try:
                with open(os.path.join(self.dir, "robots.txt"), encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                pass
            self._robots = robots_mod.Robots(
                text, info.get("status", 0), info.get("url", "")
            )
        return self._robots

    @property
    def home(self):
        for page in self.pages:
            if page.is_home and page.is_html:
                return page
        for page in self.pages:
            if page.is_html:
                return page
        return None

    def html_pages(self) -> list:
        """Fetched, 2xx, HTML pages - the population most checks sample from."""
        return [p for p in self.pages if p.is_html and p.html]

    def pages_of_type(self, *types) -> list:
        wanted = set(types)
        return [p for p in self.html_pages() if p.page_type in wanted]

    def page_types(self) -> dict:
        counts = {}
        for page in self.html_pages():
            counts[page.page_type] = counts.get(page.page_type, 0) + 1
        return counts

    def documents(self) -> list:
        """Non-HTML documents encountered, chiefly PDFs."""
        return [p for p in self.pages if p.content_type == "application/pdf"]

    def has_capability(self, name: str) -> bool:
        return bool(self.capabilities.get(name))


class Writer:
    """Builds a cache directory. Used only by the orchestrator's crawler."""

    def __init__(self, cache_dir: str, site: str, site_url: str, config: dict):
        self.dir = cache_dir
        os.makedirs(os.path.join(cache_dir, "pages"), exist_ok=True)
        self.manifest = {
            "site": site,
            "site_url": site_url,
            "config": config,
            "capabilities": {},
            "profile": {},
            "pages": [],
        }

    def add_page(self, response, page_type="other", is_home=False, discovered_via="", depth=0):
        record = {
            "url": response.url,
            "final_url": response.final_url,
            "status": response.status,
            "headers": response.headers,
            "content_type": response.content_type,
            "elapsed": round(response.elapsed, 3),
            "bytes": response.bytes_len,
            "page_type": page_type,
            "is_home": is_home,
            "error": response.error,
            "tls_error": response.tls_error,
            "truncated": response.truncated,
            "redirect_chain": response.redirect_chain,
            "discovered_via": discovered_via,
            "depth": depth,
            "rendered": False,
        }
        if response.body:
            path = os.path.join(self.dir, "pages", key_for(response.url) + ".html")
            with open(path, "wb") as fh:
                fh.write(response.body)
        self.manifest["pages"].append(record)
        return record

    def add_rendered(self, url: str, html: str):
        path = os.path.join(self.dir, "pages", key_for(url) + ".rendered")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        for record in self.manifest["pages"]:
            if record["url"] == url:
                record["rendered"] = True

    def set_robots_body(self, text: str):
        with open(os.path.join(self.dir, "robots.txt"), "w", encoding="utf-8") as fh:
            fh.write(text or "")

    def set_extras(self, extras: dict):
        with open(os.path.join(self.dir, "extras.json"), "w", encoding="utf-8") as fh:
            json.dump(extras, fh, indent=2, ensure_ascii=False)

    def set_profile(self, profile: dict):
        self.manifest["profile"] = profile

    def set_capabilities(self, capabilities: dict):
        self.manifest["capabilities"] = capabilities

    def save(self, **extra):
        self.manifest.update(extra)
        with open(os.path.join(self.dir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(self.manifest, fh, indent=2, ensure_ascii=False)


def load(cache_dir: str) -> Cache:
    return Cache(cache_dir)
