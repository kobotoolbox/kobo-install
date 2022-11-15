from __future__ import annotations


def run_docker_compose(config_dict: dict, command: list[str]) -> list[str]:

    try:
        compose_version = config_dict['compose_version']
    except KeyError:
        # Consider version as v1. If 'compose_version' key is missing, it is
        # probably because user has pulled kobo-install without running `--update`
        compose_version = 'v1'

    if compose_version == 'v1':
        return ['docker-compose'] + command
    else:
        return ['docker', 'compose'] + command
