# -*- coding: utf-8 -*-
import binascii
import json
import os
import subprocess
import sys


from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network


class Setup:

    KOBO_DOCKER_BRANCH = "multi_compose"

    def __init__(self, config):
        self.__config = config

    def run(self):
        self.__create_config()
        Config.write_config(self.__config)
        self.__render_templates()
        self.__git()

    def __create_config(self):
        config = {
            "workers_max": "4",
            "workers_start": "2",
            "debug": "2",
            "trackjs": "",
            "raven": "",
            "kobodocker_path": os.path.realpath("{}/../kobo-docker".format(
                os.path.dirname(os.path.realpath(__file__)))
            ),
            "kpi_subdomain": "kpi",
            "kc_subdomain": "kc",
            "ee_subdomain": "ee",
            "postgres_db": "kobotoolbox"
        }

        config.update(self.__config)

        CLI.colored_print("What kind of installation do you want?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Private")
        CLI.colored_print("\t2) Public")
        config["installation"] = CLI.get_response(["1", "2"], config.get("installation", "2"))

        if config.get("installation") == "1":
            CLI.colored_print("Please choose which network interface you want to use?", CLI.COLOR_SUCCESS)
            interfaces = Network.get_local_interfaces()
            for interface, ip_address in interfaces.items():
                CLI.colored_print("\t{}) {}".format(interface, ip_address))

            default_interface = interfaces["eth0"] if "eth0" in interfaces.keys() else interfaces.values()[0]
            config["local_interface"] = CLI.get_response(
                [str(interface) for interface in interfaces.values()],
                config.get("local_interface", default_interface))

        else:
            config["domain_name"] = CLI.colored_input("Domain name", CLI.COLOR_SUCCESS, config.get("domain_name", ""))
            config["kpi_subdomain"] = CLI.colored_input("KPI sub domain", CLI.COLOR_SUCCESS,
                                                        config.get("kpi_subdomain", ""))
            config["kc_subdomain"] = CLI.colored_input("KoBoCat sub domain", CLI.COLOR_SUCCESS,
                                                       config.get("kc_subdomain", ""))
            config["ee_subdomain"] = CLI.colored_input("Enketo Express sub domain name", CLI.COLOR_SUCCESS,
                                                       config.get("ee_subdomain", ""))
            CLI.colored_print("Use HTTPS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("Please note that certificate has to be installed on a load balancer!", CLI.COLOR_INFO)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            config["https"] = CLI.get_response(["1", "2"], config.get("https", "2"))

            CLI.colored_print("Number of uWSGi workers to start?", CLI.COLOR_SUCCESS)
            config["workers_start"] = CLI.get_response(
                "~\d+",
                config.get("workers_start", "1"))
            CLI.colored_print("Max uWSGi workers?", CLI.COLOR_SUCCESS)
            config["workers_max"] = CLI.get_response(
                "~\d+",
                config.get("workers_max", "2"))

        # Raven
        config["kpi_raven"] = CLI.colored_input("KPI Raven token", CLI.COLOR_SUCCESS, config.get("kpi_raven"))
        config["kobocat_raven"] = CLI.colored_input("KoBoCat Raven token", CLI.COLOR_SUCCESS, config.get("kobocat_raven"))
        config["kpi_raven_js"] = CLI.colored_input("KPI Raven JS token", CLI.COLOR_SUCCESS, config.get("kpi_raven_js"))

        # Debug
        CLI.colored_print("Enable DEBUG?", CLI.COLOR_SUCCESS)
        CLI.colored_print("Not RECOMMENDED on production!", CLI.COLOR_ERROR)
        CLI.colored_print("\t1) True")
        CLI.colored_print("\t2) False")
        config["debug"] = CLI.get_response(["1", "2"], config.get("debug", "2"))

        # Google Analytics
        config["google_ua"] = CLI.colored_input("Google Analytics Identifier", CLI.COLOR_SUCCESS, config.get("google_ua"))

        # Google API Key
        config["google_api_key"] = CLI.colored_input("Google API Key", CLI.COLOR_SUCCESS, config.get("google_api_key"))

        # Intercom
        config["intercom"] = CLI.colored_input("Intercom", CLI.COLOR_SUCCESS, config.get("intercom"))

        # SMTP
        config["smtp_host"] = CLI.colored_input("SMTP server", CLI.COLOR_SUCCESS, config.get("smtp_host"))
        config["smtp_port"] = CLI.colored_input("SMTP port", CLI.COLOR_SUCCESS, config.get("smtp_port"))
        config["smtp_user"] = CLI.colored_input("SMTP user", CLI.COLOR_SUCCESS, config.get("smtp_user"))
        if config.get("smtp_user"):
            config["smtp_password"] = CLI.colored_input("SMTP password", CLI.COLOR_SUCCESS, config.get("smtp_password"))
            CLI.colored_print("Use TLS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) True")
            CLI.colored_print("\t2) False")
            config["smtp_use_tls"] = CLI.get_response(["1", "2"], config.get("smtp_use_tls", "1"))
        config["default_from_email"] = CLI.colored_input("From email address", CLI.COLOR_SUCCESS,
                                                            config.get("default_from_email"))

        # DB
        config["postgres_db"] = CLI.colored_input("Postgres database", CLI.COLOR_SUCCESS, config.get("postgres_db"))
        config["postgres_user"] = CLI.colored_input("Postgres user", CLI.COLOR_SUCCESS, config.get("postgres_user"))
        config["postgres_password"] = CLI.colored_input("Postgres password", CLI.COLOR_SUCCESS, config.get("postgres_password"))

        # AWS
        CLI.colored_print("Use AWS?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        config["use_aws"] = CLI.get_response(["1", "2"], config.get("use_aws", "2"))
        if config["use_aws"] == "1":
            config["aws_access_key"] = CLI.colored_input("AWS Access Key", CLI.COLOR_SUCCESS,
                                                            config.get("aws_access_key"))
            config["aws_secret_key"] = CLI.colored_input("AWS Secret Key", CLI.COLOR_SUCCESS,
                                                            config.get("aws_secret_key"))
            config["aws_bucket_name"] = CLI.colored_input("AWS Bucket name", CLI.COLOR_SUCCESS,
                                                         config.get("aws_bucket_name"))


        self.__config = config
        return config

        # # TODO Postgres config
        # # Mongo detection

    def __render_templates(self):

        template_variables = {
            "USE_AWS": "" if self.__config.get("USE_AWS") == "1" else "#",
            "AWS_ACCESS_KEY_ID": self.__config.get("aws_access_key", ""),
            "AWS_SECRET_ACCESS_KEY": self.__config.get("aws_secret_key", ""),
            "AWS_BUCKET_NAME": self.__config.get("aws_bucket_name", ""),
            "GOOGLE_UA": self.__config.get("google_ua", ""),
            "GOOGLE_API_KEY": self.__config.get("google_api_key", ""),
            "INTERCOM_APP_ID": self.__config.get("intercom", ""),
            "PRIVATE_DOMAIN_NAME": self.__config.get("private_domain_name", ""),
            "PUBLIC_DOMAIN_NAME": self.__config.get("public_domain_name", ""),
            "KOBOFORM_SUBDOMAIN": self.__config.get("kpi_subdomain", ""),
            "KOBOCAT_SUBDOMAIN": self.__config.get("kc_subdomain", ""),
            "ENKETO_EXPRESS_SUBDOMAIN": self.__config.get("ee_subdomain", ""),
            "ENKETO_API_TOKEN": binascii.hexlify(os.urandom(60)),
            "DJANGO_SECRET_KEY": binascii.hexlify(os.urandom(24)),
            "KOBOCAT_RAVEN_DSN": self.__config.get("kobocat_raven", ""),
            "KPI_RAVEN_DSN": self.__config.get("kpi_raven", ""),
            "KPI_RAVEN_JS_DSN": self.__config.get("kpi_raven_js", ""),
            "POSTGRES_DB": self.__config.get("postgres_db", ""),
            "POSTGRES_USER": self.__config.get("postgres_user", ""),
            "POSTGRES_PASSWORD": self.__config.get("postgres_password", ""),
            "DEBUG": self.__config.get("debug", False) == "Y",
            "SMTP_HOST": self.__config.get("smtp_host", ""),
            "SMTP_PORT": self.__config.get("smtp_port", ""),
            "SMTP_USER": self.__config.get("smtp_user", ""),
            "SMTP_PASSWORD": self.__config.get("smtp_password", ""),
            "SMTP_USE_TLS": self.__config.get("smtp_use_tls", "1") == "1",
            "DEFAULT_FROM_EMAIL": self.__config.get("default_from_email", "")
        }

        print(template_variables)

    def __create_directory(self):
        # Installation directory
        CLI.colored_print("Where do you want to install?", CLI.COLOR_SUCCESS)
        while True:
            self.__config["kobodocker_path"] = CLI.colored_input("", CLI.COLOR_SUCCESS, self.__config.get("kobodocker_path"))
            if os.path.isdir(self.__config["kobodocker_path"]):
                break
            else:
                try:
                    os.makedirs(self.__config["kobodocker_path"])
                    break
                except Exception as e:
                    CLI.colored_print("Please verify permissions.", CLI.COLOR_ERROR)
                    raise Exception("Could not create directoy!")

    def __git(self):

        self.__create_directory()

        if not os.path.isdir("{}/.git".format(self.__config["kobodocker_path"])):
            # clone project
            try:
                git_command = [
                    "git", "clone", "https://github.com/kobotoolbox/kobo-docker",
                    self.__config["kobodocker_path"]
                ]
                subprocess.check_output(git_command, universal_newlines=True,
                                        cwd=os.path.dirname(self.__config["kobodocker_path"]))
            except subprocess.CalledProcessError as cpe:
                CLI.colored_print(cpe.output, CLI.COLOR_ERROR)

        # update project
        if os.path.isdir("{}/.git".format(self.__config["kobodocker_path"])):
            try:
                git_command = ["git", "fetch", "--tags", "--prune"]
                subprocess.check_output(
                    git_command, universal_newlines=True, cwd=self.__config["kobodocker_path"]
                )
                git_command = ["git", "checkout", "--force", Setup.KOBO_DOCKER_BRANCH]
                subprocess.check_output(
                    git_command, universal_newlines=True, cwd=self.__config["kobodocker_path"]
                )
            except subprocess.CalledProcessError as cpe:
                CLI.colored_print(cpe.output, CLI.COLOR_ERROR)