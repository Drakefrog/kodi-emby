"""Pure helpers for search routes that are also usable outside Kodi."""

from __future__ import annotations

import html
import urllib.parse


FUSE_SEARCH_ITEM_TYPES = {
    "movie": "Movie",
    "series": "Series",
}


def parse_fuse_search_params(paramstring: str) -> dict[str, str]:
    """Parse a Fuse search query without relying on Kodi's legacy parser.

    Fuse generates XML-escaped separators in some contexts.  ``parse_qsl``
    handles UTF-8, spaces, percent escapes, plus signs, and equals signs in a
    value correctly once those separators have been normalized.
    """

    if not paramstring:
        return {}

    query = html.unescape(paramstring)
    if query.startswith("?"):
        query = query[1:]

    return dict(urllib.parse.parse_qsl(query, keep_blank_values=True))


def fuse_search_item_type(item_type: str | None) -> str | None:
    """Return the canonical Emby item type supported by Fuse search."""

    if item_type is None:
        return None
    return FUSE_SEARCH_ITEM_TYPES.get(item_type.strip().lower())


def is_fuse_search_query_valid(query: str | None) -> bool:
    """Return whether a Fuse query is long enough to send to Emby."""

    return bool(query) and len(query) >= 2
