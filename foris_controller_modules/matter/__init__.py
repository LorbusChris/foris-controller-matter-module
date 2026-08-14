# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from foris_controller.handler_base import wrap_required_functions
from foris_controller.module_base import BaseModule

logger = logging.getLogger(__name__)


class MatterModule(BaseModule):
    """Matter network manager: onboarding and the commissioning window."""

    logger = logging.getLogger(__name__)

    def action_get_onboarding(self, data):
        """Onboarding status of the Matter network manager

        Reports 'present' and 'live' separately: an installed manager whose
        daemon is down is a different situation from Matter not being set up
        here at all. The pairing code is included only while a commissioning
        window is open, because that is the only time it authenticates.

        :param data: supposed to be {}
        :type data: dict
        :returns: onboarding status
        :rtype: dict
        """
        return self.handler.get_onboarding()

    def action_open_window(self, data):
        """Open a commissioning window
        :param data: supposed to be {}
        :type data: dict
        :returns: {"error": ..., "window": ...}
        :rtype: dict
        """
        res = self.handler.open_window()
        if not res.get("error"):
            self.notify("window", {"window": res.get("window", "unknown")})
        return res

    def action_close_window(self, data):
        """Close the commissioning window
        :param data: supposed to be {}
        :type data: dict
        :returns: {"error": ..., "window": ...}
        :rtype: dict
        """
        res = self.handler.close_window()
        if not res.get("error"):
            self.notify("window", {"window": res.get("window", "unknown")})
        return res

    def action_remove_fabric(self, data):
        """Unpair a controller
        :param data: {"index": ...}
        :type data: dict
        :returns: {"error": ..., "fabrics": ...}
        :rtype: dict
        """
        res = self.handler.remove_fabric(data["index"])
        if not res.get("error"):
            self.notify("remove_fabric", {"index": data["index"]})
        return res

    def action_get_settings(self, data):
        """Get the matter-netman configuration
        :param data: supposed to be {}
        :type data: dict
        :returns: current settings
        :rtype: dict
        """
        return self.handler.get_settings()

    def action_update_settings(self, data):
        """Update the matter-netman configuration and restart the daemon

        The init script bakes these options into the command line, so the
        restart is part of the action: a reply of result=True means the
        daemon the controllers now talk to runs with the settings written.

        :param data: new settings
        :type data: dict
        :returns: {'result': True/False}
        :rtype: dict
        """
        res = self.handler.update_settings(data)
        if res:
            self.notify("update_settings", data)
        return {"result": res}


@wrap_required_functions(
    [
        "get_onboarding",
        "open_window",
        "close_window",
        "remove_fabric",
        "get_settings",
        "update_settings",
    ]
)
class Handler(object):
    pass
