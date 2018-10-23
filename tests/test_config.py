# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from helpers.cli import CLI
from helpers.config import Config


def test_read_config():

    config_dict = {"kobodocker_path": "/tmp"}
    with patch.object(Config, "read_config", return_value=config_dict) as mock_conf:
        config_object = Config()
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

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_dev_mode()
        default_nginx_port = config_object.get_config().get("exposed_nginx_docker_port")
        assert not config_object.dev_mode

    config_object = test_installation()
    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_dev_mode()
        assert config_object.dev_mode
        assert default_nginx_port != config_object.get_config().get("exposed_nginx_docker_port")

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_dev_mode()
        config = config_object.get_config()
        assert not config_object.dev_mode
        assert config.get("kpi_path") == "" and config.get("kc_path") == ""


def test_server_roles_questions():
    config_object = test_read_config()
    assert config_object.frontend_questions
    assert config_object.backend_questions

    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_multi_servers()

        with patch.object(CLI, "colored_input", return_value="frontend") as mock_ci:
            config_object._Config__questions_roles()
            assert config_object.frontend_questions
            assert not config_object.backend_questions

        with patch.object(CLI, "colored_input", return_value="backend") as mock_ci:
            config_object._Config__questions_roles()
            assert not config_object.frontend_questions
            assert config_object.backend_questions
