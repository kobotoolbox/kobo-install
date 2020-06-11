# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import sys
import time
import subprocess

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.template import Template
from helpers.upgrading import migrate_single_to_two_databases


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
               "          -m, --maintenance\n"
               "                Activate maintenance mode. All traffic is redirected to maintenance page\n"
               "          -v, --version\n"
               "                Display current version\n"
               ))

    @classmethod
    def build(cls, image=None):
        """
        Builds kpi/kobocat images with `--no-caches` option
        Pulls latest `kobotoolbox/koboform_base` as well

        :param image: str
        """
        config_object = Config()
        config = config_object.get_config()

        if config_object.dev_mode or config_object.staging_mode:

            def build_image(image_):
                frontend_command = ["docker-compose",
                                    "-f", "docker-compose.frontend.yml",
                                    "-f", "docker-compose.frontend.override.yml",
                                    "-p", config_object.get_prefix("frontend"),
                                    "build", "--force-rm", "--no-cache",
                                    image_]

                CLI.run_command(frontend_command, config.get("kobodocker_path"))

            if image is None or image == "kf":
                config["kpi_dev_build_id"] = "{prefix}{timestamp}".format(
                    prefix=config_object.get_prefix("frontend"),
                    timestamp=str(int(time.time()))
                )
                config_object.write_config()
                Template.render(config_object)
                build_image("kpi")

            if image is None or image == "kc":
                pull_base_command = ["docker",
                                     "pull",
                                     "kobotoolbox/koboform_base"]

                CLI.run_command(pull_base_command, config.get("kobodocker_path"))

                config["kc_dev_build_id"] = "{prefix}{timestamp}".format(
                    prefix=config_object.get_prefix("frontend"),
                    timestamp=str(int(time.time()))
                )
                config_object.write_config()
                Template.render(config_object)
                build_image("kobocat")

    @classmethod
    def compose_frontend(cls, args):
        config_object = Config()
        config = config_object.get_config()
        command = ["docker-compose",
                   "-f", "docker-compose.frontend.yml",
                   "-f", "docker-compose.frontend.override.yml",
                   "-p", config_object.get_prefix("frontend")]
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
            "-p", config_object.get_prefix("backend")
        ]
        command.extend(args)
        subprocess.call(command, cwd=config.get("kobodocker_path"))

    @classmethod
    def info(cls, timeout=600):
        config_object = Config()
        config = config_object.get_config()

        main_url = "{}://{}.{}{}".format(
            "https" if config.get("https") == Config.TRUE else "http",
            config.get("kpi_subdomain"),
            config.get("public_domain_name"),
            ":{}".format(config.get("exposed_nginx_docker_port")) if (
                    config.get("exposed_nginx_docker_port") and
                    str(config.get("exposed_nginx_docker_port")) != Config.DEFAULT_NGINX_PORT
            ) else ""
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
            CLI.colored_print("╚═{}═╝".format(c), CLI.COLOR_WARNING)
        else:
            CLI.colored_print("KoBoToolbox could not start! "
                              "Please try `python3 run.py --logs` to see the logs.",
                              CLI.COLOR_ERROR)

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
                               "-p", config_object.get_prefix("backend"),
                               "logs", "-f"]
            CLI.run_command(backend_command, config.get("kobodocker_path"), True)

        if config_object.frontend:
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "-p", config_object.get_prefix("frontend"),
                                "logs", "-f"]
            CLI.run_command(frontend_command, config.get("kobodocker_path"), True)

    @classmethod
    def configure_maintenance(cls):
        config_object = Config()
        config = config_object.get_config()

        if not config_object.multi_servers or config_object.frontend:

            config_object.maintenance()
            Template.render_maintenance(config_object)
            config['maintenance_enabled'] = True
            config_object.write_config()
            cls.stop_nginx()
            cls.start_maintenance()

    @classmethod
    def stop_nginx(cls):
        config_object = Config()
        config = config_object.get_config()

        nginx_stop_command = ["docker-compose",
                              "-f", "docker-compose.frontend.yml",
                              "-f", "docker-compose.frontend.override.yml",
                              "-p", config_object.get_prefix("frontend"),
                              "stop", "nginx"]

        CLI.run_command(nginx_stop_command, config.get("kobodocker_path"))

    @classmethod
    def start_maintenance(cls):
        config_object = Config()
        config = config_object.get_config()

        frontend_command = ["docker-compose",
                            "-f", "docker-compose.maintenance.yml",
                            "-f", "docker-compose.maintenance.override.yml",
                            "-p", config_object.get_prefix("maintenance"),
                            "up", "-d", "maintenance"]

        CLI.run_command(frontend_command, config.get("kobodocker_path"))
        CLI.colored_print("Maintenance mode has been started",
                          CLI.COLOR_SUCCESS)

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

        if frontend_only or config_object.frontend or \
                not config_object.multi_servers:
            ports.append(nginx_port)

        if (not frontend_only or config_object.master_backend or
                config_object.slave_backend) and \
                config_object.expose_backend_ports:
            ports.append(config.get("postgresql_port", 5432))
            ports.append(config.get("mongo_port", 27017))
            ports.append(config.get("redis_main_port", 6379))
            ports.append(config.get("redis_cache_port", 6380))

        for port in ports:
            if Network.is_port_open(port):
                CLI.colored_print("Port {} is already open. "
                                  "KoboToolbox can't start".format(port),
                                  CLI.COLOR_ERROR)
                sys.exit(1)

        # Start the back-end containers
        if not frontend_only:
            if not config_object.multi_servers or \
                    config_object.master_backend or config_object.slave_backend:
                backend_role = config.get("backend_server_role", "master")

                backend_command = ["docker-compose",
                                   "-f",
                                   "docker-compose.backend.{}.yml".format(
                                       backend_role),
                                   "-f",
                                   "docker-compose.backend.{}.override.yml".format(
                                       backend_role),
                                   "-p", config_object.get_prefix("backend"),
                                   "up", "-d"]
                CLI.run_command(backend_command, config.get("kobodocker_path"))

        # If this was previously a shared-database setup, migrate to separate
        # databases for KPI and KoBoCAT
        migrate_single_to_two_databases()

        # Start the front-end containers
        if not config_object.multi_servers or config_object.frontend:
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "-p", config_object.get_prefix("frontend"),
                                "up", "-d"]

            if config.get('maintenance_enabled', False):
                cls.start_maintenance()
                # Start all front-end services except the non-maintenance NGINX
                frontend_command.extend([
                    s for s in config_object.get_service_names() if s != 'nginx'
                ])

            CLI.run_command(frontend_command, config.get("kobodocker_path"))

            # Start reverse proxy if user uses it.
            if config_object.use_letsencrypt:
                proxy_command = ["docker-compose",
                                 "up", "-d"]
                CLI.run_command(proxy_command,
                                config_object.get_letsencrypt_repo_path())

        if config.get('maintenance_enabled', False):
                CLI.colored_print("Maintenance mode is enabled. To resume "
                                  "normal operation, use `--stop-maintenance`",
                                  CLI.COLOR_INFO)
        elif not frontend_only:
            if not config_object.multi_servers or config_object.frontend:
                CLI.colored_print("Waiting for environment to be ready. "
                                  "It can take a few minutes.", CLI.COLOR_SUCCESS)
                cls.info()
            else:
                CLI.colored_print(("Backend server should be up & running! "
                                   "Please look at docker logs for further "
                                   "information"), CLI.COLOR_WARNING)

    @classmethod
    def stop(cls, output=True, frontend_only=False):
        """
        Stop containers
        """
        config_object = Config()
        config = config_object.get_config()

        if not config_object.multi_servers or config_object.frontend:
            # Shut down maintenance container in case it's up&running
            maintenance_down_command = [
                "docker-compose",
                "-f", "docker-compose.maintenance.yml",
                "-f", "docker-compose.maintenance.override.yml",
                "-p", config_object.get_prefix("maintenance"),
                "down"]

            CLI.run_command(maintenance_down_command,
                            config.get("kobodocker_path"))

            # Shut down frontend containers
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "-p", config_object.get_prefix("frontend"),
                                "down"]
            CLI.run_command(frontend_command, config.get("kobodocker_path"))

            # Stop reverse proxy if user uses it.
            if config_object.use_letsencrypt:
                proxy_command = ["docker-compose",
                                 "down"]
                CLI.run_command(proxy_command, config_object.get_letsencrypt_repo_path())

        if not frontend_only:
            if not config_object.multi_servers or config_object.master_backend:

                backend_role = config.get("backend_server_role", "master")

                backend_command = [
                    "docker-compose",
                    "-f",
                    "docker-compose.backend.{}.yml".format(backend_role),
                    "-f",
                    "docker-compose.backend.{}.override.yml".format(backend_role),
                    "-p", config_object.get_prefix("backend"),
                    "down"
                ]
                CLI.run_command(backend_command, config.get("kobodocker_path"))

        if output:
            CLI.colored_print("KoBoToolbox has been stopped", CLI.COLOR_SUCCESS)

    @classmethod
    def stop_maintenance(cls):
        """
        Stop containers
        """
        config_object = Config()
        config = config_object.get_config()

        if not config_object.multi_servers or config_object.frontend:
            # Shut down maintenance container in case it's up&running
            maintenance_down_command = [
                "docker-compose",
                "-f", "docker-compose.maintenance.yml",
                "-f", "docker-compose.maintenance.override.yml",
                "-p", config_object.get_prefix("maintenance"),
                "down"]

            CLI.run_command(maintenance_down_command,
                            config.get("kobodocker_path"))

            # Create and start NGINX container
            frontend_command = ["docker-compose",
                                "-f", "docker-compose.frontend.yml",
                                "-f", "docker-compose.frontend.override.yml",
                                "-p", config_object.get_prefix("frontend"),
                                "up", "-d", "nginx"]
            CLI.run_command(frontend_command, config.get("kobodocker_path"))

            CLI.colored_print("Maintenance mode has been stopped",
                              CLI.COLOR_SUCCESS)

            config['maintenance_enabled'] = False
            config_object.write_config()

    @classmethod
    def version(cls):
        git_commit_version_command = ["git", "rev-parse", "HEAD"]
        stdout = CLI.run_command(git_commit_version_command)

        CLI.colored_print("KoBoInstall Version: {} (build {})".format(
            Config.KOBO_INSTALL_VERSION,
            stdout.strip()[0:7],
        ), CLI.COLOR_SUCCESS)
