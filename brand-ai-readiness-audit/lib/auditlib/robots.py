"""robots.txt parsing, with first-class support for AI-assistant crawlers.

The standard library ships urllib.robotparser, but it is not usable here: it
collapses the file into an allow/deny oracle and throws away exactly what this
audit needs to report - which named agent is blocked, by which line, and
whether the block hits retrieval (the fetch that builds an answer, and the
citation with it) or only training-corpus collection.

Path matching follows the de-facto Google/RFC 9309 semantics: longest matching
rule wins, Allow wins ties, `*` is a wildcard and `$` anchors the end.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

# Which crawler does what. The distinction is the whole point of the check:
# blocking a training crawler is a defensible business decision, while blocking
# a retrieval/citation crawler removes the brand from answers that would have
# linked to it - and is almost always accidental.
#
# purpose: "retrieval"  - fetches live to build/ground an answer, usually cites
#          "training"   - collects a corpus for model training
#          "both"       - does both under one token
AI_CRAWLERS = {
    "gptbot":            {"vendor": "OpenAI",     "purpose": "training"},
    "oai-searchbot":     {"vendor": "OpenAI",     "purpose": "retrieval"},
    "chatgpt-user":      {"vendor": "OpenAI",     "purpose": "retrieval"},
    "claudebot":         {"vendor": "Anthropic",  "purpose": "training"},
    "claude-web":        {"vendor": "Anthropic",  "purpose": "retrieval"},
    "claude-user":       {"vendor": "Anthropic",  "purpose": "retrieval"},
    "claude-searchbot":  {"vendor": "Anthropic",  "purpose": "retrieval"},
    "anthropic-ai":      {"vendor": "Anthropic",  "purpose": "training"},
    "perplexitybot":     {"vendor": "Perplexity", "purpose": "retrieval"},
    "perplexity-user":   {"vendor": "Perplexity", "purpose": "retrieval"},
    "google-extended":   {"vendor": "Google",     "purpose": "training"},
    "googleother":       {"vendor": "Google",     "purpose": "both"},
    "applebot":          {"vendor": "Apple",      "purpose": "both"},
    "applebot-extended": {"vendor": "Apple",      "purpose": "training"},
    "ccbot":             {"vendor": "Common Crawl", "purpose": "training"},
    "bytespider":        {"vendor": "ByteDance",  "purpose": "training"},
    "meta-externalagent": {"vendor": "Meta",      "purpose": "training"},
    "meta-externalfetcher": {"vendor": "Meta",    "purpose": "retrieval"},
    "amazonbot":         {"vendor": "Amazon",     "purpose": "both"},
    "youbot":            {"vendor": "You.com",    "purpose": "retrieval"},
    "cohere-ai":         {"vendor": "Cohere",     "purpose": "training"},
    "diffbot":           {"vendor": "Diffbot",    "purpose": "training"},
    "timpibot":          {"vendor": "Timpi",      "purpose": "training"},
    "omgili":            {"vendor": "Webz.io",    "purpose": "training"},
}

# Classic search crawlers. Blocking these is a separate, also-severe problem:
# several assistants ground their answers on a conventional search index.
SEARCH_CRAWLERS = {
    "googlebot": "Google",
    "bingbot": "Microsoft Bing",
    "duckduckbot": "DuckDuckGo",
    "slurp": "Yahoo",
    "yandexbot": "Yandex",
    "baiduspider": "Baidu",
}


class Group:
    def __init__(self, agents):
        self.agents = agents           # lower-cased user-agent tokens
        self.rules = []                # [(is_allow, path, raw_line, line_no)]
        self.crawl_delay = None

    def match(self, path: str):
        """Longest-match rule for a path, or None if no rule applies."""
        best = None
        for is_allow, rule_path, raw, line_no in self.rules:
            if _path_matches(rule_path, path):
                weight = len(rule_path)
                if best is None or weight > best[0] or (weight == best[0] and is_allow):
                    best = (weight, is_allow, rule_path, raw, line_no)
        return best

    def blocks_everything(self) -> bool:
        m = self.match("/")
        return bool(m and not m[1])


def _path_matches(rule: str, path: str) -> bool:
    if rule == "":
        return False
    if rule == "/":
        return True
    pattern = re.escape(rule).replace(r"\*", ".*")
    if pattern.endswith(r"\$"):
        pattern = pattern[:-2] + "$"
    try:
        return re.match(pattern, path) is not None
    except re.error:
        return path.startswith(rule.split("*")[0])


class Robots:
    def __init__(self, text: str = "", status: int = 0, url: str = ""):
        self.url = url
        self.status = status
        self.text = text or ""
        self.groups = []
        self.sitemaps = []
        self.parse_notes = []
        self.exists = 200 <= status < 300
        # A robots.txt that 404s is not a defect: the correct default is
        # "everything is allowed". Only a *fetch failure* (5xx, timeout) is
        # ambiguous, because several crawlers treat that as disallow-all.
        self.fetch_failed = status == 0 or status >= 500
        if self.exists:
            self._parse()

    def _parse(self):
        current_agents, current = [], None
        expecting_agent = True
        for line_no, raw in enumerate(self.text.splitlines(), 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                self.parse_notes.append(f"line {line_no}: no directive separator: {raw.strip()[:80]}")
                continue
            field, _, value = line.partition(":")
            field = field.strip().lower()
            value = value.strip()

            if field == "user-agent":
                if not expecting_agent:
                    current_agents, current = [], None
                    expecting_agent = True
                current_agents.append(value.lower())
                continue

            if field in ("allow", "disallow"):
                if current is None:
                    if not current_agents:
                        # Rules before any User-agent line are orphaned and
                        # ignored by real crawlers - a silent, common mistake.
                        self.parse_notes.append(
                            f"line {line_no}: {field} directive appears before any User-agent line and is ignored by crawlers"
                        )
                        continue
                    current = Group(list(current_agents))
                    self.groups.append(current)
                expecting_agent = False
                path = value
                if path or field == "disallow":
                    # "Disallow:" with an empty value means allow everything.
                    if field == "disallow" and path == "":
                        continue
                    try:
                        path = unquote(path)
                    except Exception:
                        pass
                    if not path.startswith("/") and not path.startswith("*"):
                        path = "/" + path
                    current.rules.append((field == "allow", path, raw.strip(), line_no))
                continue

            if field == "sitemap":
                self.sitemaps.append(value)
                continue

            if field == "crawl-delay":
                if current is not None:
                    try:
                        current.crawl_delay = float(value)
                    except ValueError:
                        pass
                continue

    def group_for(self, agent: str):
        """Most specific group matching an agent token, per RFC 9309.

        Specificity is by longest matching agent string; the `*` group is the
        fallback and is used only when no named group matches.
        """
        agent = agent.lower()
        best, best_len = None, -1
        wildcard = None
        for group in self.groups:
            for token in group.agents:
                if token == "*":
                    if wildcard is None:
                        wildcard = group
                    continue
                if token and (token in agent or agent in token):
                    if len(token) > best_len:
                        best, best_len = group, len(token)
        return best or wildcard

    def allows(self, agent: str, url_or_path: str) -> bool:
        if not self.exists:
            # Absent robots.txt means unrestricted. Do not invent a block.
            return True
        path = url_or_path
        if path.startswith("http"):
            parts = urlsplit(path)
            path = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
        if not path.startswith("/"):
            path = "/" + path
        group = self.group_for(agent)
        if group is None:
            return True
        m = group.match(path)
        return True if m is None else bool(m[1])

    def explain(self, agent: str, path: str = "/"):
        """Why an agent is or is not blocked - the evidence for a finding."""
        group = self.group_for(agent)
        if group is None:
            return {"agent": agent, "blocked": False, "reason": "no matching User-agent group"}
        m = group.match(path if path.startswith("/") else "/" + path)
        if m is None:
            return {"agent": agent, "blocked": False, "reason": f"matched group {group.agents}, no rule for {path}"}
        _, is_allow, rule_path, raw, line_no = m
        return {
            "agent": agent,
            "blocked": not is_allow,
            "group": group.agents,
            "rule": raw,
            "line": line_no,
            "rule_path": rule_path,
        }

    def ai_crawler_status(self, path: str = "/") -> dict:
        """Blocked/allowed status for every known AI and search crawler."""
        out = {"ai": {}, "search": {}}
        for agent, info in AI_CRAWLERS.items():
            ex = self.explain(agent, path)
            ex.update(info)
            out["ai"][agent] = ex
        for agent, vendor in SEARCH_CRAWLERS.items():
            ex = self.explain(agent, path)
            ex["vendor"] = vendor
            out["search"][agent] = ex
        return out


def parse(text: str, status: int = 200, url: str = "") -> Robots:
    return Robots(text, status, url)
