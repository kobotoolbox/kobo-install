# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import sys

from helpers.setup import Setup
from helpers.cli import CLI


class Updater:
    """
    Updates kobo-install (this utility), restarts this script, and updates
    kobo-docker
    """

    @staticmethod
    def run(version='stable', update_self=True):
        # Validate kobo-docker already exists and is valid
        Setup.validate_already_run()

        if update_self:
            # Update kobo-install first
            Setup.update_koboinstall(version)
            CLI.colored_print("KoBoInstall has been updated", CLI.COLOR_SUCCESS)

            # Reload this script to use `version`.
            # NB:`argv[0]` does not automatically get set to the executable
            # path as it usually would, so we have to do it manually--hence the
            # double `sys.executable`
            os.execl(sys.executable, sys.executable, *sys.argv)

        # Update kobo-docker
        Setup.update_kobodocker()
        CLI.colored_print("KoBoToolbox has been updated", CLI.COLOR_SUCCESS)
        Setup.post_update()
