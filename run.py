#!/usr/bin/env python3
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

    if sys.version_info[0] == 2:
        CLI.colored_print("╔═══════════════════════════════════════════════════════════════╗", CLI.COLOR_ERROR)
        CLI.colored_print("║ DEPRECATION: Python 2.7 has reached the end of its life on    ║", CLI.COLOR_ERROR)
        CLI.colored_print("║ January 1st, 2020. Please upgrade your Python as Python 2.7   ║", CLI.COLOR_ERROR)
        CLI.colored_print("║ is not maintained anymore.                                    ║", CLI.COLOR_ERROR)
        CLI.colored_print("║ A future version of KoBoInstall will drop support for it.     ║", CLI.COLOR_ERROR)
        CLI.colored_print("╚═══════════════════════════════════════════════════════════════╝", CLI.COLOR_ERROR)

    if not platform.system() in ["Linux", "Darwin"]:
        CLI.colored_print("Not compatible with this OS", CLI.COLOR_ERROR)
    else:
        config = Config()
        current_config = config.get_config()
        if config.first_time:
            force_setup = True

        if force_setup:
            current_config = config.build()
            Setup.clone_kobodocker(config)
            Template.render(config)
            config.init_letsencrypt()
            Setup.update_hosts(current_config)
        else:
            if config.auto_detect_network():
                Template.render(config)
                Setup.update_hosts(current_config)

        Command.start()


if __name__ == "__main__":
    try:

        if len(sys.argv) > 2:
            if sys.argv[1] == "-cf" or sys.argv[1] == "--compose-frontend":
                Command.compose_frontend(sys.argv[2:])
            elif sys.argv[1] == "-cb" or sys.argv[1] == "--compose-backend":
                Command.compose_backend(sys.argv[2:])
            else:
                CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
        elif len(sys.argv) == 2:
            if sys.argv[1] == "-h" or sys.argv[1] == "--help":
                Command.help()
            elif sys.argv[1] == "-u" or sys.argv[1] == "--update":
                Command.update()
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
            elif sys.argv[1] == "-v" or sys.argv[1] == "--version":
                Command.version()
            elif sys.argv[1] == "-m" or sys.argv[1] == "--maintenance":
                Command.configure_maintenance()
            elif sys.argv[1] == "-sm" or sys.argv[1] == "--stop-maintenance":
                Command.stop_maintenance()
            else:
                CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
        else:
            run()

    except KeyboardInterrupt:
        CLI.colored_print("\nUser interrupted execution", CLI.COLOR_INFO)
