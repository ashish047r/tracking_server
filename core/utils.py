from urllib.parse import urlparse


def extract_full_query(final_url: str) -> str:
    """
    Returns everything after ? without decoding
    """
    parsed = urlparse(final_url)
    return parsed.query or ""
