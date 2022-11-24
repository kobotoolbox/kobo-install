from __future__ import annotations


def run_docker_compose(config_dict: dict, command: list[str]) -> list[str]:

    # Consider version as v1 if 'compose_version' key is missing. It is
    # probably because user has [git] pulled kobo-install without running `--update`
    compose_version = config_dict.get('compose_version', 'v1')

    if compose_version == 'v1':
        return ['docker-compose'] + command
    else:
        return ['docker', 'compose'] + command
