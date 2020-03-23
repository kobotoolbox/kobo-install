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
    frontend_command = kpi_run_command + _kpi_db_alias_kludge(" ".join([
                           "python", "manage.py",
                           "wait_for_database", "--retries", "30"
                       ]))
    CLI.run_command(frontend_command, config.get("kobodocker_path"))
    CLI.colored_print("The Postgres database is running!", CLI.COLOR_SUCCESS)

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

        # The Whoosh search index created under Python 2 doesn't seem to work
        # with Python 3, so rebuild it now that we've upgraded
        CLI.colored_print(
            "Rebuilding Whoosh search index for Python 3 compatibility",
            CLI.COLOR_INFO
        )
        frontend_command = kpi_run_command + _kpi_db_alias_kludge(" ".join([
                               "python", "manage.py",
                               "rebuild_index", "--noinput"
                           ]))
        CLI.run_command(frontend_command, config.get("kobodocker_path"))

    elif kpi_kc_db_empty not in [
        "True\tTrue",
        "False\tTrue",
        "False\tFalse",
    ]:
        # The output was invalid
        CLI.colored_print("An error has occurred", CLI.COLOR_ERROR)
        sys.stderr.write(kpi_kc_db_empty)
        sys.exit(1)
