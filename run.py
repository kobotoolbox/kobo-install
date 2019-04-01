#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import platform
import sys

from helpers.cli import CLI
from helpers.command import Command
from helpers.config import Config
from helpers.setup import Setup
from helpers.template import Template


def run(force_setup=False):

    if not platform.system() in ["Linux", "Darwin"]:
        CLI.colored_print("Not compatible with this OS", CLI.COLOR_ERROR)
    else:
        config = Config()
        current_config = config.get_config()
        if config.first_time:
            force_setup = True

        if force_setup:
            current_config = config.build()
            Setup.run(current_config)
            Template.render(config)
            Setup.update_hosts(current_config)
        else:
            if config.auto_detect_network():
                Template.render(config)
                Setup.update_hosts(current_config)

        Command.start()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            Command.help()
        elif sys.argv[1] == "-u" or sys.argv[1] == "--upgrade":
            Command.upgrade()
        elif sys.argv[1] == "-i" or sys.argv[1] == "--info":
            Command.info(0)
        elif sys.argv[1] == "-s" or sys.argv[1] == "--setup":
            run(force_setup=True)
        elif sys.argv[1] == "-S" or sys.argv[1] == "--stop":
            Command.stop()
        elif sys.argv[1] == "-l" or sys.argv[1] == "--logs":
            Command.logs()
        elif sys.argv[1] == "-b" or sys.argv[1] == "--build":
            Command.build()
        elif sys.argv[1] == "-bkf" or sys.argv[1] == "--build-kpi":
            Command.build("kf")
        elif sys.argv[1] == "-bkc" or sys.argv[1] == "--build-kobocat":
            Command.build("kc")
        else:
            CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    else:
        run()
