# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest
import random
import shutil
import string
import tempfile
import time


try:
    from unittest.mock import patch, mock_open, MagicMock
    builtin_open = "builtins.open"
except ImportError:
    from mock import patch, mock_open, MagicMock
    builtin_open = "__builtin__.open"

from helpers.cli import CLI
from helpers.config import Config


def reset_config(config_object):

    config_dict = dict(Config.get_config_template())
    config_dict["kobodocker_path"] = "/tmp"
    config_object.__config = config_dict


def test_read_config(overrides=None):

    config_dict = dict(Config.get_config_template())
    config_dict["kobodocker_path"] = "/tmp"
    if overrides is not None:
        config_dict.update(overrides)
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
        assert not config_object.use_letsencrypt

    return config_object


@patch("helpers.config.Config._Config__clone_repo", MagicMock(return_value=True))
def test_staging_mode():
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


@patch("helpers.config.Config._Config__clone_repo", MagicMock(return_value=True))
def test_dev_mode():
    config_object = test_installation()

    kc_repo_path = tempfile.mkdtemp()
    kpi_repo_path = tempfile.mkdtemp()

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:

        mock_colored_input.side_effect = iter(["8080", Config.TRUE, kc_repo_path, kpi_repo_path,
                                               Config.FALSE, Config.FALSE])

        config_object._Config__questions_dev_mode()
        config = config_object.get_config()
        assert config_object.dev_mode
        assert not config_object.staging_mode
        assert config_object.get_config().get("exposed_nginx_docker_port") == "8080"
        assert config.get("kpi_path") == kpi_repo_path and config.get("kc_path") == kc_repo_path
        assert config.get("npm_container") == Config.FALSE

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


def test_use_https():
    config_object = test_read_config()

    assert config_object.is_secure

    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_https()
        assert not config_object.local_install
        assert config_object.is_secure

    with patch.object(CLI, "colored_input", return_value=Config.TRUE) as mock_ci:
        config_object._Config__questions_installation_type()
        assert config_object.local_install
        assert not config_object.is_secure


@patch("helpers.config.Config._Config__clone_repo", MagicMock(return_value=True))
def test_proxy_letsencrypt():
    config_object = test_read_config()

    assert config_object.proxy
    assert config_object.use_letsencrypt

    # Force custom exposed port
    config_object._Config__config["exposed_nginx_docker_port"] = "8088"

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:
        mock_colored_input.side_effect = iter([Config.TRUE,
                                               "test@test.com",
                                               Config.TRUE,
                                               Config.DEFAULT_NGINX_PORT])  # Use default options
        config_object._Config__question_reverse_proxy()
        assert config_object.proxy
        assert config_object.use_letsencrypt
        assert config_object.block_common_http_ports
        assert config_object.get_config().get("nginx_proxy_port") == Config.DEFAULT_PROXY_PORT
        assert config_object.get_config().get("exposed_nginx_docker_port") == Config.DEFAULT_NGINX_PORT


def test_proxy_no_letsencrypt_advanced():
        config_object = test_read_config()
        # Force advanced options
        config_object._Config__config["advanced"] = Config.TRUE
        assert config_object.advanced_options
        assert config_object.proxy
        assert config_object.use_letsencrypt
        proxy_port = Config.DEFAULT_NGINX_PORT

        with patch("helpers.cli.CLI.colored_input") as mock_colored_input:
            mock_colored_input.side_effect = iter([Config.FALSE, Config.FALSE, proxy_port])
            config_object._Config__question_reverse_proxy()
            assert config_object.proxy
            assert not config_object.use_letsencrypt
            assert not config_object.block_common_http_ports
            assert config_object.get_config().get("nginx_proxy_port") == proxy_port


def test_proxy_no_letsencrypt():
    config_object = test_read_config()

    assert config_object.proxy
    assert config_object.use_letsencrypt

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__question_reverse_proxy()
        assert config_object.proxy
        assert not config_object.use_letsencrypt
        assert config_object.block_common_http_ports
        assert config_object.get_config().get("nginx_proxy_port") == Config.DEFAULT_PROXY_PORT


def test_proxy_no_letsencrypt_retains_custom_nginx_proxy_port():
    CUSTOM_PROXY_PORT = 9090
    config_object = test_read_config(overrides={
        'advanced': Config.TRUE,
        'use_letsencrypt': Config.FALSE,
        'nginx_proxy_port': str(CUSTOM_PROXY_PORT),
    })
    with patch.object(
            CLI, "colored_input",
            new=classmethod(lambda cls, message, color, default: default)
    ) as mock_ci:
        config_object._Config__question_reverse_proxy()
        assert(config_object.get_config().get("nginx_proxy_port")
               == str(CUSTOM_PROXY_PORT))


def test_no_proxy_no_ssl():
    config_object = test_read_config()
    assert config_object.is_secure
    assert config_object.get_config().get("nginx_proxy_port") == Config.DEFAULT_PROXY_PORT

    proxy_port = Config.DEFAULT_NGINX_PORT

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_https()
        assert not config_object.is_secure

        with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci_2:
            config_object._Config__question_reverse_proxy()
            assert not config_object.proxy
            assert not config_object.use_letsencrypt
            assert not config_object.block_common_http_ports
            assert config_object.get_config().get("nginx_proxy_port") == proxy_port


def test_proxy_no_ssl_advanced():
    config_object = test_read_config()
    # Force advanced options
    config_object._Config__config["advanced"] = Config.TRUE
    assert config_object.advanced_options
    assert config_object.is_secure

    with patch.object(CLI, "colored_input", return_value=Config.FALSE) as mock_ci:
        config_object._Config__questions_https()
        assert not config_object.is_secure

        # Proxy - not on the same server
        proxy_port = Config.DEFAULT_NGINX_PORT
        with patch("helpers.cli.CLI.colored_input") as mock_colored_input_1:
            mock_colored_input_1.side_effect = iter([Config.TRUE, Config.FALSE, proxy_port])
            config_object._Config__question_reverse_proxy()
            assert config_object.proxy
            assert not config_object.use_letsencrypt
            assert not config_object.block_common_http_ports
            assert config_object.get_config().get("nginx_proxy_port") == proxy_port

        # Proxy - on the same server
        proxy_port = Config.DEFAULT_PROXY_PORT
        with patch("helpers.cli.CLI.colored_input") as mock_colored_input_2:
            mock_colored_input_2.side_effect = iter([Config.TRUE, Config.TRUE, proxy_port])
            config_object._Config__question_reverse_proxy()
            assert config_object.proxy
            assert not config_object.use_letsencrypt
            assert config_object.block_common_http_ports
            assert config_object.get_config().get("nginx_proxy_port") == proxy_port


def test_port_allowed():
    config_object = test_read_config()
    # Use let's encrypt by default
    assert not config_object._Config__is_port_allowed(Config.DEFAULT_NGINX_PORT)
    assert not config_object._Config__is_port_allowed("443")
    assert config_object._Config__is_port_allowed(Config.DEFAULT_PROXY_PORT)

    # Don't use let's encrypt
    config_object._Config__config["use_letsencrypt"] = Config.FALSE
    config_object._Config__config["block_common_http_ports"] = Config.FALSE
    assert config_object._Config__is_port_allowed(Config.DEFAULT_NGINX_PORT)
    assert config_object._Config__is_port_allowed("443")


def test_create_directory():
    config_object = test_read_config()
    destination_path = tempfile.mkdtemp()

    with patch("helpers.cli.CLI.colored_input") as mock_colored_input:
        mock_colored_input.side_effect = iter([destination_path, Config.TRUE])
        config_object._Config__create_directory()
        config = config_object.get_config()
        assert config.get("kobodocker_path") == destination_path

    shutil.rmtree(destination_path)


def test_maintenance():
    config_object = test_read_config()

    # First time
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        config_object.maintenance()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input_1:
        mock_colored_input_1.side_effect = iter([
            '2hours',  # Wrong value, it should ask again
            '2 hours',  # OK
            '',  # Wrong value, it should ask again
            '20190101T0200',  # OK
            'email@example.com'
        ])
        config_object._Config__config["date_created"] = time.time()
        config_object._Config__first_time = False
        config_object.maintenance()
        config = config_object.get_config()
        expected_str = 'Tuesday,&nbsp;January&nbsp;01&nbsp;at&nbsp;02:00&nbsp;GMT'
        assert config.get('maintenance_date_str') == expected_str

