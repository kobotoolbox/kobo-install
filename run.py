# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import platform
import sys
import time

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.setup import Setup
from helpers.template import Template


def help():
    # TODO - Display help in console
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

        #__start_env(current_config)

def upgrade():
    # TODO - upgrade kobo-install && kobo-docker repo
    pass

def __start_env(config):
    main_url = "{}://{}.{}{}".format(
        "https" if config.get("https") == Config.TRUE else "http",
        config.get("kpi_subdomain"),
        config.get("public_domain_name"),
        ":{}".format(config.get("nginx_port")) if config.get("nginx_port")
                                                  and str(config.get("nginx_port")) != "80" else ""
    )
    CLI.colored_print("Launching environment", CLI.COLOR_SUCCESS)

    # Stop containers first
    if (config.get("multi") == Config.TRUE and config.get("server_role") == "backend") or \
            config.get("multi") != Config.TRUE:
        backend_command = ["docker-compose",
                           "-f", "docker-compose.backend.master.yml",
                           "-f", "docker-compose.backend.master.override.yml",
                           "down"]
        CLI.run_command(backend_command, config.get("kobodocker_path"))

    if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
            config.get("multi") != Config.TRUE:
        frontend_command = ["docker-compose",
                            "-f", "docker-compose.frontend.yml",
                            "-f", "docker-compose.frontend.override.yml",
                            "down"]
        CLI.run_command(frontend_command, config.get("kobodocker_path"))

    # Test if ports are available
    nginx_port = int(config.get("nginx_port", 80))
    ports = [nginx_port, 6379, 6380, 5672, 27017, 5432]
    for port in ports:
        if Network.is_port_open(port):
            CLI.colored_print("Port {} is already open. KoboToolbox can't start".format(port),
                              CLI.COLOR_ERROR)
            sys.exit()

    # Make them up
    if (config.get("multi") == Config.TRUE and config.get("server_role") == "backend") or \
            config.get("multi") != Config.TRUE:
        backend_command = ["docker-compose",
                           "-f", "docker-compose.backend.master.yml",
                           "-f", "docker-compose.backend.master.override.yml",
                           "up", "-d"]
        CLI.run_command(backend_command, config.get("kobodocker_path"))

    if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
            config.get("multi") != Config.TRUE:
        frontend_command = ["docker-compose",
                           "-f", "docker-compose.frontend.yml",
                           "-f", "docker-compose.frontend.override.yml",
                           "up", "-d"]
        CLI.run_command(frontend_command, config.get("kobodocker_path"))

    if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
            config.get("multi") != Config.TRUE:
        CLI.colored_print("Waiting for environment to be ready", CLI.COLOR_SUCCESS)
        stop = False
        start = int(time.time())
        success = False
        hostname = "{}.{}".format(config.get("kpi_subdomain"), config.get("public_domain_name"))
        while not stop:
            if Network.status_check(hostname, "/service_health/", nginx_port) == Network.STATUS_OK_200:
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
            username = config.get("super_user_username")
            password = config.get("super_user_password")
            username_chars_count = len(username) + 6
            password_chars_count = len(password) + 10
            url_chars_count = len(main_url) + 6
            max_chars_count = max(username_chars_count, password_chars_count, url_chars_count)

            CLI.colored_print("╔═{}═╗".format("═" * max_chars_count), CLI.COLOR_WARNING)
            CLI.colored_print("║ Ready {} ║".format(
                " " * (max_chars_count - len("Ready "))), CLI.COLOR_WARNING)
            CLI.colored_print("║ URL: {}/{} ║".format(
                main_url, " " * (max_chars_count - url_chars_count)), CLI.COLOR_WARNING)
            CLI.colored_print("║ User: {}{} ║".format(
                username, " " * (max_chars_count - username_chars_count)), CLI.COLOR_WARNING)
            CLI.colored_print("║ Password: {}{} ║".format(
                password, " " * (max_chars_count - password_chars_count)), CLI.COLOR_WARNING)
            CLI.colored_print("╚═{}═╝".format("═" * max_chars_count), CLI.COLOR_WARNING)
        else:
            CLI.colored_print("Something went wrong! Please look at docker logs", CLI.COLOR_ERROR)
    else:
        CLI.colored_print(("Backend server should be up & running! "
                          "Please look at docker logs for further information"), CLI.COLOR_WARNING)

if __name__ == "__main__":

    if len(sys.argv) > 2:
        CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            help()
        if sys.argv[1] == "-u" or sys.argv[1] == "--upgrade":
            upgrade()
        elif sys.argv[1] == "-s" or sys.argv[1] == "--setup":
            run(force_setup=True)
        else:
            CLI.colored_print("Bad syntax. Try 'run.py --help'", CLI.COLOR_ERROR)
    else:
        run()