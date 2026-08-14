# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from foris_controller.handler_base import BaseMockHandler
from foris_controller.utils import logger_wrapper

from .. import Handler

logger = logging.getLogger(__name__)


class MockMatterHandler(Handler, BaseMockHandler):
    """In-memory network manager.

    The pairing code appears and disappears with the window, exactly as it does
    on the router, so a frontend developed against this mock cannot come to
    depend on a code that is always present.
    """

    present = True
    live = True
    window = "closed"
    fabrics = 1
    fabric_list = [{"FabricIndex": 1, "VendorId": 65521, "Label": "Demo controller"}]
    thread_managed = True
    endpoints = [{"Endpoint": 0, "DeviceType": "Root Node"}]
    directory = []
    wifi_share = False
    wifi_ssid = None
    manual_code = "34970112332"
    qr = "MT:Y.K9042C00KA0648G00"

    @logger_wrapper(logger)
    def get_onboarding(self):
        if not self.present:
            return {"present": False}
        if not self.live:
            return {
                "present": True,
                "live": False,
                "commissioned": self.fabrics > 0,
                "window": "unknown",
            }
        result = {
            "present": True,
            "live": True,
            "commissioned": self.fabrics > 0,
            "fabrics": self.fabrics,
            "fabric_list": list(self.fabric_list),
            "thread_managed": self.thread_managed,
            "endpoints": list(self.endpoints),
            "directory": list(self.directory),
            "wifi_share": self.wifi_share,
            "window": self.window,
        }
        if self.wifi_ssid is not None:
            result["wifi_ssid"] = self.wifi_ssid
        if self.window in ("basic", "enhanced"):
            result["manual_code"] = self.manual_code
            result["qr"] = self.qr
        return result

    @logger_wrapper(logger)
    def open_window(self):
        MockMatterHandler.window = "basic"
        return {"error": 0, "window": MockMatterHandler.window}

    @logger_wrapper(logger)
    def close_window(self):
        MockMatterHandler.window = "closed"
        return {"error": 0, "window": MockMatterHandler.window}

    @logger_wrapper(logger)
    def remove_fabric(self, index):
        remaining = [f for f in self.fabric_list if f.get("FabricIndex") != index]
        if len(remaining) == len(self.fabric_list):
            # The daemon validates the index; an unknown one changes nothing.
            return {"error": 1, "fabrics": self.fabrics}
        MockMatterHandler.fabric_list = remaining
        MockMatterHandler.fabrics = len(remaining)
        return {"error": 0, "fabrics": MockMatterHandler.fabrics}
