# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest
import shutil
import tempfile

try:
    from unittest.mock import patch, mock_open
    builtin_open = "builtins.open"
except ImportError:
    from mock import patch, mock_open
    builtin_open = "__builtin__.open"

from helpers.cli import CLI
from helpers.config import Config


def test_read_config():

    config_dict = {"kobodocker_path": "/tmp"}
    with patch(builtin_open, mock_open(read_data=json.dumps(config_dict))) as mock_file:
        config_object = Config()
        config_object.read_config()
        assert config_object.get_config().get("kobodocker_path") == config_dict.get("kobodocker_path")
    return config_object


def test_advanced_options():
    config_object = test_read_config()
    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_advanced_options()
        assert config_object.advanced_options

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_advanced_options()
        assert not config_object.advanced_options


def test_installation():
    config_object = test_read_config()
    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_installation_type()
        assert not config_object.local_install

    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_installation_type()
        assert config_object.local_install
        assert not config_object.multi_servers

    return config_object


def test_dev_mode():
    config_object = test_read_config()
    kc_repo_path = tempfile.mkdtemp()
    kpi_repo_path = tempfile.mkdtemp()

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:
        mock_colored_input.side_effect = iter([Config.TRUE, kc_repo_path, kpi_repo_path])
        config_object._Config__questions_dev_mode()
        config = config_object.get_config()
        assert not config_object.dev_mode
        assert config_object.staging_mode
        assert config.get("kpi_path") == kpi_repo_path and config.get("kc_path") == kc_repo_path

    shutil.rmtree(kc_repo_path)
    shutil.rmtree(kpi_repo_path)

    config_object = test_installation()

    kc_repo_path = tempfile.mkdtemp()
    kpi_repo_path = tempfile.mkdtemp()

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:

        mock_colored_input.side_effect = iter(["8080", Config.TRUE, kc_repo_path, kpi_repo_path, Config.FALSE])
        config_object._Config__questions_dev_mode()
        config = config_object.get_config()
        assert config_object.dev_mode
        assert not config_object.staging_mode
        assert config_object.get_config().get("exposed_nginx_docker_port") == "8080"
        assert config.get("kpi_path") == kpi_repo_path and config.get("kc_path") == kc_repo_path

    shutil.rmtree(kc_repo_path)
    shutil.rmtree(kpi_repo_path)

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_dev_mode()
        config = config_object.get_config()
        assert not config_object.dev_mode
        assert config.get("kpi_path") == "" and config.get("kc_path") == ""


def test_server_roles_questions():
    config_object = test_read_config()
    assert config_object.frontend_questions
    assert config_object.backend_questions

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:

        mock_colored_input.side_effect = iter([Config.TRUE, "frontend", "backend", "slave"])

        config_object._Config__questions_multi_servers()

        config_object._Config__questions_roles()
        assert config_object.frontend_questions
        assert not config_object.backend_questions

        config_object._Config__questions_roles()
        assert not config_object.frontend_questions
        assert config_object.backend_questions
        assert config_object.slave_backend
