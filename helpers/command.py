# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import sys
import time
import subprocess

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.setup import Setup
from helpers.template import Template


class Command:

    @staticmethod
    def help():
        print(("Usage: python run.py [options]\n"
               "\n"
               "    Options:\n"
               "          -i, --info\n"
               "                Show KoBoToolbox Url and super user credentials\n"
               "          -l, --logs\n"
               "                Display docker logs\n"
               "          -b, --build\n"
               "                Build kpi and kobocat (only on dev/staging mode)\n"
               "          -bkf, --build-kpi\n"
               "                Build kpi (only on dev/staging mode)\n"
               "          -bkc, --build-kobocat\n"
               "                Build kobocat (only on dev/staging mode)\n"
               "          -s, --setup\n"
               "                Prompt questions to rebuild configuration. Restart KoBoToolbox\n"
               "          -S, --stop\n"
               "                Stop KoBoToolbox\n"
               "          -u, --update, --upgrade\n"
               "                Update KoBoToolbox\n"
               "          -cf, --compose-frontend [docker-compose arguments]\n"
               "                Run a docker-compose command in the front-end environment\n"
               "          -cb, --compose-backend [docker-compose arguments]\n"
               "                Run a docker-compose command in the back-end environment\n"
               "          -v, --version\n"
               "                Display current version\n"
               ))

    @classmethod
    def build(cls, image=None):
        """
        Builds kpi/kobocat images with `--no-caches` option
        Pulls latest `837577998611.dkr.ecr.us-west-2.amazonaws.com/kobotoolbox/koboform_base` as well

        :param image: str
        """
        config_object = Config()
        config = config_object.get_config()

        if config_object.dev_mode or config_object.staging_mode:

            def build_image(image_):
                frontend_command = ["docker-compose",
                                    "-f", "docker-compose.frontend.yml",
                                    "-f", "docker-compose.frontend.override.yml",
                                    "build", "--force-rm", "--no-cache",
                                    image_]

                if config.get("docker_prefix", "") != "":
                    frontend_command.insert(-4, "-p")
                    frontend_command.insert(-4, config.get("docker_prefix"))

                CLI.run_command(frontend_command, config.get("kobodocker_path"))

            pull_base_command = ["docker",
                                 "pull",
                                 "837577998611.dkr.ecr.us-west-2.amazonaws.com/kobotoolbox/koboform_base"]

            CLI.run_command(pull_base_command, config.get("kobodocker_path"))

            if image is None or image == "kf":
                config["kpi_dev_build_id"] = "{prefix}{timestamp}".format(
                    prefix="{}.".format(config.get("docker_prefix"))
                    if config.get("docker_prefix") else "",
                    timestamp=str(int(time.time()))
                )
                config_object.write_config()
                Template.render(config_object)
                build_image("kpi")

            if image is None or image == "kc":
                config["kc_dev_build_id"] = "{prefix}{timestamp}".format(
                    prefix="{}.".format(config.get("docker_prefix"))
                    if config.get("docker_prefix") else "",
                    timestamp=str(int(time.time()))
                )
                config_object.write_config()
                Template.render(config_object)
                build_image("kobocat")

    @classmethod
    def info(cls, timeout=600):
        config_object = Config()
        config = config_object.get_config()

        main_url = "{}://{}.{}{}".format(
            "https" if config.get("https") == Config.TRUE else "http",
            config.get("kpi_subdomain"),
            config.get("public_domain_name"),
            ":{}".format(config.get("exposed_nginx_docker_port")) if config.get("exposed_nginx_docker_port")
                                                                     and str(
                config.get("exposed_nginx_docker_port")) != Config.DEFAULT_NGINX_PORT else ""
        )

        stop = False
        start = int(time.time())
        success = False
        hostname = "{}.{}".format(config.get("kpi_subdomain"), config.get("public_domain_name"))
        nginx_port = int(Config.DEFAULT_NGINX_HTTPS_PORT) if config.get("https") == Config.TRUE \
            else int(config.get("exposed_nginx_docker_port", Config.DEFAULT_NGINX_PORT))
        https = config.get("https") == Config.TRUE
        already_retried = False
        while not stop:
            if Network.status_check(hostname, "/service_health/", nginx_port, https) == Network.STATUS_OK_200:
                stop = True
                success = True
            elif int(time.time()) - start >= timeout:
                if timeout > 0:
                    CLI.colored_print(
                        "\n`KoBoToolbox` has not started yet. This is can be normal with low CPU/RAM computers.\n",
                        CLI.COLOR_INFO)
                    CLI.colored_print("Wait for another {} seconds?".format(timeout), CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    response = CLI.get_response([Config.TRUE, Config.FALSE], Config.TRUE)

                    if response == Config.TRUE:
                        start = int(time.time())
                        continue
                    else:
                        if already_retried is False:
                            already_retried = True
                            CLI.colored_print(("\nSometimes frontend containers "
                                               "can not communicate with backend containers.\n"
                                               "Restarting the frontend containers usually fixes it.\n"),
                                              CLI.COLOR_INFO)
                            CLI.colored_print("Do you want to try?".format(timeout), CLI.COLOR_SUCCESS)
                            CLI.colored_print("\t1) Yes")
                            CLI.colored_print("\t2) No")
                            response = CLI.get_response([Config.TRUE, Config.FALSE], Config.TRUE)
                            if response == Config.TRUE:
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
            CLI.colored_print("KoBoToolbox could not start! Please try `python3 run.py --logs` to see the logs.", CLI.COLOR_ERROR)

        return success

    @classmethod
    def logs(cls):
        config_object = Config()
        config = config_object.get_config()

        if config_object.master_backend or config_object.slave_backend:
            backend_role = config.get("backend_server_role", "master")

            backend_command = ["docker-compose",
                               "-f", "docker-compose.backend.{}.yml".format(backend_role),
                               "-f", "docker-compose.backend.{}.override.yml".format(backend_role),
                               "logs", "-f"]
            if config.get("docker_prefix", "") != "":
                backend_command.insert(-2, "-p")
                backend_command.insert(-2, config.get("docker_prefix"))

            CLI.run_command(backend_command, config.get("kobodocker_path"), True)

        if config_object.frontend:
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "logs", "-f"]
            if config.get("docker_prefix", "") != "":
                frontend_command.insert(-2, "-p")
                frontend_command.insert(-2, config.get("docker_prefix"))

            CLI.run_command(frontend_command, config.get("kobodocker_path"), True)

    @classmethod
    def restart_frontend(cls):
        cls.start(frontend_only=True)

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
        ports = []
        if config_object.proxy:
            nginx_port = int(config.get("nginx_proxy_port", 80))
        else:
            nginx_port = int(config.get("exposed_nginx_docker_port", 80))

        if frontend_only or config_object.frontend or not config_object.multi_servers:
            ports.append(nginx_port)

        if not frontend_only or config_object.master_backend or config_object.slave_backend:
            ports.append(config.get("postgresql_port", 5432))
            ports.append(config.get("mongo_port", 27017))
            ports.append(config.get("redis_main_port", 6379))
            ports.append(config.get("redis_cache_port", 6380))

        for port in ports:
            if Network.is_port_open(port):
                CLI.colored_print("Port {} is already open. KoboToolbox can't start".format(port),
                                  CLI.COLOR_ERROR)
                sys.exit()

        # Make them up
        if not frontend_only:
            if (config.get("multi") == Config.TRUE and config.get("server_role") == "backend") or \
                    config.get("multi") != Config.TRUE:

                backend_role = config.get("backend_server_role", "master")

                backend_command = ["docker-compose",
                                   "-f", "docker-compose.backend.{}.yml".format(backend_role),
                                   "-f", "docker-compose.backend.{}.override.yml".format(backend_role),
                                   "up", "-d"]
                if config.get("docker_prefix", "") != "":
                    backend_command.insert(-2, "-p")
                    backend_command.insert(-2, config.get("docker_prefix"))

                CLI.run_command(backend_command, config.get("kobodocker_path"))

        if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
                config.get("multi") != Config.TRUE:
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "up", "-d"]

            if config.get("docker_prefix", "") != "":
                frontend_command.insert(-2, "-p")
                frontend_command.insert(-2, config.get("docker_prefix"))

            CLI.run_command(frontend_command, config.get("kobodocker_path"))

            # Start reverse proxy if user uses it.
            if config_object.use_letsencrypt:
                proxy_command = ["docker-compose",
                                 "up", "-d"]
                CLI.run_command(proxy_command, config_object.get_letsencrypt_repo_path())

        if not frontend_only:
            if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
                    config.get("multi") != Config.TRUE:
                CLI.colored_print("Waiting for environment to be ready. It can take a few minutes.", CLI.COLOR_SUCCESS)
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

        if not frontend_only:
            if (config.get("multi") == Config.TRUE and config.get("server_role") == "backend") or \
                    config.get("multi") != Config.TRUE:

                backend_role = config.get("backend_server_role", "master")

                backend_command = ["docker-compose",
                                   "-f", "docker-compose.backend.{}.yml".format(backend_role),
                                   "-f", "docker-compose.backend.{}.override.yml".format(backend_role),
                                   "down"]
                if config.get("docker_prefix", "") != "":
                    backend_command.insert(-1, "-p")
                    backend_command.insert(-1, config.get("docker_prefix"))
                CLI.run_command(backend_command, config.get("kobodocker_path"))

        if (config.get("multi") == Config.TRUE and config.get("server_role") == "frontend") or \
                config.get("multi") != Config.TRUE:
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "down"]
            if config.get("docker_prefix", "") != "":
                frontend_command.insert(-1, "-p")
                frontend_command.insert(-1, config.get("docker_prefix"))
            CLI.run_command(frontend_command, config.get("kobodocker_path"))

            # Stop reverse proxy if user uses it.
            if config_object.use_letsencrypt:
                proxy_command = ["docker-compose",
                                 "down"]
                CLI.run_command(proxy_command, config_object.get_letsencrypt_repo_path())

        if output:
            CLI.colored_print("KoBoToolbox has been stopped", CLI.COLOR_SUCCESS)

    @classmethod
    def upgrade(cls):
        config_object = Config()
        config = config_object.get_config()

        Setup.run(config)
        CLI.colored_print("KoBoToolbox has been upgraded", CLI.COLOR_SUCCESS)

        # update itself
        git_command = ["git", "pull", "origin", "shared-database-obsolete"]
        CLI.run_command(git_command)
        CLI.colored_print("KoBoInstall has been upgraded", CLI.COLOR_SUCCESS)

    @classmethod
    def version(cls):
        git_commit_version_command = ["git", "rev-parse", "HEAD"]
        stdout = CLI.run_command(git_commit_version_command)
        CLI.colored_print("KoBoInstall Version: {}".format(stdout.strip()[0:7]), CLI.COLOR_SUCCESS)

    @classmethod
    def compose_frontend(cls, args):
        config_object = Config()
        config = config_object.get_config()
        command = ["docker-compose",
                   "-f", "docker-compose.frontend.yml",
                   "-f", "docker-compose.frontend.override.yml"]
        if config.get("docker_prefix", "") != "":
            command.extend(['-p', config.get("docker_prefix")])
        command.extend(args)
        subprocess.call(command, cwd=config.get("kobodocker_path"))

    @classmethod
    def compose_backend(cls, args):
        config_object = Config()
        config = config_object.get_config()
        backend_role = config.get("backend_server_role", "master")
        command = [
            "docker-compose",
            "-f", "docker-compose.backend.{}.yml".format(backend_role),
            "-f", "docker-compose.backend.{}.override.yml".format(backend_role),
        ]
        if config.get("docker_prefix", "") != "":
            command.extend(['-p', config.get("docker_prefix")])
        command.extend(args)
        subprocess.call(command, cwd=config.get("kobodocker_path"))
