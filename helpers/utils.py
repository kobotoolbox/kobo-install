from __future__ import annotations


def run_docker_compose(config_dict: dict, command: list[str]) -> list[str]:

    return ['docker', 'compose'] + command
