# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import binascii
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
    UNIQUE_ID_FILE = ".uniqid"
    TRUE = "1"
    FALSE = "2"

    # Maybe overkill. Use this class as a singleton to get the same configuration
    # for each instantiation.
    __metaclass__ = Singleton

    def __init__(self):
        self.__config = self.read_config()
        self.__first_time = None
        self.__primary_ip = Network.get_primary_ip()

    @property
    def advanced_options(self):
        """
        Checks whether advanced options should be displayed
        :return: bool 
        """
        return self.__config.get("advanced") == Config.TRUE

    def auto_detect_network(self):
        """
        Tries to detect new ip
        :return: bool
        """
        changed = False
        if self.__config.get("local_installation") == Config.TRUE:
            local_interfaces = Network.get_local_interfaces(all=True)
            if self.__config.get("local_interface_ip") not in local_interfaces.values():
                self.__detect_network()
                self.write_config()
                changed = True
        return changed

    @property
    def aws(self):
        """
        Checks whether questions are backend only
        :return: bool
        """
        return self.__config.get("use_aws") == Config.TRUE

    @property
    def master_backend(self):
        """
        Checks whether setup is running on a master backend server
        :return: bool
        """
        return self.multi_servers and \
               self.__config.get("backend_server_role") == "master"

    @property
    def slave_backend(self):
        """
        Checks whether setup is running on a slave backend server
        :return: bool
        """
        return self.multi_servers and \
               self.__config.get("backend_server_role") == "slave"

    @property
    def backend_questions(self):
        """
        Checks whether questions are backend only
        :return: bool
        """
        return not self.multi_servers or not self.frontend

    @property
    def first_time(self):
        """
        Checks whether setup is running for the first time
        :return: bool
        """
        if self.__first_time is None:
            self.__first_time = self.__config.get("date_created") is None
        return self.__first_time

    @property
    def frontend(self):
        """
        Checks whether setup is running on a frontend server
        :return: bool
        """
        return not self.multi_servers or \
               self.__config.get("server_role") == "frontend"

    @property
    def frontend_questions(self):
        """
        Checks whether questions are frontend only
        :return: bool
        """
        return not self.multi_servers or self.frontend

    @property
    def dev_mode(self):
        return self.__config.get("dev_mode") == Config.TRUE

    @property
    def local_install(self):
        """
        Checks whether installation is for `Workstation`s
        :return: bool
        """
        return self.__config.get("local_installation") == Config.TRUE

    @property
    def multi_servers(self):
        """
        Checks whether installation is for separate frontend and backend servers
        :return: bool
        """
        return self.__config.get("multi") == Config.TRUE

    @property
    def proxy(self):
        """
        Checks whether installation is using a proxy or a load balancer
        :return: bool
        """
        return self.__config.get("proxy") == Config.TRUE

    @property
    def staging_mode(self):
        return self.__config.get("staging_mode") == Config.TRUE

    def build(self):
        """
        Build configuration based on user's answer
        :return: dict
        """
        if not self.__primary_ip:
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
                "kobodocker_path": os.path.realpath(os.path.normpath(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "..",
                    "..",
                    "kobo-docker"))
                ),
                "internal_domain_name": "docker.internal",
                "private_domain_name": "kobo.private",
                "public_domain_name": "kobo.local",
                "kpi_subdomain": "kf",
                "kc_subdomain": "kc",
                "ee_subdomain": "ee",
                "postgres_db": "kobotoolbox",
                "postgres_user": "kobo",
                "postgres_password": Config.generate_password(),
                "kc_path": "",
                "kpi_path": "",
                "super_user_username": "super_admin",
                "super_user_password": Config.generate_password(),
                "postgres_replication_password": Config.generate_password(),
                "use_aws": Config.FALSE,
                "use_private_dns": Config.FALSE,
                "master_backend_ip": self.__primary_ip,
                "local_interface_ip": self.__primary_ip,
                "multi": Config.FALSE,
                "postgres_settings": Config.FALSE,
                "postgres_ram": "8",
                "postgres_profile": "Mixed",
                "postgres_max_connections": "100",
                "postgres_settings_content": "",
                "enketo_api_token": binascii.hexlify(os.urandom(60)).decode("utf-8"),
                "django_secret_key": binascii.hexlify(os.urandom(24)).decode("utf-8"),
                "use_backup": Config.FALSE,
                "kobocat_media_schedule": "0 0 * * 0",
                "mongo_backup_schedule": "0 1 * * 0",
                "postgres_backup_schedule": "0 2 * * 0",
                "redis_backup_schedule": "0 3 * * 0",
                "aws_backup_bucket_name": "",
                "aws_backup_yearly_retention": "2",
                "aws_backup_monthly_retention": "12",
                "aws_backup_weekly_retention": "4",
                "aws_backup_daily_retention": "30",
                "aws_mongo_backup_minimum_size": "50",
                "aws_postgres_backup_minimum_size": "50",
                "aws_redis_backup_minimum_size": "5",
                "aws_backup_upload_chunk_size": "15",
                "aws_backup_bucket_deletion_rule_enabled": Config.FALSE,
                "backend_server_role": "master"
            }

            config.update(self.__config)

            self.__config = config
            self.__welcome()
            self.__create_directory()
            self.__questions_advanced_options()
            self.__questions_installation_type()

            if not self.local_install:

                if self.advanced_options:
                    self.__questions_multi_servers()
                    if self.multi_servers:
                        self.__questions_roles()
                        if self.frontend:
                            self.__questions_private_routes()

                if self.frontend_questions:
                    self.__questions_public_routes()

            else:
                self.__detect_network()

            if self.frontend_questions:
                self.__questions_smtp()
                self.__questions_super_user_credentials()

            if self.advanced_options:

                self.__questions_docker_prefix()
                self.__questions_dev_mode()
                self.__questions_postgres()
                self.__questions_ports()

                if self.frontend_questions:
                    self.__questions_aws()
                    self.__questions_google()
                    self.__questions_intercom()
                    self.__questions_raven()
                    self.__questions_uwsgi()

            self.__questions_backup()

            self.__config = config
            self.write_config()
            return config

    def get_config(self):
        return self.__config

    @staticmethod
    def generate_password():
        """
        Generate random password between 8 to 16 characters
        :return: str
        """
        characters = string.ascii_letters + "!$%+-@^~" + string.digits
        return "".join(choice(characters) for x in range(randint(10, 16)))

    def read_config(self):
        """
        Reads config from file `Config.CONFIG_FILE` if exists
        :return: dict
        """
        config = {}
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            config_file = os.path.join(base_dir, Config.CONFIG_FILE)
            with open(config_file, "r") as f:
                config = json.loads(f.read())
        except IOError:
            pass

        self.__config = config
        unique_id = self.read_unique_id()
        if not unique_id:
            self.__config["unique_id"] = int(time.time())

        return config

    def read_unique_id(self):
        """
        Reads unique id from file `Config.UNIQUE_ID_FILE`
        :return: str
        """
        unique_id = None

        try:
            unique_id_file = os.path.join(self.__config.get("kobodocker_path"),
                                          Config.UNIQUE_ID_FILE)
            with open(unique_id_file, "r") as f:
                unique_id = f.read().strip()
        except Exception as e:
            pass

        return unique_id

    def write_config(self):
        """
        Writes config to file `Config.CONFIG_FILE`.
        """
        # Adds `date_created`. This field will be use to determine first usage of the setup option.
        if self.__config.get("date_created") is None:
            self.__config["date_created"] = int(time.time())
        self.__config["date_modified"] = int(time.time())

        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            config_file = os.path.join(base_dir, Config.CONFIG_FILE)
            with open(config_file, "w") as f:
                f.write(json.dumps(self.__config))

            os.chmod(config_file, stat.S_IWRITE | stat.S_IREAD)

        except IOError:
            CLI.colored_print("Could not write configuration file", CLI.COLOR_ERROR)
            sys.exit()

    def write_unique_id(self):
        try:
            unique_id_file = os.path.join(self.__config.get("kobodocker_path"), Config.UNIQUE_ID_FILE)
            with open(unique_id_file, "w") as f:
                f.write(str(self.__config.get("unique_id")))

            os.chmod(unique_id_file, stat.S_IWRITE | stat.S_IREAD)
        except (IOError, OSError):
            CLI.colored_print("Could not write unique_id file", CLI.COLOR_ERROR)
            return False

        return True

    def __create_directory(self):
        """
        Create repository directory if it doesn't exist.
        """
        CLI.colored_print("Where do you want to install?", CLI.COLOR_SUCCESS)
        while True:
            kobodocker_path = CLI.colored_input("", CLI.COLOR_SUCCESS,
                                                self.__config.get("kobodocker_path"))

            if kobodocker_path.startswith("."):
                base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                kobodocker_path = os.path.normpath(os.path.join(base_dir, kobodocker_path))

            CLI.colored_print("Please confirm path [{}]".format(kobodocker_path),
                              CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")

            if CLI.get_response([Config.TRUE, Config.FALSE], Config.TRUE) == Config.TRUE:

                if os.path.isdir(kobodocker_path):
                    break
                else:
                    try:
                        os.makedirs(kobodocker_path)
                        break
                    except OSError:
                        CLI.colored_print("Could not create directory {}!".format(kobodocker_path), CLI.COLOR_ERROR)
                        CLI.colored_print("Please make sure you have permissions and path is correct", CLI.COLOR_ERROR)

        self.write_unique_id()
        self.__config["kobodocker_path"] = kobodocker_path
        self.__validate_installation()

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

    def __questions_advanced_options(self):
        """
        Asks if user wants to see advanced options
        """
        CLI.colored_print("Do you want to see advanced options?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["advanced"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                     self.__config.get("advanced", Config.FALSE))

    def __questions_aws(self):
        """
        Asks if user wants to see AWS option
        and asks for credentials if needed.
        """
        CLI.colored_print("Do you want to use AWS S3 storage?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["use_aws"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                    self.__config.get("use_aws", Config.FALSE))
        if self.__config["use_aws"] == Config.TRUE:
            self.__config["aws_access_key"] = CLI.colored_input("AWS Access Key", CLI.COLOR_SUCCESS,
                                                                self.__config.get("aws_access_key", ""))
            self.__config["aws_secret_key"] = CLI.colored_input("AWS Secret Key", CLI.COLOR_SUCCESS,
                                                                self.__config.get("aws_secret_key", ""))
            self.__config["aws_bucket_name"] = CLI.colored_input("AWS Bucket name", CLI.COLOR_SUCCESS,
                                                                 self.__config.get("aws_bucket_name", ""))
        else:
            self.__config["aws_access_key"] = ""
            self.__config["aws_secret_key"] = ""
            self.__config["aws_bucket_name"] = ""

    def __questions_backup(self):
        """
        Asks all questions about backups.
        """
        if self.backend_questions or (self.frontend_questions and not self.aws):

            CLI.colored_print("Do you want to activate backups?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            self.__config["use_backup"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                           self.__config.get("use_backup", Config.FALSE))

            if self.__config.get("use_backup") == Config.TRUE:
                if self.advanced_options:
                    if self.backend_questions and not self.frontend_questions:
                        self.__questions_aws()

                    schedule_regex_pattern = "^((((\d+(,\d+)*)|(\d+-\d+)|(\*(\/\d+)?)))(\s+(((\d+(,\d+)*)|(\d+\-\d+)|(\*(\/\d+)?)))){4})$"
                    CLI.colored_print("╔═════════════════════════════════════════════════════════════════╗",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("║ Schedules use linux cron syntax with UTC datetimes.             ║",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("║ For example, schedule at 12:00 AM E.S.T every Sunday would be:  ║",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("║ 0 5 * * 0                                                       ║",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("║                                                                 ║",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("║ Please visit https://crontab.guru/ to generate a cron schedule. ║",
                                      CLI.COLOR_WARNING)
                    CLI.colored_print("╚═════════════════════════════════════════════════════════════════╝",
                                      CLI.COLOR_WARNING)

                    if self.frontend_questions and not self.aws:
                        CLI.colored_print("KoBoCat media backup schedule?", CLI.COLOR_SUCCESS)
                        self.__config["kobocat_media_backup_schedule"] = CLI.get_response(
                            "~{}".format(schedule_regex_pattern),
                            self.__config.get(
                                "kobocat_media_backup_schedule",
                                "0 0 * * 0"))

                    if self.backend_questions:

                        CLI.colored_print("PostgreSQL backup schedule?", CLI.COLOR_SUCCESS)
                        self.__config["postgres_backup_schedule"] = CLI.get_response(
                            "~{}".format(schedule_regex_pattern),
                            self.__config.get(
                                "postgres_backup_schedule",
                                "0 2 * * 0"))

                        if self.master_backend:
                            CLI.colored_print("Run backups from master backend server?", CLI.COLOR_SUCCESS)
                            CLI.colored_print("\t1) Yes")
                            CLI.colored_print("\t2) No")
                            self.__config["backup_from_master"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                                   self.__config.get(
                                                                                       "backup_from_master",
                                                                                       Config.TRUE))
                        if self.master_backend or not self.multi_servers:
                            CLI.colored_print("MongoDB backup schedule?", CLI.COLOR_SUCCESS)
                            self.__config["mongo_backup_schedule"] = CLI.get_response(
                                "~{}".format(schedule_regex_pattern),
                                self.__config.get(
                                    "mongo_backup_schedule",
                                    "0 1 * * 0"))

                            CLI.colored_print("Redis backup schedule?", CLI.COLOR_SUCCESS)
                            self.__config["redis_backup_schedule"] = CLI.get_response(
                                "~{}".format(schedule_regex_pattern),
                                self.__config.get(
                                    "redis_backup_schedule",
                                    "0 3 * * 0"))
                        if self.aws:
                            self.__config["aws_backup_bucket_name"] = CLI.colored_input("AWS Backups bucket name",
                                                                                        CLI.COLOR_SUCCESS,
                                                                                        self.__config.get(
                                                                                            "aws_backup_bucket_name",
                                                                                            ""))
                            if self.__config["aws_backup_bucket_name"] != "":
                                CLI.colored_print("How many yearly backups to keep?", CLI.COLOR_SUCCESS)
                                self.__config["aws_backup_yearly_retention"] = CLI.get_response("~^\d+$",
                                                                                                self.__config.get(
                                                                                                    "aws_backup_yearly_retention",
                                                                                                    "2"))

                                CLI.colored_print("How many monthly backups to keep?", CLI.COLOR_SUCCESS)
                                self.__config["aws_backup_monthly_retention"] = CLI.get_response("~^\d+$",
                                                                                                 self.__config.get(
                                                                                                     "aws_backup_monthly_retention",
                                                                                                     "12"))

                                CLI.colored_print("How many weekly backups to keep?", CLI.COLOR_SUCCESS)
                                self.__config["aws_backup_weekly_retention"] = CLI.get_response("~^\d+$",
                                                                                                self.__config.get(
                                                                                                    "aws_backup_weekly_retention",
                                                                                                    "4"))

                                CLI.colored_print("How many daily backups to keep?", CLI.COLOR_SUCCESS)
                                self.__config["aws_backup_daily_retention"] = CLI.get_response("~^\d+$",
                                                                                               self.__config.get(
                                                                                                   "aws_backup_daily_retention",
                                                                                                   "30"))

                                CLI.colored_print("MongoDB backup minimum size (in MB)?", CLI.COLOR_SUCCESS)
                                CLI.colored_print("Files below this size will be ignored when rotating backups.",
                                                  CLI.COLOR_INFO)
                                self.__config["aws_mongo_backup_minimum_size"] = CLI.get_response("~^\d+$",
                                                                                                  self.__config.get(
                                                                                                      "aws_mongo_backup_minimum_size",
                                                                                                      "50"))

                                CLI.colored_print("PostgresSQL backup minimum size (in MB)?", CLI.COLOR_SUCCESS)
                                CLI.colored_print("Files below this size will be ignored when rotating backups.",
                                                  CLI.COLOR_INFO)
                                self.__config["aws_postgres_backup_minimum_size"] = CLI.get_response("~^\d+$",
                                                                                                     self.__config.get(
                                                                                                         "aws_postgres_backup_minimum_size",
                                                                                                         "50"))

                                CLI.colored_print("Redis backup minimum size (in MB)?", CLI.COLOR_SUCCESS)
                                CLI.colored_print("Files below this size will be ignored when rotating backups.",
                                                  CLI.COLOR_INFO)
                                self.__config["aws_redis_backup_minimum_size"] = CLI.get_response("~^\d+$",
                                                                                                  self.__config.get(
                                                                                                      "aws_redis_backup_minimum_size",
                                                                                                      "5"))

                                CLI.colored_print("Chunk size of multipart uploads (in MB)?", CLI.COLOR_SUCCESS)
                                self.__config["aws_backup_upload_chunk_size"] = CLI.get_response("~^\d+$",
                                                                                                 self.__config.get(
                                                                                                     "aws_backup_upload_chunk_size",
                                                                                                     "15"))

                                CLI.colored_print("Use AWS LifeCycle deletion rule?", CLI.COLOR_SUCCESS)
                                CLI.colored_print("\t1) Yes")
                                CLI.colored_print("\t2) No")
                                self.__config["aws_backup_bucket_deletion_rule_enabled"] = CLI.get_response(
                                    [Config.TRUE, Config.FALSE],
                                    self.__config.get("aws_backup_bucket_deletion_rule_enabled",
                                                      Config.FALSE))
        else:
            self.__config["use_backup"] = Config.FALSE

    def __questions_dev_mode(self):
        """
        Asks for developer/staging mode.

        Dev mode allows to modify nginx port and
        Staging model

        Reset to default in case of No
        """

        if self.frontend_questions:

            if self.local_install:
                # NGinX different port
                CLI.colored_print("Web server port?", CLI.COLOR_SUCCESS)
                self.__config["exposed_nginx_docker_port"] = CLI.get_response("~^\d+$",
                                                                              self.__config.get(
                                                                                  "exposed_nginx_docker_port",
                                                                                  "80"))
                CLI.colored_print("Developer mode?", CLI.COLOR_SUCCESS)
                CLI.colored_print("\t1) Yes")
                CLI.colored_print("\t2) No")
                self.__config["dev_mode"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                             self.__config.get("dev_mode", Config.FALSE))
                self.__config["staging_mode"] = Config.FALSE
            else:
                CLI.colored_print("Staging mode?", CLI.COLOR_SUCCESS)
                CLI.colored_print("\t1) Yes")
                CLI.colored_print("\t2) No")
                self.__config["staging_mode"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                 self.__config.get("staging_mode", Config.FALSE))

            if self.dev_mode or self.staging_mode:
                CLI.colored_print("╔═══════════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
                CLI.colored_print("║ Where are the files located locally? It can be absolute   ║", CLI.COLOR_WARNING)
                CLI.colored_print("║ or relative to the directory of `kobo-docker`.            ║", CLI.COLOR_WARNING)
                CLI.colored_print("║ Leave empty if you don't need to overload the repository. ║", CLI.COLOR_WARNING)
                CLI.colored_print("╚═══════════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)
                self.__config["kc_path"] = CLI.colored_input("KoBoCat files location", CLI.COLOR_SUCCESS,
                                                             self.__config.get("kc_path"))

                self.__clone_repo(self.__config["kc_path"], "kobocat")
                self.__config["kpi_path"] = CLI.colored_input("KPI files location", CLI.COLOR_SUCCESS,
                                                              self.__config.get("kpi_path"))
                self.__clone_repo(self.__config["kpi_path"], "kpi")

                # Create an unique id to build fresh image when starting containers
                if (self.__config.get("kc_dev_build_id", "") == "" or
                        self.__config.get("kc_path") != self.__config.get("kc_path")):

                    self.__config["kc_dev_build_id"] = "{prefix}{timestamp}".format(
                        prefix="{}.".format(self.__config.get("docker_prefix")) if self.__config.get("docker_prefix") else "",
                        timestamp=str(int(time.time()))
                    )
                if (self.__config.get("kpi_dev_build_id", "") == "" or
                        self.__config.get("kpi_path") != self.__config.get("kpi_path")):
                    self.__config["kpi_dev_build_id"] = "{prefix}{timestamp}".format(
                        prefix="{}.".format(self.__config.get("docker_prefix")) if self.__config.get("docker_prefix") else "",
                        timestamp=str(int(time.time()))
                    )
                if self.dev_mode:
                    # Debug
                    CLI.colored_print("Enable DEBUG?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) True")
                    CLI.colored_print("\t2) False")
                    self.__config["debug"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                              self.__config.get("debug", Config.TRUE))
            else:
                # Force reset paths
                self.__reset_dev_mode(self.staging_mode)

    def __questions_docker_prefix(self):
        """
        Asks for Docker compose prefix. It allows to start containers with a custom prefix
        """
        self.__config["docker_prefix"] = CLI.colored_input("Docker Compose prefix? (leave empty for default)",
                                                           CLI.COLOR_SUCCESS,
                                                           self.__config.get("docker_prefix", ""))

    def __questions_google(self):
        """
        Asks for Google's keys
        """
        # Google Analytics
        self.__config["google_ua"] = CLI.colored_input("Google Analytics Identifier", CLI.COLOR_SUCCESS,
                                                       self.__config.get("google_ua", ""))

        # Google API Key
        self.__config["google_api_key"] = CLI.colored_input("Google API Key", CLI.COLOR_SUCCESS,
                                                            self.__config.get("google_api_key", ""))

    def __questions_intercom(self):
        """
        Asks for Intercom API Key if any
        """
        self.__config["intercom"] = CLI.colored_input("Intercom App ID", CLI.COLOR_SUCCESS,
                                                      self.__config.get("intercom", ""))

    def __questions_installation_type(self):
        """
        Asks for installation type
        """
        CLI.colored_print("What kind of installation do you need?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) On your workstation")
        CLI.colored_print("\t2) On a server")
        self.__config["local_installation"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                               self.__config.get("local_installation", Config.FALSE))
        if self.local_install:
            # Reset previous choices, in case server role is not the same.
            self.__config["multi"] = Config.FALSE
            self.__config["use_private_dns"] = Config.FALSE

    def __questions_multi_servers(self):
        """
        Asks if installation is for only one server
        or different frontend and backend servers.
        """
        CLI.colored_print("Do you want to use separate servers for frontend and backend?",
                          CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["multi"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                  self.__config.get("multi", Config.FALSE))

    def __questions_postgres(self):
        """
        Postgres credentials and settings.

        Settings can be tweaked thanks to pgconfig.org API
        """
        self.__config["postgres_db"] = CLI.colored_input("Postgres database", CLI.COLOR_SUCCESS,
                                                         self.__config.get("postgres_db"))
        self.__config["postgres_user"] = CLI.colored_input("Postgres user", CLI.COLOR_SUCCESS,
                                                           self.__config.get("postgres_user"))
        self.__config["postgres_password"] = CLI.colored_input("Postgres password", CLI.COLOR_SUCCESS,
                                                               self.__config.get("postgres_password"))

        if self.backend_questions and self.advanced_options:
            # Postgres settings
            CLI.colored_print("Do you want to tweak PostgreSQL settings?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            self.__config["postgres_settings"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                                  self.__config.get("postgres_settings", Config.FALSE))

            if self.__config["postgres_settings"] == Config.TRUE:
                CLI.colored_print("Total Memory in GB?", CLI.COLOR_SUCCESS)
                self.__config["postgres_ram"] = CLI.get_response("~^\d+$", self.__config.get("postgres_ram", "8"))

                if self.multi_servers:
                    self.__config["postgres_profile"] = "OLTP"
                    CLI.colored_print("Number of connections?", CLI.COLOR_SUCCESS)
                    self.__config["postgres_max_connections"] = CLI.get_response(
                        "~^\d+$",
                        self.__config.get("postgres_max_connections", "100"))
                elif self.dev_mode:
                    self.__config["postgres_profile"] = "Desktop"
                else:
                    self.__config["postgres_profile"] = "Mixed"
                    CLI.colored_print("Number of connections?", CLI.COLOR_SUCCESS)
                    self.__config["postgres_max_connections"] = CLI.get_response(
                        "~^\d+$",
                        self.__config.get("postgres_max_connections", "100"))

            # use pgconfig.org API to build postgres config
            endpoint = "https://api.pgconfig.org/v1/tuning/get-config?environment_name={profile}" \
                       "&format=conf&include_pgbadger=false&max_connections={max_connections}&" \
                       "pg_version=9.5&total_ram={ram}GB&drive_type=SSD".format(
                profile=self.__config["postgres_profile"],
                ram=self.__config["postgres_ram"],
                max_connections=self.__config["postgres_max_connections"]
            )
            response = Network.curl(endpoint)
            if response:
                self.__config["postgres_settings_content"] = re.sub(r"(log|lc_).+(\n|$)", "", response)
            else:
                # If no response from API, keep defaults
                self.__config["postgres_settings"] = Config.FALSE

    def __questions_ports(self):
        """
        Customize services ports
        """
        CLI.colored_print("Do you want to customize service ports?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["customized_ports"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                             self.__config.get("customized_ports",
                                                                               Config.FALSE))
        if self.__config.get("customized_ports") == Config.TRUE:
            CLI.colored_print("PostgreSQL?", CLI.COLOR_SUCCESS)
            self.__config["postgresql_port"] = CLI.get_response("~^\d+$", self.__config.get("postgresql_port", "5432"))

            CLI.colored_print("MongoDB?", CLI.COLOR_SUCCESS)
            self.__config["mongo_port"] = CLI.get_response("~^\d+$", self.__config.get("mongo_port", "27017"))

            CLI.colored_print("Redis (main)?", CLI.COLOR_SUCCESS)
            self.__config["redis_main_port"] = CLI.get_response("~^\d+$", self.__config.get("redis_main_port", "6379"))

            CLI.colored_print("Redis (cache)?", CLI.COLOR_SUCCESS)
            self.__config["redis_cache_port"] = CLI.get_response("~^\d+$",
                                                                 self.__config.get("redis_cache_port", "6380"))
        else:
            self.__config["postgresql_port"] = "5432"
            self.__config["mongo_port"] = "27017"
            self.__config["redis_main_port"] = "6379"
            self.__config["redis_cache_port"] = "6380"

    def __questions_private_routes(self):
        """
        Asks if configuration uses a DNS for private domain names for communication
        between frontend and backend.
        Otherwise, it will create entries in `extra_hosts` in composer file based
        on the provided ip.
        """
        CLI.colored_print("Do you use DNS for private routes?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")

        self.__config["use_private_dns"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                            self.__config.get("use_private_dns",
                                                                              Config.FALSE))

        if self.__config["use_private_dns"] == Config.FALSE:
            CLI.colored_print("IP address (IPv4) of backend server?", CLI.COLOR_SUCCESS)
            self.__config["master_backend_ip"] = CLI.get_response(
                "~\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
                self.__config.get("master_backend_ip", self.__primary_ip))
        else:
            self.__config["private_domain_name"] = CLI.colored_input("Private domain name",
                                                                     CLI.COLOR_SUCCESS,
                                                                     self.__config.get(
                                                                         "private_domain_name", ""))

    def __questions_public_routes(self):
        self.__config["public_domain_name"] = CLI.colored_input("Public domain name", CLI.COLOR_SUCCESS,
                                                                self.__config.get("public_domain_name", ""))
        self.__config["kpi_subdomain"] = CLI.colored_input("KPI sub domain", CLI.COLOR_SUCCESS,
                                                           self.__config.get("kpi_subdomain", ""))
        self.__config["kc_subdomain"] = CLI.colored_input("KoBoCat sub domain", CLI.COLOR_SUCCESS,
                                                          self.__config.get("kc_subdomain", ""))
        self.__config["ee_subdomain"] = CLI.colored_input("Enketo Express sub domain name",
                                                          CLI.COLOR_SUCCESS,
                                                          self.__config.get("ee_subdomain", ""))

        parts = self.__config.get("public_domain_name", "").split(".")
        self.__config["internal_domain_name"] = "{}.internal".format(
            ".".join(parts[:-1])
        )
        if not self.multi_servers or \
                (self.multi_servers and self.__config.get("use_private_dns") == Config.FALSE):
            self.__config["private_domain_name"] = "{}.private".format(
                ".".join(parts[:-1])
            )

        CLI.colored_print("Do you use a reverse proxy or a load balancer?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["proxy"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                  self.__config.get("proxy", Config.TRUE))

        if self.proxy:
            CLI.colored_print("Use HTTPS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("Please note that certificate has to be installed on the load balancer!",
                              CLI.COLOR_INFO)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            self.__config["https"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                      self.__config.get("https", Config.TRUE))

            CLI.colored_print("Internal port used by reverse proxy?", CLI.COLOR_SUCCESS)
            self.__config["nginx_proxy_port"] = CLI.get_response("~^\d+$",
                                                                 self.__config.get("nginx_proxy_port", "80"))
        else:
            self.__config["https"] = Config.FALSE
            self.__config["nginx_proxy_port"] = "80"

    def __questions_raven(self):
        CLI.colored_print("Do you want to use Sentry?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["raven_settings"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                           self.__config.get("raven_settings", Config.FALSE))

        if self.__config.get("raven_settings") == Config.TRUE:
            self.__config["kpi_raven"] = CLI.colored_input("KPI Raven token", CLI.COLOR_SUCCESS,
                                                           self.__config.get("kpi_raven", ""))
            self.__config["kobocat_raven"] = CLI.colored_input("KoBoCat Raven token", CLI.COLOR_SUCCESS,
                                                               self.__config.get("kobocat_raven", ""))
            self.__config["kpi_raven_js"] = CLI.colored_input("KPI Raven JS token", CLI.COLOR_SUCCESS,
                                                              self.__config.get("kpi_raven_js", ""))
        else:
            self.__config["kpi_raven"] = ""
            self.__config["kobocat_raven"] = ""
            self.__config["kpi_raven_js"] = ""

    def __questions_roles(self):
        CLI.colored_print("Which role do you want to assign to this server?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) frontend")
        CLI.colored_print("\t2) backend")
        self.__config["server_role"] = CLI.get_response(["backend", "frontend"],
                                                        self.__config.get("server_role", "frontend"))

        if self.__config.get("server_role") == "backend":
            CLI.colored_print("Which role do you want to assign to this backend server?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) master")
            CLI.colored_print("\t2) slave")
            self.__config["backend_server_role"] = CLI.get_response(["master", "slave"],
                                                                    self.__config.get("backend_server_role", "master"))
        else:
            # It may be useless to force backend role when using multi servers.
            self.__config["backend_server_role"] = "master"

    def __questions_smtp(self):
        self.__config["smtp_host"] = CLI.colored_input("SMTP server", CLI.COLOR_SUCCESS,
                                                       self.__config.get("smtp_host"))
        self.__config["smtp_port"] = CLI.colored_input("SMTP port", CLI.COLOR_SUCCESS,
                                                       self.__config.get("smtp_port", "25"))
        self.__config["smtp_user"] = CLI.colored_input("SMTP user", CLI.COLOR_SUCCESS,
                                                       self.__config.get("smtp_user", ""))
        if self.__config.get("smtp_user"):
            self.__config["smtp_password"] = CLI.colored_input("SMTP password", CLI.COLOR_SUCCESS,
                                                               self.__config.get("smtp_password"))
            CLI.colored_print("Use TLS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) True")
            CLI.colored_print("\t2) False")
            self.__config["smtp_use_tls"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                             self.__config.get("smtp_use_tls", Config.TRUE))
        self.__config["default_from_email"] = CLI.colored_input("From email address", CLI.COLOR_SUCCESS,
                                                                self.__config.get("default_from_email",
                                                                                  "support@{}".format(
                                                                                      self.__config.get(
                                                                                          "public_domain_name"))))

    def __questions_super_user_credentials(self):
        # Super user. Only ask for credentials the first time.
        # Super user is created if db doesn't exists.
        username = CLI.colored_input("Super user's username", CLI.COLOR_SUCCESS,
                                     self.__config.get("super_user_username"))
        password = CLI.colored_input("Super user's password", CLI.COLOR_SUCCESS,
                                     self.__config.get("super_user_password"))

        if username == self.__config.get("super_user_username") and \
            password != self.__config.get("super_user_password") and \
                not self.first_time:
            CLI.colored_print("╔══════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
            CLI.colored_print("║ Super user's password has been changed!              ║", CLI.COLOR_WARNING)
            CLI.colored_print("║ Don't forget to apply these changes in Postgres too. ║", CLI.COLOR_WARNING)
            CLI.colored_print("║ Super user's password won't be updated if the        ║", CLI.COLOR_WARNING)
            CLI.colored_print("║ database already exists.                             ║", CLI.COLOR_WARNING)
            CLI.colored_print("╚══════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)

        self.__config["super_user_username"] = username
        self.__config["super_user_password"] = password

    def __questions_uwsgi(self):
        CLI.colored_print("Do you want to tweak uWSGI settings?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        self.__config["uwsgi_settings"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                           self.__config.get("uwsgi_settings", Config.FALSE))

        if self.__config.get("uwsgi_settings") == Config.TRUE:
            CLI.colored_print("Number of uWSGi workers to start?", CLI.COLOR_SUCCESS)
            self.__config["workers_start"] = CLI.get_response(
                "~^\d+$",
                self.__config.get("workers_start", "1"))
            CLI.colored_print("Max uWSGi workers?", CLI.COLOR_SUCCESS)
            self.__config["workers_max"] = CLI.get_response(
                "~^\d+$",
                self.__config.get("workers_max", "2"))

            CLI.colored_print("Max number of requests per worker?", CLI.COLOR_SUCCESS)
            self.__config["max_requests"] = CLI.get_response(
                "~^\d+$",
                self.__config.get("max_requests", "512"))
            CLI.colored_print("Max memory per workers in MB?", CLI.COLOR_SUCCESS)
            self.__config["soft_limit"] = CLI.get_response(
                "~^\d+$",
                self.__config.get("soft_limit", "128"))
        else:
            self.__config["workers_start"] = "1"
            self.__config["workers_max"] = "2"
            self.__config["max_requests"] = "512"
            self.__config["soft_limit"] = "128"

    def __reset_dev_mode(self, reset_nginx_port=False):
        """
        Resets several properties to their default to avoid developer mode.
        It can be useful, if user changes the type of installation on the same server

        :param reset_nginx_port: bool
        :return: bool
        """
        self.__config["dev_mode"] = Config.FALSE
        self.__config["staging_mode"] = Config.FALSE
        self.__config["kc_path"] = ""
        self.__config["kpi_path"] = ""
        self.__config["debug"] = Config.FALSE
        if reset_nginx_port:
            self.__config["exposed_nginx_docker_port"] = "80"

    def __validate_installation(self):
        """
        Validates if installation is not run over existing data.
        The check is made only the first time the setup is run.
        :return: bool
        """
        if self.first_time:
            mongo_dir_path = os.path.join(self.__config["kobodocker_path"], ".vols", "mongo")
            postgres_dir_path = os.path.join(self.__config["kobodocker_path"], ".vols", "db")
            mongo_data_exists = (os.path.exists(mongo_dir_path) and os.path.isdir(mongo_dir_path) and
                                 os.listdir(mongo_dir_path))
            postgres_data_exists = os.path.exists(postgres_dir_path) and os.path.isdir(postgres_dir_path)

            if mongo_data_exists or postgres_data_exists:
                # Not a reliable way to detect whether folder contains `kobo-install` files
                # We assume that if `docker-compose.backend.template.yml` is there,
                # Docker images are the good ones.
                # TODO Find a better way
                docker_composer_file_path = os.path.join(self.__config["kobodocker_path"],
                                                         "docker-compose.backend.template.yml")
                if not os.path.exists(docker_composer_file_path):
                    CLI.colored_print("╔════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
                    CLI.colored_print("║ WARNING !!!                                        ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║                                                    ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ You are installing over existing data.             ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║                                                    ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ It's recommended to backup your data and import it ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ to a fresh installed (by `kobo-install`) database. ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║                                                    ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ `kobo-install` uses these images:                  ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║    - MongoDB: mongo:3.4                            ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║    - PostgreSQL: mdillon/postgis:9.5               ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║                                                    ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ Be sure to upgrade to these versions before        ║", CLI.COLOR_WARNING)
                    CLI.colored_print("║ going further!                                     ║", CLI.COLOR_WARNING)
                    CLI.colored_print("╚════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)
                    CLI.colored_print("Are you sure you want to continue?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\tyes")
                    CLI.colored_print("\tno")
                    response = CLI.get_response(["yes", "no"], "no")
                    if response == "no":
                        sys.exit()
                    else:
                        # Write kobo_first_run file to run postgres container's entrypoint flawlessly.
                        os.system("echo $(date) | sudo tee -a {} > /dev/null".format(
                            os.path.join(self.__config["kobodocker_path"], ".vols", "db", "kobo_first_run")
                        ))

    def __welcome(self):
        CLI.colored_print("╔═══════════════════════════════════════════════════════════════╗", CLI.COLOR_WARNING)
        CLI.colored_print("║ Welcome to `kobo-install`!                                    ║", CLI.COLOR_WARNING)
        CLI.colored_print("║                                                               ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ You are going to be asked some questions that will            ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ determine how to build the configuration of `KoBoToolBox`.    ║", CLI.COLOR_WARNING)
        CLI.colored_print("║                                                               ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ Some questions already have default values (within brackets). ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ Just press `enter` to accept the default value or enter `-`   ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ to remove previously entered value.                           ║", CLI.COLOR_WARNING)
        CLI.colored_print("║ Otherwise choose between choices or type your answer.         ║", CLI.COLOR_WARNING)
        CLI.colored_print("╚═══════════════════════════════════════════════════════════════╝", CLI.COLOR_WARNING)

    def __clone_repo(self, repo_path, repo_name):
        if repo_path:
            if repo_path.startswith("."):
                full_repo_path = os.path.normpath(os.path.join(
                    self.__config["kobodocker_path"],
                    repo_path
                ))
            else:
                full_repo_path = repo_path

            if not os.path.isdir(full_repo_path):
                # clone repo
                try:
                    os.makedirs(full_repo_path)
                except OSError:
                    CLI.colored_print("Please verify permissions.", CLI.COLOR_ERROR)
                    sys.exit()

            # Only clone if folder is empty
            if not os.path.isdir(os.path.join(full_repo_path, ".git")):
                git_command = [
                    "git", "clone", "https://github.com/kobotoolbox/{}".format(repo_name),
                    full_repo_path
                ]

                CLI.colored_print("Cloning `{}` repository to `{}` ".format(
                    repo_name,
                    full_repo_path), CLI.COLOR_INFO)
                CLI.run_command(git_command, cwd=os.path.dirname(full_repo_path))
