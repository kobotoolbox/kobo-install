# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import sys
import time

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.setup import Setup


class Command:

    @staticmethod
    def help():
        print(("Usage: python run.py [options]\n"
               "\n"
               "    Options:\n"
               "          -i, --info\n"
               "                Show KoBoToolbox Url and super user credentials\n"
               "          -s, --setup\n"
               "                Prompt questions to rebuild configuration. Restart KoBoToolbox\n"
               "          -S, --stop\n"
               "                Stop KoBoToolbox\n"
               "          -u, --upgrade\n"
               "                Upgrade KoBoToolbox\n"
               ))

    @classmethod
    def info(cls, timeout=5*60):
        config_object = Config()
        config = config_object.get_config()

        main_url = "{}://{}.{}{}".format(
            "https" if config.get("https") == Config.TRUE else "http",
            config.get("kpi_subdomain"),
            config.get("public_domain_name"),
            ":{}".format(config.get("exposed_nginx_docker_port")) if config.get("exposed_nginx_docker_port")
                                                      and str(config.get("exposed_nginx_docker_port")) != "80" else ""
        )

        stop = False
        start = int(time.time())
        success = False
        hostname = "{}.{}".format(config.get("kpi_subdomain"), config.get("public_domain_name"))
        nginx_port = 443 if config.get("https") == Config.TRUE else int(config.get("exposed_nginx_docker_port", "80"))
        already_retried = False
        while not stop:
            if Network.status_check(hostname, "/service_health/", nginx_port) == Network.STATUS_OK_200:
                stop = True
                success = True
            elif int(time.time()) - start >= timeout:
                if timeout > 0:
                    if config_object.first_time:
                        CLI.colored_print("`KoBoToolbox` has not started yet, try for another {} minutes".format(timeout), CLI.COLOR_INFO)
                        start = int(time.time())
                    else:
                        # sometimes frontend can not communicate with backend. docker-compose down/up fixes it.
                        if not already_retried:
                            CLI.colored_print(("`KoBoToolbox` has not started yet, sometimes frontend containers"
                                               "can not communicate with backend containers.\n"
                                               "Let's restart frontend containers.\n"),
                                              CLI.COLOR_INFO)
                            already_retried = True
                            start = int(time.time())
                            cls.restart_frontend()
                            continue
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

        return success

    @classmethod
    def restart_frontend(cls):
        cls.start()

    @classmethod
    def start(cls, frontend_only=False):
        config_object = Config()
        config = config_object.get_config()
        
        cls.stop(output=False, frontend_only=frontend_only)
        if frontend_only:
            CLI.colored_print("Launching frontend containers", CLI.COLOR_SUCCESS)
        else:
            CLI.colored_print("Launching environment", CLI.COLOR_SUCCESS)

        # Test if ports are available
        nginx_port = int(config.get("exposed_nginx_docker_port", 80))
        if not frontend_only:
            ports = [nginx_port, 6379, 6380, 5672, 27017, 5432]
        else:
            ports = [nginx_port]

        for port in ports:
            if Network.is_port_open(port):
                CLI.colored_print("Port {} is already open. KoboToolbox can't start".format(port),
                                  CLI.COLOR_ERROR)
                sys.exit()

        # Make them up
        if not frontend_only:
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

        if not frontend_only:
            if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
                    config.get("multi") != Config.TRUE:
                CLI.colored_print("Waiting for environment to be ready", CLI.COLOR_SUCCESS)
                cls.info()
            else:
                CLI.colored_print(("Backend server should be up & running! "
                                   "Please look at docker logs for further information"), CLI.COLOR_WARNING)

    @classmethod
    def stop(cls, output=True, frontend_only=False):
        """
        Stop containers
        """
        config_object = Config()
        config = config_object.get_config()

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

        if output:
            CLI.colored_print("KoBoToolbox has been stopped", CLI.COLOR_SUCCESS)

    @classmethod
    def upgrade(cls):
        config_object = Config()
        config = config_object.get_config()

        Setup.run(config)
        CLI.colored_print("KoBoToolbox has been upgraded", CLI.COLOR_SUCCESS)
