# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import binascii
import fnmatch
import os
from string import Template as PyTemplate
import sys

from helpers.cli import CLI
from helpers.config import Config


class Template:

    @classmethod
    def render(cls, config_object):

        config = config_object.get_config()

        if config_object.local_install:
            nginx_port = config.get("exposed_nginx_docker_port", "80")
        else:
            nginx_port = config.get("nginx_proxy_port", "80")

        template_variables = {
            "PROTOCOL": "https" if config.get("https") == Config.TRUE else "http",
            "USE_HTTPS": "" if config.get("https") == Config.TRUE else "#",
            "USE_AWS": "" if config.get("use_aws") == Config.TRUE else "#",
            "AWS_ACCESS_KEY_ID": config.get("aws_access_key", ""),
            "AWS_SECRET_ACCESS_KEY": config.get("aws_secret_key", ""),
            "AWS_BUCKET_NAME": config.get("aws_bucket_name", ""),
            "AWS_BACKUP_BUCKET_NAME": config.get("aws_backup_bucket_name", ""),
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
            "DEBUG": config.get("debug", False) == Config.TRUE,
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
            "USE_DNS": "" if config.get("local_installation") == Config.TRUE or
                              config.get("use_private_dns") == Config.FALSE else "#",
            "WORKERS_MAX": config.get("workers_max", ""),
            "WORKERS_START": config.get("workers_start", ""),
            "KC_PATH": config.get("kc_path", ""),
            "KPI_PATH": config.get("kpi_path", ""),
            "USE_KPI_DEV_MODE": "#" if config.get("kpi_path", "") == "" else "",
            "USE_KC_DEV_MODE": "#" if config.get("kc_path", "") == "" else "",
            "KC_DEV_BUILD_ID": config.get("kc_dev_build_id", ""),
            "KPI_DEV_BUILD_ID": config.get("kpi_dev_build_id", ""),
            "NGINX_PUBLIC_PORT": config.get("exposed_nginx_docker_port", "80"),
            "NGINX_EXPOSED_PORT": nginx_port,
            "MAX_REQUESTS": config.get("max_request", "512"),
            "SOFT_LIMIT": int(config.get("soft_limit", "128")) * 1024 * 1024,
            "POSTGRES_REPLICATION_PASSWORD": config.get("postgres_replication_password"),
            "WSGI_SERVER": "runserver_plus" if config.get("dev_mode") == Config.TRUE else "uWSGI",
            "USE_X_FORWARDED_HOST": "" if config.get("dev_mode") == Config.TRUE else "#",
            "OVERRIDE_POSTGRES_MASTER": "" if config.get("postgres_settings") == Config.TRUE else "#",
            "POSTGRES_MASTER_APP_PROFILE": config.get("postgres_profile", ""),
            "POSTGRES_MASTER_RAM": config.get("postgres_ram", ""),
            "POSTGRES_MASTER_SETTINGS": config.get("postgres_settings_content", ""),
            "POSTGRES_PORT": config.get("postgresql_port", "5432"),
            "RABBITMQ_PORT": config.get("rabbit_port", "5672"),
            "MONGO_PORT": config.get("mongo_port", "27017"),
            "REDIS_MAIN_PORT": config.get("redis_main_port", "6739"),
            "REDIS_CACHE_PORT": config.get("redis_cache_port", "6380")
        }

        for root, dirnames, filenames in os.walk("./templates"):
            destination_directory = cls.__create_directory(root, config)
            for filename in fnmatch.filter(filenames, '*.tpl'):
                with open(os.path.join(root, filename), "r") as template:
                    t = PyTemplate(template.read())
                    with open(os.path.join(destination_directory, filename[:-4]), "w") as f:
                        f.write(t.substitute(template_variables))

    @staticmethod
    def __create_directory(path, config):
        environment_directory = os.path.realpath("{}/../kobo-deployments".format(config["kobodocker_path"]))
        if "docker-compose" in path:
            destination_directory = config["kobodocker_path"]
        else:
            destination_directory = path.replace("./templates", environment_directory)
            if not os.path.isdir(destination_directory):
                try:
                    os.makedirs(destination_directory)
                except Exception as e:
                    CLI.colored_print("Please verify permissions.", CLI.COLOR_ERROR)
                    sys.exit()

        return destination_directory
