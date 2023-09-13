# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.template import Template
from helpers.upgrading import Upgrading
from helpers.utils import run_docker_compose


class Command:

    @staticmethod
    def help():
        output = [
            'Usage: python3 run.py [options]',
            '',
            '    Options:',
            '          -i, --info',
            '                Show KoboToolbox Url and super user credentials',
            '          -l, --logs',
            '                Display docker logs',
            '          -b, --build',
            '                Build kpi and kobocat (only on dev/staging mode)',
            '          -bkf, --build-kpi',
            '                Build kpi (only on dev/staging mode)',
            '          -bkc, --build-kobocat',
            '                Build kobocat (only on dev/staging mode)',
            '          -s, --setup',
            '                Prompt questions to (re)write configuration files',
            '          -S, --stop',
            '                Stop KoboToolbox',
            '          -u, --update, --upgrade [branch or tag]',
            '                Update KoboToolbox',
            '          -cf, --compose-frontend [docker-compose arguments]',
            '                Run a docker-compose command in the front-end '
            'environment',
            '          -cb, --compose-backend [docker-compose arguments]',
            '                Run a docker-compose command in the back-end '
            'environment',
            '          -m, --maintenance',
            '                Activate maintenance mode. All traffic is '
            'redirected to maintenance page',
            '          -sm, --stop-maintenance',
            '                Stop maintenance mode',
            '          -v, --version',
            '                Display current version',
            ''
        ]
        print('\n'.join(output))

    @classmethod
    def build(cls, image=None):
        """
        Builds kpi/kobocat images with `--no-caches` option
        Pulls latest `kobotoolbox/koboform_base` as well

        :param image: str
        """
        config = Config()
        dict_ = config.get_dict()

        if config.dev_mode or config.staging_mode:

            def build_image(image_):
                frontend_command = run_docker_compose(dict_, [
                    '-f', 'docker-compose.frontend.yml',
                    '-f', 'docker-compose.frontend.override.yml',
                    '-p', config.get_prefix('frontend'),
                    'build', '--force-rm', '--no-cache',
                    image_
                ])

                CLI.run_command(frontend_command, dict_['kobodocker_path'])

            if image is None or image == 'kf':
                prefix = config.get_prefix('frontend')
                timestamp = int(time.time())
                dict_['kpi_dev_build_id'] = f'{prefix}{timestamp}'
                config.write_config()
                Template.render(config)
                build_image('kpi')

            if image is None or image == 'kc':
                pull_base_command = [
                    'docker',
                    'pull',
                    'kobotoolbox/koboform_base',
                ]

                CLI.run_command(pull_base_command, dict_['kobodocker_path'])

                prefix = config.get_prefix('frontend')
                timestamp = int(time.time())
                dict_['kc_dev_build_id'] = f'{prefix}{timestamp}'
                config.write_config()
                Template.render(config)
                build_image('kobocat')

    @classmethod
    def compose_frontend(cls, args):
        config = Config()
        dict_ = config.get_dict()
        command = run_docker_compose(dict_, [
           '-f', 'docker-compose.frontend.yml',
           '-f', 'docker-compose.frontend.override.yml',
           '-p', config.get_prefix('frontend')
        ])

        cls.__validate_custom_yml(config, command)
        command.extend(args)
        subprocess.call(command, cwd=dict_['kobodocker_path'])

    @classmethod
    def compose_backend(cls, args):
        config = Config()
        dict_ = config.get_dict()
        backend_role = dict_['backend_server_role']
        command = run_docker_compose(dict_, [
            '-f', f'docker-compose.backend.{backend_role}.yml',
            '-f', f'docker-compose.backend.{backend_role}.override.yml',
            '-p', config.get_prefix('backend')
        ])
        cls.__validate_custom_yml(config, command)
        command.extend(args)
        subprocess.call(command, cwd=dict_['kobodocker_path'])

    @classmethod
    def info(cls, timeout=600):
        config = Config()
        dict_ = config.get_dict()

        nginx_port = dict_['exposed_nginx_docker_port']

        main_url = '{}://{}.{}{}'.format(
            'https' if dict_['https'] else 'http',
            dict_['kpi_subdomain'],
            dict_['public_domain_name'],
            ':{}'.format(nginx_port) if (
                    nginx_port and
                    str(nginx_port) != Config.DEFAULT_NGINX_PORT
            ) else ''
        )

        stop = False
        start = int(time.time())
        success = False
        hostname = f"{dict_['kpi_subdomain']}.{dict_['public_domain_name']}"
        https = dict_['https']
        nginx_port = int(Config.DEFAULT_NGINX_HTTPS_PORT) \
            if https else int(dict_['exposed_nginx_docker_port'])
        already_retried = False
        while not stop:
            if Network.status_check(hostname,
                                    '/service_health/',
                                    nginx_port, https) == Network.STATUS_OK_200:
                stop = True
                success = True
            elif int(time.time()) - start >= timeout:
                if timeout > 0:
                    CLI.colored_print(
                        '\n`KoBoToolbox` has not started yet. '
                        'This is can be normal with low CPU/RAM computers.\n',
                        CLI.COLOR_INFO)
                    question = f'Wait for another {timeout} seconds?'
                    response = CLI.yes_no_question(question)
                    if response:
                        start = int(time.time())
                        continue
                    else:
                        if not already_retried:
                            already_retried = True
                            CLI.colored_print(
                                '\nSometimes front-end containers cannot '
                                'communicate with back-end containers.\n'
                                'Restarting the front-end containers usually '
                                'fixes it.\n', CLI.COLOR_INFO)
                            question = 'Would you like to try?'
                            response = CLI.yes_no_question(question)
                            if response:
                                start = int(time.time())
                                cls.restart_frontend()
                                continue
                stop = True
            else:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(10)

        # Create a new line
        print('')

        if success:
            username = dict_['super_user_username']
            password = dict_['super_user_password']

            message = (
                'Ready\n'
                f'URL: {main_url}\n'
                f'User: {username}\n'
                f'Password: {password}'
            )
            CLI.framed_print(message,
                             color=CLI.COLOR_SUCCESS)

        else:
            message = (
                'KoBoToolbox could not start!\n'
                'Please try `python3 run.py --logs` to see the logs.'
            )
            CLI.framed_print(message, color=CLI.COLOR_ERROR)

        return success

    @classmethod
    def logs(cls):
        config = Config()
        dict_ = config.get_dict()

        if config.primary_backend or config.secondary_backend:
            backend_role = dict_['backend_server_role']
            backend_command = run_docker_compose(dict_, [
                '-f', f'docker-compose.backend.{backend_role}.yml',
                '-f', f'docker-compose.backend.{backend_role}.override.yml',
                '-p', config.get_prefix('backend'),
                'logs', '-f'
            ])
            cls.__validate_custom_yml(config, backend_command)
            CLI.run_command(backend_command, dict_['kobodocker_path'], True)

        if config.frontend:
            frontend_command = run_docker_compose(dict_, [
                '-f', 'docker-compose.frontend.yml',
                '-f', 'docker-compose.frontend.override.yml',
                '-p', config.get_prefix('frontend'),
                'logs', '-f',
            ])

            cls.__validate_custom_yml(config, frontend_command)
            CLI.run_command(frontend_command, dict_['kobodocker_path'], True)

    @classmethod
    def configure_maintenance(cls):
        config = Config()
        dict_ = config.get_dict()

        if not config.multi_servers or config.frontend:

            config.maintenance()
            Template.render_maintenance(config)
            dict_['maintenance_enabled'] = True
            config.write_config()
            cls.stop_nginx()
            cls.start_maintenance()

    @classmethod
    def stop_nginx(cls):
        config = Config()
        dict_ = config.get_dict()

        nginx_stop_command = run_docker_compose(dict_, [
            '-f', 'docker-compose.frontend.yml',
            '-f', 'docker-compose.frontend.override.yml',
            '-p', config.get_prefix('frontend'),
            'stop', 'nginx',
        ])

        cls.__validate_custom_yml(config, nginx_stop_command)
        CLI.run_command(nginx_stop_command, dict_['kobodocker_path'])

    @classmethod
    def start_maintenance(cls):
        config = Config()
        dict_ = config.get_dict()

        frontend_command = run_docker_compose(dict_, [
            '-f', 'docker-compose.maintenance.yml',
            '-f', 'docker-compose.maintenance.override.yml',
            '-p', config.get_prefix('maintenance'),
            'up', '-d',
        ])

        CLI.run_command(frontend_command, dict_['kobodocker_path'])
        CLI.colored_print('Maintenance mode has been started',
                          CLI.COLOR_SUCCESS)

    @classmethod
    def restart_frontend(cls):
        cls.start(frontend_only=True)

    @classmethod
    def start(cls, frontend_only=False, force_setup=False):
        config = Config()
        dict_ = config.get_dict()

        cls.stop(output=False, frontend_only=frontend_only)
        if frontend_only:
            CLI.colored_print('Launching front-end containers', CLI.COLOR_INFO)
        else:
            CLI.colored_print('Launching environment', CLI.COLOR_INFO)

        # Test if ports are available
        ports = []
        if config.proxy:
            nginx_port = int(dict_['nginx_proxy_port'])
        else:
            nginx_port = int(dict_['exposed_nginx_docker_port'])

        if frontend_only or config.frontend or \
                not config.multi_servers:
            ports.append(nginx_port)

        if (not frontend_only or config.primary_backend or
                config.secondary_backend) and \
                config.expose_backend_ports:
            ports.append(dict_['postgresql_port'])
            ports.append(dict_['mongo_port'])
            ports.append(dict_['redis_main_port'])
            ports.append(dict_['redis_cache_port'])

        for port in ports:
            if Network.is_port_open(port):
                CLI.colored_print(f'Port {port} is already open. '
                                  'KoboToolbox cannot start',
                                  CLI.COLOR_ERROR)
                sys.exit(1)

        # Start the back-end containers
        if not frontend_only and config.backend:

            backend_role = dict_['backend_server_role']

            backend_command = run_docker_compose(dict_, [
                '-f', f'docker-compose.backend.{backend_role}.yml',
                '-f', f'docker-compose.backend.{backend_role}.override.yml',
                '-p', config.get_prefix('backend'),
                'up', '-d'
            ])

            cls.__validate_custom_yml(config, backend_command)
            CLI.run_command(backend_command, dict_['kobodocker_path'])

        # Start the front-end containers
        if config.frontend:

            # If this was previously a shared-database setup, migrate to
            # separate databases for KPI and KoBoCAT
            Upgrading.migrate_single_to_two_databases(config)

            frontend_command = run_docker_compose(dict_, [
                '-f', 'docker-compose.frontend.yml',
                '-f', 'docker-compose.frontend.override.yml',
                '-p', config.get_prefix('frontend'),
                'up', '-d',
            ])

            if dict_['maintenance_enabled']:
                cls.start_maintenance()
                # Start all front-end services except the non-maintenance NGINX
                frontend_command.extend([
                    s for s in config.get_service_names() if s != 'nginx'
                ])

            cls.__validate_custom_yml(config, frontend_command)
            CLI.run_command(frontend_command, dict_['kobodocker_path'])

            # Start reverse proxy if user uses it.
            if config.use_letsencrypt:
                if force_setup:
                    # Let's Encrypt NGINX container needs kobo-docker NGINX
                    # container to be started first
                    config.init_letsencrypt()

                proxy_command = run_docker_compose(dict_, ['up', '-d'])
                CLI.run_command(
                    proxy_command, config.get_letsencrypt_repo_path()
                )

        if dict_['maintenance_enabled']:
            CLI.colored_print(
                'Maintenance mode is enabled. To resume '
                'normal operation, use `--stop-maintenance`',
                CLI.COLOR_INFO,
            )
        elif not frontend_only:
            if not config.multi_servers or config.frontend:
                CLI.colored_print('Waiting for environment to be ready. '
                                  'It can take a few minutes.', CLI.COLOR_INFO)
                cls.info()
            else:
                backend_server_role = dict_['backend_server_role']
                CLI.colored_print(
                    (f'{backend_server_role} backend server is starting up '
                     'and should be up & running soon!\nPlease look at docker '
                     'logs for further information: '
                     '`python3 run.py -cb logs -f`'),
                    CLI.COLOR_WARNING)

    @classmethod
    def stop(cls, output=True, frontend_only=False):
        """
        Stop containers.
        Because containers share the same network, containers must be stopped
        first, then "down-ed" to remove any attached internal networks.
        The order must respected to avoid removing networks with active endpoints.
        """
        config = Config()

        if not config.multi_servers or config.frontend:
            # Stop maintenance container in case it's up&running
            cls.stop_containers('maintenance')

            # Stop reverse proxy if user uses it.
            if config.use_letsencrypt:
                cls.stop_containers('certbot')

            # Stop down front-end containers
            cls.stop_containers('frontend')

            # Clean maintenance services
            cls.stop_containers('maintenance', down=True)

            # Clean certbot services if user uses it.
            if config.use_letsencrypt:
                cls.stop_containers('certbot', down=True)

        if not frontend_only and config.backend:
            cls.stop_containers('backend', down=True)

        # Clean front-end services
        if not config.multi_servers or config.frontend:
            cls.stop_containers('frontend', down=True)

        if output:
            CLI.colored_print('KoboToolbox has been stopped', CLI.COLOR_SUCCESS)

    @classmethod
    def stop_containers(cls, group: str, down: bool = False):

        config = Config()
        dict_ = config.get_dict()
        backend_role = dict_['backend_server_role']

        if group not in ['frontend', 'backend', 'certbot', 'maintenance']:
            raise Exception('Unknown group')

        group_docker_maps = {
            'frontend': {
                'options': [
                    '-f', 'docker-compose.frontend.yml',
                    '-f', 'docker-compose.frontend.override.yml',
                    '-p', config.get_prefix('frontend'),
                ],
                'custom_yml': True,
            },
            'backend': {
                'options': [
                    '-f', f'docker-compose.backend.{backend_role}.yml',
                    '-f', f'docker-compose.backend.{backend_role}.override.yml',
                    '-p', config.get_prefix('backend'),
                ],
                'custom_yml': True,
            },
            'certbot': {
                'options': [],
                'custom_yml': False,
                'path': config.get_letsencrypt_repo_path(),
            },
            'maintenance': {
                'options': [
                    '-f', 'docker-compose.maintenance.yml',
                    '-f', 'docker-compose.maintenance.override.yml',
                    '-p', config.get_prefix('maintenance'),
                ],
                'custom_yml': False,
            }
        }

        path = group_docker_maps[group].get('path', dict_['kobodocker_path'])
        mode = 'stop' if not down else 'down'
        options = group_docker_maps[group]['options']
        command = run_docker_compose(dict_,  options + [mode])
        if group_docker_maps[group]['custom_yml']:
            cls.__validate_custom_yml(config, command)

        CLI.run_command(command, path)

    @classmethod
    def stop_maintenance(cls):
        """
        Stop maintenance mode
        """
        config = Config()
        dict_ = config.get_dict()

        if not config.multi_servers or config.frontend:
            # Stop maintenance container in case it's up&running
            cls.stop_containers('maintenance')

            # Create and start NGINX container
            frontend_command = run_docker_compose(dict_, [
                '-f', 'docker-compose.frontend.yml',
                '-f', 'docker-compose.frontend.override.yml',
                '-p', config.get_prefix('frontend'),
                'up', '-d',
                'nginx',
            ])

            cls.__validate_custom_yml(config, frontend_command)
            CLI.run_command(frontend_command, dict_['kobodocker_path'])

            CLI.colored_print('Maintenance mode has been stopped',
                              CLI.COLOR_SUCCESS)

            dict_['maintenance_enabled'] = False
            config.write_config()

    @classmethod
    def version(cls):
        git_commit_version_command = ['git', 'rev-parse', 'HEAD']
        stdout = CLI.run_command(git_commit_version_command)
        build = stdout.strip()[0:7]
        version = Config.KOBO_INSTALL_VERSION
        CLI.colored_print(
            f'kobo-install Version: {version} (build {build})',
            CLI.COLOR_SUCCESS,
        )

    @staticmethod
    def __validate_custom_yml(config, command):
        """
        Validate whether docker-compose must start the containers with a
        custom YML file in addition to the default. If the file does not yet exist,
        kobo-install is paused until the user creates it and resumes the setup manually.

        If user has chosen to use a custom YML file, it is injected into `command`
        before being executed.
        """
        dict_ = config.get_dict()
        frontend_command = True
        # Detect if it's a front-end command or back-end command
        for part in command:
            if 'backend' in part:
                frontend_command = False
                break

        start_index = 5 if dict_.get('compose_version', 'v1') == 'v1' else 6

        if frontend_command and dict_['use_frontend_custom_yml']:
            custom_file = '{}/docker-compose.frontend.custom.yml'.format(
                dict_['kobodocker_path']
            )

            does_custom_file_exist = os.path.exists(custom_file)
            while not does_custom_file_exist:
                message = (
                    'Please create your custom configuration in\n'
                    '`{custom_file}`.'
                ).format(custom_file=custom_file)
                CLI.framed_print(message, color=CLI.COLOR_INFO, columns=90)
                input('Press any key when it is done...')
                does_custom_file_exist = os.path.exists(custom_file)

            # Add custom file to docker-compose command
            command.insert(start_index, '-f')
            command.insert(start_index + 1, 'docker-compose.frontend.custom.yml')

        if not frontend_command and dict_['use_backend_custom_yml']:
            backend_server_role = dict_['backend_server_role']
            custom_file = '{}/docker-compose.backend.{}.custom.yml'.format(
                dict_['kobodocker_path'],
                backend_server_role
            )

            does_custom_file_exist = os.path.exists(custom_file)
            while not does_custom_file_exist:
                message = (
                    'Please create your custom configuration in\n'
                    '`{custom_file}`.'
                ).format(custom_file=custom_file)
                CLI.framed_print(message, color=CLI.COLOR_INFO, columns=90)
                input('Press any key when it is done...')
                does_custom_file_exist = os.path.exists(custom_file)

            # Add custom file to docker-compose command
            command.insert(start_index, '-f')
            command.insert(
                start_index + 1,
                'docker-compose.backend.{}.custom.yml'.format(backend_server_role),
            )
