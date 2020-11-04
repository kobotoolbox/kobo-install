# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import fnmatch
import json
import os
import re
import stat
import sys

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

from string import Template as PyTemplate

from helpers.cli import CLI
from helpers.config import Config


class Template:
    UNIQUE_ID_FILE = '.uniqid'

    @classmethod
    def render(cls, config_object, force=False):

        config = config_object.get_config()
        template_variables = cls.__get_template_variables(config_object)

        environment_directory = config_object.get_env_files_path()
        unique_id = cls.__read_unique_id(environment_directory)
        if force is not True and \
                unique_id is not None and str(
            config.get('unique_id', '')) != str(unique_id):
            CLI.colored_print(
                '╔═════════════════════════════════════════════════════════════════════╗',
                CLI.COLOR_WARNING)
            CLI.colored_print(
                '║ WARNING!                                                            ║',
                CLI.COLOR_WARNING)
            CLI.colored_print(
                '║ Existing environment files are detected. Files will be overwritten. ║',
                CLI.COLOR_WARNING)
            CLI.colored_print(
                '╚═════════════════════════════════════════════════════════════════════╝',
                CLI.COLOR_WARNING)

            CLI.colored_print('Do you want to continue?', CLI.COLOR_SUCCESS)
            CLI.colored_print('\t1) Yes')
            CLI.colored_print('\t2) No')

            if CLI.get_response(
                    [Config.TRUE, Config.FALSE],
                    Config.FALSE) == Config.FALSE:
                sys.exit()

        cls.__write_unique_id(environment_directory, config.get('unique_id'))

        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        templates_path_parent = os.path.join(base_dir, 'templates')

        # Environment
        templates_path = os.path.join(templates_path_parent,
                                      Config.ENV_FILES_DIR,
                                      '')
        for root, dirnames, filenames in os.walk(templates_path):
            destination_directory = cls.__create_directory(
                environment_directory,
                root,
                templates_path)
            cls.__write_templates(template_variables,
                                  root,
                                  destination_directory,
                                  filenames)

        # kobo-docker
        templates_path = os.path.join(templates_path_parent, 'kobo-docker')
        for root, dirnames, filenames in os.walk(templates_path):
            destination_directory = config.get('kobodocker_path')
            cls.__write_templates(template_variables,
                                  root,
                                  destination_directory,
                                  filenames)

        # nginx-certbox
        if config_object.use_letsencrypt:
            templates_path = os.path.join(templates_path_parent,
                                          Config.LETSENCRYPT_DOCKER_DIR, '')
            for root, dirnames, filenames in os.walk(templates_path):
                destination_directory = cls.__create_directory(
                    config_object.get_letsencrypt_repo_path(),
                    root,
                    templates_path)
                cls.__write_templates(template_variables,
                                      root,
                                      destination_directory,
                                      filenames)

    @classmethod
    def render_maintenance(cls, config_object):

        config = config_object.get_config()
        template_variables = cls.__get_template_variables(config_object)

        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        templates_path_parent = os.path.join(base_dir, 'templates')

        # kobo-docker
        templates_path = os.path.join(templates_path_parent, 'kobo-docker')
        for root, dirnames, filenames in os.walk(templates_path):
            filenames = [filename
                         for filename in filenames if 'maintenance' in filename]
            destination_directory = config.get('kobodocker_path')
            cls.__write_templates(template_variables,
                                  root,
                                  destination_directory,
                                  filenames)

    @classmethod
    def __create_directory(cls, template_root_directory, path='', base_dir=''):

        # Handle case when path is root and equals ''.
        path = os.path.join(path, '')

        destination_directory = os.path.realpath(os.path.join(
            template_root_directory,
            path.replace(base_dir, '')
        ))

        if not os.path.isdir(destination_directory):
            try:
                os.makedirs(destination_directory)
            except OSError:
                CLI.colored_print(
                    'Can not create {}. '
                    'Please verify permissions!'.format(destination_directory),
                    CLI.COLOR_ERROR)
                sys.exit(1)

        return destination_directory

    @staticmethod
    def __get_template_variables(config_object):

        config = config_object.get_config()

        def _get_value(property_, true_value='', false_value='#',
                       comparison_value=Config.TRUE):
            return true_value \
                if config.get(property_) == comparison_value \
                else false_value

        if config_object.proxy:
            nginx_port = config.get('nginx_proxy_port')
        else:
            nginx_port = config.get('exposed_nginx_docker_port')

        return {
            'PROTOCOL': _get_value('https', 'https', 'http'),
            'USE_HTTPS': _get_value('https'),
            'USE_AWS': _get_value('use_aws'),
            'AWS_ACCESS_KEY_ID': config.get('aws_access_key', ''),
            'AWS_SECRET_ACCESS_KEY': config.get('aws_secret_key', ''),
            'AWS_BUCKET_NAME': config.get('aws_bucket_name', ''),
            'GOOGLE_UA': config.get('google_ua', ''),
            'GOOGLE_API_KEY': config.get('google_api_key', ''),
            'INTERNAL_DOMAIN_NAME': config.get('internal_domain_name', ''),
            'PRIVATE_DOMAIN_NAME': config.get('private_domain_name', ''),
            'PUBLIC_DOMAIN_NAME': config.get('public_domain_name', ''),
            'KOBOFORM_SUBDOMAIN': config.get('kpi_subdomain', ''),
            'KOBOCAT_SUBDOMAIN': config.get('kc_subdomain', ''),
            'ENKETO_SUBDOMAIN': config.get('ee_subdomain', ''),
            'KOBO_SUPERUSER_USERNAME': config.get('super_user_username', ''),
            'KOBO_SUPERUSER_PASSWORD': config.get('super_user_password', ''),
            'ENKETO_API_KEY': config.get('enketo_api_token'),
            'DJANGO_SECRET_KEY': config.get('django_secret_key'),
            'ENKETO_ENCRYPTION_KEY': config.get('enketo_encryption_key'),
            'ENKETO_LESS_SECURE_ENCRYPTION_KEY': config.get(
                'enketo_less_secure_encryption_key'),
            'KOBOCAT_RAVEN_DSN': config.get('kobocat_raven', ''),
            'KPI_RAVEN_DSN': config.get('kpi_raven', ''),
            'KPI_RAVEN_JS_DSN': config.get('kpi_raven_js', ''),
            'KC_POSTGRES_DB': config.get('kc_postgres_db', ''),
            'KPI_POSTGRES_DB': config.get('kpi_postgres_db', ''),
            'POSTGRES_USER': config.get('postgres_user', ''),
            'POSTGRES_PASSWORD': config.get('postgres_password', ''),
            'POSTGRES_PASSWORD_URL_ENCODED': quote_plus(
                config.get('postgres_password', '')),
            'DEBUG': config.get('debug', False) == Config.TRUE,
            'SMTP_HOST': config.get('smtp_host', ''),
            'SMTP_PORT': config.get('smtp_port', ''),
            'SMTP_USER': config.get('smtp_user', ''),
            'SMTP_PASSWORD': config.get('smtp_password', ''),
            'SMTP_USE_TLS': config.get('smtp_use_tls',
                                       Config.TRUE) == Config.TRUE,
            'DEFAULT_FROM_EMAIL': config.get('default_from_email', ''),
            'PRIMARY_BACKEND_IP': config.get('primary_backend_ip'),
            'LOCAL_INTERFACE_IP': config.get('local_interface_ip'),
            'KC_PATH': config.get('kc_path', ''),
            'KPI_PATH': config.get('kpi_path', ''),
            'USE_KPI_DEV_MODE': _get_value('kpi_path',
                                           true_value='#',
                                           false_value='',
                                           comparison_value=''),
            'USE_KC_DEV_MODE': _get_value('kc_path',
                                          true_value='#',
                                          false_value='',
                                          comparison_value=''),
            'KC_DEV_BUILD_ID': config.get('kc_dev_build_id', ''),
            'KPI_DEV_BUILD_ID': config.get('kpi_dev_build_id', ''),
            'NGINX_PUBLIC_PORT': config.get('exposed_nginx_docker_port',
                                            Config.DEFAULT_NGINX_PORT),
            'NGINX_EXPOSED_PORT': nginx_port,
            'UWSGI_WORKERS_MAX': config.get('uwsgi_workers_max'),
            'UWSGI_WORKERS_START': config.get('uwsgi_workers_start'),
            'UWSGI_MAX_REQUESTS': config.get('uwsgi_max_requests'),
            'UWSGI_SOFT_LIMIT': int(
                config.get('uwsgi_soft_limit')) * 1024 * 1024,
            'UWSGI_HARAKIRI': config.get('uwsgi_harakiri'),
            'UWSGI_WORKER_RELOAD_MERCY': config.get(
                'uwsgi_worker_reload_mercy'),
            'UWSGI_PASS_TIMEOUT': int(config.get('uwsgi_harakiri')) + 10,
            'POSTGRES_REPLICATION_PASSWORD': config.get(
                'postgres_replication_password'),
            'WSGI_SERVER': 'runserver_plus' if config_object.dev_mode else 'uWSGI',
            'USE_X_FORWARDED_HOST': '' if config_object.dev_mode else '#',
            'OVERRIDE_POSTGRES_SETTINGS': _get_value('postgres_settings'),
            'POSTGRES_APP_PROFILE': config.get('postgres_profile', ''),
            'POSTGRES_RAM': config.get('postgres_ram', ''),
            'POSTGRES_SETTINGS': config.get('postgres_settings_content', ''),
            'POSTGRES_BACKUP_FROM_SECONDARY': _get_value(
                'backup_from_primary',
                comparison_value=Config.FALSE),
            'POSTGRES_PORT': config.get('postgresql_port', '5432'),
            'MONGO_PORT': config.get('mongo_port', '27017'),
            'REDIS_MAIN_PORT': config.get('redis_main_port', '6739'),
            'REDIS_CACHE_PORT': config.get('redis_cache_port', '6380'),
            'USE_BACKUP': '' if config.get(
                'use_backup') == Config.TRUE else '#',
            'USE_WAL_E': _get_value('use_wal_e'),
            'USE_AWS_BACKUP': '' if config_object.aws and
                                    config.get('use_backup') == Config.TRUE and
                                    config.get(
                                        'aws_backup_bucket_name') != '' else '#',
            'USE_MEDIA_BACKUP': '' if (not config_object.aws and
                                       config.get('use_backup') == Config.TRUE) else '#',
            'KOBOCAT_MEDIA_BACKUP_SCHEDULE': config.get(
                'kobocat_media_backup_schedule'),
            'MONGO_BACKUP_SCHEDULE': config.get('mongo_backup_schedule'),
            'POSTGRES_BACKUP_SCHEDULE': config.get('postgres_backup_schedule'),
            'REDIS_BACKUP_SCHEDULE': config.get('redis_backup_schedule'),
            'AWS_BACKUP_BUCKET_NAME': config.get('aws_backup_bucket_name'),
            'AWS_BACKUP_YEARLY_RETENTION': config.get(
                'aws_backup_yearly_retention'),
            'AWS_BACKUP_MONTHLY_RETENTION': config.get(
                'aws_backup_monthly_retention'),
            'AWS_BACKUP_WEEKLY_RETENTION': config.get(
                'aws_backup_weekly_retention'),
            'AWS_BACKUP_DAILY_RETENTION': config.get(
                'aws_backup_daily_retention'),
            'AWS_MONGO_BACKUP_MINIMUM_SIZE': config.get(
                'aws_mongo_backup_minimum_size'),
            'AWS_POSTGRES_BACKUP_MINIMUM_SIZE': config.get(
                'aws_postgres_backup_minimum_size'),
            'AWS_REDIS_BACKUP_MINIMUM_SIZE': config.get(
                'aws_redis_backup_minimum_size'),
            'AWS_BACKUP_UPLOAD_CHUNK_SIZE': config.get(
                'aws_backup_upload_chunk_size'),
            'AWS_BACKUP_BUCKET_DELETION_RULE_ENABLED': _get_value(
                'aws_backup_bucket_deletion_rule_enabled', 'True', 'False'),
            'LETSENCRYPT_EMAIL': config.get('letsencrypt_email'),
            'MAINTENANCE_ETA': config.get('maintenance_eta', ''),
            'MAINTENANCE_DATE_ISO': config.get('maintenance_date_iso', ''),
            'MAINTENANCE_DATE_STR': config.get('maintenance_date_str', ''),
            'MAINTENANCE_EMAIL': config.get('maintenance_email', ''),
            'USE_NPM_FROM_HOST': '' if (config_object.dev_mode and
                                        config.get(
                                            'npm_container') == Config.FALSE) else '#',
            'DOCKER_PREFIX': config_object.get_prefix('backend'),
            'USE_BACKEND_NETWORK': _get_value('expose_backend_ports',
                                              comparison_value=Config.FALSE),
            'EXPOSE_BACKEND_PORTS': _get_value('expose_backend_ports'),
            'USE_FAKE_DNS': _get_value('local_installation'),
            'ADD_BACKEND_EXTRA_HOSTS': '' if (
                        config_object.expose_backend_ports and
                        not config_object.use_private_dns) else '#',
            'USE_EXTRA_HOSTS': '' if (config_object.local_install or
                                      config_object.expose_backend_ports and
                                      not config_object.use_private_dns) else '#',
            'MONGO_ROOT_USERNAME': config.get('mongo_root_username'),
            'MONGO_ROOT_PASSWORD': config.get('mongo_root_password'),
            'MONGO_USER_USERNAME': config.get('mongo_user_username'),
            'MONGO_USER_PASSWORD': config.get('mongo_user_password'),
            'REDIS_PASSWORD': config.get('redis_password'),
            'REDIS_PASSWORD_URL_ENCODED': quote_plus(
                config.get('redis_password')),
            'REDIS_PASSWORD_JS_ENCODED': json.dumps(
                config.get('redis_password')),
        }

    @staticmethod
    def __read_unique_id(destination_directory):
        """
        Reads unique id from file `Template.UNIQUE_ID_FILE`
        :return: str
        """
        unique_id = ''

        if os.path.isdir(destination_directory):
            try:
                unique_id_file = os.path.join(destination_directory,
                                              Template.UNIQUE_ID_FILE)
                with open(unique_id_file, 'r') as f:
                    unique_id = f.read().strip()
            except IOError:
                pass
        else:
            unique_id = None

        return unique_id

    @staticmethod
    def __write_templates(template_variables_, root_, destination_directory_,
                          filenames_):
        for filename in fnmatch.filter(filenames_, '*.tpl'):
            with open(os.path.join(root_, filename), 'r') as template:
                t = ExtendedPyTemplate(template.read(), template_variables_)
                with open(os.path.join(destination_directory_, filename[:-4]),
                          'w') as f:
                    f.write(t.substitute(template_variables_))

    @classmethod
    def __write_unique_id(cls, destination_directory, unique_id):
        try:
            unique_id_file = os.path.join(destination_directory,
                                          Template.UNIQUE_ID_FILE)
            # Ensure kobo-deployment is created.
            cls.__create_directory(destination_directory)

            with open(unique_id_file, 'w') as f:
                f.write(str(unique_id))

            os.chmod(unique_id_file, stat.S_IWRITE | stat.S_IREAD)

        except (IOError, OSError):
            CLI.colored_print('Could not write unique_id file', CLI.COLOR_ERROR)
            return False

        return True


class ExtendedPyTemplate(PyTemplate):
    """
    Basic class to add conditional substitution to `string.Template`

    Usage example:
    ```
    {
        'host': 'redis-cache.kobo.local',
        'port': '6379'{% if REDIS_PASSWORD %},{% endif REDIS_PASSWORD %}
        {% if REDIS_PASSWORD %}
        'password': ${REDIS_PASSWORD}
        {% endif REDIS_PASSWORD %}
    }
    ```

    If `REDIS_PASSWORD` equals '123456', output would be:
    ```
    {
        'host': 'redis-cache.kobo.local',
        'port': '6379',
        'password': '123456'
    }
    ```

    If `REDIS_PASSWORD` equals '' (or `False` or `None`), output would be:
    ```
    {
        'host': 'redis-cache.kobo.local',
        'port': '6379'

    }
    ```

    """
    IF_PATTERN = '{{% if {} %}}'
    ENDIF_PATTERN = '{{% endif {} %}}'

    def __init__(self, template, template_variables_):
        for key, value in template_variables_.items():
            if self.IF_PATTERN.format(key) in template:
                if value:
                    if_pattern = r'{}\s*'.format(self.IF_PATTERN.format(key))
                    endif_pattern = r'\s*{}'.format(
                        self.ENDIF_PATTERN.format(key))
                    template = re.sub(if_pattern, '', template)
                    template = re.sub(endif_pattern, '', template)
                else:
                    pattern = r'{}(.|\s)*?{}'.format(
                        self.IF_PATTERN.format(key),
                        self.ENDIF_PATTERN.format(key))
                    template = re.sub(pattern, '', template)
        super(ExtendedPyTemplate, self).__init__(template)
