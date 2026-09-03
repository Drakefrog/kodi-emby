# Gnu General Public License - see LICENSE.TXT

from uuid import uuid4 as uuid4
import xbmcaddon
import xbmcvfs

from .kodi_utils import HomeWindow
from .simple_logging import SimpleLogging

log = SimpleLogging(__name__)


class ClientInformation:
    # Keep the wire identity stable so Emby servers that identify or allow
    # clients by name see the same identity as Infuse.
    INFUSE_CLIENT = "Infuse-Direct"
    INFUSE_VERSION = "8.0.4"

    @staticmethod
    def get_device_id() -> str:
        window = HomeWindow()
        client_id = window.get_property("client_id")

        if client_id:
            return client_id

        legacy_guid_path = xbmcvfs.translatePath("special://temp/embycon_guid")
        profile = xbmcaddon.Addon().getAddonInfo("profile")
        profile_guid_path = xbmcvfs.translatePath(
            profile.rstrip("/\\") + "/embycon_guid"
        )
        log.debug("emby_guid_path: {0}", profile_guid_path)

        client_id = ""
        for guid_path in (profile_guid_path, legacy_guid_path):
            try:
                if not xbmcvfs.exists(guid_path):
                    continue
                guid = xbmcvfs.File(guid_path)
                client_id = guid.read().strip()
                guid.close()
            except Exception as error:
                log.debug("Unable to read emby guid {0}: {1}", guid_path, error)
            if client_id:
                break

        generated = not client_id
        if generated:
            client_id = uuid4().hex
            log.debug("Generating a new guid: {0}", client_id)
        try:
            profile_dir = profile_guid_path.rsplit("/", 1)[0]
            xbmcvfs.mkdirs(profile_dir)
            guid = xbmcvfs.File(profile_guid_path, "w")
            guid.write(client_id)
            guid.close()
        except Exception as error:
            log.debug("Unable to persist emby guid in profile: {0}", error)
            try:
                guid = xbmcvfs.File(legacy_guid_path, "w")
                guid.write(client_id)
                guid.close()
            except Exception as legacy_error:
                log.debug("Unable to persist legacy emby guid: {0}", legacy_error)

        if generated:
            log.debug("emby_client_id (NEW): {0}", client_id)
        else:
            log.debug("emby_client_id: {0}", client_id)

        window.set_property("client_id", client_id)
        return client_id

    @staticmethod
    def get_version() -> str:
        addon = xbmcaddon.Addon()
        return addon.getAddonInfo("version")

    @staticmethod
    def get_client() -> str:
        return ClientInformation.INFUSE_CLIENT

    @staticmethod
    def get_client_version() -> str:
        return ClientInformation.INFUSE_VERSION

    @staticmethod
    def get_user_agent() -> str:
        return "%s/%s" % (
            ClientInformation.INFUSE_CLIENT,
            ClientInformation.INFUSE_VERSION,
        )
