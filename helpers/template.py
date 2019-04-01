# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import binascii
import fnmatch
import os
from string import Template as PyTemplate
import stat
import sys

from helpers.cli import CLI
from helpers.config import Config


class Template:

    UNIQUE_ID_FILE = ".uniqid"

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
            "GOOGLE_UA": config.get("google_ua", ""),
            "GOOGLE_API_KEY": config.get("google_api_key", ""),
            "INTERCOM_APP_ID": config.get("intercom", ""),
            "INTERNAL_DOMAIN_NAME": config.get("internal_domain_name", ""),
            "PRIVATE_DOMAIN_NAME": config.get("private_domain_name", ""),
            "PUBLIC_DOMAIN_NAME": config.get("public_domain_name", ""),
            "KOBOFORM_SUBDOMAIN": config.get("kpi_subdomain", ""),
            "KOBOCAT_SUBDOMAIN": config.get("kc_subdomain", ""),
            "ENKETO_SUBDOMAIN": config.get("ee_subdomain", ""),
            "KOBO_SUPERUSER_USERNAME": config.get("super_user_username", ""),
            "KOBO_SUPERUSER_PASSWORD": config.get("super_user_password", ""),
            "ENKETO_API_TOKEN": config.get("enketo_api_token", binascii.hexlify(os.urandom(60))),
            "DJANGO_SECRET_KEY": config.get("django_secret_key", binascii.hexlify(os.urandom(24))),
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
            "MAX_REQUESTS": config.get("max_requests", "512"),
            "SOFT_LIMIT": int(config.get("soft_limit", "128")) * 1024 * 1024,
            "POSTGRES_REPLICATION_PASSWORD": config.get("postgres_replication_password"),
            "WSGI_SERVER": "runserver_plus" if config.get("dev_mode") == Config.TRUE else "uWSGI",
            "USE_X_FORWARDED_HOST": "" if config.get("dev_mode") == Config.TRUE else "#",
            "OVERRIDE_POSTGRES_SETTINGS": "" if config.get("postgres_settings") == Config.TRUE else "#",
            "POSTGRES_APP_PROFILE": config.get("postgres_profile", ""),
            "POSTGRES_RAM": config.get("postgres_ram", ""),
            "POSTGRES_SETTINGS": config.get("postgres_settings_content", ""),
            "POSTGRES_BACKUP_FROM_SLAVE": "" if config.get("backup_from_master") == Config.FALSE else "#",
            "POSTGRES_PORT": config.get("postgresql_port", "5432"),
            "MONGO_PORT": config.get("mongo_port", "27017"),
            "REDIS_MAIN_PORT": config.get("redis_main_port", "6739"),
            "REDIS_CACHE_PORT": config.get("redis_cache_port", "6380"),
            "USE_BACKUP": "" if config.get("use_backup") == Config.TRUE else "#",
            "USE_AWS_BACKUP": "" if config_object.aws and
                                    config.get("use_backup") == Config.TRUE and
                                    config.get("aws_backup_bucket_name") != "" else "#",
            "USE_MEDIA_BACKUP": "" if not config_object.aws and config.get("use_backup") == Config.TRUE else "#",
            "KOBOCAT_MEDIA_BACKUP_SCHEDULE": config.get("kobocat_media_backup_schedule"),
            "MONGO_BACKUP_SCHEDULE": config.get("mongo_backup_schedule"),
            "POSTGRES_BACKUP_SCHEDULE": config.get("postgres_backup_schedule"),
            "REDIS_BACKUP_SCHEDULE": config.get("redis_backup_schedule"),
            "AWS_BACKUP_BUCKET_NAME": config.get("aws_backup_bucket_name"),
            "AWS_BACKUP_YEARLY_RETENTION": config.get("aws_backup_yearly_retention"),
            "AWS_BACKUP_MONTHLY_RETENTION": config.get("aws_backup_monthly_retention"),
            "AWS_BACKUP_WEEKLY_RETENTION": config.get("aws_backup_weekly_retention"),
            "AWS_BACKUP_DAILY_RETENTION": config.get("aws_backup_daily_retention"),
            "AWS_MONGO_BACKUP_MINIMUM_SIZE": config.get("aws_mongo_backup_minimum_size"),
            "AWS_POSTGRES_BACKUP_MINIMUM_SIZE": config.get("aws_postgres_backup_minimum_size"),
            "AWS_REDIS_BACKUP_MINIMUM_SIZE": config.get("aws_redis_backup_minimum_size"),
            "AWS_BACKUP_UPLOAD_CHUNK_SIZE": config.get("aws_backup_upload_chunk_size"),
            "AWS_BACKUP_BUCKET_DELETION_RULE_ENABLED": "False" if config.get(
                "aws_backup_bucket_deletion_rule_enabled") == Config.FALSE else "True",
        }

        environment_directory = os.path.realpath(os.path.normpath(os.path.join(config["kobodocker_path"],
                                                                               "..",
                                                                               "kobo-deployments")))
        unique_id = cls.__read_unique_id(environment_directory)
        if unique_id is not None and str(config.get("unique_id", "")) != str(unique_id):
            CLI.colored_print("╔═════════════════════════════════════════════════════════════════════╗",
                              CLI.COLOR_WARNING)
            CLI.colored_print("║ WARNING!                                                            ║",
                              CLI.COLOR_WARNING)
            CLI.colored_print("║ Existing environment files are detected. Files will be overwritten. ║",
                              CLI.COLOR_WARNING)
            CLI.colored_print("╚═════════════════════════════════════════════════════════════════════╝",
                              CLI.COLOR_WARNING)

            CLI.colored_print("Do you want to continue?", CLI.COLOR_SUCCESS)
            CLI.colored_print("\t1) Yes")
            CLI.colored_print("\t2) No")

            if CLI.get_response([Config.TRUE, Config.FALSE], Config.FALSE) == Config.FALSE:
                sys.exit()

        cls.__write_unique_id(environment_directory, config.get("unique_id"))

        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        templates_path = os.path.join(base_dir, "templates")
        for root, dirnames, filenames in os.walk(templates_path):
            destination_directory = cls.__create_directory(environment_directory, root, config, base_dir)
            for filename in fnmatch.filter(filenames, '*.tpl'):
                with open(os.path.join(root, filename), "r") as template:
                    t = PyTemplate(template.read())
                    with open(os.path.join(destination_directory, filename[:-4]), "w") as f:
                        f.write(t.substitute(template_variables))

    @classmethod
    def __create_directory(cls, environment_directory, path="", config={}, base_dir=""):

        if "docker-compose" in path:
            destination_directory = config.get("kobodocker_path")
        else:
            path = os.path.join(path, "")  # Handle case when path is root and equals "".
            destination_directory = os.path.realpath(os.path.join(environment_directory,
                                                 path.replace(os.path.join(
                                                     base_dir, "templates", ""), "")))
            if not os.path.isdir(destination_directory):
                try:
                    os.makedirs(destination_directory)
                except OSError:
                    CLI.colored_print("Can not create {}. Please verify permissions!".format(destination_directory),
                                      CLI.COLOR_ERROR)
                    sys.exit()

        return destination_directory

    @staticmethod
    def __read_unique_id(destination_directory):
        """
        Reads unique id from file `Template.UNIQUE_ID_FILE`
        :return: str
        """
        unique_id = ""

        if os.path.isdir(destination_directory):
            try:
                unique_id_file = os.path.join(destination_directory, Template.UNIQUE_ID_FILE)
                with open(unique_id_file, "r") as f:
                    unique_id = f.read().strip()
            except IOError:
                pass
        else:
            unique_id = None

        return unique_id

    @classmethod
    def __write_unique_id(cls, destination_directory, unique_id):
        try:
            unique_id_file = os.path.join(destination_directory, Template.UNIQUE_ID_FILE)
            # Ensure kobo-deployment is created.
            cls.__create_directory(destination_directory)

            with open(unique_id_file, "w") as f:
                f.write(str(unique_id))

            os.chmod(unique_id_file, stat.S_IWRITE | stat.S_IREAD)

        except (IOError, OSError):
            CLI.colored_print("Could not write unique_id file", CLI.COLOR_ERROR)
            return False

        return True
