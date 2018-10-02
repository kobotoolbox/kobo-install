# -*- coding: utf-8 -*-
from __future__ import print_function

import platform
import sys
import time

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
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
        else:
            if config.auto_detect_network():
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
    CLI.colored_print("Launching environment", CLI.COLOR_SUCCESS)
    # Stop containers first
    backend_command = ["docker-compose", "-f", "docker-compose.backend.master.yml", "down"]
    CLI.run_command(backend_command, config.get("kobodocker_path"))
    frontend_command = ["docker-compose",
                        "-f",
                        "docker-compose.frontend.yml",
                        "-f",
                        "docker-compose.frontend.override.yml",
                        "down"]
    CLI.run_command(frontend_command, config.get("kobodocker_path"))

    # Make them up
    backend_command = ["docker-compose", "-f", "docker-compose.backend.master.yml", "up", "-d"]
    CLI.run_command(backend_command, config.get("kobodocker_path"))
    frontend_command = ["docker-compose",
                       "-f",
                       "docker-compose.frontend.yml",
                       "-f",
                       "docker-compose.frontend.override.yml",
                       "up", "-d"]
    CLI.run_command(frontend_command, config.get("kobodocker_path"))
    CLI.colored_print("Waiting for environment to be ready", CLI.COLOR_SUCCESS)
    stop = False
    start = int(time.time())
    success = False
    hostname = "{}.{}".format(config.get("kpi_subdomain"), config.get("public_domain_name"))
    while not stop:
        if Network.status_check(hostname, "/service_health/") == Network.STATUS_OK_200:
            stop = True
            success = True
        elif int(time.time()) - start >= 5 * 60:
            stop = True
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(10)

    # Create a new line
    print("")

    if success:
        CLI.colored_print("╔══════{}══╗".format("═" * char_count), CLI.COLOR_WARNING)
        CLI.colored_print("║ Ready {} ║".format(" " * char_count), CLI.COLOR_WARNING)
        CLI.colored_print("║ URL: {}/ ║".format(main_url), CLI.COLOR_WARNING)
        CLI.colored_print("╚══════{}══╝".format("═" * char_count), CLI.COLOR_WARNING)
    else:
        CLI.colored_print("Something went wrong! Please look at docker logs", CLI.COLOR_ERROR)

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