# -*- coding: utf-8 -*-

import sys
import time
import subprocess

from helpers.cli import CLI
from helpers.config import Config
from helpers.network import Network
from helpers.template import Template
from helpers.upgrading import Upgrading


class Command:

    @staticmethod
    def help():
        output = [
            'Usage: python run.py [options]',
            '',
            '    Options:',
            '          -i, --info',
            '                Show KoBoToolbox Url and super user credentials',
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
            '                Stop KoBoToolbox',
            '          -u, --update, --upgrade [branch or tag]',
            '                Update KoBoToolbox',
            '          -cf, --compose-frontend [docker-compose arguments]',
            '                Run a docker-compose command in the front-end '
            'environment',
            '          -cb, --compose-backend [docker-compose arguments]',
            '                Run a docker-compose command in the back-end '
            'environment',
            '          -m, --maintenance',
            '                Activate maintenance mode. All traffic is '
            'redirected to maintenance page',
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
                frontend_command = [
                    'docker-compose',
                    '-f',
                    'docker-compose.frontend.yml',
                    '-f',
                    'docker-compose.frontend.override.yml',
                    '-p', config.get_prefix('frontend'),
                    'build', '--force-rm', '--no-cache',
                    image_
                ]

                CLI.run_command(frontend_command, dict_['kobodocker_path'])

            if image is None or image == 'kf':
                dict_['kpi_dev_build_id'] = '{prefix}{timestamp}'.format(
                    prefix=config.get_prefix('frontend'),
                    timestamp=str(int(time.time()))
                )
                config.write_config()
                Template.render(config)
                build_image('kpi')

            if image is None or image == 'kc':
                pull_base_command = ['docker',
                                     'pull',
                                     'kobotoolbox/koboform_base']

                CLI.run_command(pull_base_command, dict_['kobodocker_path'])

                dict_['kc_dev_build_id'] = '{prefix}{timestamp}'.format(
                    prefix=config.get_prefix('frontend'),
                    timestamp=str(int(time.time()))
                )
                config.write_config()
                Template.render(config)
                build_image('kobocat')

    @classmethod
    def compose_frontend(cls, args):
        config = Config()
        dict_ = config.get_dict()
        command = ['docker-compose',
                   '-f', 'docker-compose.frontend.yml',
                   '-f', 'docker-compose.frontend.override.yml',
                   '-p', config.get_prefix('frontend')]
        command.extend(args)
        subprocess.call(command, cwd=dict_['kobodocker_path'])

    @classmethod
    def compose_backend(cls, args):
        config = Config()
        dict_ = config.get_dict()
        backend_role = dict_['backend_server_role']
        command = [
            'docker-compose',
            '-f', 'docker-compose.backend.{}.yml'.format(backend_role),
            '-f', 'docker-compose.backend.{}.override.yml'.format(backend_role),
            '-p', config.get_prefix('backend')
        ]
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
        hostname = '{}.{}'.format(dict_['kpi_subdomain'],
                                  dict_['public_domain_name'])
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
                    question = 'Wait for another {} seconds?'.format(timeout)
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
                                'Restarting the frontend containers usually '
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
                'URL: {url}\n'
                'User: {username}\n'
                'Password: {password}'
            ).format(
                url=main_url,
                username=username,
                password=password)
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

            backend_command = ['docker-compose',
                               '-f',
                               'docker-compose.backend.{}.yml'.format(
                                   backend_role),
                               '-f',
                               'docker-compose.backend.{}.override.yml'.format(
                                   backend_role),
                               '-p',
                               config.get_prefix('backend'),
                               'logs',
                               '-f'
                               ]
            CLI.run_command(backend_command,
                            dict_['kobodocker_path'],
                            True)

        if config.frontend:
            frontend_command = ['docker-compose',
                                '-f', 'docker-compose.frontend.yml',
                                '-f', 'docker-compose.frontend.override.yml',
                                '-p', config.get_prefix('frontend'),
                                'logs', '-f']
            CLI.run_command(frontend_command,
                            dict_['kobodocker_path'],
                            True)

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

        nginx_stop_command = ['docker-compose',
                              '-f', 'docker-compose.frontend.yml',
                              '-f', 'docker-compose.frontend.override.yml',
                              '-p', config.get_prefix('frontend'),
                              'stop', 'nginx']

        CLI.run_command(nginx_stop_command, dict_['kobodocker_path'])

    @classmethod
    def start_maintenance(cls):
        config = Config()
        dict_ = config.get_dict()

        frontend_command = ['docker-compose',
                            '-f', 'docker-compose.maintenance.yml',
                            '-f', 'docker-compose.maintenance.override.yml',
                            '-p', config.get_prefix('maintenance'),
                            'up', '-d']

        CLI.run_command(frontend_command, dict_['kobodocker_path'])
        CLI.colored_print('Maintenance mode has been started',
                          CLI.COLOR_SUCCESS)

    @classmethod
    def restart_frontend(cls):
        cls.start(frontend_only=True)

    @classmethod
    def start(cls, frontend_only=False):
        config = Config()
        dict_ = config.get_dict()

        cls.stop(output=False, frontend_only=frontend_only)
        if frontend_only:
            CLI.colored_print('Launching frontend containers', CLI.COLOR_INFO)
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
                CLI.colored_print('Port {} is already open. '
                                  'KoboToolbox cannot start'.format(port),
                                  CLI.COLOR_ERROR)
                sys.exit(1)

        # Start the back-end containers
        if not frontend_only and config.backend:

            backend_role = dict_['backend_server_role']

            backend_command = [
                'docker-compose',
                '-f',
                'docker-compose.backend.{}.yml'.format(backend_role),
                '-f',
                'docker-compose.backend.{}.override.yml'.format(backend_role),
                '-p',
                config.get_prefix('backend'),
                'up',
                '-d'
            ]
            CLI.run_command(backend_command, dict_['kobodocker_path'])

        # Start the front-end containers
        if config.frontend:

            # If this was previously a shared-database setup, migrate to
            # separate databases for KPI and KoBoCAT
            Upgrading.migrate_single_to_two_databases(config)

            frontend_command = ['docker-compose',
                                '-f', 'docker-compose.frontend.yml',
                                '-f', 'docker-compose.frontend.override.yml',
                                '-p', config.get_prefix('frontend'),
                                'up', '-d']

            if dict_['maintenance_enabled']:
                cls.start_maintenance()
                # Start all front-end services except the non-maintenance NGINX
                frontend_command.extend([
                    s for s in config.get_service_names() if s != 'nginx'
                ])

            CLI.run_command(frontend_command, dict_['kobodocker_path'])

            # Start reverse proxy if user uses it.
            if config.use_letsencrypt:
                proxy_command = ['docker-compose',
                                 'up', '-d']
                CLI.run_command(proxy_command,
                                config.get_letsencrypt_repo_path())

        if dict_['maintenance_enabled']:
                CLI.colored_print('Maintenance mode is enabled. To resume '
                                  'normal operation, use `--stop-maintenance`',
                                  CLI.COLOR_INFO)
        elif not frontend_only:
            if not config.multi_servers or config.frontend:
                CLI.colored_print('Waiting for environment to be ready. '
                                  'It can take a few minutes.', CLI.COLOR_INFO)
                cls.info()
            else:
                CLI.colored_print(
                    ('{} backend server is starting up and should be '
                     'up & running soon!\nPlease look at docker logs for '
                     'further information: `python3 run.py -cb logs -f`'.format(
                        dict_['backend_server_role'])),
                    CLI.COLOR_WARNING)

    @classmethod
    def stop(cls, output=True, frontend_only=False):
        """
        Stop containers
        """
        config = Config()
        dict_ = config.get_dict()

        if not config.multi_servers or config.frontend:
            # Shut down maintenance container in case it's up&running
            maintenance_down_command = [
                'docker-compose',
                '-f', 'docker-compose.maintenance.yml',
                '-f', 'docker-compose.maintenance.override.yml',
                '-p', config.get_prefix('maintenance'),
                'down']

            CLI.run_command(maintenance_down_command,
                            dict_['kobodocker_path'])

            # Shut down frontend containers
            frontend_command = ['docker-compose',
                                '-f', 'docker-compose.frontend.yml',
                                '-f', 'docker-compose.frontend.override.yml',
                                '-p', config.get_prefix('frontend'),
                                'down']
            CLI.run_command(frontend_command, dict_['kobodocker_path'])

            # Stop reverse proxy if user uses it.
            if config.use_letsencrypt:
                proxy_command = ['docker-compose',
                                 'down']
                CLI.run_command(proxy_command,
                                config.get_letsencrypt_repo_path())

        if not frontend_only and config.backend:
            backend_role = dict_['backend_server_role']

            backend_command = [
                'docker-compose',
                '-f',
                'docker-compose.backend.{}.yml'.format(backend_role),
                '-f',
                'docker-compose.backend.{}.override.yml'.format(backend_role),
                '-p', config.get_prefix('backend'),
                'down'
            ]
            CLI.run_command(backend_command, dict_['kobodocker_path'])

        if output:
            CLI.colored_print('KoBoToolbox has been stopped', CLI.COLOR_SUCCESS)

    @classmethod
    def stop_maintenance(cls):
        """
        Stop maintenance mode
        """
        config = Config()
        dict_ = config.get_dict()

        if not config.multi_servers or config.frontend:
            # Shut down maintenance container in case it's up&running
            maintenance_down_command = [
                'docker-compose',
                '-f', 'docker-compose.maintenance.yml',
                '-f', 'docker-compose.maintenance.override.yml',
                '-p', config.get_prefix('maintenance'),
                'down']

            CLI.run_command(maintenance_down_command,
                            dict_['kobodocker_path'])

            # Create and start NGINX container
            frontend_command = ['docker-compose',
                                '-f', 'docker-compose.frontend.yml',
                                '-f', 'docker-compose.frontend.override.yml',
                                '-p', config.get_prefix('frontend'),
                                'up', '-d', 'nginx']
            CLI.run_command(frontend_command, dict_['kobodocker_path'])

            CLI.colored_print('Maintenance mode has been stopped',
                              CLI.COLOR_SUCCESS)

            dict_['maintenance_enabled'] = False
            config.write_config()

    @classmethod
    def version(cls):
        git_commit_version_command = ['git', 'rev-parse', 'HEAD']
        stdout = CLI.run_command(git_commit_version_command)

        CLI.colored_print('kobo-install Version: {} (build {})'.format(
            Config.KOBO_INSTALL_VERSION,
            stdout.strip()[0:7],
        ), CLI.COLOR_SUCCESS)
