"""Wikivoyage fetcher with on-disk cache and HTTP retry/backoff."""
from __future__ import annotations

import pathlib
import time
from typing import Optional

import requests

WIKIVOYAGE_USER_AGENT = (
    "TripPlannerClassProject/0.1 (educational; contact: nanditarad@example.com)"
)
WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"

CACHE_DIR = pathlib.Path("data/wikivoyage_cache")


def _slug(title: str) -> str:
    return title.replace("/", "_").replace(" ", "_")


def fetch_wikitext(title: str, max_attempts: int = 3) -> Optional[tuple[str, str]]:
    """Fetch a Wikivoyage article's wikitext.

    Returns ``(canonical_title, wikitext)`` or ``None`` if the page does not
    exist. The canonical title accounts for Wikivoyage redirects (e.g.
    'Lisboa' -> 'Lisbon') so downstream metadata stays consistent.

    On disk: ``data/wikivoyage_cache/{slug}.wiki`` stores raw wikitext.
    Cache hits return ``(title, cached_text)`` immediately.
    Network errors get exponential-backoff retries (0.5s, 1s, 2s).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{_slug(title)}.wiki"
    if cache_file.exists():
        return title, cache_file.read_text()

    last_err: Optional[Exception] = None
    for attempt in range(max_attempts):
        try:
            r = requests.get(
                WIKIVOYAGE_API,
                params={
                    "action": "parse",
                    "page": title,
                    "format": "json",
                    "prop": "wikitext",
                    "redirects": 1,
                },
                headers={"User-Agent": WIKIVOYAGE_USER_AGENT},
                timeout=30,
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                # Page doesn't exist (e.g. {"error": {"code": "missingtitle"}})
                return None
            text = data["parse"]["wikitext"]["*"]
            canonical = data["parse"].get("title", title)
            cache_file.write_text(text)
            time.sleep(0.1)  # be a polite citizen
            return canonical, text
        except (requests.RequestException, ValueError, KeyError) as e:
            last_err = e
            if attempt < max_attempts - 1:
                time.sleep(0.5 * (2 ** attempt))

    print(f"  [fetch_wikitext] {title!r}: giving up after {max_attempts} attempts: {last_err}")
    return None
