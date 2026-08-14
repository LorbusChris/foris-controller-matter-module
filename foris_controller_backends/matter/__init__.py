# SPDX-License-Identifier: GPL-3.0-or-later

"""Backend for the Matter network manager.

The manager daemon publishes a ``matter`` ubus object carrying its onboarding
information and local control of the commissioning window. When the daemon is
down its factory configuration still tells an installed manager apart from an
absent one, which is the difference between "Matter is not set up here" and
"Matter is set up and currently broken".
"""

import logging
import os
import re
import typing

from foris_controller_backends.cmdline import BaseCmdLine, inject_cmdline_root
from foris_controller_backends.files import BaseFile, path_exists
from foris_controller_backends.ubus import UbusBackend

logger = logging.getLogger(__name__)

#: Synthesized when the daemon cannot be reached at all.
ERROR_UNREACHABLE = 255

MATTER_FACTORY_INI = "/etc/matter/chip_factory.ini"
MATTER_KVS_INI = "/etc/matter/data/chip_kvs.ini"
QRENCODE = "/usr/bin/qrencode"

#: A Matter onboarding payload is the MT: prefix plus base38.
QR_PAYLOAD_RE = re.compile(r"^MT:[0-9A-Z.-]+$")
#: Fabric metadata keys (f/<index>/...) appear in the KVS once a controller has
#: commissioned the device.
KVS_FABRIC_RE = re.compile(r"^f/[0-9a-f]+/")


class MatterFiles(BaseFile):
    """The two on-disk readings that survive the daemon being down."""

    def factory_config(self) -> typing.Optional[dict]:
        if not path_exists(MATTER_FACTORY_INI):
            return None
        try:
            content = self._file_content(MATTER_FACTORY_INI)
        except OSError:
            return None
        config = {}
        for line in content.splitlines():
            match = re.match(r"^([a-z-]+)=(.*)$", line.strip())
            if match:
                config[match.group(1)] = match.group(2)
        return config

    def commissioned(self) -> bool:
        if not path_exists(MATTER_KVS_INI):
            return False
        try:
            content = self._file_content(MATTER_KVS_INI)
        except OSError:
            return False
        return any(KVS_FABRIC_RE.match(line) for line in content.splitlines())


class MatterQr(BaseCmdLine):
    """Optional server-side QR rendering.

    The frontend gets an SVG it can show as-is, which keeps the payload off any
    third-party rendering service. Absent qrencode is not an error: the manual
    pairing code is always there.
    """

    @staticmethod
    def svg(payload: typing.Optional[str]) -> typing.Optional[str]:
        if not payload or not QR_PAYLOAD_RE.match(payload):
            return None
        if not os.access(inject_cmdline_root(QRENCODE), os.X_OK):
            return None
        retval, stdout, _ = BaseCmdLine._run_command(
            QRENCODE, "-t", "svg", "-m", "2", "-o", "-", payload
        )
        if retval != 0:
            return None
        try:
            svg = stdout.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return svg or None


class MatterUbus:
    """Thin wrapper over the ``matter`` ubus object."""

    OBJECT = "matter"

    @staticmethod
    def call(method: str, data: typing.Optional[dict] = None) -> typing.Optional[dict]:
        return UbusBackend.call_ubus(MatterUbus.OBJECT, method, data)


class MatterState:
    files = MatterFiles()

    def get_onboarding(self) -> dict:
        """Onboarding status; the daemon is authoritative when it answers.

        The pairing code only authenticates while a commissioning window is
        open, so it is handed out only then: a page that always showed the code
        would suggest pairing is always possible.
        """
        status = MatterUbus.call("status")
        if status is not None:
            window = status.get("Window", "closed")
            result = {
                "present": True,
                "live": True,
                "commissioned": (status.get("Fabrics") or 0) > 0,
                "fabrics": status.get("Fabrics") or 0,
                "thread_managed": status.get("ThreadManaged", False),
                "window": window,
            }
            for key, field in (
                ("FabricList", "fabric_list"),
                ("Endpoints", "endpoints"),
                ("WifiShare", "wifi_share"),
                ("WifiSsid", "wifi_ssid"),
                ("Directory", "directory"),
            ):
                if status.get(key) is not None:
                    result[field] = status[key]
            if window in ("basic", "enhanced") and status.get("ManualCode") is not None:
                result["manual_code"] = status["ManualCode"]
                if status.get("QrCode") is not None:
                    result["qr"] = status["QrCode"]
                    svg = MatterQr.svg(status["QrCode"])
                    if svg is not None:
                        result["qr_svg"] = svg
            return result

        # Without the daemon there is no commissioning window and no pairing;
        # report only that Matter management is installed but unreachable.
        if self.files.factory_config() is None:
            return {"present": False}
        return {
            "present": True,
            "live": False,
            "commissioned": self.files.commissioned(),
            "window": "unknown",
        }


class MatterCmds:
    @staticmethod
    def open_window() -> dict:
        return MatterCmds._window("open_commissioning_window")

    @staticmethod
    def close_window() -> dict:
        return MatterCmds._window("close_commissioning_window")

    @staticmethod
    def _window(method: str) -> dict:
        reply = MatterUbus.call(method, {})
        if reply is None:
            return {"error": ERROR_UNREACHABLE}
        result = {"error": reply.get("Error", 0)}
        if reply.get("Window") is not None:
            result["window"] = reply["Window"]
        return result

    @staticmethod
    def remove_fabric(index: int) -> dict:
        """Unpair a controller; the daemon validates the index."""
        reply = MatterUbus.call("remove_fabric", {"index": index})
        if reply is None:
            return {"error": ERROR_UNREACHABLE}
        result = {"error": reply.get("Error", 0)}
        if reply.get("Fabrics") is not None:
            result["fabrics"] = reply["Fabrics"]
        return result
