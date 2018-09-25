# -*- coding: utf-8 -*-
import binascii
import fnmatch
import os
from string import Template as PyTemplate

from helpers.cli import CLI
from helpers.config import Config


class Template:

    @staticmethod
    def render(config):

        template_variables = {
            "PROTOCOL": "https" if config.get("https") == Config.TRUE else "http",
            "USE_AWS": "" if config.get("use_aws") == Config.TRUE else "#",
            "AWS_ACCESS_KEY_ID": config.get("aws_access_key", ""),
            "AWS_SECRET_ACCESS_KEY": config.get("aws_secret_key", ""),
            "AWS_BUCKET_NAME": config.get("aws_bucket_name", ""),
            "GOOGLE_UA": config.get("google_ua", ""),
            "GOOGLE_API_KEY": config.get("google_api_key", ""),
            "INTERCOM_APP_ID": config.get("intercom", ""),
            "PRIVATE_DOMAIN_NAME": config.get("private_domain_name", ""),
            "PUBLIC_DOMAIN_NAME": config.get("public_domain_name", ""),
            "KOBOFORM_SUBDOMAIN": config.get("kpi_subdomain", ""),
            "KOBOCAT_SUBDOMAIN": config.get("kc_subdomain", ""),
            "ENKETO_SUBDOMAIN": config.get("ee_subdomain", ""),
            "KOBO_SUPERUSER_USERNAME": config.get("super_user_username", ""),
            "KOBO_SUPERUSER_PASSWORD": config.get("super_user_password", ""),
            "ENKETO_API_TOKEN": binascii.hexlify(os.urandom(60)),
            "DJANGO_SECRET_KEY": binascii.hexlify(os.urandom(24)),
            "KOBOCAT_RAVEN_DSN": config.get("kobocat_raven", ""),
            "KPI_RAVEN_DSN": config.get("kpi_raven", ""),
            "KPI_RAVEN_JS_DSN": config.get("kpi_raven_js", ""),
            "POSTGRES_DB": config.get("postgres_db", ""),
            "POSTGRES_USER": config.get("postgres_user", ""),
            "POSTGRES_PASSWORD": config.get("postgres_password", ""),
            "DEBUG": config.get("debug", False) == "Y",
            "SMTP_HOST": config.get("smtp_host", ""),
            "SMTP_PORT": config.get("smtp_port", ""),
            "SMTP_USER": config.get("smtp_user", ""),
            "SMTP_PASSWORD": config.get("smtp_password", ""),
            "SMTP_USE_TLS": config.get("smtp_use_tls", Config.TRUE) == Config.TRUE,
            "DEFAULT_FROM_EMAIL": config.get("default_from_email", ""),
            "MASTER_BACKEND_IP": config.get("master_backend_ip"),
            "LOCAL_INTERFACE_IP": config.get("local_interface_ip"),
            "USE_PUBLIC_DNS": "" if config.get("local_installation") == Config.TRUE else "#",
            "USE_PRIVATE_DNS": "#" if config.get("use_private_dns") == Config.TRUE else "",
            "WORKERS_MAX": config.get("workers_max", ""),
            "WORKERS_START": config.get("workers_start", ""),
        }

        environment_directory = os.path.realpath("{}/../kobo-deployments".format(config["kobodocker_path"]))
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
                    t = PyTemplate(template.read())
                    print("RENDER {}".format(os.path.join(root, filename)))
                    print(t.substitute(template_variables))
                    print("           ")
                    print("           ")