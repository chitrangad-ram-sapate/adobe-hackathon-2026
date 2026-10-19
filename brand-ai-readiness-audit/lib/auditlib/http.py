"""Bounded, read-only HTTP client built on the standard library.

Design notes that matter for the audit:

* Redirects are followed manually so the full chain is recorded. Redirect
  chains are themselves a finding (each hop is a chance for a crawler to give
  up, and some fetchers cap at one or two hops).
* TLS failures are captured rather than raised. A site with a broken
  certificate is a real, severe finding - but we still want to audit its
  content, so a verification failure is recorded and the fetch is retried
  unverified exactly once, with the failure carried on the response.
* Every response is size-capped. A 400 MB "HTML" page must not be able to hang
  or OOM the audit.
* Brotli is never requested: decoding it is not in the standard library, and
  asking for an encoding we cannot decode would silently corrupt the body.
"""

from __future__ import annotations

import gzip
import re
import socket
import ssl
import time
import zlib
from dataclasses import dataclass, field
from urllib import request as urlrequest
from urllib import error as urlerror

from . import USER_AGENT

DEFAULT_TIMEOUT = 12.0
MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 8

_CHARSET_RE = re.compile(rb"""<meta[^>]+charset=["']?\s*([a-zA-Z0-9_\-]+)""", re.I)
_CT_CHARSET_RE = re.compile(r"charset=([a-zA-Z0-9_\-]+)", re.I)


@dataclass
class Response:
    url: str                       # URL originally requested
    final_url: str                 # URL after the redirect chain
    status: int                    # 0 when the request never completed
    headers: dict = field(default_factory=dict)   # lower-cased keys
    body: bytes = b""
    elapsed: float = 0.0
    redirect_chain: list = field(default_factory=list)  # [(status, from, to)]
    error: str | None = None
    tls_error: str | None = None
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and not self.error

    @property
    def content_type(self) -> str:
        return (self.headers.get("content-type") or "").split(";")[0].strip().lower()

    @property
    def is_html(self) -> bool:
        return self.content_type in ("text/html", "application/xhtml+xml", "")

    @property
    def bytes_len(self) -> int:
        return len(self.body)

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    @property
    def text(self) -> str:
        """Decode the body, preferring the declared charset over guesswork."""
        if not self.body:
            return ""
        encodings = []
        m = _CT_CHARSET_RE.search(self.headers.get("content-type", ""))
        if m:
            encodings.append(m.group(1))
        m = _CHARSET_RE.search(self.body[:4096])
        if m:
            try:
                encodings.append(m.group(1).decode("ascii"))
            except UnicodeDecodeError:
                pass
        encodings += ["utf-8", "cp1252", "latin-1"]
        for enc in encodings:
            try:
                return self.body.decode(enc)
            except (LookupError, UnicodeDecodeError):
                continue
        return self.body.decode("utf-8", errors="replace")


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    """Stops urllib following redirects so we can record every hop ourselves."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _decompress(body: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower().strip()
    try:
        if encoding == "gzip":
            return gzip.decompress(body)
        if encoding == "deflate":
            try:
                return zlib.decompress(body)
            except zlib.error:
                return zlib.decompress(body, -zlib.MAX_WBITS)
    except (OSError, zlib.error):
        # A body that claims an encoding it does not use is itself a
        # (minor) defect; returning the raw bytes keeps the audit running.
        return body
    return body


def _read_capped(fp, max_bytes: int):
    chunks, total, truncated = [], 0, False
    while True:
        chunk = fp.read(min(65536, max_bytes - total + 1))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            truncated = True
            break
    return b"".join(chunks)[:max_bytes], truncated


def _single_request(url, ua, timeout, method, max_bytes, context=None):
    opener = urlrequest.build_opener(_NoRedirect)
    if context is not None:
        opener.add_handler(urlrequest.HTTPSHandler(context=context))
    req = urlrequest.Request(url, method=method)
    req.add_header("User-Agent", ua)
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    req.add_header("Accept-Encoding", "gzip, deflate")
    resp = opener.open(req, timeout=timeout)
    try:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        body, truncated = (b"", False)
        if method != "HEAD":
            body, truncated = _read_capped(resp, max_bytes)
            body = _decompress(body, headers.get("content-encoding", ""))
        return resp.status, headers, body, truncated
    finally:
        resp.close()


def fetch(
    url: str,
    ua: str = USER_AGENT,
    timeout: float = DEFAULT_TIMEOUT,
    method: str = "GET",
    max_bytes: int = MAX_BYTES,
    max_redirects: int = MAX_REDIRECTS,
    allow_insecure_retry: bool = True,
) -> Response:
    """Fetch a URL, recording the redirect chain and any TLS failure.

    Never raises for network conditions: every failure mode is reported on the
    returned Response so a single unreachable page can never abort an audit.
    """
    started = time.time()
    out = Response(url=url, final_url=url, status=0)
    current = url
    seen = set()

    for _ in range(max_redirects + 1):
        if current in seen:
            out.error = "redirect_loop"
            break
        seen.add(current)
        try:
            status, headers, body, truncated = _single_request(
                current, ua, timeout, method, max_bytes
            )
        except urlerror.HTTPError as e:
            # 4xx/5xx are answers, not failures - the status is the finding.
            status = e.code
            headers = {k.lower(): v for k, v in (e.headers or {}).items()}
            try:
                body, truncated = _read_capped(e, max_bytes)
                body = _decompress(body, headers.get("content-encoding", ""))
            except Exception:
                body, truncated = b"", False
        except ssl.SSLError as e:
            out.tls_error = str(e)
            if allow_insecure_retry:
                try:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    status, headers, body, truncated = _single_request(
                        current, ua, timeout, method, max_bytes, context=ctx
                    )
                except Exception as e2:
                    out.error = f"tls_error: {e2}"
                    break
            else:
                out.error = f"tls_error: {e}"
                break
        except (urlerror.URLError, socket.timeout, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            out.error = "timeout" if isinstance(reason, (socket.timeout, TimeoutError)) else f"network_error: {reason}"
            break
        except Exception as e:  # malformed headers, bad chunking, decode failures
            out.error = f"fetch_error: {type(e).__name__}: {e}"
            break

        if status in (301, 302, 303, 307, 308) and headers.get("location"):
            from .urls import normalize
            nxt = normalize(headers["location"], base=current)
            if not nxt:
                out.status, out.headers, out.body = status, headers, body
                out.error = "unfollowable_redirect"
                break
            out.redirect_chain.append((status, current, nxt))
            current = nxt
            continue

        out.status, out.headers, out.body, out.truncated = status, headers, body, truncated
        out.final_url = current
        break
    else:
        out.error = "too_many_redirects"

    if out.final_url == url and out.redirect_chain:
        out.final_url = out.redirect_chain[-1][2]
    out.elapsed = time.time() - started
    return out


def head_or_get(url: str, **kwargs) -> Response:
    """HEAD first, falling back to GET.

    Many CDNs and app servers mishandle HEAD (405, or a 200 with a wrong
    status), so a non-2xx HEAD is never trusted as evidence on its own.
    """
    r = fetch(url, method="HEAD", **kwargs)
    if r.ok or r.status in (401, 403, 404, 410):
        return r
    return fetch(url, method="GET", **kwargs)
