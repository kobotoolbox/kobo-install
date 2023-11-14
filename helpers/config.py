# -*- coding: utf-8 -*-
import binascii
import json
import os
import re
import shutil
import stat
import string
import sys
import time
from datetime import datetime
from random import choice

from helpers.aws_validation import AWSValidation
from helpers.cli import CLI
from helpers.network import Network
from helpers.singleton import Singleton
from helpers.upgrading import Upgrading
from helpers.utils import run_docker_compose


# Use this class as a singleton to get the same configuration
# for each instantiation.
class Config(metaclass=Singleton):

    CONFIG_FILE = '.run.conf'
    UNIQUE_ID_FILE = '.uniqid'
    UPSERT_DB_USERS_TRIGGER_FILE = '.upsert_db_users'
    LETSENCRYPT_DOCKER_DIR = 'nginx-certbot'
    ENV_FILES_DIR = 'kobo-env'
    DEFAULT_PROXY_PORT = '8080'
    DEFAULT_NGINX_PORT = '80'
    DEFAULT_NGINX_HTTPS_PORT = '443'
    KOBO_DOCKER_BRANCH = '2.023.37j'
    KOBO_INSTALL_VERSION = '8.1.1'
    MAXIMUM_AWS_CREDENTIAL_ATTEMPTS = 3
    ALLOWED_PASSWORD_CHARACTERS = (
        string.ascii_letters
        + string.digits
    )

    def __init__(self):
        self.__first_time = None
        self.__dict = self.read_config()

    @property
    def advanced_options(self):
        """
        Checks whether advanced options should be displayed

        Returns:
            bool
        """
        return self.__dict['advanced']

    def auto_detect_network(self):
        """
        Tries to detect new ip

        Returns:
            bool: `True` if network has changed
        """
        changed = False
        local_interfaces = Network.get_local_interfaces(all_=True)

        if self.__dict['local_interface_ip'] not in local_interfaces.values():
            self.__detect_network()
            self.write_config()
            changed = True
        return changed

    @property
    def aws(self):
        """
        Checks whether questions are back end only

        Returns:
            bool
        """
        return self.__dict['use_aws']

    @property
    def backend(self):
        return not self.multi_servers or not self.frontend

    def build(self):
        """
        Build configuration based on user's answers

        Returns:
            dict: all values from user's responses needed to create
            configuration files
        """
        if not Network.get_primary_ip():
            message = (
                'No valid networks detected. Can not continue!\n'
                'Please connect to a network and re-run the command.'
            )
            CLI.framed_print(message, color=CLI.COLOR_ERROR)
            sys.exit(1)
        else:

            self.__welcome()
            self.__dict = self.get_upgraded_dict()

            self.__create_directory()
            self.__questions_advanced_options()
            self.__questions_installation_type()
            self.__detect_network()

            if not self.local_install:
                if self.advanced_options:
                    self.__questions_multi_servers()
                    if self.multi_servers:
                        self.__questions_roles()
                        if self.frontend or self.secondary_backend:
                            self.__questions_private_routes()
                    else:
                        self.__reset(fake_dns=True)

                if self.frontend:
                    self.__questions_public_routes()
                    self.__questions_https()
                    self.__questions_reverse_proxy()

            if self.frontend:
                self.__questions_smtp()
                self.__questions_super_user_credentials()

            if self.advanced_options:
                self.__questions_docker_prefix()
                self.__questions_dev_mode()
                self.__questions_postgres()
                self.__questions_mongo()
                self.__questions_redis()
                self.__questions_ports()

                if self.frontend:
                    self.__questions_secret_keys()
                    self.__questions_aws()
                    self.__questions_google()
                    self.__questions_raven()
                    self.__questions_uwsgi()
                    self.__questions_service_account()
                    self.__questions_session_cookies()

                self.__questions_custom_yml()

            else:
                self.__secure_mongo()

            self.__questions_backup()

            self.write_config()

            return self.__dict

    @property
    def block_common_http_ports(self):
        return self.use_letsencrypt or self.__dict['block_common_http_ports']

    @property
    def expose_backend_ports(self):
        return self.__dict['expose_backend_ports']

    def get_env_files_path(self):
        current_path = os.path.realpath(os.path.normpath(os.path.join(
            self.__dict['kobodocker_path'],
            '..',
            Config.ENV_FILES_DIR
        )))

        old_path = os.path.realpath(os.path.normpath(os.path.join(
            self.__dict['kobodocker_path'],
            '..',
            'kobo-deployments'
        )))

        # if old location is detected, move it to new path.
        if os.path.exists(old_path) and not os.path.exists(current_path):
            shutil.move(old_path, current_path)

        return current_path

    def get_letsencrypt_repo_path(self):
        return os.path.realpath(os.path.normpath(os.path.join(
            self.__dict['kobodocker_path'],
            '..',
            Config.LETSENCRYPT_DOCKER_DIR
        )))

    def get_prefix(self, role):
        roles = {
            'frontend': 'kobofe',
            'backend': 'kobobe',
            'maintenance': 'kobomaintenance'
        }

        try:
            prefix_ = roles[role]
        except KeyError:
            CLI.colored_print('Invalid composer file', CLI.COLOR_ERROR)
            sys.exit(1)

        if not self.__dict['docker_prefix']:
            return prefix_

        return f"{self.__dict['docker_prefix']}-{prefix_}"

    def get_upgraded_dict(self):
        """
        Sometimes during upgrades, some keys are changed/deleted/added.
        This method helps to get a compliant dict to expected config

        Returns:
            dict
        """

        upgraded_dict = self.get_template()
        upgraded_dict.update(self.__dict)

        # Upgrade to use two databases
        upgraded_dict = Upgrading.two_databases(upgraded_dict, self.__dict)

        # Upgrade to use new terminology primary/secondary
        upgraded_dict = Upgrading.new_terminology(upgraded_dict)

        # Upgrade to use booleans in `self.__dict`
        upgraded_dict = Upgrading.use_booleans(upgraded_dict)

        upgraded_dict = Upgrading.set_compose_version(upgraded_dict)

        return upgraded_dict

    @property
    def dev_mode(self):
        return self.__dict['dev_mode'] is True

    @property
    def first_time(self):
        """
        Checks whether setup is running for the first time

        Returns:
            bool
        """
        if self.__first_time is None:
            self.__first_time = self.__dict.get('date_created') is None
        return self.__first_time

    @property
    def frontend(self):
        """
        Checks whether setup is running on a front-end server

        Returns:
            dict: all values from user's responses needed to create
            configuration files
        """
        return (
            not self.multi_servers or self.__dict['server_role'] == 'frontend'
        )

    @classmethod
    def generate_password(cls, required_chars_count=20):
        """
        Generate n characters long random password

        Returns:
            str
        """
        return ''.join(
            choice(cls.ALLOWED_PASSWORD_CHARACTERS)
            for _ in range(required_chars_count)
        )

    def get_dict(self):
        return self.__dict

    def get_service_names(self):
        service_list_command = run_docker_compose(self.__dict, [
            '-f', 'docker-compose.frontend.yml',
            '-f', 'docker-compose.frontend.override.yml',
            'config', '--services',
        ])

        services = CLI.run_command(
            service_list_command, self.__dict['kobodocker_path']
        )
        return services.strip().split('\n')

    @classmethod
    def get_template(cls):

        primary_ip = Network.get_primary_ip()

        # Keep properties sorted alphabetically
        return {
            'advanced': False,
            'aws_access_key': '',
            'aws_backup_bucket_deletion_rule_enabled': False,
            'aws_backup_bucket_name': '',
            'aws_backup_daily_retention': '30',
            'aws_backup_monthly_retention': '12',
            'aws_backup_upload_chunk_size': '15',
            'aws_backup_weekly_retention': '4',
            'aws_backup_yearly_retention': '2',
            'aws_bucket_name': '',
            'aws_credentials_valid': False,
            'aws_mongo_backup_minimum_size': '50',
            'aws_postgres_backup_minimum_size': '50',
            'aws_redis_backup_minimum_size': '5',
            'aws_s3_region_name': 'us-east-1',
            'aws_secret_key': '',
            'aws_validate_credentials': True,
            'backend_server_role': 'primary',
            'backup_from_primary': True,
            'block_common_http_ports': True,
            'custom_secret_keys': False,
            'customized_ports': False,
            'debug': False,
            'default_from_email': 'support@kobo.local',
            'dev_mode': False,
            'django_secret_key': binascii.hexlify(os.urandom(50)).decode(),
            'django_session_cookie_age': 604800,
            'docker_prefix': '',
            'ee_subdomain': 'ee',
            'enketo_api_token': binascii.hexlify(os.urandom(60)).decode(),
            'enketo_encryption_key': binascii.hexlify(os.urandom(60)).decode(),
            # default value from enketo. Because it was not customizable before
            # we want to keep the same value when users upgrade.
            'enketo_less_secure_encryption_key': 'this $3cr3t key is crackable',
            'expose_backend_ports': False,
            'exposed_nginx_docker_port': Config.DEFAULT_NGINX_PORT,
            'google_api_key': '',
            'google_ua': '',
            'https': True,
            'internal_domain_name': 'docker.internal',
            'kc_dev_build_id': '',
            'kc_path': '',
            'kc_postgres_db': 'kobocat',
            'kc_subdomain': 'kc',
            'kobocat_media_backup_schedule': '0 0 * * 0',
            'kobocat_raven': '',
            'kobodocker_path': os.path.realpath(os.path.normpath(os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                '..',
                '..',
                'kobo-docker'))
            ),
            'kpi_dev_build_id': '',
            'kpi_path': '',
            'kpi_postgres_db': 'koboform',
            'kpi_raven': '',
            'kpi_raven_js': '',
            'kpi_subdomain': 'kf',
            'local_installation': False,
            'local_interface': Network.get_primary_interface(),
            'local_interface_ip': primary_ip,
            'letsencrypt_email': 'support@kobo.local',
            'maintenance_date_iso': '',
            'maintenance_date_str': '',
            'maintenance_email': 'support@kobo.local',
            'maintenance_enabled': False,
            'maintenance_eta': '2 hours',
            'mongo_backup_schedule': '0 1 * * 0',
            'mongo_port': '27017',
            'mongo_root_password': Config.generate_password(),
            'mongo_root_username': 'root',
            'mongo_user_password': Config.generate_password(),
            'mongo_user_username': 'kobo',
            'multi': False,
            'nginx_proxy_port': Config.DEFAULT_PROXY_PORT,
            'npm_container': True,
            'postgres_cpus': '1',
            'postgres_backup_schedule': '0 2 * * 0',
            'postgres_hard_drive_type': 'hdd',
            'postgres_max_connections': '100',
            'postgres_password': Config.generate_password(),
            'postgres_profile': 'Mixed',
            'postgres_ram': '2',
            'postgres_replication_password': Config.generate_password(),
            'postgres_settings': False,
            'postgres_settings_content': '\n'.join([
                '# Generated by PGConfig 3.1.0 (1d600ea0d1d79f13dd7ed686f9e2befc1fcf9226)',
                '# https://api.pgconfig.org/v1/tuning/get-config?format=conf&include_pgbadger=false&max_connections=100&pg_version=14&environment_name=Mixed&total_ram=2GB&cpus=1&drive_type=SSD&os_type=linux',
                '',
                '# Memory Configuration',
                'shared_buffers = 256MB',
                'effective_cache_size = 768MB',
                'work_mem = 2MB',
                'maintenance_work_mem = 51MB',
                '',
                '# Checkpoint Related Configuration',
                'min_wal_size = 2GB',
                'max_wal_size = 3GB',
                'checkpoint_completion_target = 0.9',
                'wal_buffers = -1',
                '',
                '# Network Related Configuration',
                "listen_addresses = '*'",
                'max_connections = 100',
                '',
                '# Storage Configuration',
                'random_page_cost = 1.1',
                'effective_io_concurrency = 200',
                '',
                '# Worker Processes Configuration',
                'max_worker_processes = 8',
                'max_parallel_workers_per_gather = 2',
                'max_parallel_workers = 2',
                '',
                ''
            ]),
            'postgres_user': 'kobo',
            'postgresql_port': '5432',
            'primary_backend_ip': primary_ip,
            'private_domain_name': 'kobo.private',
            'proxy': True,
            'public_domain_name': 'kobo.local',
            'raven_settings': False,
            'redis_backup_schedule': '0 3 * * 0',
            'redis_cache_max_memory': '',
            'redis_cache_port': '6380',
            'redis_main_port': '6379',
            'redis_password': Config.generate_password(),
            'review_host': True,
            'run_redis_containers': True,
            'server_role': 'frontend',
            'service_account_whitelisted_hosts': True,
            'smtp_host': '',
            'smtp_password': '',
            'smtp_port': '25',
            'smtp_user': '',
            'smtp_use_tls': False,
            'staging_mode': False,
            'super_user_password': Config.generate_password(),
            'super_user_username': 'super_admin',
            'two_databases': True,
            'use_aws': False,
            'use_backup': False,
            'use_backend_custom_yml': False,
            'use_celery': True,
            'use_frontend_custom_yml': False,
            'use_letsencrypt': True,
            'use_private_dns': False,
            'use_wal_e': False,
            'uwsgi_harakiri': '120',
            'uwsgi_max_requests': '1024',
            'uwsgi_settings': False,
            'uwsgi_soft_limit': '1024',
            'uwsgi_worker_reload_mercy': '120',
            'uwsgi_workers_max': '4',
            'uwsgi_workers_start': '2',
        }

    @property
    def is_secure(self):
        return self.__dict['https'] is True

    def init_letsencrypt(self):
        if self.frontend and self.use_letsencrypt:
            reverse_proxy_path = self.get_letsencrypt_repo_path()
            reverse_proxy_command = [
                '/bin/bash',
                'init-letsencrypt.sh'
            ]
            CLI.run_command(reverse_proxy_command, reverse_proxy_path)

    @property
    def local_install(self):
        """
        Checks whether installation is for `Workstation`s

        Returns:
            bool
        """
        return self.__dict['local_installation']

    def maintenance(self):
        self.__questions_maintenance()

    @property
    def primary_backend(self):
        """
        Checks whether setup is running on a primary back-end server

        Returns:
            bool
        """
        return (
            self.multi_servers
            and self.__dict['server_role'] == 'backend'
            and self.__dict['backend_server_role'] == 'primary'
        )

    @property
    def multi_servers(self):
        """
        Checks whether installation is for separate front-end and back-end
        servers

        Returns:
            bool
        """
        return self.__dict['multi']

    @property
    def proxy(self):
        """
        Checks whether installation is using a proxy or a load balancer

        Returns:
            bool
        """
        return self.__dict['proxy']

    def read_config(self):
        """
        Reads config from file `Config.CONFIG_FILE` if exists

        Returns:
            dict
        """
        dict_ = {}
        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
            config_file = os.path.join(base_dir, Config.CONFIG_FILE)
            with open(config_file, 'r') as f:
                dict_ = json.loads(f.read())
        except IOError:
            pass

        self.__dict = dict_
        unique_id = self.read_unique_id()
        if not unique_id:
            self.__dict['unique_id'] = int(time.time())

        return dict_

    def read_unique_id(self):
        """
        Reads unique id from file `Config.UNIQUE_ID_FILE`

        Returns:
            str
        """
        unique_id = None

        try:
            unique_id_file = os.path.join(self.__dict['kobodocker_path'],
                                          Config.UNIQUE_ID_FILE)
        except KeyError:
            if self.first_time:
                return None
            else:
                CLI.framed_print('Bad configuration! The path of kobo-docker '
                                 'path is missing. Please delete `.run.conf` '
                                 'and start from scratch',
                                 color=CLI.COLOR_ERROR)
                sys.exit(1)

        try:
            with open(unique_id_file, 'r') as f:
                unique_id = f.read().strip()
        except FileNotFoundError:
            pass

        return unique_id

    @property
    def secondary_backend(self):
        """
        Checks whether setup is running on a secondary back-end server

        Returns:
            bool
        """
        return (
            self.multi_servers
            and self.__dict['server_role'] == 'backend'
            and self.__dict['backend_server_role'] == 'secondary'
        )

    def set_config(self, value):
        self.__dict = value

    @property
    def staging_mode(self):
        return self.__dict['staging_mode']

    @property
    def use_letsencrypt(self):
        return not self.local_install and self.__dict['use_letsencrypt']

    @property
    def use_private_dns(self):
        return self.__dict['use_private_dns']

    def validate_aws_credentials(self):
        validation = AWSValidation(
            aws_access_key_id=self.__dict['aws_access_key'],
            aws_secret_access_key=self.__dict['aws_secret_key'],
        )
        self.__dict['aws_credentials_valid'] = validation.validate_credentials()

    def validate_passwords(self):

        passwords = {
            'PostgreSQL': {
                'password': self.__dict['postgres_password'],
                'pattern': self.__get_password_validation_pattern(
                    add_prefix=False
                ),
            },
            'PostgreSQL replication': {
                'password': self.__dict['postgres_replication_password'],
                'pattern': self.__get_password_validation_pattern(
                    add_prefix=False
                ),
            },
            'MongoDB root’s': {
                'password': self.__dict['mongo_root_password'],
                'pattern': self.__get_password_validation_pattern(
                    add_prefix=False
                ),
            },
            'MongoDB user’s': {
                'password': self.__dict['mongo_user_password'],
                'pattern': self.__get_password_validation_pattern(
                    add_prefix=False
                ),
            },
            'Redis': {
                'password': self.__dict['redis_password'],
                # redis password can be empty
                'pattern': self.__get_password_validation_pattern(
                    allow_empty=True, add_prefix=False
                ),
            },
        }
        errors = []
        psql_replication = passwords.pop('PostgreSQL replication')
        for label, config_ in passwords.items():
            if not re.match(config_['pattern'], config_['password']):
                errors.append(label)
                CLI.colored_print(
                    f'{label} password contains unsupported characters.',
                    CLI.COLOR_ERROR
                )
        if errors:
            CLI.colored_print(
                'You should run `python3 run.py --setup` to update.',
                CLI.COLOR_WARNING
            )

        # PostgreSQL replication password must be handled separately because
        # it is set in PostgreSQL on the first launch and nothing is done
        # afterwards in subsequent starts to update it if it has changed.
        if not re.match(
            psql_replication['pattern'], psql_replication['password']
        ):
            CLI.colored_print(
                'PostgreSQL replication password contains unsupported characters.',
                CLI.COLOR_ERROR
            )
            CLI.colored_print(
                'It must be changed manually in `kobo-install/.run.conf` '
                '(and PostgreSQL itself if you use replication).',
                CLI.COLOR_WARNING
            )

    def write_config(self):
        """
        Writes config to file `Config.CONFIG_FILE`.
        """
        # Adds `date_created`. This field will be use to determine
        # first usage of the setup option.
        if self.__dict.get('date_created') is None:
            self.__dict['date_created'] = int(time.time())
        self.__dict['date_modified'] = int(time.time())

        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
            config_file = os.path.join(base_dir, Config.CONFIG_FILE)
            with open(config_file, 'w') as f:
                f.write(json.dumps(self.__dict, indent=2, sort_keys=True))

            os.chmod(config_file, stat.S_IWRITE | stat.S_IREAD)

        except IOError:
            CLI.colored_print('Could not write configuration file',
                              CLI.COLOR_ERROR)
            sys.exit(1)

    def write_unique_id(self):
        try:
            unique_id_file = os.path.join(self.__dict['kobodocker_path'],
                                          Config.UNIQUE_ID_FILE)
            with open(unique_id_file, 'w') as f:
                f.write(str(self.__dict['unique_id']))

            os.chmod(unique_id_file, stat.S_IWRITE | stat.S_IREAD)
        except (IOError, OSError):
            CLI.colored_print('Could not write unique_id file', CLI.COLOR_ERROR)
            return False

        return True

    def __create_directory(self):
        """
        Create repository directory if it doesn't exist.
        """
        CLI.colored_print('Where do you want to install?', CLI.COLOR_QUESTION)
        while True:
            kobodocker_path = CLI.colored_input(
                '',
                CLI.COLOR_QUESTION,
                self.__dict['kobodocker_path']
            )

            if kobodocker_path.startswith('.'):
                base_dir = os.path.dirname(
                    os.path.dirname(os.path.realpath(__file__)))
                kobodocker_path = os.path.normpath(
                    os.path.join(base_dir, kobodocker_path))

            question = f'Please confirm path [{kobodocker_path}]'
            response = CLI.yes_no_question(question)
            if response is True:
                if os.path.isdir(kobodocker_path):
                    break
                else:
                    try:
                        os.makedirs(kobodocker_path)
                        break
                    except OSError:
                        CLI.colored_print(
                            f'Could not create directory {kobodocker_path}!',
                            CLI.COLOR_ERROR)
                        CLI.colored_print(
                            'Please make sure you have permissions '
                            'and path is correct',
                            CLI.COLOR_ERROR)

        self.__dict['kobodocker_path'] = kobodocker_path
        self.write_unique_id()
        self.__validate_installation()

    def __clone_repo(self, repo_path, repo_name):
        if repo_path:
            if repo_path.startswith('.'):
                full_repo_path = os.path.normpath(os.path.join(
                    self.__dict['kobodocker_path'],
                    repo_path
                ))
            else:
                full_repo_path = repo_path

            if not os.path.isdir(full_repo_path):
                # clone repo
                try:
                    os.makedirs(full_repo_path)
                except OSError:
                    CLI.colored_print('Please verify permissions.',
                                      CLI.COLOR_ERROR)
                    sys.exit(1)

            # Only clone if folder is empty
            if not os.path.isdir(os.path.join(full_repo_path, '.git')):
                git_command = [
                    'git', 'clone',
                    f'https://github.com/kobotoolbox/{repo_name}',
                    full_repo_path
                ]

                CLI.colored_print(
                    f'Cloning `{repo_name}` repository to `{full_repo_path}`',
                    CLI.COLOR_INFO
                )
                CLI.run_command(git_command,
                                cwd=os.path.dirname(full_repo_path))

    def __detect_network(self):

        self.__dict['local_interface_ip'] = Network.get_primary_ip()

        if self.frontend:
            self.__dict['primary_backend_ip'] = self.__dict[
                'local_interface_ip']

        if self.advanced_options:
            CLI.colored_print(
                'Please choose which network interface you want to use?',
                CLI.COLOR_QUESTION)
            interfaces = Network.get_local_interfaces()
            all_interfaces = Network.get_local_interfaces(all_=True)
            docker_interface = 'docker0'
            interfaces.update({'other': 'Other'})

            if self.__dict['local_interface'] == docker_interface and \
                    docker_interface in all_interfaces:
                interfaces.update(
                    {docker_interface: all_interfaces.get(docker_interface)})

            for interface, ip_address in interfaces.items():
                CLI.colored_print(f'\t{interface}) {ip_address}')

            choices = [str(interface) for interface in interfaces.keys()]
            choices.append('other')
            response = CLI.get_response(
                choices,
                default=self.__dict['local_interface']
            )

            if response == 'other':
                interfaces = Network.get_local_interfaces(all_=True)
                for interface, ip_address in interfaces.items():
                    CLI.colored_print(f'\t{interface}) {ip_address}')

                choices = [str(interface) for interface in interfaces.keys()]
                self.__dict['local_interface'] = CLI.get_response(
                    choices,
                    self.__dict['local_interface']
                )
            else:
                self.__dict['local_interface'] = response

            self.__dict['local_interface_ip'] = interfaces[
                self.__dict['local_interface']]

            if self.frontend:
                self.__dict['primary_backend_ip'] = self.__dict[
                    'local_interface_ip']

    def __get_password_validation_pattern(
        self, chars=8, allow_empty=False, add_prefix=True
    ):
        """
        Return regex pattern needed to validate passwords.

        When it is passed to `CLI.get_response()`, it has to be prefixed with a
        '~' in order to tell `CLI.get_response()` that the validator is a regex,
        not a regular string.
        """
        pattern = f'[{self.ALLOWED_PASSWORD_CHARACTERS}]{{{chars},}}'
        prefix = '~' if add_prefix else ''
        if allow_empty:
            pattern += '|'
        return rf'{prefix}^{pattern}$'

    def __questions_advanced_options(self):
        """
        Asks if user wants to see advanced options
        """
        self.__dict['advanced'] = CLI.yes_no_question(
            'Do you want to see advanced options?',
            default=self.__dict['advanced'])

    def __questions_aws(self):
        """
        Asks if user wants to see AWS option
        and asks for credentials if needed.
        """
        self.__dict['use_aws'] = CLI.yes_no_question(
            'Do you want to use AWS S3 storage?',
            default=self.__dict['use_aws']
        )
        self.__questions_aws_configuration()
        self.__questions_aws_validate_credentials()

    def __questions_aws_configuration(self):

        if self.__dict['use_aws']:
            self.__dict['aws_access_key'] = CLI.colored_input(
                'AWS Access Key', CLI.COLOR_QUESTION,
                self.__dict['aws_access_key'])
            self.__dict['aws_secret_key'] = CLI.colored_input(
                'AWS Secret Key', CLI.COLOR_QUESTION,
                self.__dict['aws_secret_key'])
            self.__dict['aws_bucket_name'] = CLI.colored_input(
                'AWS Bucket Name', CLI.COLOR_QUESTION,
                self.__dict['aws_bucket_name'])
            self.__dict['aws_s3_region_name'] = CLI.colored_input(
                'AWS Region Name', CLI.COLOR_QUESTION,
                self.__dict['aws_s3_region_name'])
        else:
            self.__dict['aws_access_key'] = ''
            self.__dict['aws_secret_key'] = ''
            self.__dict['aws_bucket_name'] = ''
            self.__dict['aws_s3_region_name'] = ''

    def __questions_aws_validate_credentials(self):
        """
        Prompting user whether they would like to validate their entered AWS
        credentials or continue without validation.
        """
        # Resetting validation when setup is rerun
        self.__dict['aws_credentials_valid'] = False
        aws_credential_attempts = 0

        if self.__dict['use_aws']:
            self.__dict['aws_validate_credentials'] = CLI.yes_no_question(
                'Would you like to validate your AWS credentials?',
                default=self.__dict['aws_validate_credentials'],
            )

        if self.__dict['use_aws'] and self.__dict['aws_validate_credentials']:
            while (
                not self.__dict['aws_credentials_valid']
                and aws_credential_attempts
                <= self.MAXIMUM_AWS_CREDENTIAL_ATTEMPTS
            ):
                aws_credential_attempts += 1
                self.validate_aws_credentials()
                attempts_remaining = (
                    self.MAXIMUM_AWS_CREDENTIAL_ATTEMPTS
                    - aws_credential_attempts
                )
                if (
                    not self.__dict['aws_credentials_valid']
                    and attempts_remaining > 0
                ):
                    CLI.colored_print(
                        'Invalid credentials, please try again.',
                        CLI.COLOR_WARNING,
                    )
                    CLI.colored_print(
                        'Attempts remaining for AWS validation: {}'.format(
                            attempts_remaining
                        ),
                        CLI.COLOR_INFO,
                    )
                    self.__questions_aws_configuration()
            else:
                if not self.__dict['aws_credentials_valid']:
                    CLI.colored_print(
                        'Please restart configuration', CLI.COLOR_ERROR
                    )
                    sys.exit(1)
                else:
                    CLI.colored_print(
                        'AWS credentials successfully validated',
                        CLI.COLOR_SUCCESS
                    )

    def __questions_aws_backup_settings(self):

        self.__dict['aws_backup_bucket_name'] = CLI.colored_input(
            'AWS Backups bucket name', CLI.COLOR_QUESTION,
            self.__dict['aws_backup_bucket_name'])

        if self.__dict['aws_backup_bucket_name'] != '':

            backup_from_primary = self.__dict['backup_from_primary']

            CLI.colored_print('How many yearly backups to keep?',
                              CLI.COLOR_QUESTION)
            self.__dict['aws_backup_yearly_retention'] = CLI.get_response(
                r'~^\d+$', self.__dict['aws_backup_yearly_retention'])

            CLI.colored_print('How many monthly backups to keep?',
                              CLI.COLOR_QUESTION)
            self.__dict['aws_backup_monthly_retention'] = CLI.get_response(
                r'~^\d+$', self.__dict['aws_backup_monthly_retention'])

            CLI.colored_print('How many weekly backups to keep?',
                              CLI.COLOR_QUESTION)
            self.__dict['aws_backup_weekly_retention'] = CLI.get_response(
                r'~^\d+$', self.__dict['aws_backup_weekly_retention'])

            CLI.colored_print('How many daily backups to keep?',
                              CLI.COLOR_QUESTION)
            self.__dict['aws_backup_daily_retention'] = CLI.get_response(
                r'~^\d+$', self.__dict['aws_backup_daily_retention'])

            if (not self.multi_servers or
                    (self.primary_backend and backup_from_primary) or
                    (self.secondary_backend and not backup_from_primary)):
                CLI.colored_print('PostgresSQL backup minimum size (in MB)?',
                                  CLI.COLOR_QUESTION)
                CLI.colored_print(
                    'Files below this size will be ignored when '
                    'rotating backups.',
                    CLI.COLOR_INFO)
                self.__dict[
                    'aws_postgres_backup_minimum_size'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['aws_postgres_backup_minimum_size'])

            if self.primary_backend or not self.multi_servers:
                CLI.colored_print('MongoDB backup minimum size (in MB)?',
                                  CLI.COLOR_QUESTION)
                CLI.colored_print(
                    'Files below this size will be ignored when '
                    'rotating backups.',
                    CLI.COLOR_INFO)
                self.__dict[
                    'aws_mongo_backup_minimum_size'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['aws_mongo_backup_minimum_size'])

                CLI.colored_print('Redis backup minimum size (in MB)?',
                                  CLI.COLOR_QUESTION)
                CLI.colored_print(
                    'Files below this size will be ignored when '
                    'rotating backups.',
                    CLI.COLOR_INFO)
                self.__dict[
                    'aws_redis_backup_minimum_size'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['aws_redis_backup_minimum_size'])

            CLI.colored_print('Chunk size of multipart uploads (in MB)?',
                              CLI.COLOR_QUESTION)
            self.__dict['aws_backup_upload_chunk_size'] = CLI.get_response(
                r'~^\d+$', self.__dict['aws_backup_upload_chunk_size'])

            response = CLI.yes_no_question(
                'Use AWS LifeCycle deletion rule?',
                default=self.__dict['aws_backup_bucket_deletion_rule_enabled']
            )
            self.__dict['aws_backup_bucket_deletion_rule_enabled'] = response

    def __questions_backup(self):
        """
        Asks all questions about backups.
        """
        if self.backend or (self.frontend and not self.aws):

            self.__dict['use_backup'] = CLI.yes_no_question(
                'Do you want to activate backups?',
                default=self.__dict['use_backup']
            )

            if self.__dict['use_backup']:
                if self.advanced_options:
                    if self.backend and not self.frontend:
                        self.__questions_aws()

                    # Prompting user whether they want to use WAL-E for
                    # continuous archiving - only if they are using aws
                    # for backups
                    if self.aws:
                        if self.primary_backend or not self.multi_servers:
                            self.__dict['use_wal_e'] = CLI.yes_no_question(
                                'Do you want to use WAL-E for continuous '
                                'archiving of PostgreSQL backups?',
                                default=self.__dict['use_wal_e']
                            )
                            if self.__dict['use_wal_e']:
                                self.__dict['backup_from_primary'] = True
                        else:
                            # WAL-E cannot run on secondary
                            self.__dict['use_wal_e'] = False
                    else:
                        # WAL-E is only supported with AWS
                        self.__dict['use_wal_e'] = False

                    schedule_regex_pattern = (
                        r'^\-|((((\d+(,\d+)*)|(\d+-\d+)|(\*(\/\d+)?)))'
                        r'(\s+(((\d+(,\d+)*)|(\d+\-\d+)|(\*(\/\d+)?)))){4})?$'
                    )
                    message = (
                        'Schedules use linux cron syntax with UTC datetimes.\n'
                        'For example, schedule at 12:00 AM E.S.T every Sunday '
                        'would be:\n'
                        '0 5 * * 0\n'
                        '\n'
                        'Please visit https://crontab.guru/ to generate a '
                        'cron schedule.'
                    )
                    CLI.framed_print(message, color=CLI.COLOR_INFO)
                    CLI.colored_print(
                        'Leave empty (or use `-` to empty) to deactivate backups'
                        ' for a specific\nservice.',
                        color=CLI.COLOR_WARNING
                    )
                    if self.frontend and not self.aws:
                        CLI.colored_print('KoBoCat media backup schedule?',
                                          CLI.COLOR_QUESTION)
                        self.__dict[
                            'kobocat_media_backup_schedule'] = CLI.get_response(
                            f'~{schedule_regex_pattern}',
                            self.__dict['kobocat_media_backup_schedule'])

                    if self.backend:
                        if self.__dict['use_wal_e'] or not self.multi_servers:
                            # We are on primary back-end server
                            self.__dict['backup_from_primary'] = True
                            backup_postgres = True
                        else:
                            if self.primary_backend:
                                default_response = self.__dict['backup_from_primary']
                            else:
                                default_response = not self.__dict[
                                    'backup_from_primary']

                            backup_postgres = CLI.yes_no_question(
                                'Run PostgreSQL backup from this server?',
                                default=default_response
                            )

                            if self.primary_backend:
                                self.__dict['backup_from_primary'] = backup_postgres
                            else:
                                self.__dict['backup_from_primary'] = not backup_postgres

                        if backup_postgres:
                            CLI.colored_print('PostgreSQL backup schedule?',
                                              CLI.COLOR_QUESTION)
                            self.__dict[
                                'postgres_backup_schedule'] = CLI.get_response(
                                f'~{schedule_regex_pattern}',
                                self.__dict['postgres_backup_schedule'])
                        else:
                            self.__dict['postgres_backup_schedule'] = ''

                        if self.primary_backend or not self.multi_servers:
                            CLI.colored_print('MongoDB backup schedule?',
                                              CLI.COLOR_QUESTION)
                            self.__dict[
                                'mongo_backup_schedule'] = CLI.get_response(
                                f'~{schedule_regex_pattern}',
                                self.__dict['mongo_backup_schedule'])

                        if self.__dict['run_redis_containers']:
                            CLI.colored_print('Redis backup schedule?',
                                              CLI.COLOR_QUESTION)
                            self.__dict[
                                'redis_backup_schedule'] = CLI.get_response(
                                f'~{schedule_regex_pattern}',
                                self.__dict['redis_backup_schedule'])
                        else:
                            self.__dict['redis_backup_schedule'] = ''

                        if self.aws:
                            self.__questions_aws_backup_settings()
                    else:
                        # Back to default value
                        self.__dict['backup_from_primary'] = True
            else:
                self.__reset(no_backups=True)
        else:
            self.__reset(no_backups=True)

    def __questions_custom_yml(self):

        if self.frontend:
            self.__dict['use_frontend_custom_yml'] = CLI.yes_no_question(
                'Do you want to add additional settings to the front-end '
                'docker containers?',
                default=self.__dict['use_frontend_custom_yml'],
            )

        if self.backend:
            self.__dict['use_backend_custom_yml'] = CLI.yes_no_question(
                'Do you want to add additional settings to the back-end '
                'docker containers?',
                default=self.__dict['use_backend_custom_yml']
            )

    def __questions_dev_mode(self):
        """
        Asks for developer/staging mode.

        Dev mode allows to modify nginx port and
        Staging model

        Reset to default in case of No
        """

        if self.frontend:

            if self.local_install:
                # NGINX different port
                CLI.colored_print('Web server port?', CLI.COLOR_QUESTION)
                self.__dict['exposed_nginx_docker_port'] = CLI.get_response(
                    r'~^\d+$', self.__dict['exposed_nginx_docker_port'])
                self.__dict['dev_mode'] = CLI.yes_no_question(
                    'Use developer mode?',
                    default=self.__dict['dev_mode']
                )
                self.__dict['staging_mode'] = False
                if self.dev_mode:
                    self.__dict['use_celery'] = CLI.yes_no_question(
                        'Use Celery for background tasks?',
                        default=self.__dict['use_celery']
                    )

            else:
                self.__dict['staging_mode'] = CLI.yes_no_question(
                    'Use staging mode?',
                    default=self.__dict['staging_mode']
                )
                self.__dict['dev_mode'] = False
                self.__dict['use_celery'] = True

            if self.dev_mode or self.staging_mode:
                message = (
                    'Where are the files located locally? It can be absolute '
                    'or relative to the directory of `kobo-docker`.\n\n'
                    'Leave empty if you do not need to overload the repository.'
                )
                CLI.framed_print(message, color=CLI.COLOR_INFO)

                kc_path = self.__dict['kc_path']
                self.__dict['kc_path'] = CLI.colored_input(
                    'KoBoCat files location?', CLI.COLOR_QUESTION,
                    self.__dict['kc_path'])
                self.__clone_repo(self.__dict['kc_path'], 'kobocat')

                kpi_path = self.__dict['kpi_path']
                self.__dict['kpi_path'] = CLI.colored_input(
                    'KPI files location?', CLI.COLOR_QUESTION,
                    self.__dict['kpi_path'])
                self.__clone_repo(self.__dict['kpi_path'], 'kpi')

                # Create an unique id to build fresh image
                # when starting containers
                if (
                    not self.__dict['kc_dev_build_id'] or
                    self.__dict['kc_path'] != kc_path
                ):
                    prefix = self.get_prefix('frontend')
                    timestamp = int(time.time())
                    self.__dict['kc_dev_build_id'] = f'{prefix}{timestamp}'

                if (
                    not self.__dict['kpi_dev_build_id'] or
                    self.__dict['kpi_path'] != kpi_path
                ):
                    prefix = self.get_prefix('frontend')
                    timestamp = int(time.time())
                    self.__dict['kpi_dev_build_id'] = f'{prefix}{timestamp}'

                if self.dev_mode:
                    self.__dict['debug'] = CLI.yes_no_question(
                        'Enable DEBUG?',
                        default=self.__dict['debug']
                    )

                    # Front-end development
                    self.__dict['npm_container'] = CLI.yes_no_question(
                        'How do you want to run `npm`?',
                        default=self.__dict['npm_container'],
                        labels=[
                            'From within the container',
                            'Locally',
                        ]
                    )
            else:
                # Force reset paths
                self.__reset(production=True, nginx_default=self.staging_mode)

    def __questions_docker_prefix(self):
        """
        Asks for Docker compose prefix. It allows to start
        containers with a custom prefix
        """
        self.__dict['docker_prefix'] = CLI.colored_input(
            'Docker Compose prefix? (leave empty for default)',
            CLI.COLOR_QUESTION,
            self.__dict['docker_prefix'])

    def __questions_google(self):
        """
        Asks for Google's keys
        """
        # Google Analytics
        self.__dict['google_ua'] = CLI.colored_input(
            'Google Analytics Identifier', CLI.COLOR_QUESTION,
            self.__dict['google_ua'])

        # Google API Key
        self.__dict['google_api_key'] = CLI.colored_input(
            'Google API Key',
            CLI.COLOR_QUESTION,
            self.__dict['google_api_key'])

    def __questions_https(self):
        """
        Asks for HTTPS usage
        """
        self.__dict['https'] = CLI.yes_no_question(
            'Do you want to use HTTPS?',
            default=self.__dict['https']
        )
        if self.is_secure:
            message = (
                'Please note that certificates must be installed on a '
                'reverse-proxy or a load balancer.'
                'kobo-install can install one, if needed.'
            )
            CLI.framed_print(message, color=CLI.COLOR_INFO)

    def __questions_installation_type(self):
        """
        Asks for installation type
        """
        previous_installation_type = self.__dict['local_installation']

        self.__dict['local_installation'] = CLI.yes_no_question(
            'What kind of installation do you need?',
            default=self.__dict['local_installation'],
            labels=[
                'On your workstation',
                'On a server',
            ]
        )
        if self.local_install:
            message = (
                'WARNING!\n\n'
                'SSRF protection is disabled with local installation'
            )
            CLI.framed_print(message, color=CLI.COLOR_WARNING)

        if previous_installation_type != self.__dict['local_installation']:
            # Reset previous choices, in case server role is not the same.
            self.__reset(
                production=not self.local_install,
                http=self.local_install,
                fake_dns=self.local_install,
            )

    def __questions_maintenance(self):
        if self.first_time:
            message = (
                'You must run setup first: `python3 run.py --setup` '
            )
            CLI.framed_print(message, color=CLI.COLOR_INFO)
            sys.exit(1)

        def _round_nearest_quarter(dt):
            minutes = int(
                15 * round((float(dt.minute) + float(dt.second) / 60) / 15))
            return datetime(dt.year, dt.month, dt.day, dt.hour,
                            minutes if minutes < 60 else 0)

        CLI.colored_print('How long do you plan to this maintenance will last?',
                          CLI.COLOR_QUESTION)
        self.__dict['maintenance_eta'] = CLI.get_response(
            r'~^[\w\ ]+$',
            self.__dict['maintenance_eta'])

        date_start = _round_nearest_quarter(datetime.utcnow())
        iso_format = '%Y%m%dT%H%M'
        CLI.colored_print('Start Date/Time (ISO format) GMT?',
                          CLI.COLOR_QUESTION)
        self.__dict['maintenance_date_iso'] = CLI.get_response(
            r'~^\d{8}T\d{4}$', date_start.strftime(iso_format))
        self.__dict['maintenance_date_iso'] = self.__dict[
            'maintenance_date_iso'].upper()

        date_iso = self.__dict['maintenance_date_iso']
        self.__dict['maintenance_date_str'] = datetime.strptime(date_iso,
                                                                iso_format). \
            strftime('%A,&nbsp;%B&nbsp;%d&nbsp;at&nbsp;%H:%M&nbsp;GMT')

        self.__dict['maintenance_email'] = CLI.colored_input(
            'Contact during maintenance?',
            CLI.COLOR_QUESTION,
            self.__dict['maintenance_email']
        )
        self.write_config()

    def __questions_mongo(self):
        """
        Ask for MongoDB credentials only when server is for:
        - primary back end
        - single server installation
        """
        if self.primary_backend or not self.multi_servers:
            mongo_user_username = self.__dict['mongo_user_username']
            mongo_user_password = self.__dict['mongo_user_password']
            mongo_root_username = self.__dict['mongo_root_username']
            mongo_root_password = self.__dict['mongo_root_password']

            CLI.colored_print("MongoDB root's username?",
                              CLI.COLOR_QUESTION)
            self.__dict['mongo_root_username'] = CLI.get_response(
                r'~^\w+$',
                self.__dict['mongo_root_username'],
                to_lower=False)

            CLI.colored_print("MongoDB root's password?", CLI.COLOR_QUESTION)
            self.__dict['mongo_root_password'] = CLI.get_response(
                self.__get_password_validation_pattern(),
                self.__dict['mongo_root_password'],
                to_lower=False,
                error_msg=(
                    'Invalid password. '
                    'Rules: Alphanumeric characters only, 8 characters minimum'
                )
            )

            CLI.colored_print("MongoDB user's username?",
                              CLI.COLOR_QUESTION)
            self.__dict['mongo_user_username'] = CLI.get_response(
                r'~^\w+$',
                self.__dict['mongo_user_username'],
                to_lower=False)

            CLI.colored_print("MongoDB user's password?", CLI.COLOR_QUESTION)
            self.__dict['mongo_user_password'] = CLI.get_response(
                self.__get_password_validation_pattern(),
                self.__dict['mongo_user_password'],
                to_lower=False,
                error_msg=(
                    'Invalid password. '
                    'Rules: Alphanumeric characters only, 8 characters minimum'
                )
            )

            if (
                not self.__dict.get('mongo_secured')
                or mongo_user_username != self.__dict['mongo_user_username']
                or mongo_user_password != self.__dict['mongo_user_password']
                or mongo_root_username != self.__dict['mongo_root_username']
                or mongo_root_password != self.__dict['mongo_root_password']
            ) and not self.first_time:

                # Because chances are high we cannot communicate with DB
                # (e.g ports not exposed, containers down), we delegate the task
                # to MongoDB container to update (create/delete) users.
                # (see. `kobo-docker/mongo/upsert_users.sh`)
                # We have to transmit old users (and their respective DB) to
                # MongoDB to let it know which users need to be deleted.

                # `content` will be read by MongoDB container at next boot
                # It should contains users to delete if any.
                # Its format should be: `<user><TAB><database>`
                content = ''

                if (
                    mongo_user_username != self.__dict['mongo_user_username']
                    or mongo_root_username != self.__dict['mongo_root_username']
                ):

                    message = (
                        'WARNING!\n\n'
                        "MongoDB root's and/or user's usernames have changed!"
                    )
                    CLI.framed_print(message)
                    question = 'Do you want to remove old users?'
                    response = CLI.yes_no_question(question)
                    if response is True:
                        usernames_by_db = {
                            mongo_user_username: 'formhub',
                            mongo_root_username: 'admin'
                        }
                        for username, db in usernames_by_db.items():
                            if username != '':
                                content += '{cr}{username}\t{db}'.format(
                                    cr='\n' if content else '',
                                    username=username,
                                    db=db
                                )

                self.__write_upsert_db_users_trigger_file(content, 'mongo')

            self.__dict['mongo_secured'] = True

    def __questions_multi_servers(self):
        """
        Asks if installation is for only one server
        or different front-end and back-end servers.
        """
        self.__dict['multi'] = CLI.yes_no_question(
            'Do you want to use separate servers for front end and back end?',
            default=self.__dict['multi']
        )

    def __questions_postgres(self):
        """
        Postgres credentials and settings.

        Settings can be tweaked thanks to pgconfig.org API
        """
        CLI.colored_print('KoBoCat PostgreSQL database name?',
                          CLI.COLOR_QUESTION)
        kc_postgres_db = CLI.get_response(
            r'~^\w+$',
            self.__dict['kc_postgres_db'],
            to_lower=False
        )

        CLI.colored_print('KPI PostgreSQL database name?',
                          CLI.COLOR_QUESTION)
        kpi_postgres_db = CLI.get_response(
            r'~^\w+$',
            self.__dict['kpi_postgres_db'],
            to_lower=False)

        while kpi_postgres_db == kc_postgres_db:
            kpi_postgres_db = CLI.colored_input(
                'KPI must use its own PostgreSQL database, not share one with '
                'KoBoCAT. Please enter another database',
                CLI.COLOR_ERROR,
                Config.get_template()['kpi_postgres_db'],
            )

        if (kc_postgres_db != self.__dict['kc_postgres_db'] or
                (kpi_postgres_db != self.__dict['kpi_postgres_db'] and
                 self.__dict['two_databases'])):
            message = (
                'WARNING!\n\n'
                'PostgreSQL database names have changed!\n'
                'kobo-install does not support database name changes after '
                'database initialization.\n'
                'Data will not appear in KPI and/or KoBoCAT.'
            )
            CLI.framed_print(message)

            response = CLI.yes_no_question(
                'Do you want to continue?',
                default=False
            )
            if response is False:
                sys.exit(0)

        self.__dict['kc_postgres_db'] = kc_postgres_db
        self.__dict['kpi_postgres_db'] = kpi_postgres_db
        self.__dict['two_databases'] = True

        postgres_user = self.__dict['postgres_user']
        postgres_password = self.__dict['postgres_password']

        CLI.colored_print("PostgreSQL user's username?",
                          CLI.COLOR_QUESTION)
        self.__dict['postgres_user'] = CLI.get_response(
            r'~^\w+$',
            self.__dict['postgres_user'],
            to_lower=False)

        CLI.colored_print("PostgreSQL user's password?", CLI.COLOR_QUESTION)
        self.__dict['postgres_password'] = CLI.get_response(
            self.__get_password_validation_pattern(),
            self.__dict['postgres_password'],
            to_lower=False,
            error_msg=(
                'Invalid password. '
                'Rules: Alphanumeric characters only, 8 characters minimum'
            )
        )

        if (postgres_user != self.__dict['postgres_user'] or
            postgres_password != self.__dict['postgres_password']) and \
                not self.first_time:

            # Because chances are high we cannot communicate with DB
            # (e.g ports not exposed, containers down), we delegate the task
            # to PostgreSQL container to update (create/delete) users.
            # (see. `kobo-docker/postgres/shared/upsert_users.sh`)
            # We need to transmit old user to PostgreSQL to let it know
            # what was the previous username to log in before performing any
            # action.

            # `content` will be read by PostgreSQL container at next boot
            # It should always contain previous username and a boolean
            # for deletion.
            # Its format should be: `<user><TAB><boolean>`
            content = f'{postgres_user}\tfalse'

            if postgres_user != self.__dict['postgres_user']:

                CLI.colored_print("PostgreSQL user's username has changed!",
                                  CLI.COLOR_WARNING)
                question = 'Do you want to remove old user?',
                response = CLI.yes_no_question(question)
                if response is True:
                    content = f'{postgres_user}\ttrue'
                    message = (
                        'WARNING!\n\n'
                        'User cannot be deleted if it has been used to '
                        'initialize PostgreSQL server.\n'
                        'You will need to do it manually!'
                    )
                    CLI.framed_print(message)

            self.__write_upsert_db_users_trigger_file(content, 'postgres')

        if self.backend:
            # Postgres settings
            self.__dict['postgres_settings'] = CLI.yes_no_question(
                'Do you want to tweak PostgreSQL settings?',
                default=self.__dict['postgres_settings']
            )

            template = self.get_template()

            if self.__dict['postgres_settings']:

                CLI.colored_print('Launching pgconfig.org API container...',
                                  CLI.COLOR_INFO)

                # From https://docs.pgconfig.org/api/#available-parameters
                # Parameters are case-sensitive, for example
                # `environment_name` must be one these values:
                # - `WEB`
                # - `OLTP`,
                # - `DW`
                # - `Mixed`
                # - `Desktop`
                # It's case-sensitive.

                CLI.colored_print('Number of CPUs?', CLI.COLOR_QUESTION)
                self.__dict['postgres_cpus'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['postgres_cpus'])

                CLI.colored_print('Total Memory in GB?', CLI.COLOR_QUESTION)
                self.__dict['postgres_ram'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['postgres_ram'])

                CLI.colored_print('Storage type?', CLI.COLOR_QUESTION)
                CLI.colored_print('\thdd) Hard Disk Drive')
                CLI.colored_print('\tssd) Solid State Drive')
                CLI.colored_print('\tsan) Storage Area Network')
                self.__dict['postgres_hard_drive_type'] = CLI.get_response(
                    ['hdd', 'ssd', 'san'],
                    self.__dict['postgres_hard_drive_type'].lower())

                CLI.colored_print('Number of connections?', CLI.COLOR_QUESTION)
                self.__dict['postgres_max_connections'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['postgres_max_connections'])

                if self.multi_servers:
                    multi_servers_profiles = ['web', 'oltp', 'dw', 'mixed']
                    if (
                        self.__dict['postgres_profile'].lower()
                        not in multi_servers_profiles
                    ):
                        self.__dict['postgres_profile'] = template[
                            'postgres_profile'
                        ]

                    CLI.colored_print('Application profile?', CLI.COLOR_QUESTION)
                    CLI.colored_print('\tweb) General Web application')
                    CLI.colored_print(
                        '\toltp) ERP or long transaction applications')
                    CLI.colored_print('\tdw) DataWare house')
                    CLI.colored_print('\tmixed) DB and APP on the same server')

                    self.__dict['postgres_profile'] = CLI.get_response(
                        ['web', 'oltp', 'dw', 'mixed'],
                        self.__dict['postgres_profile'].lower())

                    self.__dict['postgres_profile'] = self.__dict[
                        'postgres_profile'].upper()

                elif self.dev_mode:
                    self.__dict['postgres_profile'] = 'Desktop'
                else:
                    self.__dict['postgres_profile'] = 'Mixed'

                # Use pgconfig.org API to get the configuration
                # Notes: It has failed several times in the past.
                endpoint = (
                    'https://api.pgconfig.org/v1/tuning/get-config'
                    '?environment_name={profile}&format=conf'
                    '&include_pgbadger=false'
                    '&cpus={cpus}'
                    '&max_connections={max_connections}'
                    '&pg_version=14'
                    '&total_ram={ram}GB'
                    '&drive_type={drive_type}'
                    '&os_type=linux'
                )
                endpoint = endpoint.format(
                    profile=self.__dict['postgres_profile'],
                    ram=self.__dict['postgres_ram'],
                    cpus=self.__dict['postgres_cpus'],
                    max_connections=self.__dict['postgres_max_connections'],
                    drive_type=self.__dict['postgres_hard_drive_type'].upper()
                )
                response = Network.curl(endpoint)
                if response:
                    # Patch response because of https://github.com/pgconfig/api/issues/13
                    configuration = re.sub(r'(\d+)KB', r'\1kB', response)
                    self.__dict['postgres_settings_content'] = configuration
                else:
                    CLI.colored_print('\nAn error has occurred. Current '
                                      'PostgreSQL settings will be used',
                                      CLI.COLOR_INFO)

            else:
                # Forcing the default settings to remain even if there
                # is an existing value in .run.conf. Without this,
                # the value for `postgres_settings_content` would not update

                self.__dict['postgres_settings_content'] = template[
                    'postgres_settings_content'
                ]

    def __questions_ports(self):
        """
        Customize services ports
        """

        def reset_ports():
            self.__dict['postgresql_port'] = '5432'
            self.__dict['mongo_port'] = '27017'
            self.__dict['redis_main_port'] = '6379'
            self.__dict['redis_cache_port'] = '6380'

        if not self.multi_servers:
            self.__dict['expose_backend_ports'] = CLI.yes_no_question(
                'Do you want to expose back-end container ports '
                '(`PostgreSQL`, `MongoDB`, `Redis`)?',
                default=self.__dict['expose_backend_ports']
            )
        else:
            self.__dict['expose_backend_ports'] = True

        if not self.expose_backend_ports:
            reset_ports()
            return

        if self.backend:
            message = (
                'WARNING!\n\n'
                'When exposing back-end container ports, it is STRONGLY '
                'recommended to use a firewall to grant access to front-end '
                'containers only.'
            )
            CLI.framed_print(message)

        self.__dict['customized_ports'] = CLI.yes_no_question(
            'Do you want to customize service ports?',
            default=self.__dict['customized_ports']
        )

        if not self.__dict['customized_ports']:
            reset_ports()
            return

        CLI.colored_print('PostgreSQL?', CLI.COLOR_QUESTION)
        self.__dict['postgresql_port'] = CLI.get_response(
            r'~^\d+$', self.__dict['postgresql_port'])

        CLI.colored_print('MongoDB?', CLI.COLOR_QUESTION)
        self.__dict['mongo_port'] = CLI.get_response(
            r'~^\d+$', self.__dict['mongo_port'])

        CLI.colored_print('Redis (main)?', CLI.COLOR_QUESTION)
        self.__dict['redis_main_port'] = CLI.get_response(
            r'~^\d+$', self.__dict['redis_main_port'])

        CLI.colored_print('Redis (cache)?', CLI.COLOR_QUESTION)
        self.__dict['redis_cache_port'] = CLI.get_response(
            r'~^\d+$', self.__dict['redis_cache_port'])

    def __questions_private_routes(self):
        """
        Asks if configuration uses a DNS for private domain names
        for communication between front end and back end.
        Otherwise, it will create entries in `extra_hosts` in composer
        file based on the provided ip.
        """
        self.__dict['use_private_dns'] = CLI.yes_no_question(
            'Do you use DNS for private routes?',
            default=self.__dict['use_private_dns']
        )
        if self.__dict['use_private_dns'] is False:
            CLI.colored_print('IP address (IPv4) of primary back-end server?',
                              CLI.COLOR_QUESTION)
            self.__dict['primary_backend_ip'] = CLI.get_response(
                r'~\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
                self.__dict['primary_backend_ip'])
        else:
            self.__dict['private_domain_name'] = CLI.colored_input(
                'Private domain name?',
                CLI.COLOR_QUESTION,
                self.__dict['private_domain_name'])

    def __questions_public_routes(self):
        """
        Asks for public domain names
        """

        self.__dict['public_domain_name'] = CLI.colored_input(
            'Public domain name?', CLI.COLOR_QUESTION,
            self.__dict['public_domain_name'])
        self.__dict['kpi_subdomain'] = CLI.colored_input(
            'KPI sub domain?',
            CLI.COLOR_QUESTION,
            self.__dict['kpi_subdomain']
        )
        self.__dict['kc_subdomain'] = CLI.colored_input(
            'KoBoCat sub domain?',
            CLI.COLOR_QUESTION,
            self.__dict['kc_subdomain']
        )
        self.__dict['ee_subdomain'] = CLI.colored_input(
            'Enketo Express sub domain name?',
            CLI.COLOR_QUESTION,
            self.__dict['ee_subdomain']
        )

        parts = self.__dict['public_domain_name'].split('.')
        domain_wo_tld = '.'.join(parts[:-1])
        self.__dict['internal_domain_name'] = f'{domain_wo_tld}.internal'

        if not self.multi_servers or \
                (self.multi_servers and not self.use_private_dns):
            self.__dict['private_domain_name'] = f'{domain_wo_tld}.private'

    def __questions_raven(self):
        self.__dict['raven_settings'] = CLI.yes_no_question(
            'Do you want to use Sentry?',
            default=self.__dict['raven_settings']
        )
        if self.__dict['raven_settings'] is True:
            self.__dict['kpi_raven'] = CLI.colored_input(
                'KPI Raven token',
                CLI.COLOR_QUESTION,
                self.__dict['kpi_raven'])
            self.__dict['kobocat_raven'] = CLI.colored_input(
                'KoBoCat Raven token', CLI.COLOR_QUESTION,
                self.__dict['kobocat_raven'])
            self.__dict['kpi_raven_js'] = CLI.colored_input(
                'KPI Raven JS token', CLI.COLOR_QUESTION,
                self.__dict['kpi_raven_js'])
        else:
            self.__dict['kpi_raven'] = ''
            self.__dict['kobocat_raven'] = ''
            self.__dict['kpi_raven_js'] = ''

    def __questions_redis(self):
        """
        Ask for Redis password only when server is for:
        - primary back end
        - single server installation
        """
        if self.backend:
            self.__dict['run_redis_containers'] = CLI.yes_no_question(
                'Do you want to run the Redis containers from this server?',
                default=self.__dict['run_redis_containers']
            )
        else:
            self.__dict['run_redis_containers'] = True

        if self.__dict['run_redis_containers']:
            CLI.colored_print('Redis password?', CLI.COLOR_QUESTION)
            self.__dict['redis_password'] = CLI.get_response(
                self.__get_password_validation_pattern(allow_empty=True),
                self.__dict['redis_password'],
                to_lower=False,
                error_msg=(
                    'Invalid password. '
                    'Rules: Alphanumeric characters only, 8 characters minimum'
                )
            )

            if not self.__dict['redis_password']:
                message = (
                    'WARNING!\n\n'
                    'It is STRONGLY recommended to set a password for Redis '
                    'as well.'
                )
                CLI.framed_print(message)
                response = CLI.yes_no_question(
                    'Do you want to continue without password?',
                    default=False
                )
                if response is False:
                    self.__questions_redis()

            if self.backend:
                CLI.colored_print('Max memory (MB) for Redis cache container?',
                                  CLI.COLOR_QUESTION)
                CLI.colored_print('Leave empty for no limits',
                                  CLI.COLOR_INFO)
                self.__dict['redis_cache_max_memory'] = CLI.get_response(
                    r'~^(\d+|-)?$',
                    self.__dict['redis_cache_max_memory'])

    def __questions_reverse_proxy(self):

        if self.is_secure:

            self.__dict['use_letsencrypt'] = CLI.yes_no_question(
                "Auto-install HTTPS certificates with Let's Encrypt?",
                default=self.__dict['use_letsencrypt'],
                labels=[
                    'Yes',
                    'No - Use my own reverse-proxy/load-balancer',
                ]
            )
            self.__dict['proxy'] = True
            self.__dict[
                'exposed_nginx_docker_port'] = Config.DEFAULT_NGINX_PORT

            if self.use_letsencrypt:
                self.__dict['nginx_proxy_port'] = Config.DEFAULT_PROXY_PORT

                message = (
                    'WARNING!\n\n'
                    'Domain names must be publicly accessible.\n'
                    "Otherwise Let's Encrypt will not be able to valid your "
                    'certificates.'
                )
                CLI.framed_print(message)

                if self.first_time:
                    email = self.__dict['default_from_email']
                    self.__dict['letsencrypt_email'] = email

                while True:
                    letsencrypt_email = CLI.colored_input(
                        "Email address for Let's Encrypt?",
                        CLI.COLOR_QUESTION,
                        self.__dict['letsencrypt_email'])
                    question = f'Please confirm [{letsencrypt_email}]'
                    response = CLI.yes_no_question(question)
                    if response is True:
                        self.__dict['letsencrypt_email'] = letsencrypt_email
                        break

                self.__clone_repo(self.get_letsencrypt_repo_path(),
                                  'nginx-certbot')
        else:
            if self.advanced_options:
                self.__dict['proxy'] = CLI.yes_no_question(
                    'Are kobo-docker containers behind a '
                    'reverse-proxy/load-balancer?',
                    default=self.__dict['proxy']
                )
                self.__dict['use_letsencrypt'] = False
            else:
                self.__dict['proxy'] = False

        if self.proxy:
            # When proxy is enabled, public port is 80 or 443.
            # @TODO Give the user the possibility to customize it too.
            self.__dict[
                'exposed_nginx_docker_port'] = Config.DEFAULT_NGINX_PORT
            if self.advanced_options:
                if not self.use_letsencrypt:
                    response = CLI.yes_no_question(
                        'Is your reverse-proxy/load-balancer installed on '
                        'this server?',
                        default=self.__dict['block_common_http_ports']
                    )
                    self.__dict['block_common_http_ports'] = response
                else:
                    self.__dict['block_common_http_ports'] = True

                if not self.__is_port_allowed(
                        self.__dict['nginx_proxy_port']):
                    # Force nginx proxy port if port is not allowed
                    self.__dict[
                        'nginx_proxy_port'] = Config.DEFAULT_PROXY_PORT

                if not self.use_letsencrypt:
                    CLI.colored_print('Internal port used by reverse proxy?',
                                      CLI.COLOR_QUESTION)
                    while True:
                        self.__dict['nginx_proxy_port'] = CLI.get_response(
                            r'~^\d+$',
                            self.__dict['nginx_proxy_port'])
                        if self.__is_port_allowed(
                                self.__dict['nginx_proxy_port']):
                            break
                        else:
                            CLI.colored_print('Ports 80 and 443 are reserved!',
                                              CLI.COLOR_ERROR)
            else:
                self.__dict['block_common_http_ports'] = True
                if not self.use_letsencrypt:
                    CLI.colored_print(
                        'Internal port used by reverse proxy is '
                        f'{Config.DEFAULT_PROXY_PORT}.',
                        CLI.COLOR_WARNING)
                self.__dict['nginx_proxy_port'] = Config.DEFAULT_PROXY_PORT

        else:
            self.__dict['use_letsencrypt'] = False
            self.__dict['nginx_proxy_port'] = Config.DEFAULT_NGINX_PORT
            self.__dict['block_common_http_ports'] = False

    def __questions_roles(self):
        CLI.colored_print('Which role do you want to assign to this server?',
                          CLI.COLOR_QUESTION)
        CLI.colored_print('\t1) frontend')
        CLI.colored_print('\t2) backend')
        self.__dict['server_role'] = CLI.get_response(
            ['backend', 'frontend'],
            self.__dict['server_role'])

        if self.__dict['server_role'] == 'backend':
            CLI.colored_print(
                'Which role do you want to assign to this back-end server?',
                CLI.COLOR_QUESTION)
            CLI.colored_print('\t1) primary')
            CLI.colored_print('\t2) secondary')
            self.__dict['backend_server_role'] = CLI.get_response(
                ['primary', 'secondary'],
                self.__dict['backend_server_role'])
        else:
            # It may be useless to force back-end role when using multi servers.
            self.__dict['backend_server_role'] = 'primary'

    def __questions_secret_keys(self):
        self.__dict['custom_secret_keys'] = CLI.yes_no_question(
            'Do you want to customize the application secret keys?',
            default=self.__dict['custom_secret_keys']
        )
        if self.__dict['custom_secret_keys'] is True:
            CLI.colored_print("Django's secret key?", CLI.COLOR_QUESTION)
            self.__dict['django_secret_key'] = CLI.get_response(
                r'~^.{50,}$',
                self.__dict['django_secret_key'],
                to_lower=False,
                error_msg='Too short. 50 characters minimum.')

            CLI.colored_print("Enketo's api key?", CLI.COLOR_QUESTION)
            self.__dict['enketo_api_token'] = CLI.get_response(
                r'~^.{50,}$',
                self.__dict['enketo_api_token'],
                to_lower=False,
                error_msg='Too short. 50 characters minimum.')

            CLI.colored_print("Enketo's encryption key?", CLI.COLOR_QUESTION)
            self.__dict['enketo_encryption_key'] = CLI.get_response(
                r'~^.{50,}$',
                self.__dict['enketo_encryption_key'],
                to_lower=False,
                error_msg='Too short. 50 characters minimum.')

            CLI.colored_print("Enketo's less secure encryption key?",
                              CLI.COLOR_QUESTION)
            self.__dict[
                'enketo_less_secure_encryption_key'] = CLI.get_response(
                r'~^.{10,}$',
                self.__dict['enketo_less_secure_encryption_key'],
                to_lower=False,
                error_msg='Too short. 10 characters minimum.')

    def __questions_service_account(self):
        if not self.local_install:
            self.__dict['service_account_whitelisted_hosts'] = CLI.yes_no_question(
                'Do you want to restrict API calls between KPI and KoBoCAT '
                'to their internal domain names?',
                default=self.__dict['service_account_whitelisted_hosts']
            )
        else:
            self.__dict['service_account_whitelisted_hosts'] = False

    def __questions_session_cookies(self):
        # convert seconds to hours
        session_length_in_hours = (
            int(self.__dict['django_session_cookie_age'] / 60 / 60)
        )
        # Ask user's input and validate it
        CLI.colored_print(
            'Length of users\' session (in hours)?',
            CLI.COLOR_QUESTION,
        )
        session_length_in_hours = CLI.get_response(
            r'~^\d+$',
            str(session_length_in_hours),
        )
        # convert it back to seconds
        self.__dict['django_session_cookie_age'] = (
            int(session_length_in_hours) * 60 * 60
        )

    def __questions_smtp(self):
        self.__dict['smtp_host'] = CLI.colored_input('SMTP server?',
                                                     CLI.COLOR_QUESTION,
                                                     self.__dict['smtp_host'])
        self.__dict['smtp_port'] = CLI.colored_input('SMTP port?',
                                                     CLI.COLOR_QUESTION,
                                                     self.__dict['smtp_port'])
        self.__dict['smtp_user'] = CLI.colored_input('SMTP user?',
                                                     CLI.COLOR_QUESTION,
                                                     self.__dict['smtp_user'])
        if self.__dict['smtp_user']:
            self.__dict['smtp_password'] = CLI.colored_input(
                'SMTP password',
                CLI.COLOR_QUESTION,
                self.__dict['smtp_password']
            )
            self.__dict['smtp_use_tls'] = CLI.yes_no_question(
                'Use TLS?',
                default=self.__dict['smtp_use_tls']
            )

        if self.first_time:
            domain_name = self.__dict['public_domain_name']
            self.__dict['default_from_email'] = f'support@{domain_name}'

        self.__dict['default_from_email'] = CLI.colored_input(
            'From email address?',
            CLI.COLOR_QUESTION,
            self.__dict['default_from_email']
        )

    def __questions_super_user_credentials(self):
        # Super user. Only ask for credentials the first time.
        # Super user is created if db doesn't exists.
        username = CLI.colored_input("Super user's username?",
                                     CLI.COLOR_QUESTION,
                                     self.__dict['super_user_username'])
        password = CLI.colored_input("Super user's password?",
                                     CLI.COLOR_QUESTION,
                                     self.__dict['super_user_password'])

        if username == self.__dict['super_user_username'] and \
                password != self.__dict['super_user_password'] and \
                not self.first_time:
            message = (
                'WARNING!\n\n'
                'You have configured a new password for the super user.\n'
                'This change will *not* take effect if KoboToolbox has ever '
                'been started before. Please use the web interface to change '
                'passwords for existing users.\n'
                'If you have forgotten your password:\n'
                '1. Enter the KPI container with `python3 run.py -cf exec kpi '
                'bash`;\n'
                '2. Create a new super user with `./manage.py '
                'createsuperuser`;\n'
                '3. Type `exit` to leave the KPI container;'
            )
            CLI.framed_print(message)
        self.__dict['super_user_username'] = username
        self.__dict['super_user_password'] = password

    def __questions_uwsgi(self):

        if not self.dev_mode:
            self.__dict['uwsgi_settings'] = CLI.yes_no_question(
                'Do you want to tweak uWSGI settings?',
                default=self.__dict['uwsgi_settings']
            )

            if self.__dict['uwsgi_settings']:
                CLI.colored_print('Number of uWSGI workers to start?',
                                  CLI.COLOR_QUESTION)
                self.__dict['uwsgi_workers_start'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_workers_start'])

                CLI.colored_print('Maximum uWSGI workers?', CLI.COLOR_QUESTION)
                self.__dict['uwsgi_workers_max'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_workers_max'])

                CLI.colored_print('Maximum number of requests per worker?',
                                  CLI.COLOR_QUESTION)
                self.__dict['uwsgi_max_requests'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_max_requests'])

                CLI.colored_print('Stop spawning workers if uWSGI memory use '
                                  'exceeds this many MB: ',
                                  CLI.COLOR_QUESTION)
                self.__dict['uwsgi_soft_limit'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_soft_limit'])

                CLI.colored_print('Maximum time (in seconds) before killing an '
                                  'unresponsive worker?', CLI.COLOR_QUESTION)
                self.__dict['uwsgi_harakiri'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_harakiri'])

                CLI.colored_print('Maximum time (in seconds) a worker can take '
                                  'to reload/shutdown?', CLI.COLOR_QUESTION)
                self.__dict['uwsgi_worker_reload_mercy'] = CLI.get_response(
                    r'~^\d+$',
                    self.__dict['uwsgi_worker_reload_mercy'])

                return

        self.__dict['uwsgi_workers_start'] = '2'
        self.__dict['uwsgi_workers_max'] = '4'
        self.__dict['uwsgi_max_requests'] = '1024'
        self.__dict['uwsgi_soft_limit'] = '1024'
        self.__dict['uwsgi_harakiri'] = '120'
        self.__dict['uwsgi_worker_reload_mercy'] = '120'

    def __is_port_allowed(self, port):
        return not (self.block_common_http_ports and port in [
            Config.DEFAULT_NGINX_PORT,
            Config.DEFAULT_NGINX_HTTPS_PORT])

    def __reset(self, **kwargs):
        """
        Resets several properties to their default.
        It can be useful, if user changes the type of installation on
        the same server

        Kwargs:
            production (bool): If `True`, reset config to production mode
            http (bool): If `True`, only set values related to http/https config
            fake_dns (bool): If `True`, reset config to fake dns on docker-compose files  # noqa
            nginx_default (bool): If `True`, reset NGINX exposed port to default
        """
        all_ = True if not kwargs else False
        production = kwargs.get('production', False)
        http = kwargs.get('http', False)
        fake_dns = kwargs.get('fake_dns', False)
        nginx_default = kwargs.get('nginx_default', False)
        no_backups = kwargs.get('no_backups', False)

        if production or all_:
            self.__dict['dev_mode'] = False
            self.__dict['staging_mode'] = False
            self.__dict['kc_path'] = ''
            self.__dict['kpi_path'] = ''
            self.__dict['debug'] = False
            self.__dict['use_celery'] = True
            if nginx_default:
                self.__dict[
                    'exposed_nginx_docker_port'] = Config.DEFAULT_NGINX_PORT

        if fake_dns or all_:
            self.__dict['use_private_dns'] = False

        if http or all_:
            self.__dict['multi'] = False
            self.__dict['https'] = False
            self.__dict['proxy'] = False
            self.__dict['nginx_proxy_port'] = Config.DEFAULT_NGINX_PORT
            self.__dict['use_letsencrypt'] = False

        if no_backups or all_:
            self.__dict['backup_from_primary'] = True
            self.__dict['use_backup'] = False
            self.__dict['use_wal_e'] = False

    def __secure_mongo(self):
        """
        Force creations of MongoDB users/passwords when users upgrade from
        a non secure version of kobo-install
        """
        # ToDo remove duplicated code with `__questions_mongo`
        if not self.__dict.get('mongo_secured') and not self.first_time:
            self.__write_upsert_db_users_trigger_file('', 'mongo')

        self.__dict['mongo_secured'] = True

    def __validate_installation(self):
        """
        Validates if installation is not run over existing data.
        The check is made only the first time the setup is run.
        :return: bool
        """
        if self.first_time:
            mongo_dir_path = os.path.join(self.__dict['kobodocker_path'],
                                          '.vols', 'mongo')
            postgres_dir_path = os.path.join(self.__dict['kobodocker_path'],
                                             '.vols', 'db')
            mongo_data_exists = (
                    os.path.exists(mongo_dir_path) and os.path.isdir(
                mongo_dir_path) and
                    os.listdir(mongo_dir_path))
            postgres_data_exists = os.path.exists(
                postgres_dir_path) and os.path.isdir(postgres_dir_path)

            if mongo_data_exists or postgres_data_exists:
                # Not a reliable way to detect whether folder contains
                # kobo-install files. We assume that if
                # `docker-compose.backend.template.yml` is there, Docker
                # images are the good ones.
                # TODO Find a better way
                docker_composer_file_path = os.path.join(
                    self.__dict['kobodocker_path'],
                    'docker-compose.backend.template.yml')
                if not os.path.exists(docker_composer_file_path):
                    message = (
                        'WARNING!\n\n'
                        'You are installing over existing data.\n'
                        '\n'
                        'It is recommended to backup your data and import it '
                        'to a fresh installed (by KoBoInstall) database.\n'
                        '\n'
                        'kobo-install uses these images:\n'
                        '    - MongoDB: mongo:3.4\n'
                        '    - PostgreSQL: mdillon/postgis:9.5\n'
                        '\n'
                        'Be sure to upgrade to these versions before going '
                        'further!'
                    )
                    CLI.framed_print(message)
                    response = CLI.yes_no_question(
                        'Are you sure you want to continue?',
                        default=False
                    )
                    if response is False:
                        sys.exit(0)
                    else:
                        CLI.colored_print(
                            'Privileges escalation is needed to prepare DB',
                            CLI.COLOR_WARNING)
                        # Write `kobo_first_run` file to run postgres
                        # container's entrypoint flawlessly.
                        filepath = os.path.join(
                            self.__dict['kobodocker_path'],
                            '.vols',
                            'db',
                            'kobo_first_run'
                        )
                        os.system(
                            f'echo $(date) | sudo tee -a {filepath} > /dev/null'
                        )

    @staticmethod
    def __welcome():
        message = (
            'Welcome to kobo-install.\n'
            '\n'
            'You are going to be asked some questions that will determine how '
            'to build the configuration of `KoboToolBox`.\n'
            '\n'
            'Some questions already have default values (within brackets).\n'
            'Just press `enter` to accept the default value or enter `-` to '
            'remove previously entered value.\n'
            'Otherwise choose between choices or type your answer. '
        )
        CLI.framed_print(message, color=CLI.COLOR_INFO)

    def __write_upsert_db_users_trigger_file(self, content, destination):
        try:
            trigger_file = os.path.join(self.__dict['kobodocker_path'],
                                        destination,
                                        Config.UPSERT_DB_USERS_TRIGGER_FILE)
            with open(trigger_file, 'w') as f:
                f.write(content)
        except (IOError, OSError):
            filename = Config.UPSERT_DB_USERS_TRIGGER_FILE
            CLI.colored_print(f'Could not write {filename} file',
                              CLI.COLOR_ERROR)
            return False

        return True
