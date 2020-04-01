# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import subprocess
import sys

from helpers.cli import CLI
from helpers.config import Config


def migrate_single_to_two_databases():
    """
    Check the contents of the databases. If KPI's is empty or doesn't exist
    while KoBoCAT's has user data, then we are migrating from a
    single-database setup
    """
    config_object = Config()
    config = config_object.get_config()
    backend_role = config.get("backend_server_role", "master")

    def _kpi_db_alias_kludge(command):
        """
        Sorry, this is not very nice. See
        https://github.com/kobotoolbox/kobo-docker/issues/264.
        """
        set_env = 'DATABASE_URL="${KPI_DATABASE_URL}"'
        return [
            "bash", "-c",
            "{} {}".format(set_env, command)
        ]

    kpi_run_command = ["docker-compose",
                       "-f", "docker-compose.frontend.yml",
                       "-f", "docker-compose.frontend.override.yml",
                       "-p", config_object.get_prefix("frontend"),
                       "run", "--rm", "kpi"]

    # Make sure Postgres is running
    # We add this message to users because when AWS backups are activated,
    # it takes a long time to install the virtualenv in PostgreSQL container,
    # so the `wait_for_database` below sits there a while.
    # It makes us think KoBoInstall is frozen.
    CLI.colored_print("Waiting for PostgreSQL database to be up & running...",
                      CLI.COLOR_INFO)
    frontend_command = kpi_run_command + _kpi_db_alias_kludge(" ".join([
                           "python", "manage.py",
                           "wait_for_database", "--retries", "45"
                       ]))
    CLI.run_command(frontend_command, config.get("kobodocker_path"))
    CLI.colored_print("The PostgreSQL database is running!", CLI.COLOR_SUCCESS)

    frontend_command = kpi_run_command + _kpi_db_alias_kludge(" ".join([
                            "python", "manage.py",
                            "is_database_empty", "kpi", "kobocat"
                       ]))
    output = CLI.run_command(frontend_command, config.get("kobodocker_path"))
    # TODO: read only stdout and don't consider stderr unless the exit code
    # is non-zero. Currently, `output` combines both stdout and stderr
    kpi_kc_db_empty = output.strip().split("\n")[-1]

    if kpi_kc_db_empty == "True\tFalse":
        # KPI empty but KC is not: run the two-database upgrade script
        CLI.colored_print(
            "Upgrading from single-database setup to separate databases "
            "for KPI and KoBoCAT",
            CLI.COLOR_INFO
        )
        _message_lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║  Upgrading to separate databases is required to run the      ║",
            "║  latest release of KoBoToolbox, but it may be a slow process ║",
            "║  if you have a lot of data. Expect at least one minute of    ║",
            "║  downtime for every 1,500 KPI assets. Assets are surveys and ║",
            "║  library items: questions, blocks, and templates.            ║",
            "║  Survey *submissions* are not involved.                      ║",
            "║                                                              ║",
            "║  To postpone this process, downgrade to the last             ║",
            "║  single-database release by stopping this script and         ║",
            "║  executing the following command:                            ║",
            "║                                                              ║",
            "║       git checkout 2.019.52-final-shared-database            ║",
            "║                                                              ║",
            "║  Then, re-run this script.                                   ║",
            "╚══════════════════════════════════════════════════════════════╝",
        ]
        CLI.colored_print('\n'.join(_message_lines), CLI.COLOR_WARNING)
        CLI.colored_print("Do you want to proceed?", CLI.COLOR_SUCCESS)
        CLI.colored_print("\t1) Yes")
        CLI.colored_print("\t2) No")
        response = CLI.get_response([Config.TRUE, Config.FALSE], Config.FALSE)
        if response != Config.TRUE:
            sys.exit(0)

        backend_command = [
            "docker-compose",
            "-f",
            "docker-compose.backend.{}.yml".format(backend_role),
            "-f",
            "docker-compose.backend.{}.override.yml".format(backend_role),
            "-p", config_object.get_prefix("backend"),
            "exec", "postgres", "bash",
            "/kobo-docker-scripts/master/clone_data_from_kc_to_kpi.sh",
            "--noinput"
        ]
        try:
            subprocess.check_call(
                backend_command, cwd=config.get("kobodocker_path")
            )
        except subprocess.CalledProcessError:
            CLI.colored_print("An error has occurred", CLI.COLOR_ERROR)
            sys.exit(1)

    elif kpi_kc_db_empty not in [
        "True\tTrue",
        "False\tTrue",
        "False\tFalse",
    ]:
        # The output was invalid
        CLI.colored_print("An error has occurred", CLI.COLOR_ERROR)
        sys.stderr.write(kpi_kc_db_empty)
        sys.exit(1)
