#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import platform
import sys

if (
    sys.version_info[0] == 2
    or (sys.version_info[0] == 3 and sys.version_info[1] <= 5)
):
    # Do not import any classes because they can contain not supported syntax
    # for older python versions. (i.e. avoid SyntaxError on imports)
    message = (
        '╔══════════════════════════════════════════════════════╗\n'
        '║                                                      ║\n'
        '║ Your Python version has reached the end of its life. ║\n'
        '║ Please upgrade it as it is not maintained anymore.   ║\n'
        '║                                                      ║\n'
        '╚══════════════════════════════════════════════════════╝'
    )
    print("\033[1;31m" + message + '\033[0;0m')
    sys.exit(1)

from helpers.cli import CLI
from helpers.command import Command
from helpers.config import Config
from helpers.setup import Setup
from helpers.template import Template
from helpers.updater import Updater


def run(force_setup=False):

    if not platform.system() in ['Linux', 'Darwin']:
        CLI.colored_print('Not compatible with this OS', CLI.COLOR_ERROR)
    else:
        config = Config()
        dict_ = config.get_dict()
        if config.first_time:
            force_setup = True

        if force_setup:
            dict_ = config.build()
            Setup.clone_kobodocker(config)
            Template.render(config)
            Setup.update_hosts(dict_)
        else:
            if config.auto_detect_network():
                Template.render(config)
                Setup.update_hosts(dict_)

        config.validate_passwords()
        Command.start(force_setup=force_setup)


if __name__ == '__main__':
    try:

        # avoid infinite self-updating loops
        update_self = Updater.NO_UPDATE_SELF_OPTION not in sys.argv
        while True:
            try:
                sys.argv.remove(Updater.NO_UPDATE_SELF_OPTION)
            except ValueError:
                break

        if len(sys.argv) > 2:
            if sys.argv[1] == '-cf' or sys.argv[1] == '--compose-frontend':
                Command.compose_frontend(sys.argv[2:])
            elif sys.argv[1] == '-cb' or sys.argv[1] == '--compose-backend':
                Command.compose_backend(sys.argv[2:])
            elif sys.argv[1] == '-u' or sys.argv[1] == '--update':
                Updater.run(sys.argv[2], update_self=update_self)
            elif sys.argv[1] == '--upgrade':
                Updater.run(sys.argv[2], update_self=update_self)
            elif sys.argv[1] == '--auto-update':
                Updater.run(sys.argv[2], cron=True, update_self=update_self)
            else:
                CLI.colored_print("Bad syntax. Try 'run.py --help'",
                                  CLI.COLOR_ERROR)
        elif len(sys.argv) == 2:
            if sys.argv[1] == '-h' or sys.argv[1] == '--help':
                Command.help()
            elif sys.argv[1] == '-u' or sys.argv[1] == '--update':
                Updater.run(update_self=update_self)
            elif sys.argv[1] == '--upgrade':
                # 'update' was called 'upgrade' in a previous release; accept
                # either 'update' or 'upgrade' here to ease the transition
                Updater.run(update_self=update_self)
            elif sys.argv[1] == '--auto-update':
                Updater.run(cron=True, update_self=update_self)
            elif sys.argv[1] == '-i' or sys.argv[1] == '--info':
                Command.info(0)
            elif sys.argv[1] == '-s' or sys.argv[1] == '--setup':
                run(force_setup=True)
            elif sys.argv[1] == '-S' or sys.argv[1] == '--stop':
                Command.stop()
            elif sys.argv[1] == '-l' or sys.argv[1] == '--logs':
                Command.logs()
            elif sys.argv[1] == '-b' or sys.argv[1] == '--build':
                Command.build()
            elif sys.argv[1] == '-bkf' or sys.argv[1] == '--build-kpi':
                Command.build('kf')
            elif sys.argv[1] == '-bkc' or sys.argv[1] == '--build-kobocat':
                Command.build('kc')
            elif sys.argv[1] == '-v' or sys.argv[1] == '--version':
                Command.version()
            elif sys.argv[1] == '-m' or sys.argv[1] == '--maintenance':
                Command.configure_maintenance()
            elif sys.argv[1] == '-sm' or sys.argv[1] == '--stop-maintenance':
                Command.stop_maintenance()
            else:
                CLI.colored_print("Bad syntax. Try 'run.py --help'",
                                  CLI.COLOR_ERROR)
        else:
            run()

    except KeyboardInterrupt:
        CLI.colored_print('\nUser interrupted execution', CLI.COLOR_INFO)
