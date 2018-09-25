# -*- coding: utf-8 -*-

import platform
import sys

from helpers.cli import CLI
from helpers.config import Config
from helpers.setup import Setup


def help():
    pass

def run(force_setup=False):

    if not platform.system() in ["Linux", "Darwin"]:
        CLI.colored_print("Not compatible with this OS", CLI.COLOR_ERROR)
    else:
        current_config = Config.read_config()
        if not current_config:
            force_setup = True

        if force_setup:
            setup = Setup(current_config)
            setup.run()


if __name__ == "__main__":

    if len(sys.argv) > 2:
        CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            help()
        elif sys.argv[1] == "-s" or sys.argv[1] == "--setup":
            run(force_setup=True)
        else:
            CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    else:
        run()