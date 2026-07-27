"""Sprint 6 Task 1 — HTTP reachability classifier + robots.txt gate.

Classifies a target URL into one of:
    ok             — reachable, send away
    site_not_found — HTTP 404 (Stage 0 early skip)
    waf_403        — HTTP 403 likely from WAF (noAI candidate)
    transient_5xx  — HTTP 5xx, may recover (noAI per Pareto)
    network_error  — DNS / TCP / SSL failure (noAI per Pareto)
    robots_disallow — robots.txt explicitly disallows our UA on the path

Used by Stage 1.5 (LocalGeneralFormProvider) as the very first gate before
launching Playwright. Cheap HEAD request avoids burning a browser context
on dead URLs.

NOTE: Sync with src/lib/browser/engine.ts L130-180 (HTTP HEAD precheck)
and src/lib/browser/reachability/*.ts when those are introduced.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional
from urllib import robotparser
from urllib.parse import urlparse

import httpx

# Reuse the same default UA / headers as the CF7 HTTP POST path so the bot
# fingerprint matches across stages.
try:
    from skill.core._http_form_sender import _DEFAULT_HEADERS, _DEFAULT_USER_AGENT
except ImportError:
    from _http_form_sender import _DEFAULT_HEADERS, _DEFAULT_USER_AGENT  # type: ignore

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
_REACH_HTTP_TIMEOUT_SEC = 8.0


# -----------------------------------------------------------------------------
# Result
# -----------------------------------------------------------------------------
@dataclass
class ReachabilityResult:
    """Result of a reachability probe.

    status values:
        ok | site_not_found | waf_403 | transient_5xx | network_error | robots_disallow
    """

    status: str
    http_code: Optional[int]
    detail: str

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"


# -----------------------------------------------------------------------------
# robots.txt check
# -----------------------------------------------------------------------------
def _check_robots(url: str, user_agent: str = _DEFAULT_USER_AGENT) -> ReachabilityResult:
    """Read robots.txt for the URL's origin and check Disallow.

    Fail Safe: any error in fetching / parsing robots.txt -> treated as
    'allowed' (return ok). Over-eager skipping costs revenue; over-eager
    sending costs IP reputation, but for B2B contact forms the latter is
    bounded by other checks (UA + delay).
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ReachabilityResult(status="ok", http_code=None, detail="invalid-url-fallback-ok")
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            return ReachabilityResult(
                status="robots_disallow",
                http_code=None,
                detail=f"robots.txt disallows {user_agent} on {url}",
            )
        return ReachabilityResult(status="ok", http_code=None, detail="robots-allow")
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        return ReachabilityResult(
            status="ok",
            http_code=None,
            detail=f"robots-check-failed-treat-as-allowed: {type(e).__name__}",
        )


# -----------------------------------------------------------------------------
# HTTP HEAD/GET probe
# -----------------------------------------------------------------------------
async def _probe_http(
    url: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
) -> ReachabilityResult:
    """Send a HEAD request first, fall back to GET if HEAD is rejected.

    Many CDN/WAF stacks block HEAD with 405; treat that as ok and let the
    downstream Playwright GET reveal the real status.
    """
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=_REACH_HTTP_TIMEOUT_SEC,
            headers=_DEFAULT_HEADERS,
            follow_redirects=True,
        )
    try:
        try:
            resp = await client.head(url)
            if resp.status_code == 405:
                # Server rejected HEAD; try GET to get the real code.
                resp = await client.get(url)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError) as e:
            return ReachabilityResult(
                status="network_error",
                http_code=None,
                detail=f"{type(e).__name__}: {e}"[:200],
            )

        code = resp.status_code
        if code == 404:
            return ReachabilityResult(
                status="site_not_found",
                http_code=code,
                detail="HTTP 404",
            )
        if code == 403:
            return ReachabilityResult(
                status="waf_403",
                http_code=code,
                detail="HTTP 403 (likely WAF / IP block)",
            )
        if 500 <= code < 600:
            return ReachabilityResult(
                status="transient_5xx",
                http_code=code,
                detail=f"HTTP {code}",
            )
        # All other codes (2xx / 3xx / unexpected 4xx) -> ok and let the
        # downstream form detector do its job.
        return ReachabilityResult(
            status="ok",
            http_code=code,
            detail=f"HTTP {code}",
        )
    finally:
        if own_client:
            await client.aclose()


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
async def classify_reachability(
    url: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
    skip_robots: bool = False,
) -> ReachabilityResult:
    """Public Stage 0 gate.

    Args:
        url: target URL to classify.
        client: optional shared httpx.AsyncClient.
        skip_robots: skip the robots.txt check (used by Sprint 5 tests that
            don't want to hit external robots.txt).

    Returns:
        ReachabilityResult.
    """
    if not skip_robots:
        # robots.txt probe is sync (urllib) — run in default executor so we
        # don't block the asyncio loop. For Sprint 6 KISS, just inline since
        # robots.txt fetches are usually <100 ms.
        robots = await asyncio.get_event_loop().run_in_executor(
            None, _check_robots, url
        )
        if robots.status == "robots_disallow":
            return robots
    return await _probe_http(url, client=client)


# -----------------------------------------------------------------------------
# Module self-check
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    async def _demo() -> None:
        result = await classify_reachability(
            "https://example.com/", skip_robots=True
        )
        print(f"[_reachability] {result}")

    asyncio.run(_demo())
