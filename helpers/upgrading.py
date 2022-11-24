# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from shutil import which

from helpers.cli import CLI
from helpers.utils import run_docker_compose


class Upgrading:

    @staticmethod
    def migrate_single_to_two_databases(config: 'helpers.Config'):
        """
        Check the contents of the databases. If KPI's is empty or doesn't exist
        while KoBoCAT's has user data, then we are migrating from a
        single-database setup

        Args
            config (helpers.config.Config)
        """
        dict_ = config.get_dict()
        backend_role = dict_['backend_server_role']

        def _kpi_db_alias_kludge(command):
            """
            Sorry, this is not very nice. See
            https://github.com/kobotoolbox/kobo-docker/issues/264.
            """
            set_env = 'DATABASE_URL="${KPI_DATABASE_URL}"'
            return ['bash', '-c', f'{set_env} {command}']

        kpi_run_command = run_docker_compose(dict_, [
           '-f', 'docker-compose.frontend.yml',
           '-f', 'docker-compose.frontend.override.yml',
           '-p', config.get_prefix('frontend'),
           'run', '--rm', 'kpi'
        ])

        # Make sure Postgres is running
        # We add this message to users because when AWS backups are activated,
        # it takes a long time to install the virtualenv in PostgreSQL
        # container, so the `wait_for_database` below sits there a while.
        # It makes us think kobo-install is frozen.
        CLI.colored_print(
            'Waiting for PostgreSQL database to be up & running...',
            CLI.COLOR_INFO)
        frontend_command = kpi_run_command + _kpi_db_alias_kludge(' '.join([
                               'python', 'manage.py',
                               'wait_for_database', '--retries', '45'
                           ]))
        CLI.run_command(frontend_command, dict_['kobodocker_path'])
        CLI.colored_print('The PostgreSQL database is running!',
                          CLI.COLOR_SUCCESS)

        frontend_command = kpi_run_command + _kpi_db_alias_kludge(' '.join([
                                'python', 'manage.py',
                                'is_database_empty', 'kpi', 'kobocat'
                           ]))
        output = CLI.run_command(frontend_command, dict_['kobodocker_path'])
        # TODO: read only stdout and don't consider stderr unless the exit code
        # is non-zero. Currently, `output` combines both stdout and stderr
        kpi_kc_db_empty = output.strip().split('\n')[-1]

        if kpi_kc_db_empty == 'True\tFalse':
            # KPI empty but KC is not: run the two-database upgrade script
            CLI.colored_print(
                'Upgrading from single-database setup to separate databases '
                'for KPI and KoBoCAT',
                CLI.COLOR_INFO
            )
            message = (
                'Upgrading to separate databases is required to run the latest '
                'release of KoBoToolbox, but it may be a slow process if you '
                'have a lot of data. Expect at least one minute of downtime '
                'for every 1,500 KPI assets. Assets are surveys and library '
                'items: questions, blocks, and templates.\n'
                '\n'
                'To postpone this process, downgrade to the last '
                'single-database release by stopping this script and executing '
                'the following commands:\n'
                '\n'
                '       python3 run.py --stop\n'
                '       git fetch\n'
                '       git checkout shared-database-obsolete\n'
                '       python3 run.py --update\n'
                '       python3 run.py --setup\n'
            )
            CLI.framed_print(message)
            message = (
                'For help, visit https://community.kobotoolbox.org/t/upgrading-'
                'to-separate-databases-for-kpi-and-kobocat/7202.'
            )
            CLI.colored_print(message, CLI.COLOR_WARNING)
            response = CLI.yes_no_question(
                'Do you want to proceed?',
                default=False
            )
            if response is False:
                sys.exit(0)

            backend_command = run_docker_compose(dict_, [
                '-f', f'docker-compose.backend.{backend_role}.yml',
                '-f', f'docker-compose.backend.{backend_role}.override.yml',
                '-p', config.get_prefix('backend'),
                'exec', 'postgres', 'bash',
                '/kobo-docker-scripts/primary/clone_data_from_kc_to_kpi.sh',
                '--noinput'
            ])
            try:
                subprocess.check_call(
                    backend_command, cwd=dict_['kobodocker_path']
                )
            except subprocess.CalledProcessError:
                CLI.colored_print('An error has occurred', CLI.COLOR_ERROR)
                sys.exit(1)

        elif kpi_kc_db_empty not in [
            'True\tTrue',
            'False\tTrue',
            'False\tFalse',
        ]:
            # The output was invalid
            CLI.colored_print('An error has occurred', CLI.COLOR_ERROR)
            sys.stderr.write(kpi_kc_db_empty)
            sys.exit(1)

    @staticmethod
    def new_terminology(upgraded_dict: dict) -> dict:
        """
        Updates configuration to use new `kobo-docker` terminology.
        See: https://github.com/kobotoolbox/kobo-docker/pull/294

        Args:
            upgraded_dict (dict): Configuration values to be upgraded

        Returns:
            dict
        """

        backend_role = upgraded_dict['backend_server_role']
        if backend_role in ['master', 'slave']:
            upgraded_dict['backend_server_role'] = 'primary' \
                if backend_role == 'master' else 'secondary'

        return upgraded_dict

    @staticmethod
    def set_compose_version(upgraded_dict: dict) -> dict:

        if 'compose_version' not in upgraded_dict:
            # FIXME On macOS, Docker Desktop always installs a symlink for
            #   `docker-compose`. Version will be always detected as v1 even if
            #   user has chosen v2 in Docker Desktop preferences.
            compose_version = 'v2' if which('docker-compose') is None else 'v1'
            upgraded_dict['compose_version'] = compose_version

        return upgraded_dict

    @staticmethod
    def two_databases(upgraded_dict: dict, current_dict: dict) -> dict:
        """
        If the configuration came from a previous version that had a single
        Postgres database, we need to make sure the new `kc_postgres_db` is
        set to the name of that single database, *not* the default from
        `Config.get_template()`

        Args:
            upgraded_dict (dict): Configuration values to be upgraded
            current_dict (dict): Current configuration values
                                 (i.e. `Config.get_dict()`)
        Returns:
            dict

        """

        try:
            current_dict['postgres_db']
        except KeyError:
            # Install has been made with two databases.
            return upgraded_dict

        try:
            current_dict['kc_postgres_db']
        except KeyError:
            # Configuration does not have names of KPI and KoBoCAT databases.
            # Let's copy old single database name to KoBoCAT database name
            upgraded_dict['kc_postgres_db'] = current_dict['postgres_db']

            # Force this property to False. It helps to detect whether the
            # database names have changed in `Config.__questions_postgres()`
            upgraded_dict['two_databases'] = False

        return upgraded_dict

    @staticmethod
    def use_booleans(upgraded_dict: dict) -> dict:
        """
        Until version 3.x, two constants (`Config.TRUE` and `Config.FALSE`) were
        used to store "Yes/No"  users' responses. It made the code more
        complex than it should have been.
        This method converts these values to boolean.
            - `Config.TRUE` -> `True`
            - `Config.FALSE` -> False`
        Args:
            upgraded_dict (dict): Configuration values to be upgraded

        Returns:
              dict
        """
        try:
            upgraded_dict['use_booleans_v4']
        except KeyError:
            pass
        else:
            return upgraded_dict

        boolean_properties = [
            'advanced',
            'aws_backup_bucket_deletion_rule_enabled',
            'backup_from_primary',
            'block_common_http_ports',
            'custom_secret_keys',
            'customized_ports',
            'debug',
            'dev_mode',
            'expose_backend_ports',
            'https',
            'local_installation',
            'multi',
            'npm_container',
            'postgres_settings',
            'proxy',
            'raven_settings',
            'review_host',
            'smtp_use_tls',
            'staging_mode',
            'two_databases',
            'use_aws',
            'use_backup',
            'use_letsencrypt',
            'use_private_dns',
            'use_wal_e',
            'uwsgi_settings',
        ]
        for property_ in boolean_properties:
            try:
                if isinstance(upgraded_dict[property_], bool):
                    continue
            except KeyError:
                pass
            else:
                upgraded_dict[property_] = True \
                    if upgraded_dict[property_] == '1' else False

        upgraded_dict['use_booleans_v4'] = True

        return upgraded_dict
