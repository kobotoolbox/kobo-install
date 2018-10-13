# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import os
from random import choice, randint
import re
import stat
import string
import sys
import time

from helpers.cli import CLI
from helpers.network import Network
from helpers.singleton import Singleton


class Config:

    CONFIG_FILE = ".run.conf"
    TRUE = "1"
    FALSE = "2"

    # Maybe overkill. Use this class as a singleton to get the same configuration
    # for each instantiation.
    __metaclass__ = Singleton

    def __init__(self):
        self.__config = self.read_config()

    def auto_detect_network(self):
        changed = False
        if self.__config.get("local_installation") == Config.TRUE:
            local_interfaces = Network.get_local_interfaces(all=True)
            if self.__config.get("local_interface_ip") not in local_interfaces.values():
                self.__detect_network()
                self.write_config()
                changed = True
        return changed

    def build(self):

        primary_ip = Network.get_primary_ip()

        if not primary_ip:
            CLI.colored_print("╔══════════════════════════════════════════════════════╗", CLI.COLOR_ERROR)
            CLI.colored_print("║ No valid networks detected. Can not continue!        ║", CLI.COLOR_ERROR)
            CLI.colored_print("║ Please connect to a network and re-run the command.  ║", CLI.COLOR_ERROR)
            CLI.colored_print("╚══════════════════════════════════════════════════════╝", CLI.COLOR_ERROR)
            sys.exit()
        else:
            config = {
                "workers_max": "2",
                "workers_start": "1",
                "debug": Config.FALSE,
                "kobodocker_path": os.path.realpath("{}/../../kobo-docker".format(
                    os.path.dirname(os.path.realpath(__file__)))
                ),
                "public_domain_name": "kobo.local",
                "kpi_subdomain": "kpi",
                "kc_subdomain": "kc",
                "ee_subdomain": "ee",
                "postgres_db": "kobotoolbox",
                "postgres_user": "kobo",
                "postgres_password": "kobo",
                "private_domain_name": "docker.internal",
                "kc_path": "",
                "kpi_path": "",
                "super_user_username": "super_admin",
                "super_user_password": self.__generate_password(),
                "use_aws": Config.FALSE,
                "use_private_dns": Config.FALSE,
                "master_backend_ip": primary_ip,
                "local_interface_ip": primary_ip,
                "multi": Config.FALSE
            }

            first_time = self.__config.get("date_created") is None
            config.update(self.__config)
            # Avoid asking questions related to frontend, if role is only for backend
            frontend_questions = config.get("multi") == Config.FALSE or config.get("server_role") == "frontend"

            self.__config = config
            self.__create_directory()

            CLI.colored_print("Do you want to see advanced options?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            self.__config["advanced"] = CLI.get_response([Config.TRUE, Config.FALSE], config.get("advanced", Config.FALSE))

            CLI.colored_print("What kind of installation do you need?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) On your workstation")
            CLI.colored_print("\t2) On a server")
            self.__config["local_installation"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                   config.get("local_installation", Config.FALSE))
            if config.get("local_installation") == Config.FALSE:

                if config.get("advanced") == Config.TRUE:
                    CLI.colored_print("Do you want to use separate servers for frontend and backend?",
                                      CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    self.__config["multi"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                              config.get("multi", Config.FALSE))

                    if config.get("multi") == Config.TRUE:
                        CLI.colored_print("Which role do you want to assign to this server?", CLI.COLOR_SUCCESS)
                        CLI.colored_print("\t1) frontend")
                        CLI.colored_print("\t2) backend")
                        self.__config["server_role"] = CLI.get_response(["backend", "frontend"],
                                                                        config.get("server_role", "frontend"))

                        if self.__config.get("server_role") == "frontend":
                            frontend_questions = True
                            CLI.colored_print("Do you use DNS for private routes?", CLI.COLOR_SUCCESS)
                            CLI.colored_print("\t1) Yes")
                            CLI.colored_print("\t2) No")

                            self.__config["use_private_dns"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                                config.get("use_private_dns", Config.FALSE))

                            if self.__config["use_private_dns"] == Config.FALSE:
                                CLI.colored_print("IP address (IPv4) of backend server?", CLI.COLOR_SUCCESS)
                                self.__config["master_backend_ip"] = CLI.get_response(
                                    "~\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
                                    config.get("master_backend_ip", primary_ip))
                            else:
                                self.__config["private_domain_name"] = CLI.colored_input("Private domain name",
                                                                                         CLI.COLOR_SUCCESS,
                                                                                         config.get("private_domain_name", ""))
                        else:
                            frontend_questions = False

                if frontend_questions:
                    self.__config["public_domain_name"] = CLI.colored_input("Public domain name", CLI.COLOR_SUCCESS,
                                                                            config.get("public_domain_name", ""))
                    self.__config["kpi_subdomain"] = CLI.colored_input("KPI sub domain", CLI.COLOR_SUCCESS,
                                                                       config.get("kpi_subdomain", ""))
                    self.__config["kc_subdomain"] = CLI.colored_input("KoBoCat sub domain", CLI.COLOR_SUCCESS,
                                                                      config.get("kc_subdomain", ""))
                    self.__config["ee_subdomain"] = CLI.colored_input("Enketo Express sub domain name",
                                                                      CLI.COLOR_SUCCESS,
                                                                      config.get("ee_subdomain", ""))

                    CLI.colored_print("Use HTTPS?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("Please note that certificate has to be installed on a load balancer!",
                                      CLI.COLOR_INFO)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    self.__config["https"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                              config.get("https", Config.TRUE))
            else:
                # Reset previous choices, in case server role is not the same.
                self.__config["multi"] = Config.FALSE
                self.__config["use_private_dns"] = Config.FALSE
                frontend_questions = True

                self.__detect_network()

            if frontend_questions:
                # SMTP.
                self.__config["smtp_host"] = CLI.colored_input("SMTP server", CLI.COLOR_SUCCESS, config.get("smtp_host"))
                self.__config["smtp_port"] = CLI.colored_input("SMTP port", CLI.COLOR_SUCCESS, config.get("smtp_port", "25"))
                self.__config["smtp_user"] = CLI.colored_input("SMTP user", CLI.COLOR_SUCCESS, config.get("smtp_user", ""))
                if self.__config.get("smtp_user"):
                    self.__config["smtp_password"] = CLI.colored_input("SMTP password", CLI.COLOR_SUCCESS,
                                                                       config.get("smtp_password"))
                    CLI.colored_print("Use TLS?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) True")
                    CLI.colored_print("\t2) False")
                    self.__config["smtp_use_tls"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                     config.get("smtp_use_tls", Config.TRUE))
                self.__config["default_from_email"] = CLI.colored_input("From email address", CLI.COLOR_SUCCESS,
                                                                        "support@{}".format(
                                                                            self.__config.get("public_domain_name")))

                # Super user. Only ask for credentials the first time.
                # Super user is created if db doesn't exists.
                username = CLI.colored_input("Super user's username", CLI.COLOR_SUCCESS,
                                             config.get("super_user_username"))
                password = CLI.colored_input("Super user's password", CLI.COLOR_SUCCESS,
                                             config.get("super_user_password"))

                if (username != config.get("super_user_username") or password != config.get("super_user_password")) and \
                        not first_time:
                    CLI.colored_print("╔══════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
                    CLI.colored_print("║ Username or password have been changed!              ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ Don't forget to apply these changes in Postgres too. ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ Super user's credentials won't be updated if the     ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ database already exists.                             ║", CLI.COLOR_WARNING)
                    CLI.colored_print("╚══════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)

                self.__config["super_user_username"] = username
                self.__config["super_user_password"] = password

            if config.get("advanced") == Config.TRUE:

                # Dev Mode
                if frontend_questions and config.get("local_installation") == Config.TRUE:
                    #NGinX different port
                    CLI.colored_print("Web server port?", CLI.COLOR_SUCCESS)
                    self.__config["nginx_port"] = CLI.get_response("~\d+",
                                                                config.get("nginx_port", "80"))

                    CLI.colored_print("Developer mode?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    self.__config["dev_mode"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                config.get("dev_mode", Config.FALSE))
                    if self.__config["dev_mode"] == Config.TRUE:
                        CLI.colored_print("╔═══════════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
                        CLI.colored_print("║ Where are the files located locally? It can be absolute   ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║ or relative to the directory of the installation.         ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║ Leave empty if you don't need to overload the repository. ║", CLI.COLOR_WARNING)
                        CLI.colored_print("╚═══════════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)
                        self.__config["kc_path"] = CLI.colored_input("KoBoCat files location", CLI.COLOR_SUCCESS,
                                                                            config.get("kc_path"))
                        self.__config["kpi_path"] = CLI.colored_input("KPI files location", CLI.COLOR_SUCCESS,
                                                                            config.get("kpi_path"))
                    else:
                        # Force reset paths
                        self.__config["kc_path"] = ""
                        self.__config["kpi_path"] = ""
                else:
                    # Force reset paths
                    self.__config["dev_mode"] = Config.FALSE
                    self.__config["kc_path"] = ""
                    self.__config["kpi_path"] = ""

                # DB
                self.__config["postgres_db"] = CLI.colored_input("Postgres database", CLI.COLOR_SUCCESS,
                                                                 config.get("postgres_db"))
                self.__config["postgres_user"] = CLI.colored_input("Postgres user", CLI.COLOR_SUCCESS,
                                                                   config.get("postgres_user"))
                self.__config["postgres_password"] = CLI.colored_input("Postgres password", CLI.COLOR_SUCCESS,
                                                                       config.get("postgres_password"))
                if frontend_questions:
                    # AWS
                    CLI.colored_print("Use AWS?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    self.__config["use_aws"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                config.get("use_aws", Config.FALSE))
                    if self.__config["use_aws"] == Config.TRUE:
                        self.__config["aws_access_key"] = CLI.colored_input("AWS Access Key", CLI.COLOR_SUCCESS,
                                                                            config.get("aws_access_key", ""))
                        self.__config["aws_secret_key"] = CLI.colored_input("AWS Secret Key", CLI.COLOR_SUCCESS,
                                                                            config.get("aws_secret_key", ""))
                        self.__config["aws_bucket_name"] = CLI.colored_input("AWS Bucket name", CLI.COLOR_SUCCESS,
                                                                             config.get("aws_bucket_name", ""))

                    CLI.colored_print("Number of uWSGi workers to start?", CLI.COLOR_SUCCESS)
                    self.__config["workers_start"] = CLI.get_response(
                        "~\d+",
                        config.get("workers_start", "4"))
                    CLI.colored_print("Max uWSGi workers?", CLI.COLOR_SUCCESS)
                    self.__config["workers_max"] = CLI.get_response(
                        "~\d+",
                        config.get("workers_max", "2"))

                    # Google Analytics
                    self.__config["google_ua"] = CLI.colored_input("Google Analytics Identifier", CLI.COLOR_SUCCESS,
                                                                   config.get("google_ua", ""))

                    # Google API Key
                    self.__config["google_api_key"] = CLI.colored_input("Google API Key", CLI.COLOR_SUCCESS,
                                                                        config.get("google_api_key", ""))

                    # Intercom
                    self.__config["intercom"] = CLI.colored_input("Intercom", CLI.COLOR_SUCCESS, config.get("intercom", ""))

                    # Raven
                    self.__config["kpi_raven"] = CLI.colored_input("KPI Raven token", CLI.COLOR_SUCCESS,
                                                                   config.get("kpi_raven", ""))
                    self.__config["kobocat_raven"] = CLI.colored_input("KoBoCat Raven token", CLI.COLOR_SUCCESS,
                                                                       config.get("kobocat_raven", ""))
                    self.__config["kpi_raven_js"] = CLI.colored_input("KPI Raven JS token", CLI.COLOR_SUCCESS,
                                                                      config.get("kpi_raven_js", ""))

                    # Debug
                    CLI.colored_print("Enable DEBUG?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("Not RECOMMENDED on production!", CLI.COLOR_ERROR)
                    CLI.colored_print("\t1) True")
                    CLI.colored_print("\t2) False")
                    self.__config["debug"] = CLI.get_response([Config.TRUE, Config.FALSE], config.get("debug", Config.FALSE))

            # If first time
            backend_questions = config.get("multi") != Config.TRUE or config.get("server_role") != "frontend"
            if first_time and backend_questions:
                mongo_dir_path = "{}/.vols/mongo".format(self.__config["kobodocker_path"])
                postgres_dir_path = "{}/.vols/db".format(self.__config["kobodocker_path"])
                mongo_data_exists = (os.path.exists(mongo_dir_path) and os.path.isdir(mongo_dir_path) and
                    os.listdir(mongo_dir_path))
                postgres_data_exists = os.path.exists(postgres_dir_path) and os.path.isdir(postgres_dir_path)

                if mongo_data_exists or postgres_data_exists:
                    unknown_mongo_version = self.__is_db_image_version_unknown(
                        "mongo", "kobotoolbox/mongo:latest")
                    unknown_postgres_version = self.__is_db_image_version_unknown(
                        "postgres", "kobotoolbox/postgres:latest")

                    if unknown_mongo_version or unknown_postgres_version:
                        self.__config["overload_backend"] = False
                        CLI.colored_print("╔═══════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
                        CLI.colored_print("║ Existing data detected, but could not detect docker   ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║ images.                                               ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║                                                       ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║ MongoDB and PostgresSQL images must be:               ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║    - mongo:3.4                                        ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║    - mdillon/postgis:9.5                              ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║                                                       ║", CLI.COLOR_WARNING)
                        CLI.colored_print("║ Be sure to match these versions before going further! ║", CLI.COLOR_WARNING)
                        CLI.colored_print("╚═══════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)
                        CLI.colored_print("Do you want to continue?", CLI.COLOR_SUCCESS)
                        CLI.colored_print("\tyes")
                        CLI.colored_print("\tno")
                        response = CLI.get_response(["yes", "no"], "no")
                        if response == "no":
                            sys.exit()
                    else:
                        self.__config["overload_backend"] = True

            self.__config = config
            self.write_config()
            return config

    def get_config(self):
        return self.__config

    def read_config(self):
        config = {}
        try:
            with open(Config.CONFIG_FILE, "r") as f:
                config = json.loads(f.read())
        except Exception as e:
            pass

        self.__config = config
        return config

    def write_config(self):
        if self.__config.get("date_created") is None:
           self.__config["date_created"] = int(time.time())
        self.__config["date_modified"] = int(time.time())

        try:
            with open(Config.CONFIG_FILE, "w") as f:
                f.write(json.dumps(self.__config))

            os.chmod(Config.CONFIG_FILE, stat.S_IWRITE | stat.S_IREAD)

        except Exception as e:
            CLI.colored_print("Could not write configuration file", CLI.COLOR_ERROR)
            return False

        return True

    def __create_directory(self):
        # Installation directory
        CLI.colored_print("Where do you want to install?", CLI.COLOR_SUCCESS)
        while True:
            kobodocker_path = CLI.colored_input("", CLI.COLOR_SUCCESS,
                                                self.__config.get("kobodocker_path"))
            if os.path.isdir(kobodocker_path):
                break
            else:
                try:
                    os.makedirs(kobodocker_path)
                    break
                except Exception as e:
                    CLI.colored_print("Could not create directory {}!".format(kobodocker_path), CLI.COLOR_ERROR)
                    CLI.colored_print("Please make sure you have permissions and path is correct", CLI.COLOR_ERROR)

        self.__config["kobodocker_path"] = kobodocker_path

    def __is_db_image_version_unknown(self, database, master_version):
        """
        Tries to detect current docker image for `database`.
        It's compared to current `master` branch of `kobo-docker` repository.

        :param database: str
        :param master_version: str
        :return: bool
        """
        unknown_version = True
        docker_composer_file_path = "{}/docker-compose.yml".format(self.__config["kobodocker_path"])
        if os.path.exists(docker_composer_file_path):
            try:
                content = ""
                with open(docker_composer_file_path, "r") as docker_composer_file:
                    content = docker_composer_file.read()

                version_search = re.search(r"{}:\s+image: ([^\n]*)".format(database), content)
                if version_search:
                    version = version_search.group(1)
                    if version == master_version:
                        unknown_version = False
            except:
                pass

        return unknown_version

    def __detect_network(self):

        self.__config["local_interface_ip"] = Network.get_primary_ip()
        self.__config["master_backend_ip"] = self.__config["local_interface_ip"]

        if self.__config.get("advanced") == Config.TRUE:
            CLI.colored_print("Please choose which network interface you want to use?", CLI.COLOR_SUCCESS)
            interfaces = Network.get_local_interfaces()
            interfaces.update({"other": "Other"})
            for interface, ip_address in interfaces.items():
                CLI.colored_print("\t{}) {}".format(interface, ip_address))

            choices = [str(interface) for interface in interfaces.keys()]
            choices.append("other")
            response = CLI.get_response(
                choices,
                self.__config.get("local_interface", Network.get_primary_interface()))

            if response == "other":
                interfaces = Network.get_local_interfaces(all=True)
                for interface, ip_address in interfaces.items():
                    CLI.colored_print("\t{}) {}".format(interface, ip_address))

                choices = [str(interface) for interface in interfaces.keys()]
                self.__config["local_interface"] = CLI.get_response(
                    choices,
                    self.__config.get("local_interface", Network.get_primary_interface()))
            else:
                self.__config["local_interface"] = response

            self.__config["local_interface_ip"] = interfaces[self.__config.get("local_interface")]
            self.__config["master_backend_ip"] = self.__config.get("local_interface_ip")

    def __generate_password(self):
        characters = string.ascii_letters + "!#$%&*+-?@^~" + string.digits
        return "".join(choice(characters) for x in range(randint(10, 16)))
