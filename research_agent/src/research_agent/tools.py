from smolagents import tool
from ddgs import DDGS
import httpx
import trafilatura
from urllib.parse import urlparse


def _domain(url: str) -> str:
    """Return the bare domain for a URL, e.g. 'en.wikipedia.org'."""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


@tool
def get_search_results_as_string(query: str, num_results: int = 5) -> str:
    """
    Search the web and return a formatted list of results (title, URL, domain,
    snippet). Use this to discover relevant pages; then use fetch_page to read
    the full content of the promising ones.

    Args:
        query: The search query.
        num_results: How many results to return. Default 5, maximum 10.
    """
    # Clamp so the LLM can't blow up the context window.
    num_results = max(1, min(int(num_results), 10))

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
    except Exception as e:
        return f"ERROR: Search failed for '{query}': {type(e).__name__}: {e}"

    if not results:
        return f"ERROR: No results found for query '{query}'."

    lines = [f"Search results for: {query}", ""]
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "").strip() or "(no title)"
        url = (r.get("href") or "").strip()
        snippet = (r.get("body") or "").strip()
        dom = _domain(url)

        lines.append(f"[{i}] {title}")
        lines.append(f"    URL: {url}")
        lines.append(f"    Domain: {dom}")
        if snippet:
            lines.append(f"    Snippet: {snippet}")
        lines.append("")  # blank line between results

    return "\n".join(lines).strip()


@tool
def fetch_page(url: str, max_chars: int = 8000) -> str:
    """
    Download a web page and return its main readable text, stripped of HTML,
    navigation, ads, and scripts.

    Use this after web_search to read the full content of a promising result.
    Prefer authoritative sources (Wikipedia, .gov, .edu, major news, docs).

    Args:
        url: The full URL to fetch (must start with http:// or https://).
        max_chars: Maximum number of characters to return. Default 8000.
            Text beyond this is truncated to protect the context window.
    """
    # 1. Basic sanity check — the LLM sometimes passes bare domains.
    if not url.startswith(("http://", "https://")):
        return f"ERROR: '{url}' is not a valid URL. It must start with http:// or https://"

    # 2. Download the page.
    try:
        headers = {
            # Many sites block the default httpx user-agent. Pretend to be a browser.
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        }
        response = httpx.get(
            url,
            headers=headers,
            timeout=15.0,          # don't hang forever
            follow_redirects=True, # many URLs redirect (http->https, /old->/new)
        )
        response.raise_for_status()  # raise on 4xx/5xx
    except httpx.TimeoutException:
        return f"ERROR: Timed out while fetching {url}"
    except httpx.HTTPStatusError as e:
        return f"ERROR: HTTP {e.response.status_code} while fetching {url}"
    except httpx.RequestError as e:
        return f"ERROR: Network error while fetching {url}: {e}"

    html = response.text

    # 3. Extract the main article text. trafilatura returns None if it can't
    #    find anything article-like (e.g. a login page or a 404 page).
    extracted = trafilatura.extract(
        html,
        include_comments=False,   # drop user comments
        include_tables=True,      # keep tables — often useful for facts
        favor_precision=True,     # be conservative; drop junk rather than include it
    )

    if not extracted:
        return f"ERROR: Could not extract readable text from {url}"

    # 4. Truncate to the character budget.
    if len(extracted) > max_chars:
        extracted = extracted[:max_chars] + "\n\n[...truncated...]"

    # 5. Prefix with the URL so the LLM always sees the source of this text.
    #    This is what lets it cite correctly later.
    return f"SOURCE: {url}\n\n{extracted}"


