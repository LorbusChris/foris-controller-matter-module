# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from foris_controller.handler_base import BaseOpenwrtHandler
from foris_controller.utils import logger_wrapper

from foris_controller_backends.matter import MatterCmds, MatterState, MatterUci

from .. import Handler

logger = logging.getLogger(__name__)


class OpenwrtMatterHandler(Handler, BaseOpenwrtHandler):
    state = MatterState()
    cmds = MatterCmds()
    uci = MatterUci()

    @logger_wrapper(logger)
    def get_onboarding(self):
        return self.state.get_onboarding()

    @logger_wrapper(logger)
    def open_window(self):
        return self.cmds.open_window()

    @logger_wrapper(logger)
    def close_window(self):
        return self.cmds.close_window()

    @logger_wrapper(logger)
    def remove_fabric(self, index):
        return self.cmds.remove_fabric(index)

    @logger_wrapper(logger)
    def get_settings(self):
        return self.uci.get_settings()

    @logger_wrapper(logger)
    def update_settings(self, data):
        return self.uci.update_settings(data)
