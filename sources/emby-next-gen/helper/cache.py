import threading
from . import utils

QueryCache = {}
EmbyItemIndex = {} # EmbyId -> [(ListItem, ContentRequest), ...]
PathItemIndex = {} # path -> ListItem
CacheLock = threading.Lock()
DynamicPrefetch = {}
DynamicPrefetchInFlight = set()
DynamicPrefetchLock = threading.Lock()

def reserve_dynamic_prefetch(CacheKey):
    """Reserve one Dynamic page for background loading.

    A reservation is deliberately separate from QueryCache: prefetched items
    are raw API results and are converted into Kodi directory items only when
    the user opens that page.
    """
    with utils.SafeLock(DynamicPrefetchLock):
        if CacheKey in DynamicPrefetch or CacheKey in DynamicPrefetchInFlight:
            return False

        DynamicPrefetchInFlight.add(CacheKey)
        return True

def store_dynamic_prefetch(CacheKey, Items):
    with utils.SafeLock(DynamicPrefetchLock):
        DynamicPrefetchInFlight.discard(CacheKey)

        if CacheKey not in DynamicPrefetch:
            DynamicPrefetch[CacheKey] = Items

def release_dynamic_prefetch(CacheKey):
    with utils.SafeLock(DynamicPrefetchLock):
        DynamicPrefetchInFlight.discard(CacheKey)

def take_dynamic_prefetch(CacheKey):
    with utils.SafeLock(DynamicPrefetchLock):
        return DynamicPrefetch.pop(CacheKey, None)

def add_cachemapping(EmbyId, ListItem, ContentRequest):
    EmbyId = str(EmbyId)

    with utils.SafeLock(CacheLock):
        if EmbyId not in EmbyItemIndex:
            EmbyItemIndex[EmbyId] = []

        EmbyItemIndex[EmbyId].append((ListItem, ContentRequest))

def add_pathcachemapping(path, ListItem):
    with utils.SafeLock(CacheLock):
        PathItemIndex[path] = ListItem

def reset_querycache():
    with utils.SafeLock(CacheLock):
        QueryCache.clear()
        EmbyItemIndex.clear()
        PathItemIndex.clear()

    with utils.SafeLock(DynamicPrefetchLock):
        DynamicPrefetch.clear()
        DynamicPrefetchInFlight.clear()

    utils.refresh_DynamicNode()

def update_querycache_userdata(UserDatas):
    ItemUpdate = []
    ItemDelete = []

    with utils.SafeLock(CacheLock):
        for UserData in UserDatas:
            EmbyId = str(UserData[0])

            if EmbyId in EmbyItemIndex:
                ItemUpdate.append((UserData, list(EmbyItemIndex[EmbyId])))

        for ctype, entries in QueryCache.items():
            for cid in entries:
                if cid.startswith("forcedrefresh_"):
                    ItemDelete.append((ctype, cid))

        for ctype, cid in ItemDelete:
            del QueryCache[ctype][cid]

    for UserData, items in ItemUpdate:
        position_ticks = UserData[1]

        if position_ticks is not None:
            KodiPosition = round(float(position_ticks / 10000000.0), 6)
        else:
            KodiPosition = -1

        LastPlayed = UserData[2]
        PlayCount = UserData[3]
        PlaybackEnded = UserData[4]

        for ListItem, ContentRequest in items:
            if ContentRequest in ("MusicArtist", "MusicAlbum", "Audio"):
                InfoTag = ListItem.getMusicInfoTag()

                if PlayCount == -1:
                    if PlaybackEnded:
                        current = InfoTag.getPlayCount()
                        if isinstance(current, int):
                            InfoTag.setPlayCount(current + 1)
                else:
                    InfoTag.setPlayCount(PlayCount if PlayCount else 0)
            else:
                InfoTag = ListItem.getVideoInfoTag()

                if KodiPosition != -1:
                    if KodiPosition > 60:
                        InfoTag.setResumePoint(float(KodiPosition))
                    else:
                        InfoTag.setResumePoint(0.0)

                if PlayCount == -1:
                    if PlaybackEnded:
                        current = InfoTag.getPlayCount()

                        if isinstance(current, int):
                            InfoTag.setPlaycount(current + 1)
                else:
                    InfoTag.setPlaycount(PlayCount if PlayCount else 0)

                if LastPlayed:
                    InfoTag.setLastPlayed(LastPlayed)

    if ItemUpdate or ItemDelete:
        utils.refresh_DynamicNode()
