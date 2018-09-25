# -*- coding: utf-8 -*-

import platform
import sys

from helpers.cli import CLI
from helpers.config import Config
from helpers.setup import Setup
from helpers.template import Template


def help():
    # TODO
    pass

def run(force_setup=False):

    if not platform.system() in ["Linux", "Darwin"]:
        CLI.colored_print("Not compatible with this OS", CLI.COLOR_ERROR)
    else:
        config = Config()
        current_config = config.get_config()
        if not current_config:
            force_setup = True

        if force_setup:
            current_config = config.build()
            Setup.run(current_config)

        Template.render(current_config)
        Setup.update_hosts(current_config)
        __start_env(current_config)

def __start_env(config):
    main_url = "{}://{}.{}".format(
        "https" if config.get("https") == Config.TRUE else "http",
        config.get("kpi_subdomain"),
        config.get("public_domain_name")
    )
    char_count = len(main_url)
    CLI.colored_print("Launching environment...", CLI.COLOR_SUCCESS)
    backend_command = ["docker-compose", "-f", "docker-compose.backend.master.yml", "up", "-d"]
    CLI.run_command(backend_command, config.get("kobodocker_path"))

    frontend_command = ["docker-compose",
                       "-f",
                       "docker-compose.frontend.yml",
                       "-f",
                       "docker-compose.frontend.override.yml",
                       "up", "-d"]
    CLI.run_command(frontend_command, config.get("kobodocker_path"))
    CLI.colored_print("Environment is launched!", CLI.COLOR_SUCCESS)
    CLI.colored_print("╔══════{}══╗".format("═" * char_count), CLI.COLOR_WARNING)
    CLI.colored_print("║ URL: {}/ ║".format(main_url), CLI.COLOR_WARNING)
    CLI.colored_print("╚══════{}══╝".format("═" * char_count), CLI.COLOR_WARNING)
    CLI.colored_print("It takes up to 5 minutes to all services to be ready", CLI.COLOR_SUCCESS)

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