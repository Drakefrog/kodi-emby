"""Small, Kodi-independent helpers for Emby-backed detail widgets."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable


DETAIL_ITEM_TYPES = {"movie": "Movie", "series": "Series"}
DETAIL_CAST = "DETAIL_CAST"
DETAIL_SIMILAR = "DETAIL_SIMILAR"
DETAIL_ITEM = "DETAIL_ITEM"
DETAIL_SHOW = "SHOW_DETAIL"
DETAIL_PERSON = "DETAIL_PERSON"
DETAIL_PERSON_FAILURE = "DETAIL_PERSON_FAILURE"
DETAIL_CAST_FAILURE = "DETAIL_CAST_FAILURE"
DETAIL_SIMILAR_FAILURE = "DETAIL_SIMILAR_FAILURE"
DETAIL_CAST_TTL = 10 * 60
DETAIL_SIMILAR_TTL = 30 * 60
DETAIL_PERSON_TTL = 24 * 60 * 60
DETAIL_FAILURE_TTL = 60
DETAIL_CACHE_MODES = {
    DETAIL_CAST,
    DETAIL_SIMILAR,
    DETAIL_CAST_FAILURE,
    DETAIL_SIMILAR_FAILURE,
    DETAIL_PERSON,
    DETAIL_PERSON_FAILURE,
}
_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def canonical_detail_item_type(item_type: str | None) -> str | None:
    """Return the Emby item type supported by the detail dialog."""

    if item_type is None:
        return None
    return DETAIL_ITEM_TYPES.get(item_type.strip().lower())


def is_detail_item_type(item_type: str | None) -> bool:
    return canonical_detail_item_type(item_type) is not None


def is_valid_detail_item_id(item_id: str | None) -> bool:
    """Only allow IDs that are safe to place in an Emby path/query."""

    return bool(item_id) and _ITEM_ID_RE.fullmatch(str(item_id)) is not None


def detail_route_url(
    mode: str, item_id: str, item_type: str | None = None
) -> str:
    """Build a Kodi plugin URL for one of the detail widget routes."""

    if mode not in (DETAIL_CAST, DETAIL_SIMILAR, DETAIL_ITEM, DETAIL_SHOW, DETAIL_PERSON):
        raise ValueError("unsupported detail route")
    if not is_valid_detail_item_id(item_id):
        raise ValueError("invalid detail item id")
    route = "plugin://plugin.video.embycon/?mode=" + mode + "&id=" + str(item_id)
    if mode in (DETAIL_ITEM, DETAIL_SHOW):
        canonical_type = canonical_detail_item_type(item_type)
        if canonical_type is None:
            raise ValueError("item type is required for detail item route")
        route += "&type=" + canonical_type
    return route


def detail_payload_from_response(mode: str, response: Any) -> dict | None:
    """Keep only the response shape needed by a detail widget."""

    if not isinstance(response, dict):
        return None
    if mode == DETAIL_CAST:
        people = response.get("People", [])
        return {"People": people} if isinstance(people, list) else None
    if mode == DETAIL_SIMILAR:
        items = response.get("Items", [])
        return {"Items": items} if isinstance(items, list) else None
    return None


def valid_people(people: Any) -> list[dict]:
    """Keep Emby's order while removing invalid or repeated people IDs."""

    if not isinstance(people, list):
        return []
    result: list[dict] = []
    seen: set[str] = set()
    for person in people:
        if not isinstance(person, dict):
            continue
        person_id = person.get("Id")
        name = person.get("Name")
        if not is_valid_detail_item_id(person_id) or not isinstance(name, str) or not name.strip():
            continue
        person_id = str(person_id)
        if person_id in seen:
            continue
        seen.add(person_id)
        result.append(person)
    return result


def emby_person_fields(person: Any) -> dict[str, str]:
    """Map only Emby's person fields; never invent TMDb-backed metadata."""

    if not isinstance(person, dict):
        return {}
    image_tags = person.get("ImageTags")
    primary_tag = person.get("PrimaryImageTag")
    if not primary_tag and isinstance(image_tags, dict):
        primary_tag = image_tags.get("Primary")
    locations = person.get("ProductionLocations")
    if isinstance(locations, list):
        place = ", ".join(str(value) for value in locations if value)
    else:
        place = str(locations or "")
    return {
        "header": str(person.get("Name") or ""),
        "textbox": str(person.get("Overview") or ""),
        "birthday": str(person.get("PremiereDate") or ""),
        "deathday": str(person.get("EndDate") or ""),
        "place_of_birth": place,
        "gender": str(person.get("Gender") or ""),
        "primary_image_tag": str(primary_tag or ""),
    }


def detail_cache_filename(cache_root: str, scope: str, mode: str, item_id: str) -> str:
    """Return an isolated cache filename for a user/server/detail route."""

    if mode not in DETAIL_CACHE_MODES:
        raise ValueError("unsupported detail route")
    if not is_valid_detail_item_id(item_id):
        raise ValueError("invalid detail item id")
    digest = hashlib.sha256(
        (scope + "|" + mode + "|" + str(item_id)).encode("utf-8")
    ).hexdigest()
    return os.path.join(cache_root, "detail_" + digest + ".json")


@dataclass
class TimedPayloadCache:
    """JSON-backed cache with an injected clock for deterministic tests."""

    cache_root: str
    scope: str
    now: Callable[[], float] = time.time

    def get(self, mode: str, item_id: str, ttl: int) -> Any | None:
        filename = detail_cache_filename(self.cache_root, self.scope, mode, item_id)
        try:
            with open(filename, "r", encoding="utf-8") as cache_file:
                entry = json.load(cache_file)
            if self.now() - float(entry["saved_at"]) < ttl:
                return entry["payload"]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        return None

    def put(self, mode: str, item_id: str, payload: Any) -> None:
        os.makedirs(self.cache_root, exist_ok=True)
        filename = detail_cache_filename(self.cache_root, self.scope, mode, item_id)
        temporary = filename + ".tmp"
        with open(temporary, "w", encoding="utf-8") as cache_file:
            json.dump({"saved_at": self.now(), "payload": payload}, cache_file)
        os.replace(temporary, filename)
