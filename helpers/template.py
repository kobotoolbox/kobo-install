# -*- coding: utf-8 -*-
import fnmatch
import json
import os
import re
import stat
import sys
from string import Template as PyTemplate

from helpers.cli import CLI
from helpers.config import Config


class Template:
    UNIQUE_ID_FILE = '.uniqid'

    @classmethod
    def render(cls, config, force=False):
        """
        Write configuration files based on `config`

        Args:
            config (helpers.config.Config)
            force (bool)
        """

        dict_ = config.get_dict()
        template_variables = cls.__get_template_variables(config)

        environment_directory = config.get_env_files_path()
        unique_id = cls.__read_unique_id(environment_directory)
        if (
            not force and unique_id
            and str(dict_.get('unique_id', '')) != str(unique_id)
        ):
            message = (
                'WARNING!\n\n'
                'Existing environment files are detected. Files will be '
                'overwritten.'
            )
            CLI.framed_print(message)
            response = CLI.yes_no_question(
                'Do you want to continue?',
                default=False
            )
            if not response:
                sys.exit(0)

        cls.__write_unique_id(environment_directory, dict_['unique_id'])

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
            destination_directory = dict_['kobodocker_path']
            cls.__write_templates(template_variables,
                                  root,
                                  destination_directory,
                                  filenames)

        # nginx-certbox
        if config.use_letsencrypt:
            templates_path = os.path.join(templates_path_parent,
                                          Config.LETSENCRYPT_DOCKER_DIR, '')
            for root, dirnames, filenames in os.walk(templates_path):
                destination_directory = cls.__create_directory(
                    config.get_letsencrypt_repo_path(),
                    root,
                    templates_path)
                cls.__write_templates(template_variables,
                                      root,
                                      destination_directory,
                                      filenames)

    @classmethod
    def render_maintenance(cls, config):

        dict_ = config.get_dict()
        template_variables = cls.__get_template_variables(config)

        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        templates_path_parent = os.path.join(base_dir, 'templates')

        # kobo-docker
        templates_path = os.path.join(templates_path_parent, 'kobo-docker')
        for root, dirnames, filenames in os.walk(templates_path):
            filenames = [filename
                         for filename in filenames if 'maintenance' in filename]
            destination_directory = dict_['kobodocker_path']
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
                    f'Can not create {destination_directory}. '
                    'Please verify permissions!',
                    CLI.COLOR_ERROR)
                sys.exit(1)

        return destination_directory

    @staticmethod
    def __get_template_variables(config):
        """
        Write configuration files based on `config`

        Args:
            config (helpers.config.Config)
        """

        dict_ = config.get_dict()

        def _get_value(property_, true_value='', false_value='#',
                       comparison_value=True):
            return (
                true_value
                if dict_[property_] == comparison_value
                else false_value
            )

        if config.proxy:
            nginx_port = dict_['nginx_proxy_port']
        else:
            nginx_port = dict_['exposed_nginx_docker_port']

        return {
            'PROTOCOL': _get_value('https', 'https', 'http'),
            'USE_HTTPS': _get_value('https'),
            'USE_AWS': _get_value('use_aws'),
            'AWS_ACCESS_KEY_ID': dict_['aws_access_key'],
            'AWS_SECRET_ACCESS_KEY': dict_['aws_secret_key'],
            'AWS_BUCKET_NAME': dict_['aws_bucket_name'],
            'AWS_S3_REGION_NAME': dict_['aws_s3_region_name'],
            'GOOGLE_UA': dict_['google_ua'],
            'GOOGLE_API_KEY': dict_['google_api_key'],
            'INTERNAL_DOMAIN_NAME': dict_['internal_domain_name'],
            'PRIVATE_DOMAIN_NAME': dict_['private_domain_name'],
            'PUBLIC_DOMAIN_NAME': dict_['public_domain_name'],
            'KOBOFORM_SUBDOMAIN': dict_['kpi_subdomain'],
            'KOBOCAT_SUBDOMAIN': dict_['kc_subdomain'],
            'ENKETO_SUBDOMAIN': dict_['ee_subdomain'],
            'KOBO_SUPERUSER_USERNAME': dict_['super_user_username'],
            'KOBO_SUPERUSER_PASSWORD': dict_['super_user_password'],
            'ENKETO_API_KEY': dict_['enketo_api_token'],
            'DJANGO_SECRET_KEY': dict_['django_secret_key'],
            'DJANGO_SESSION_COOKIE_AGE': dict_['django_session_cookie_age'],
            'ENKETO_ENCRYPTION_KEY': dict_['enketo_encryption_key'],
            'ENKETO_LESS_SECURE_ENCRYPTION_KEY': dict_[
                'enketo_less_secure_encryption_key'],
            'KOBOCAT_RAVEN_DSN': dict_['kobocat_raven'],
            'KPI_RAVEN_DSN': dict_['kpi_raven'],
            'KPI_RAVEN_JS_DSN': dict_['kpi_raven_js'],
            'KC_POSTGRES_DB': dict_['kc_postgres_db'],
            'KPI_POSTGRES_DB': dict_['kpi_postgres_db'],
            'POSTGRES_USER': dict_['postgres_user'],
            'POSTGRES_PASSWORD': dict_['postgres_password'],
            'DEBUG': dict_['debug'],
            'SMTP_HOST': dict_['smtp_host'],
            'SMTP_PORT': dict_['smtp_port'],
            'SMTP_USER': dict_['smtp_user'],
            'SMTP_PASSWORD': dict_['smtp_password'],
            'SMTP_USE_TLS': dict_['smtp_use_tls'],
            'DEFAULT_FROM_EMAIL': dict_['default_from_email'],
            'PRIMARY_BACKEND_IP': dict_['primary_backend_ip'],
            'LOCAL_INTERFACE_IP': dict_['local_interface_ip'],
            'KC_PATH': dict_['kc_path'],
            'KPI_PATH': dict_['kpi_path'],
            'USE_KPI_DEV_MODE': _get_value('kpi_path',
                                           true_value='#',
                                           false_value='',
                                           comparison_value=''),
            'USE_KC_DEV_MODE': _get_value('kc_path',
                                          true_value='#',
                                          false_value='',
                                          comparison_value=''),
            'KC_DEV_BUILD_ID': dict_['kc_dev_build_id'],
            'KPI_DEV_BUILD_ID': dict_['kpi_dev_build_id'],
            'NGINX_PUBLIC_PORT': dict_['exposed_nginx_docker_port'],
            'NGINX_EXPOSED_PORT': nginx_port,
            'UWSGI_WORKERS_MAX': dict_['uwsgi_workers_max'],
            # Deactivate cheaper algorithm if defaults are 1 worker to start and
            # 2 maximum.
            'UWSGI_WORKERS_START': (
                ''
                if dict_['uwsgi_workers_start'] == '1' and dict_['uwsgi_workers_max'] == '2'
                else dict_['uwsgi_workers_start']
            ),
            'UWSGI_MAX_REQUESTS': dict_['uwsgi_max_requests'],
            'UWSGI_SOFT_LIMIT': int(
                dict_['uwsgi_soft_limit']) * 1024 * 1024,
            'UWSGI_HARAKIRI': dict_['uwsgi_harakiri'],
            'UWSGI_WORKER_RELOAD_MERCY': dict_[
                'uwsgi_worker_reload_mercy'],
            'UWSGI_PASS_TIMEOUT': int(dict_['uwsgi_harakiri']) + 10,
            'POSTGRES_REPLICATION_PASSWORD': dict_[
                'postgres_replication_password'],
            'WSGI_SERVER': 'runserver_plus' if config.dev_mode else 'uWSGI',
            'USE_X_FORWARDED_HOST': '' if config.dev_mode else '#',
            'OVERRIDE_POSTGRES_SETTINGS': _get_value('postgres_settings'),
            'POSTGRES_APP_PROFILE': dict_['postgres_profile'],
            'POSTGRES_RAM': dict_['postgres_ram'],
            'POSTGRES_SETTINGS': dict_['postgres_settings_content'],
            'POSTGRES_BACKUP_FROM_SECONDARY': _get_value(
                'backup_from_primary',
                comparison_value=False),
            'POSTGRES_PORT': dict_['postgresql_port'],
            'MONGO_PORT': dict_['mongo_port'],
            'REDIS_MAIN_PORT': dict_['redis_main_port'],
            'REDIS_CACHE_PORT': dict_['redis_cache_port'],
            'REDIS_CACHE_MAX_MEMORY': dict_['redis_cache_max_memory'],
            'USE_BACKUP': '' if dict_['use_backup'] else '#',
            'USE_WAL_E': _get_value('use_wal_e'),
            'USE_AWS_BACKUP': '' if (config.aws and
                                     dict_['aws_backup_bucket_name'] != '' and
                                     dict_['use_backup']) else '#',
            'USE_MEDIA_BACKUP': '' if (not config.aws and
                                       dict_['use_backup']) else '#',
            'KOBOCAT_MEDIA_BACKUP_SCHEDULE': dict_[
                'kobocat_media_backup_schedule'],
            'MONGO_BACKUP_SCHEDULE': dict_['mongo_backup_schedule'],
            'POSTGRES_BACKUP_SCHEDULE': dict_['postgres_backup_schedule'],
            'REDIS_BACKUP_SCHEDULE': dict_['redis_backup_schedule'],
            'AWS_BACKUP_BUCKET_NAME': dict_['aws_backup_bucket_name'],
            'AWS_BACKUP_YEARLY_RETENTION': dict_[
                'aws_backup_yearly_retention'],
            'AWS_BACKUP_MONTHLY_RETENTION': dict_[
                'aws_backup_monthly_retention'],
            'AWS_BACKUP_WEEKLY_RETENTION': dict_[
                'aws_backup_weekly_retention'],
            'AWS_BACKUP_DAILY_RETENTION': dict_[
                'aws_backup_daily_retention'],
            'AWS_MONGO_BACKUP_MINIMUM_SIZE': dict_[
                'aws_mongo_backup_minimum_size'],
            'AWS_POSTGRES_BACKUP_MINIMUM_SIZE': dict_[
                'aws_postgres_backup_minimum_size'],
            'AWS_REDIS_BACKUP_MINIMUM_SIZE': dict_[
                'aws_redis_backup_minimum_size'],
            'AWS_BACKUP_UPLOAD_CHUNK_SIZE': dict_[
                'aws_backup_upload_chunk_size'],
            'AWS_BACKUP_BUCKET_DELETION_RULE_ENABLED': _get_value(
                'aws_backup_bucket_deletion_rule_enabled', 'True', 'False'),
            'LETSENCRYPT_EMAIL': dict_['letsencrypt_email'],
            'MAINTENANCE_ETA': dict_['maintenance_eta'],
            'MAINTENANCE_DATE_ISO': dict_['maintenance_date_iso'],
            'MAINTENANCE_DATE_STR': dict_['maintenance_date_str'],
            'MAINTENANCE_EMAIL': dict_['maintenance_email'],
            'USE_NPM_FROM_HOST': '' if (config.dev_mode and
                                        not dict_['npm_container']) else '#',
            'DOCKER_NETWORK_BACKEND_PREFIX': config.get_prefix('backend'),
            'DOCKER_NETWORK_FRONTEND_PREFIX': config.get_prefix('frontend'),
            'USE_BACKEND_NETWORK': _get_value('expose_backend_ports',
                                              comparison_value=False),
            'EXPOSE_BACKEND_PORTS': _get_value('expose_backend_ports'),
            'USE_FAKE_DNS': _get_value('local_installation'),
            'ADD_BACKEND_EXTRA_HOSTS': '' if (
                        config.expose_backend_ports and
                        not config.use_private_dns) else '#',
            'USE_EXTRA_HOSTS': '' if (config.local_install or
                                      config.expose_backend_ports and
                                      not config.use_private_dns) else '#',
            'MONGO_ROOT_USERNAME': dict_['mongo_root_username'],
            'MONGO_ROOT_PASSWORD': dict_['mongo_root_password'],
            'MONGO_USER_USERNAME': dict_['mongo_user_username'],
            'MONGO_USER_PASSWORD': dict_['mongo_user_password'],
            'REDIS_PASSWORD': dict_['redis_password'],
            'REDIS_PASSWORD_JS_ENCODED': json.dumps(
                dict_['redis_password']),
            'USE_DEV_MODE': _get_value('dev_mode'),
            'USE_CELERY': _get_value('use_celery', comparison_value=False),
            'ENKETO_ALLOW_PRIVATE_IP_ADDRESS': _get_value(
                'local_installation',
                true_value='true',
                false_value='false'
            ),
            'RUN_REDIS_CONTAINERS': _get_value('run_redis_containers'),
            'USE_REDIS_CACHE_MAX_MEMORY': _get_value(
                'redis_cache_max_memory',
                true_value='#',
                false_value='',
                comparison_value='',
            ),
            'USE_LETSENSCRYPT': '#' if config.use_letsencrypt else '',
            'USE_SERVICE_ACCOUNT_WHITELISTED_HOSTS': (
                '#'
                if config.local_install
                else _get_value('service_account_whitelisted_hosts')
            ),
            'DOCKER_COMPOSE_CMD': _get_value(
                'compose_version', 'docker-compose', 'docker', 'v1'
            ),
            # Keep leading space in front of suffix if any
            'DOCKER_COMPOSE_SUFFIX': _get_value(
                'compose_version', '', 'compose', 'v1'
            )
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
