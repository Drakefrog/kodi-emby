"""Emby-backed content routes used by Arctic Fuse's Info dialog."""

from __future__ import annotations

import os
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from .datamanager import DataManager
from .detail_utils import (
    DETAIL_CAST,
    DETAIL_CAST_FAILURE,
    DETAIL_CAST_TTL,
    DETAIL_FAILURE_TTL,
    DETAIL_ITEM,
    DETAIL_PERSON,
    DETAIL_PERSON_FAILURE,
    DETAIL_PERSON_TTL,
    DETAIL_SHOW,
    DETAIL_SIMILAR,
    DETAIL_SIMILAR_FAILURE,
    DETAIL_SIMILAR_TTL,
    TimedPayloadCache,
    detail_payload_from_response,
    emby_person_fields,
    canonical_detail_item_type,
    is_valid_detail_item_id,
    valid_people,
)
from .downloadutils import DownloadUtils
from .dir_functions import process_directory
from .item_functions import (
    DisplayOptions,
    GuiOptions,
    add_gui_item,
    extract_item_info,
)
from .simple_logging import SimpleLogging


log = SimpleLogging(__name__)

EMBYCON_PLUGIN_URL = "plugin://plugin.video.embycon/"


def _cache() -> TimedPayloadCache:
    download_utils = DownloadUtils()
    profile = xbmcvfs.translatePath(
        xbmcaddon.Addon().getAddonInfo("profile")
    )
    scope = "%s|%s" % (download_utils.get_server(), download_utils.get_user_id())
    return TimedPayloadCache(os.path.join(profile, "detail_cache"), scope)


def _fetch_detail_payload(mode: str, item_id: str) -> dict | None:
    if not is_valid_detail_item_id(item_id):
        log.debug("Ignoring invalid detail item id")
        return None

    try:
        cache = _cache()
    except Exception as error:
        log.debug("Unable to initialise detail cache: {0}", error)
        cache = None
    ttl = DETAIL_CAST_TTL if mode == DETAIL_CAST else DETAIL_SIMILAR_TTL
    failure_mode = (
        DETAIL_CAST_FAILURE if mode == DETAIL_CAST else DETAIL_SIMILAR_FAILURE
    )
    failed = cache.get(failure_mode, item_id, DETAIL_FAILURE_TTL) if cache is not None else None
    if failed is not None:
        log.debug("Detail failure cooldown hit: {0}/{1}", mode, item_id)
        return None
    cached = cache.get(mode, item_id, ttl) if cache is not None else None
    if cached is not None and isinstance(cached, dict):
        log.debug("Detail cache hit: {0}/{1}", mode, item_id)
        return cached

    if mode == DETAIL_CAST:
        url = (
            "{server}/emby/Users/{userid}/Items/"
            + item_id
            + "?Fields=People&format=json"
        )
    elif mode == DETAIL_SIMILAR:
        url = (
            "{server}/emby/Items/"
            + item_id
            + "/Similar?UserId={userid}&Limit=20&Fields={field_filters}&format=json"
        )
    else:
        return None

    try:
        result = DataManager().get_content(url)
    except Exception as error:
        log.debug("Detail route failed: {0}", error)
        try:
            if cache is not None:
                cache.put(failure_mode, item_id, {"failed": True})
        except (OSError, TypeError, ValueError) as cache_error:
            log.debug("Unable to save detail failure cooldown: {0}", cache_error)
        return None

    payload = detail_payload_from_response(mode, result)
    if payload is None:
        try:
            if cache is not None:
                cache.put(failure_mode, item_id, {"failed": True})
        except (OSError, TypeError, ValueError) as cache_error:
            log.debug("Unable to save detail failure cooldown: {0}", cache_error)
        return None

    try:
        if cache is not None:
            cache.put(mode, item_id, payload)
    except (OSError, TypeError, ValueError) as error:
        # A cache failure must not make the Info dialog fail.
        log.debug("Unable to save detail cache: {0}", error)
    return payload


def render_detail_cast(handle: int, params: dict[str, str]) -> int:
    """Render every valid Emby person for Fuse's person dialog."""

    item_id = params.get("id")
    payload = _fetch_detail_payload(DETAIL_CAST, item_id or "")
    list_items = []
    if payload is not None:
        download_utils = DownloadUtils()
        server = download_utils.get_server()
        for person in valid_people(payload.get("People", [])):
            person_id = person.get("Id")
            person_name = person.get("Name")
            if not is_valid_detail_item_id(person_id) or not person_name:
                continue

            list_item = xbmcgui.ListItem(label=person_name, offscreen=True)
            list_item.setProperty("id", str(person_id))
            # A person is not a Kodi-library actor DBID.  Keep the opaque Emby
            # identity in a dedicated property so non-numeric IDs remain safe.
            list_item.setProperty("dbtype", "person")
            list_item.setProperty("tmdb_type", "person")
            list_item.setProperty("person_source", "emby")
            list_item.setProperty("emby_person_id", str(person_id))
            list_item.setProperty("emby_person_type", str(person.get("Type") or ""))
            list_item.setProperty("emby_person_role", str(person.get("Role") or ""))
            if person.get("Role"):
                list_item.setLabel2(person["Role"])

            person_tag = person.get("PrimaryImageTag")
            if person_tag and server:
                person_thumbnail = download_utils.image_url(
                    person_id, "Primary", 0, 400, 400, person_tag, server=server
                )
                list_item.setArt({"thumb": person_thumbnail, "poster": person_thumbnail})

            action_url = (
                sys.argv[0]
                + "?mode=NEW_SEARCH_PERSON&person_id="
                + urllib.parse.quote(str(person_id), safe="")
            )
            list_item.setPath(action_url)
            list_items.append((action_url, list_item, True))

    xbmcplugin.setContent(handle, "artists")
    xbmcplugin.addDirectoryItems(handle, list_items)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
    return len(list_items)


def _fetch_person_payload(person_id: str) -> dict | None:
    """Fetch one complete Emby person record with a scoped short failure cache."""

    if not is_valid_detail_item_id(person_id):
        return None
    try:
        cache = _cache()
    except Exception as error:
        log.debug("Unable to initialise person cache: {0}", error)
        cache = None
    if cache is not None and cache.get(DETAIL_PERSON_FAILURE, person_id, DETAIL_FAILURE_TTL):
        return None
    if cache is not None:
        cached = cache.get(DETAIL_PERSON, person_id, DETAIL_PERSON_TTL)
        if isinstance(cached, dict):
            return cached
    url = (
        "{server}/emby/Users/{userid}/Items/" + person_id
        + "?Fields=Overview,People,ProductionLocations,ImageTags,PrimaryImageTag,PremiereDate,EndDate,Gender&format=json"
    )
    try:
        result = DataManager().get_content(url)
    except Exception as error:
        log.debug("Emby person request failed: {0}", error)
        result = None
    if not isinstance(result, dict) or not result.get("Name"):
        if cache is not None:
            try:
                cache.put(DETAIL_PERSON_FAILURE, person_id, {"failed": True})
            except (OSError, TypeError, ValueError):
                pass
        return None
    if cache is not None:
        try:
            cache.put(DETAIL_PERSON, person_id, result)
        except (OSError, TypeError, ValueError):
            pass
    return result


def render_detail_person(handle: int, params: dict[str, str]) -> int:
    """Complete a visible Emby-person dialog without allowing stale replies in."""

    person_id = params.get("id", "")
    request_id = params.get("request_id", "")
    # 1114 is a skin XML window, not a Python-addressable Kodi window.  Use
    # Home (10000), which exists for every plugin invocation, as the hand-off
    # namespace.  The skin mirrors/clears these properties with its dialog.
    window = xbmcgui.Window(10000)
    # The skin assigns both before opening 1114. A late response is ignored
    # after A->B navigation or closing the dialog.
    current_id = window.getProperty("emby_person_id")
    current_request = window.getProperty("emby_person_request")
    if person_id != current_id or request_id != current_request:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        return 0
    person = _fetch_person_payload(person_id)
    if person is not None and window.getProperty("emby_person_id") == person_id and window.getProperty("emby_person_request") == request_id:
        fields = emby_person_fields(person)
        for key in ("header", "textbox", "birthday", "deathday", "place_of_birth", "gender"):
            window.setProperty("emby_person_" + key, fields.get(key, ""))
        tag = fields.get("primary_image_tag")
        server = DownloadUtils().get_server()
        if tag and server:
            image = DownloadUtils().image_url(person_id, "Primary", 0, 400, 400, tag, server=server)
            window.setProperty("emby_person_poster", image)
    # Clear the spinner even after a failure, but never modify a newer dialog.
    if window.getProperty("emby_person_id") == person_id and window.getProperty("emby_person_request") == request_id:
        window.clearProperty("emby_person_pending")
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
    return 0


def _normalise_similar_item(item: dict) -> dict:
    """Fill fields expected by the existing EmbyCon item mapper."""

    result = dict(item)
    item_type = result.get("Type")
    result.setdefault("Id", "")
    result.setdefault("Etag", "")
    result.setdefault("IsFolder", item_type == "Series")
    result.setdefault("LocationType", "FileSystem")
    result.setdefault("Name", "")
    result.setdefault("SortName", result["Name"])
    result.setdefault("Status", None)
    result.setdefault("Taglines", [])
    result.setdefault("TagItems", [])
    result.setdefault("ProductionYear", None)
    result.setdefault("PremiereDate", None)
    result.setdefault("DateCreated", None)
    result.setdefault("AirTime", None)
    result.setdefault("MediaStreams", [])
    result.setdefault("People", None)
    result.setdefault("Studios", [])
    result.setdefault("ProductionLocations", [])
    result.setdefault("Genres", [])
    result.setdefault("SeriesName", None)
    result.setdefault("Overview", None)
    result.setdefault("RunTimeTicks", None)
    result.setdefault("ChildCount", 0)
    result.setdefault("RecursiveItemCount", 0)
    result.setdefault("OfficialRating", None)
    result.setdefault("CommunityRating", 0.0)
    result.setdefault("CriticRating", 0.0)
    result.setdefault("IndexNumber", None)
    result.setdefault("Album", None)
    result.setdefault("Artists", [])
    result.setdefault("AlbumArtist", None)
    user_data = {
        "Played": False,
        "IsFavorite": False,
        "PlaybackPositionTicks": None,
        "UnplayedItemCount": 0,
    }
    raw_user_data = result.get("UserData")
    if isinstance(raw_user_data, dict):
        user_data.update(raw_user_data)
    result["UserData"] = user_data
    image_tags = {
        "Primary": None,
        "Thumb": None,
        "Banner": None,
        "Logo": None,
        "Art": None,
        "Disc": None,
    }
    raw_image_tags = result.get("ImageTags")
    if isinstance(raw_image_tags, dict):
        image_tags.update(raw_image_tags)
    result["ImageTags"] = image_tags
    result.setdefault("BackdropImageTags", [])
    result.setdefault("ParentBackdropItemId", None)
    result.setdefault("ParentBackdropImageTags", [])
    result.setdefault("SeriesId", None)
    result.setdefault("SeriesPrimaryImageTag", None)
    result.setdefault("ParentPrimaryImageTag", None)
    result.setdefault("ParentPrimaryItemId", None)
    return result


def render_detail_similar(handle: int, params: dict[str, str]) -> int:
    """Render Similar results through the normal EmbyCon item builder."""

    item_id = params.get("id")
    payload = _fetch_detail_payload(DETAIL_SIMILAR, item_id or "")
    if payload is None:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        return 0

    download_utils = DownloadUtils()
    server = download_utils.get_server()
    if not server:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        return 0

    settings = xbmcaddon.Addon()
    gui_options = GuiOptions(
        server=server,
        max_image_width=int(settings.getSetting("max_image_width")),
        use_prem_date_for_added=settings.getSetting("use_prem_date_for_added") == "true",
    )
    display_options = DisplayOptions(
        addCounts=settings.getSetting("addCounts") == "true",
        addResumePercent=settings.getSetting("addResumePercent") == "true",
        addSubtitleAvailable=settings.getSetting("addSubtitleAvailable") == "true",
    )

    list_items = []
    content_types = set()
    for raw_item in payload.get("Items", []):
        if not isinstance(raw_item, dict):
            continue
        item = _normalise_similar_item(raw_item)
        if item.get("Type") not in ("Movie", "Series") or not item.get("Id"):
            continue
        try:
            item_details = extract_item_info(item, gui_options, download_utils)
            if item_details.item_type == "Series":
                item_url = (
                    "{server}/emby/Shows/"
                    + item_details.id
                    + "/Seasons?userId={userid}&Fields={field_filters}&format=json"
                )
                is_folder = True
                content_types.add("tvshows")
            else:
                item_url = item_details.id
                is_folder = False
                content_types.add("movies")
            gui_item = add_gui_item(
                item_url, item_details, display_options, folder=is_folder
            )
            if gui_item:
                # The recommendation is nested inside Fuse's Info dialog.
                # Let the skin hand this item's Emby identity to OPEN_DETAIL
                # instead of reopening the parent item with Action(Info).
                gui_item.list_item.setProperty("emby_detail_action", "OPEN_DETAIL")
                list_items.append(gui_item.as_tuple())
        except Exception as error:
            log.debug("Skipping malformed similar item: {0}", error)

    if len(content_types) > 1:
        content_type = "videos"
    elif content_types:
        content_type = content_types.pop()
    else:
        content_type = "videos"
    xbmcplugin.setContent(handle, content_type)
    xbmcplugin.addDirectoryItems(handle, list_items)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
    return len(list_items)


def _detail_item_url(item_id: str, item_type: str) -> str:
    """Build a one-item Emby query for a real Kodi directory item."""

    return (
        "{server}/emby/Users/{userid}/Items"
        "?Ids="
        + item_id
        + "&IncludeItemTypes="
        + item_type
        + "&Limit=1&Fields={field_filters}&format=json"
    )


def _load_detail_gui_item(item_id: str, item_type: str):
    """Load exactly one real Emby GUI item for a movie or series detail."""

    directory_result = process_directory(
        _detail_item_url(item_id, item_type),
        None,
        {"media_type": "movies" if item_type == "Movie" else "tvshows"},
        False,
    )
    if directory_result is None or directory_result.dir_items is None:
        log.debug("Detail item query returned no directory: {0}/{1}", item_id, item_type)
        return None
    if len(directory_result.dir_items) != 1:
        log.debug(
            "Detail item query returned {0} items: {1}/{2}",
            len(directory_result.dir_items),
            item_id,
            item_type,
        )
        return None

    gui_item = directory_result.dir_items[0]
    if gui_item is None or gui_item.list_item is None:
        log.debug("Detail item query returned an invalid GUI item: {0}/{1}", item_id, item_type)
        return None
    return gui_item


def render_detail_item(handle: int, params: dict[str, str]) -> int:
    """Render one Emby item so Kodi can use it as the active Info item."""

    item_id = params.get("id", "")
    item_type = canonical_detail_item_type(params.get("type"))
    if not is_valid_detail_item_id(item_id) or item_type is None:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        return 0

    gui_item = _load_detail_gui_item(item_id, item_type)
    if gui_item is None:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        return 0

    content_type = "movies" if item_type == "Movie" else "tvshows"
    xbmcplugin.setContent(handle, content_type)
    xbmcplugin.addDirectoryItems(handle, [gui_item.as_tuple()])
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
    return 1


def show_detail(params: dict[str, str]) -> None:
    """Open an Emby movie or series directly in Kodi's standard info dialog."""

    item_id = params.get("id", "")
    item_type = canonical_detail_item_type(params.get("type"))
    if not is_valid_detail_item_id(item_id) or item_type is None:
        log.debug("Ignoring invalid direct detail route: {0}/{1}", item_id, item_type)
        return

    try:
        gui_item = _load_detail_gui_item(item_id, item_type)
    except Exception as error:
        log.debug("Unable to load direct detail route {0}/{1}: {2}", item_id, item_type, error)
        return
    if gui_item is None:
        log.debug("Unable to open direct detail route: {0}/{1}", item_id, item_type)
        return

    log.debug("Opening direct Emby detail dialog: {0}/{1}", item_id, item_type)
    xbmcgui.Dialog().info(gui_item.list_item)


def open_detail(params: dict[str, str]) -> None:
    """Open a selected Emby item from Fuse's second-stage Info action."""

    item_id = params.get("item_id", "")
    item_type = canonical_detail_item_type(params.get("item_type"))
    if not is_valid_detail_item_id(item_id) or item_type is None:
        log.debug("Ignoring invalid detail handoff: {0}/{1}", item_id, item_type)
        return

    detail_url = (
        EMBYCON_PLUGIN_URL
        + "?mode="
        + DETAIL_SHOW
        + "&id="
        + urllib.parse.quote(item_id, safe="")
        + "&type="
        + urllib.parse.quote(item_type, safe="")
    )
    # Open the target ListItem directly after all skin information dialogs have
    # closed. Do not activate Videos: that creates a one-item MyVideoNav page
    # and makes a later global Action(Info) race the directory request.
    xbmc.executebuiltin("Dialog.Close(1114,true)")
    xbmc.executebuiltin("Dialog.Close(1190,true)")
    xbmc.executebuiltin("Dialog.Close(movieinformation,true)")
    xbmc.executebuiltin(
        "AlarmClock(embycon_show_detail,RunPlugin(%s),00:01,silent)"
        % detail_url
    )
