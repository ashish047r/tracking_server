import re
import logging

import httpx
import os

from urllib.parse import urlparse

BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY_URL")

logger = logging.getLogger(__name__)

# Patterns to detect JS/meta redirects in response body
_JS_REDIRECT_PATTERNS = [
    re.compile(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'window\.location\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'document\.location\.href\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'document\.location\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']refresh["\'][^>]+content\s*=\s*["\'][^"\']*url\s*=\s*([^"\'"\s>]+)', re.IGNORECASE),
    re.compile(r'<meta[^>]+content\s*=\s*["\'][^"\']*url\s*=\s*([^"\'"\s>]+)[^>]+http-equiv\s*=\s*["\']refresh["\']', re.IGNORECASE),
]


def _extract_js_redirect(body: str) -> str | None:
    for pattern in _JS_REDIRECT_PATTERNS:
        match = pattern.search(body)
        if match:
            url = match.group(1).strip()
            if url.startswith(("http://", "https://")):
                return url
    return None


async def fetch_final_url(tracking_url: str, max_js_hops: int = 5) -> dict:
    client_kwargs = dict(
        follow_redirects=True,
        max_redirects=20,
        timeout=30.0,
        verify=False,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    # Use proxy only for the initial tracking URL fetch
    async with httpx.AsyncClient(proxy=BRIGHTDATA_PROXY, **client_kwargs) as proxy_client:
        response = await proxy_client.get(tracking_url)
        hops = [{"url": str(r.url), "status": r.status_code} for r in response.history]

    logger.info(
        "After proxy fetch: url=%s | status=%d | hops=%d | body_len=%d",
        response.url, response.status_code, len(hops), len(response.text),
    )

    # Follow any remaining redirects WITHOUT proxy
    # (affiliate networks like Impact/8odi.net may behave differently through proxies)
    async with httpx.AsyncClient(**client_kwargs) as direct_client:
        for _ in range(max_js_hops):
            body = response.text

            # Check for JS/meta redirects in the body
            js_url = _extract_js_redirect(body)
            if js_url:
                logger.info("Following JS redirect: %s -> %s", response.url, js_url)
                hops.append({"url": str(response.url), "status": response.status_code})
                response = await direct_client.get(js_url)
                hops.extend(
                    {"url": str(r.url), "status": r.status_code}
                    for r in response.history
                )
                continue

            # If we're stuck on an intermediate domain (not the final landing page),
            # try fetching the current URL directly without proxy
            current_host = urlparse(str(response.url)).hostname or ""
            if current_host.endswith(("8odi.net", "ojrq.net", "evyy.net", "pntra.net")):
                logger.info(
                    "Intermediate domain detected (%s), re-fetching without proxy: %s",
                    current_host, response.url,
                )
                hops.append({"url": str(response.url), "status": response.status_code})
                response = await direct_client.get(str(response.url))
                hops.extend(
                    {"url": str(r.url), "status": r.status_code}
                    for r in response.history
                )
                continue

            break  # We're at the final URL

    logger.info(
        "Final result: url=%s | status=%d | total_hops=%d",
        response.url, response.status_code, len(hops),
    )

    return {
        "final_url": str(response.url),
        "status_code": response.status_code,
        "hops": hops,
    }



# -------------------------------------------------------
# MULTI-PARAM EXTRACTION
# -------------------------------------------------------

def extract_params(final_url: str, param_keys: list[str]) -> str:
    """
    Extracts selected query params from final resolved URL.
    Preserves original URL encoding by working with the raw query string.
    """
    parsed = urlparse(final_url)
    raw_query = parsed.query
    if not raw_query:
        return ""

    wanted = set(param_keys)
    parts = []
    for pair in raw_query.split("&"):
        key = pair.split("=", 1)[0]
        if key in wanted:
            parts.append(pair)

    return "&".join(parts)
























