
import httpx
import os
import builtins

from urllib.parse import urljoin, urlparse, parse_qs

MAX_HOPS = 10
BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY_URL")


async def fetch_final_url(tracking_url: str) -> dict:
    visited = builtins.set()
    current_url = tracking_url
    hops = []

    async with httpx.AsyncClient(
    follow_redirects=False,
    timeout=15.0,
    proxy=BRIGHTDATA_PROXY,
    verify=False,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    },
) as client:


        for _ in range(MAX_HOPS):
            if current_url in visited:
                raise Exception("Redirect loop detected")

            visited.add(current_url)

            response = await client.get(current_url)

            hops.append({
                "url": current_url,
                "status": response.status_code,
                "location": response.headers.get("location"),
            })

            if 300 <= response.status_code < 400 and "location" in response.headers:
                current_url = urljoin(current_url, response.headers["location"])
                continue

            ip_check = await client.get("https://geo.brdtest.com/mygeo.json")
            print("PROXY IP DEBUG:", ip_check.json())

            return {
                "final_url": str(response.url),
                "status_code": response.status_code,
                "hops": hops
            }

        raise Exception("Too many redirects")



# -------------------------------------------------------
# MULTI-PARAM EXTRACTION
# -------------------------------------------------------

def extract_params(final_url: str, param_keys: list[str]) -> dict:
    """
    Extracts selected query params from final resolved URL.
    """
    parsed = urlparse(final_url)
    query = parse_qs(parsed.query)

    extracted = {}

    for key in param_keys:
        values = query.get(key)
        if values and values[0]:
            extracted[key] = values[0]

    return extracted
























