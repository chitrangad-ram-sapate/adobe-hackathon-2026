"""
auditlib - shared, standard-library-only primitives for the
brand-ai-readiness-audit marketplace.

Every skill in the marketplace reads the *same* crawl cache through this
package. That is what makes the decomposition cheap: the site is fetched once
by the orchestrator, and each detector is a pure function from the cache to a
list of findings. No detector performs its own crawl.

Hard constraints, deliberately:

* Standard library only. No pip install stands between a grader and a working
  audit. Optional accelerators (a real browser engine for render measurement)
  are detected at run time and degrade honestly when absent.
* Read-only. GET and HEAD to the audited origin. Never POST, never a form,
  never an authenticated area, never a write of any kind to the target.
* Bounded. Every network call has a timeout and a response size cap; every
  crawl has a page budget and a wall-clock budget.
"""

import sys

__version__ = "1.0.0"

MARKETPLACE_VERSION = "1.0.0"

# Identifies this auditor honestly to the sites it fetches, and gives operators
# something to search for in their logs.
USER_AGENT = (
    "BrandAIReadinessAudit/1.0 (+read-only site audit; respects robots.txt)"
)

# Used only by the differential access probe in site-access-audit, to detect
# CDN/WAF rules that serve real content to browsers and a challenge page to
# everything else. Never used for general crawling.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def force_utf8_stdout():
    """Make stdout UTF-8 regardless of the platform's console encoding.

    Detector output is JSON containing whatever text the audited site
    published - arrows, curly quotes, non-Latin scripts. On Windows the default
    console encoding is a legacy code page, so writing that JSON raises
    UnicodeEncodeError and the detector fails for a reason that has nothing to
    do with the site. Every script that prints JSON calls this first, and every
    caller reads the pipe as UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
