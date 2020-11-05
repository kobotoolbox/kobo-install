# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
try:
    from unittest.mock import patch, mock_open
    builtin_open = 'builtins.open'
except ImportError:
    from mock import patch, mock_open
    builtin_open = '__builtin__.open'

from helpers.config import Config
from helpers.singleton import Singleton, with_metaclass


def read_config(overrides=None):

    config_dict = dict(Config.get_template())
    config_dict['kobodocker_path'] = '/tmp'
    if overrides is not None:
        config_dict.update(overrides)

    str_config = json.dumps(config_dict)
    with patch(builtin_open, mock_open(read_data=str_config)) as mock_file:
        config = Config()
        config.read_config()
        dict_ = config.get_dict()
        assert config_dict['kobodocker_path'] == dict_['kobodocker_path']

    return config


def reset_config(config):

    dict_ = dict(Config.get_template())
    dict_['kobodocker_path'] = '/tmp'
    config.__dict = dict_


def write_trigger_upsert_db_users(*args):
    content = args[1]
    with open('/tmp/upsert_db_users', 'w') as f:
        f.write(content)


class MockCommand:
    """
    Create a mock class for Python2 retro compatibility.
    Python2 does not pass the class as the first argument explicitly when
    `run_command` (as a standalone method) is used as a mock.
    """
    @classmethod
    def run_command(cls, command, cwd=None, polling=False):
        if 'docker-compose' != command[0]:
            message = 'Command: `{}` is not implemented!'.format(command[0])
            raise Exception(message)

        mock_docker = MockDocker()
        return mock_docker.compose(command, cwd)


class MockDocker(with_metaclass(Singleton)):

    PRIMARY_BACKEND_CONTAINERS = ['primary_postgres',
                                  'mongo',
                                  'redis_main',
                                  'redis_cache']
    SECONDARY_BACKEND_CONTAINERS = ['secondary_postgres']
    FRONTEND_CONTAINERS = ['nginx', 'kobocat', 'kpi', 'enketo_express']
    MAINTENANCE_CONTAINERS = ['maintenance', 'kobocat', 'kpi', 'enketo_express']
    LETSENCRYPT = ['letsencrypt_nginx', 'certbot']

    def __init__(self):
        self.__containers = []

    def ps(self):
        return self.__containers

    def compose(self, command, cwd):
        config_object = Config()
        letsencrypt = cwd == config_object.get_letsencrypt_repo_path()

        if command[-2] == 'config':
            return '\n'.join([c
                              for c in self.FRONTEND_CONTAINERS
                              if c != 'nginx'])
        if command[-2] == 'up':
            if letsencrypt:
                self.__containers += self.LETSENCRYPT
            elif 'primary' in command[2]:
                self.__containers += self.PRIMARY_BACKEND_CONTAINERS
            elif 'secondary' in command[2]:
                self.__containers += self.SECONDARY_BACKEND_CONTAINERS
            elif 'maintenance' in command[2]:
                self.__containers += self.MAINTENANCE_CONTAINERS
            elif 'frontend' in command[2]:
                self.__containers += self.FRONTEND_CONTAINERS
        elif command[-1] == 'down':
            try:
                if letsencrypt:
                    for container in self.LETSENCRYPT:
                        self.__containers.remove(container)
                elif 'primary' in command[2]:
                    for container in self.PRIMARY_BACKEND_CONTAINERS:
                        self.__containers.remove(container)
                elif 'secondary' in command[2]:
                    for container in self.SECONDARY_BACKEND_CONTAINERS:
                        self.__containers.remove(container)
                elif 'maintenance' in command[2]:
                    for container in self.MAINTENANCE_CONTAINERS:
                        self.__containers.remove(container)
                elif 'frontend' in command[2]:
                    for container in self.FRONTEND_CONTAINERS:
                        self.__containers.remove(container)
            except ValueError:
                # Try to take a container down but was not up before.
                pass

        return True


class MockUpgrading:

    @staticmethod
    def migrate_single_to_two_databases(config):
        pass
