# -*- coding: utf-8 -*-
import binascii
import fnmatch
import os
from string import Template

import subprocess

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network


class Setup:

    KOBO_DOCKER_BRANCH = "multi_compose"
    TRUE = "1"
    FALSE = "2"

    def __init__(self, config):
        self.__config = config

    def render_templates(self):

        template_variables = {
            "PROTOCOL": "https" if self.__config.get("https") == Setup.TRUE else "http",
            "USE_AWS": "" if self.__config.get("use_aws") == Setup.TRUE else "#",
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
            "ENKETO_SUBDOMAIN": self.__config.get("ee_subdomain", ""),
            "KOBO_SUPERUSER_USERNAME": self.__config.get("super_user_username", ""),
            "KOBO_SUPERUSER_PASSWORD": self.__config.get("super_user_password", ""),
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
            "SMTP_USE_TLS": self.__config.get("smtp_use_tls", Setup.TRUE) == Setup.TRUE,
            "DEFAULT_FROM_EMAIL": self.__config.get("default_from_email", ""),
            "MASTER_BACKEND_IP": self.__config.get("master_backend_ip"),
            "LOCAL_INTERFACE_IP": self.__config.get("local_interface_ip"),
            "USE_PUBLIC_DNS": "" if self.__config.get("local_installation") == Setup.TRUE else "#",
            "USE_PRIVATE_DNS": "#" if self.__config.get("use_private_dns") == Setup.TRUE else "",
            "WORKERS_MAX": self.__config.get("workers_max", ""),
            "WORKERS_START": self.__config.get("workers_start", ""),
        }

        environment_directory = os.path.realpath("{}/../kobo-deployments".format(self.__config["kobodocker_path"]))
        if not os.path.isdir(environment_directory):
            try:
                os.makedirs(environment_directory)
            except Exception as e:
                CLI.colored_print("Please verify permissions.", CLI.COLOR_ERROR)
                raise Exception("Could not create environment directory!")

        matches = []
        for root, dirnames, filenames in os.walk("./templates"):
            for filename in fnmatch.filter(filenames, '*.tpl'):
                with open(os.path.join(root, filename), "r") as template:
                    t = Template(template.read())
                    print("RENDER {}".format(os.path.join(root, filename)))
                    print(t.substitute(template_variables))
                    print("           ")
                    print("           ")

        #print(matches)
        #print(template_variables)

    def run(self):
        self.__create_config()
        Config.write_config(self.__config)
        self.render_templates()
        #self.__git()

    def __create_config(self):
        config = {
            "workers_max": "4",
            "workers_start": "2",
            "debug": Setup.FALSE,
            "kobodocker_path": os.path.realpath("{}/../kobo-docker".format(
                os.path.dirname(os.path.realpath(__file__)))
            ),
            "public_domain_name": "kobotoolbox.local",
            "kpi_subdomain": "kpi",
            "kc_subdomain": "kc",
            "ee_subdomain": "ee",
            "postgres_db": "kobotoolbox",
            "postgres_user": "kobo",
            "postgres_password": "kobo",
            "private_domain_name": "docker.internal"
        }

        first_time = self.__config.get("date_created") is None

        config.update(self.__config)


        CLI.colored_print("Do you want to see advanced options?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        config["advanced"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("advanced", Setup.FALSE))

        CLI.colored_print("What kind of installation do you need?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) On your workstation")
        CLI.colored_print("\t2) On a server")
        config["local_installation"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("local_installation", Setup.FALSE))
        config["local_interface_ip"] = Network.get_primary_ip()
        config["master_backend_ip"] = Network.get_primary_ip()

        if config.get("local_installation") == Setup.FALSE:

            config["public_domain_name"] = CLI.colored_input("Public domain name", CLI.COLOR_SUCCESS, config.get("public_domain_name", ""))
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
            config["https"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("https", Setup.TRUE))

            if config.get("advanced") == Setup.TRUE:
                CLI.colored_print("Do you want to use separate containers for frontend and backend?", CLI.COLOR_SUCCESS)
                CLI.colored_print("\t1) Yes")
                CLI.colored_print("\t2) No")
                config["multi"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("multi", Setup.FALSE))

                if config.get("multi") == Setup.TRUE:
                    CLI.colored_print("Do you use a DNS for private routes?", CLI.COLOR_SUCCESS)
                    CLI.colored_print("\t1) Yes")
                    CLI.colored_print("\t2) No")
                    config["use_private_dns"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("use_private_dns", Setup.FALSE))

                    if config["use_private_dns"] == Setup.FALSE:
                        CLI.colored_print("IP address (IPv4) of backend server?", CLI.COLOR_SUCCESS)
                        config["master_backend_ip"] = CLI.get_response(
                            "~\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
                            config.get("master_backend_ip"))

        elif config.get("advanced") == Setup.TRUE:
            CLI.colored_print("Please choose which network interface you want to use?", CLI.COLOR_SUCCESS)
            interfaces = Network.get_local_interfaces()
            for interface, ip_address in interfaces.items():
                CLI.colored_print("\t{}) {}".format(interface, ip_address))

            config["local_interface"] = CLI.get_response(
                [str(interface) for interface in interfaces.keys()],
                config.get("local_interface"))

            config["local_interface_ip"] = interfaces[config.get("local_interface")]
            config["master_backend_ip"] = config.get("local_interface_ip")

        # SMTP.
        config["smtp_host"] = CLI.colored_input("SMTP server", CLI.COLOR_SUCCESS, config.get("smtp_host"))
        config["smtp_port"] = CLI.colored_input("SMTP port", CLI.COLOR_SUCCESS, config.get("smtp_port"))
        config["smtp_user"] = CLI.colored_input("SMTP user", CLI.COLOR_SUCCESS, config.get("smtp_user"))
        if config.get("smtp_user"):
            config["smtp_password"] = CLI.colored_input("SMTP password", CLI.COLOR_SUCCESS, config.get("smtp_password"))
            CLI.colored_print("Use TLS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) True")
            CLI.colored_print("\t2) False")
            config["smtp_use_tls"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("smtp_use_tls", Setup.TRUE))
        config["default_from_email"] = CLI.colored_input("From email address", CLI.COLOR_SUCCESS,
                                                            config.get("default_from_email"))

        # Super user. Only ask for credentials the first time.
        # Super user is created if db doesn't exists.
        username = CLI.colored_input("Super user's username", CLI.COLOR_SUCCESS,
                                                          config.get("super_user_username"))
        password = CLI.colored_input("Super user's password", CLI.COLOR_SUCCESS,
                                                          config.get("super_user_password"))

        if (username != config.get("super_user_username") or password != config.get("super_user_password")) and \
            not first_time:
            CLI.colored_print("########################################################", CLI.COLOR_WARNING)
            CLI.colored_print("# Username or password have been changed!              #", CLI.COLOR_WARNING)
            CLI.colored_print("# Don't forget to apply these changes in Postgres too. #", CLI.COLOR_WARNING)
            CLI.colored_print("# Super user's credentials won't be updated if the     #", CLI.COLOR_WARNING)
            CLI.colored_print("# database already exists.                             #", CLI.COLOR_WARNING)
            CLI.colored_print("########################################################", CLI.COLOR_WARNING)

        config["super_user_username"] = username
        config["super_user_password"] = password

        if config.get("advanced") == Setup.TRUE:
            # DB
            config["postgres_db"] = CLI.colored_input("Postgres database", CLI.COLOR_SUCCESS, config.get("postgres_db"))
            config["postgres_user"] = CLI.colored_input("Postgres user", CLI.COLOR_SUCCESS, config.get("postgres_user"))
            config["postgres_password"] = CLI.colored_input("Postgres password", CLI.COLOR_SUCCESS,
                                                            config.get("postgres_password"))
            # AWS
            CLI.colored_print("Use AWS?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")
            config["use_aws"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("use_aws", Setup.FALSE))
            if config["use_aws"] == Setup.TRUE:
                config["aws_access_key"] = CLI.colored_input("AWS Access Key", CLI.COLOR_SUCCESS,
                                                             config.get("aws_access_key"))
                config["aws_secret_key"] = CLI.colored_input("AWS Secret Key", CLI.COLOR_SUCCESS,
                                                             config.get("aws_secret_key"))
                config["aws_bucket_name"] = CLI.colored_input("AWS Bucket name", CLI.COLOR_SUCCESS,
                                                              config.get("aws_bucket_name"))

            CLI.colored_print("Number of uWSGi workers to start?", CLI.COLOR_SUCCESS)
            config["workers_start"] = CLI.get_response(
                "~\d+",
                config.get("workers_start", Setup.TRUE))
            CLI.colored_print("Max uWSGi workers?", CLI.COLOR_SUCCESS)
            config["workers_max"] = CLI.get_response(
                "~\d+",
                config.get("workers_max", "2"))

            # Google Analytics
            config["google_ua"] = CLI.colored_input("Google Analytics Identifier", CLI.COLOR_SUCCESS,
                                                    config.get("google_ua"))

            # Google API Key
            config["google_api_key"] = CLI.colored_input("Google API Key", CLI.COLOR_SUCCESS,
                                                         config.get("google_api_key"))

            # Intercom
            config["intercom"] = CLI.colored_input("Intercom", CLI.COLOR_SUCCESS, config.get("intercom"))

            # Raven
            config["kpi_raven"] = CLI.colored_input("KPI Raven token", CLI.COLOR_SUCCESS, config.get("kpi_raven"))
            config["kobocat_raven"] = CLI.colored_input("KoBoCat Raven token", CLI.COLOR_SUCCESS,
                                                        config.get("kobocat_raven"))
            config["kpi_raven_js"] = CLI.colored_input("KPI Raven JS token", CLI.COLOR_SUCCESS, config.get("kpi_raven_js"))

            # Debug
            CLI.colored_print("Enable DEBUG?", CLI.COLOR_SUCCESS)
            CLI.colored_print("Not RECOMMENDED on production!", CLI.COLOR_ERROR)
            CLI.colored_print("\t1) True")
            CLI.colored_print("\t2) False")
            config["debug"] = CLI.get_response([Setup.TRUE, Setup.FALSE], config.get("debug", Setup.FALSE))

        self.__config = config

        print(config)

        return config

        # # TODO Postgres config
        # # Mongo detection

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
                    raise Exception("Could not create kobo-docker directory!")

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