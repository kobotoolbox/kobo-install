# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import sys
try:
    from imp import reload
except ImportError:
    from importlib import reload

from helpers.setup import Setup
from helpers.cli import CLI


class Updater:
    """
    This class exists only to reload imported modules after updates.
    All the code must in other modules to be reloaded
    """

    @staticmethod
    def run(version=None):
        # Update kobo-install first
        Setup.update_koboinstall(version)
        CLI.colored_print("KoBoInstall has been updated", CLI.COLOR_SUCCESS)

        # Reload modules
        for module_ in sys.modules.values():
            if 'kobo-install' in str(module_):
                reload(module_)

        # Update kobo-docker
        Setup.update_kobodocker()
        Setup.post_update()
