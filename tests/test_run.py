# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest.mock import patch, MagicMock
    builtin_open = 'builtins.open'
except ImportError:
    from mock import patch, MagicMock
    builtin_open = '__builtin__.open'

from helpers.command import Command
from helpers.config import Config
from .utils import (
    read_config,
    MockCommand,
    MockDocker,
)


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_trivial():
    config_object = read_config()
    Command.start()
    mock_docker = MockDocker()
    expected_containers = MockDocker.FRONTEND_CONTAINERS + \
        MockDocker.PRIMARY_BACKEND_CONTAINERS + \
        MockDocker.LETSENCRYPT
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_no_letsencrypt():
    config_object = read_config()
    config_object._Config__config['use_letsencrypt'] = False
    Command.start()
    mock_docker = MockDocker()
    expected_containers = MockDocker.FRONTEND_CONTAINERS + \
        MockDocker.PRIMARY_BACKEND_CONTAINERS
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_frontend():
    config_object = read_config()
    Command.start(frontend_only=True)
    mock_docker = MockDocker()
    expected_containers = MockDocker.FRONTEND_CONTAINERS + \
        MockDocker.LETSENCRYPT
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_primary_backend():
    config_object = read_config()
    config_object._Config__config['backend_server_role'] = 'primary'
    config_object._Config__config['server_role'] = 'backend'
    config_object._Config__config['multi'] = Config.TRUE

    Command.start()
    mock_docker = MockDocker()
    expected_containers = MockDocker.PRIMARY_BACKEND_CONTAINERS
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_secondary_backend():
    config_object = read_config()
    config_object._Config__config['backend_server_role'] = 'secondary'
    config_object._Config__config['server_role'] = 'backend'
    config_object._Config__config['multi'] = Config.TRUE

    mock_docker = MockDocker()
    Command.start()
    expected_containers = MockDocker.SECONDARY_BACKEND_CONTAINERS
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker


@patch('helpers.network.Network.is_port_open',
       MagicMock(return_value=False))
@patch('helpers.command.migrate_single_to_two_databases',
       MagicMock(return_value=None))
@patch('helpers.command.Command.info',
       MagicMock(return_value=True))
@patch('helpers.cli.CLI.run_command',
       new=MockCommand.run_command)
def test_toggle_maintenance():
    config_object = read_config()
    mock_docker = MockDocker()
    Command.start()
    expected_containers = MockDocker.FRONTEND_CONTAINERS + \
                          MockDocker.PRIMARY_BACKEND_CONTAINERS + \
                          MockDocker.LETSENCRYPT
    assert sorted(mock_docker.ps()) == sorted(expected_containers)

    config_object._Config__config['maintenance_enabled'] = True
    Command.start()
    maintenance_containers = MockDocker.PRIMARY_BACKEND_CONTAINERS + \
                             MockDocker.MAINTENANCE_CONTAINERS + \
                             MockDocker.LETSENCRYPT
    assert sorted(mock_docker.ps()) == sorted(maintenance_containers)
    config_object._Config__config['maintenance_enabled'] = False
    Command.start()
    assert sorted(mock_docker.ps()) == sorted(expected_containers)
    Command.stop()
    assert len(mock_docker.ps()) == 0
    del mock_docker

