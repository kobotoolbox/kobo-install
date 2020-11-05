# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import pytest
import os
import shutil
import tempfile
import time

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from helpers.cli import CLI
from helpers.config import Config
from .utils import (
    read_config,
    write_trigger_upsert_db_users,
)

CHOICE_YES = '1'
CHOICE_NO = '2'


def test_read_config():
    config = read_config()


def test_advanced_options():
    config = read_config()
    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_YES) as mock_ci:
        config._Config__questions_advanced_options()
        assert config.advanced_options

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_advanced_options()
        assert not config.advanced_options


def test_installation():
    config = read_config()
    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_installation_type()
        assert not config.local_install

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_YES) as mock_ci:
        config._Config__questions_installation_type()
        assert config.local_install
        assert not config.multi_servers
        assert not config.use_letsencrypt

    return config


@patch('helpers.config.Config._Config__clone_repo',
       MagicMock(return_value=True))
def test_staging_mode():
    config = read_config()
    kc_repo_path = tempfile.mkdtemp()
    kpi_repo_path = tempfile.mkdtemp()

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        mock_colored_input.side_effect = iter([CHOICE_YES,
                                               kc_repo_path,
                                               kpi_repo_path])
        config._Config__questions_dev_mode()
        dict_ = config.get_dict()
        assert not config.dev_mode
        assert config.staging_mode
        assert dict_['kpi_path'] == kpi_repo_path and \
               dict_['kc_path'] == kc_repo_path

    shutil.rmtree(kc_repo_path)
    shutil.rmtree(kpi_repo_path)


@patch('helpers.config.Config._Config__clone_repo',
       MagicMock(return_value=True))
def test_dev_mode():
    config = test_installation()

    kc_repo_path = tempfile.mkdtemp()
    kpi_repo_path = tempfile.mkdtemp()

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        mock_colored_input.side_effect = iter(['8080',
                                               CHOICE_YES,
                                               kc_repo_path,
                                               kpi_repo_path,
                                               CHOICE_YES,
                                               CHOICE_NO,
                                               ])

        config._Config__questions_dev_mode()
        dict_ = config.get_dict()
        assert config.dev_mode
        assert not config.staging_mode
        assert config.get_dict().get(
            'exposed_nginx_docker_port') == '8080'
        assert dict_['kpi_path'] == kpi_repo_path and \
               dict_['kc_path'] == kc_repo_path
        assert dict_['npm_container'] is False

    shutil.rmtree(kc_repo_path)
    shutil.rmtree(kpi_repo_path)

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_dev_mode()
        dict_ = config.get_dict()
        assert not config.dev_mode
        assert dict_['kpi_path'] == '' and dict_['kc_path'] == ''


def test_server_roles_questions():
    config = read_config()
    assert config.frontend_questions
    assert config.backend_questions

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        mock_colored_input.side_effect = iter(
            [CHOICE_YES, 'frontend', 'backend', 'secondary'])

        config._Config__questions_multi_servers()

        config._Config__questions_roles()
        assert config.frontend_questions
        assert not config.backend_questions

        config._Config__questions_roles()
        assert not config.frontend_questions
        assert config.backend_questions
        assert config.secondary_backend


def test_use_https():
    config = read_config()

    assert config.is_secure

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_YES) as mock_ci:
        config._Config__questions_https()
        assert not config.local_install
        assert config.is_secure

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_YES) as mock_ci:
        config._Config__questions_installation_type()
        assert config.local_install
        assert not config.is_secure


@patch('helpers.config.Config._Config__clone_repo',
       MagicMock(return_value=True))
def test_proxy_letsencrypt():
    config = read_config()

    assert config.proxy
    assert config.use_letsencrypt

    # Force custom exposed port
    config._Config__dict['exposed_nginx_docker_port'] = '8088'

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        # Use default options
        mock_colored_input.side_effect = iter([CHOICE_YES,
                                               'test@test.com',
                                               CHOICE_YES,
                                               Config.DEFAULT_NGINX_PORT])
        config._Config__questions_reverse_proxy()
        dict_ = config.get_dict()
        assert config.proxy
        assert config.use_letsencrypt
        assert config.block_common_http_ports
        assert dict_['nginx_proxy_port'] == Config.DEFAULT_PROXY_PORT
        assert dict_['exposed_nginx_docker_port'] == Config.DEFAULT_NGINX_PORT


def test_proxy_no_letsencrypt_advanced():
    config = read_config()
    # Force advanced options
    config._Config__dict['advanced'] = True
    assert config.advanced_options
    assert config.proxy
    assert config.use_letsencrypt
    proxy_port = Config.DEFAULT_NGINX_PORT

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        mock_colored_input.side_effect = iter(
            [CHOICE_NO, CHOICE_NO, proxy_port])
        config._Config__questions_reverse_proxy()
        dict_ = config.get_dict()
        assert config.proxy
        assert not config.use_letsencrypt
        assert not config.block_common_http_ports
        assert dict_['nginx_proxy_port'] == proxy_port


def test_proxy_no_letsencrypt():
    config = read_config()

    assert config.proxy
    assert config.use_letsencrypt

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_reverse_proxy()
        dict_ = config.get_dict()
        assert config.proxy
        assert not config.use_letsencrypt
        assert config.block_common_http_ports
        assert dict_['nginx_proxy_port'] == Config.DEFAULT_PROXY_PORT


def test_proxy_no_letsencrypt_retains_custom_nginx_proxy_port():
    custom_proxy_port = 9090
    config = read_config(overrides={
        'advanced': True,
        'use_letsencrypt': False,
        'nginx_proxy_port': str(custom_proxy_port),
    })
    with patch.object(
            CLI, 'colored_input',
            new=classmethod(lambda cls, message, color, default: default)
    ) as mock_ci:
        config._Config__questions_reverse_proxy()
        dict_ = config.get_dict()
        assert dict_['nginx_proxy_port'] == str(custom_proxy_port)


def test_no_proxy_no_ssl():
    config = read_config()
    dict_ = config.get_dict()
    assert config.is_secure
    assert dict_['nginx_proxy_port'] == Config.DEFAULT_PROXY_PORT

    proxy_port = Config.DEFAULT_NGINX_PORT

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_https()
        assert not config.is_secure

        with patch.object(CLI, 'colored_input',
                          return_value=CHOICE_NO) as mock_ci_2:
            config._Config__questions_reverse_proxy()
            dict_ = config.get_dict()
            assert not config.proxy
            assert not config.use_letsencrypt
            assert not config.block_common_http_ports
            assert dict_['nginx_proxy_port'] == proxy_port


def test_proxy_no_ssl_advanced():
    config = read_config()
    # Force advanced options
    config._Config__dict['advanced'] = True
    assert config.advanced_options
    assert config.is_secure

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci:
        config._Config__questions_https()
        assert not config.is_secure

        # Proxy - not on the same server
        proxy_port = Config.DEFAULT_NGINX_PORT
        with patch('helpers.cli.CLI.colored_input') as mock_colored_input_1:
            mock_colored_input_1.side_effect = iter(
                [CHOICE_YES, CHOICE_NO, proxy_port])
            config._Config__questions_reverse_proxy()
            dict_ = config.get_dict()
            assert config.proxy
            assert not config.use_letsencrypt
            assert not config.block_common_http_ports
            assert dict_['nginx_proxy_port'] == proxy_port

        # Proxy - on the same server
        proxy_port = Config.DEFAULT_PROXY_PORT
        with patch('helpers.cli.CLI.colored_input') as mock_colored_input_2:
            mock_colored_input_2.side_effect = iter(
                [CHOICE_YES, CHOICE_YES, proxy_port])
            config._Config__questions_reverse_proxy()
            dict_ = config.get_dict()
            assert config.proxy
            assert not config.use_letsencrypt
            assert config.block_common_http_ports
            assert dict_['nginx_proxy_port'] == proxy_port


def test_port_allowed():
    config = read_config()
    # Use let's encrypt by default
    assert not config._Config__is_port_allowed(Config.DEFAULT_NGINX_PORT)
    assert not config._Config__is_port_allowed('443')
    assert config._Config__is_port_allowed(Config.DEFAULT_PROXY_PORT)

    # Don't use let's encrypt
    config._Config__dict['use_letsencrypt'] = False
    config._Config__dict['block_common_http_ports'] = False
    assert config._Config__is_port_allowed(Config.DEFAULT_NGINX_PORT)
    assert config._Config__is_port_allowed('443')


def test_create_directory():
    config = read_config()
    destination_path = tempfile.mkdtemp()

    with patch('helpers.cli.CLI.colored_input') as mock_colored_input:
        mock_colored_input.side_effect = iter([destination_path, CHOICE_YES])
        config._Config__create_directory()
        dict_ = config.get_dict()
        assert dict_['kobodocker_path'] == destination_path

    shutil.rmtree(destination_path)


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
def test_maintenance():
    config = read_config()

    # First time
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        config.maintenance()
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
        config._Config__dict['date_created'] = time.time()
        config._Config__first_time = False
        config.maintenance()
        dict_ = config.get_dict()
        expected_str = 'Tuesday,&nbsp;January&nbsp;01&nbsp;' \
                       'at&nbsp;02:00&nbsp;GMT'
        assert dict_['maintenance_date_str'] == expected_str


def test_exposed_ports():
    config = read_config()
    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_YES) as mock_ci:
        # Choose multi servers options
        config._Config__questions_multi_servers()

        with patch('helpers.cli.CLI.colored_input') as mock_ci:
            # Choose to customize ports
            mock_ci.side_effect = iter(
                [CHOICE_YES, '5532', '27117', '6479', '6480'])
            config._Config__questions_ports()

            assert config._Config__dict['postgresql_port'] == '5532'
            assert config._Config__dict['mongo_port'] == '27117'
            assert config._Config__dict['redis_main_port'] == '6479'
            assert config._Config__dict['redis_cache_port'] == '6480'
            assert config.expose_backend_ports

    with patch.object(CLI, 'colored_input',
                      return_value=CHOICE_NO) as mock_ci_1:
        # Choose to single server
        config._Config__questions_multi_servers()

        with patch.object(CLI, 'colored_input',
                          return_value=CHOICE_NO) as mock_ci_2:
            # Choose to not expose ports
            config._Config__questions_ports()

            assert config._Config__dict['postgresql_port'] == '5432'
            assert config._Config__dict['mongo_port'] == '27017'
            assert config._Config__dict['redis_main_port'] == '6379'
            assert config._Config__dict['redis_cache_port'] == '6380'
            assert not config.expose_backend_ports


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
def test_force_secure_mongo():
    config = read_config()
    config_ = config.get_dict()

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        # We need to run it like if user has already run the setup once to
        # force MongoDB to 'upsert' users.
        config._Config__first_time = False
        # Run with no advanced options

        mock_ci.side_effect = iter([
            config_['kobodocker_path'],
            CHOICE_YES,  # Confirm path
            CHOICE_NO,
            CHOICE_NO,
            config_['public_domain_name'],
            config_['kpi_subdomain'],
            config_['kc_subdomain'],
            config_['ee_subdomain'],
            CHOICE_NO,  # Do you want to use HTTPS?
            config_.get('smtp_host', ''),
            config_.get('smtp_port', '25'),
            config_.get('smtp_user', ''),
            'test@test.com',
            config_['super_user_username'],
            config_['super_user_password'],
            CHOICE_NO,
        ])
        new_config = config.build()
        assert new_config['mongo_secured'] is True


@patch('helpers.config.Config._Config__write_upsert_db_users_trigger_file',
       new=write_trigger_upsert_db_users)
def test_secure_mongo_advanced_options():
    config = read_config()
    config._Config__dict['advanced'] = True

    # Try when setup is run for the first time.
    config._Config__first_time = True
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([
            'root',
            'root_password',
            'mongo_kobo_user',
            'mongo_password',
        ])
        config._Config__questions_mongo()
        assert not os.path.exists('/tmp/upsert_db_users')

    # Try when setup has been already run once
    # If it's an upgrade, users should not see:
    # ╔══════════════════════════════════════════════════════╗
    # ║ MongoDB root's and/or user's usernames have changed! ║
    # ╚══════════════════════════════════════════════════════╝
    config._Config__first_time = False
    config._Config__dict['mongo_secured'] = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([
            'root',
            'root_password',
            'mongo_kobo_user',
            'mongo_password',
        ])
        config._Config__questions_mongo()
        assert os.path.exists('/tmp/upsert_db_users')
        assert os.path.getsize('/tmp/upsert_db_users') == 0
        os.remove('/tmp/upsert_db_users')

    # Try when setup has been already run once
    # If it's NOT an upgrade, Users should see:
    # ╔══════════════════════════════════════════════════════╗
    # ║ MongoDB root's and/or user's usernames have changed! ║
    # ╚══════════════════════════════════════════════════════╝
    config._Config__dict['mongo_secured'] = True
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([
            'root',
            'root_passw0rd',
            'kobo_user',
            'mongo_password',
            CHOICE_YES,
        ])
        config._Config__questions_mongo()
        assert os.path.exists('/tmp/upsert_db_users')
        assert os.path.getsize('/tmp/upsert_db_users') != 0
        os.remove('/tmp/upsert_db_users')


@patch('helpers.config.Config._Config__write_upsert_db_users_trigger_file',
       new=write_trigger_upsert_db_users)
def test_update_mongo_passwords():
    config = read_config()
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        config._Config__first_time = False
        config._Config__dict['mongo_root_username'] = 'root'
        config._Config__dict['mongo_user_username'] = 'user'
        mock_ci.side_effect = iter([
            'root',
            'root_password',
            'user',
            'mongo_password'
        ])
        config._Config__questions_mongo()
        assert os.path.exists('/tmp/upsert_db_users')
        assert os.path.getsize('/tmp/upsert_db_users') == 0
        os.remove('/tmp/upsert_db_users')


@patch('helpers.config.Config._Config__write_upsert_db_users_trigger_file',
       new=write_trigger_upsert_db_users)
def test_update_mongo_usernames():
    config = read_config()
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        config._Config__first_time = False
        config._Config__dict['mongo_root_username'] = 'root'
        config._Config__dict['mongo_user_username'] = 'user'
        mock_ci.side_effect = iter([
            'admin',
            'root_password',
            'another_user',
            'mongo_password',
            CHOICE_YES  # Delete users
        ])
        config._Config__questions_mongo()
        assert os.path.exists('/tmp/upsert_db_users')
        with open('/tmp/upsert_db_users', 'r') as f:
            content = f.read()
        expected_content = 'user\tformhub\nroot\tadmin'
        assert content == expected_content
        os.remove('/tmp/upsert_db_users')


@patch('helpers.config.Config._Config__write_upsert_db_users_trigger_file',
       new=write_trigger_upsert_db_users)
def test_update_postgres_password():
    """
    Does **NOT** test if user is updated in PostgreSQL but the file creation
    (and its content) used to trigger the action by PostgreSQL container.

    When password changes, file must contain `<user><TAB><deletion boolean>`
    Users should not be deleted if they already exist.
    """
    config = read_config()
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        config._Config__first_time = False
        config._Config__dict['postgres_user'] = 'user'
        config._Config__dict['postgres_password'] = 'password'
        mock_ci.side_effect = iter([
            'kobocat',
            'koboform',
            'user',
            'user_password',
            CHOICE_NO,  # Tweak settings
        ])
        config._Config__questions_postgres()
        assert os.path.exists('/tmp/upsert_db_users')
        with open('/tmp/upsert_db_users', 'r') as f:
            content = f.read()
        expected_content = 'user\tfalse'
        assert content == expected_content
        os.remove('/tmp/upsert_db_users')


@patch('helpers.config.Config._Config__write_upsert_db_users_trigger_file',
       new=write_trigger_upsert_db_users)
def test_update_postgres_username():
    """
    Does **NOT** test if user is updated in PostgreSQL but the file creation
    (and its content) used to trigger the action by PostgreSQL container.

    When username changes, file must contain `<user><TAB><deletion boolean>`
    """
    config = read_config()
    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        config._Config__first_time = False
        config._Config__dict['postgres_user'] = 'user'
        config._Config__dict['postgres_password'] = 'password'
        mock_ci.side_effect = iter([
            'kobocat',
            'koboform',
            'another_user',
            'password',
            CHOICE_YES,  # Delete user
            CHOICE_NO,  # Tweak settings
        ])
        config._Config__questions_postgres()
        assert os.path.exists('/tmp/upsert_db_users')
        with open('/tmp/upsert_db_users', 'r') as f:
            content = f.read()
        expected_content = 'user\ttrue'
        assert content == expected_content
        os.remove('/tmp/upsert_db_users')


def test_update_postgres_db_name_from_single_database():
    """
    Simulate upgrade from single database to two databases.
    With two databases, KoBoCat has its own database. We ensure that
    `kc_postgres_db` gets `postgres_db` value.
    """
    config = read_config()
    dict_ = config.get_dict()
    old_db_name = 'postgres_db_kobo'
    config._Config__dict['postgres_db'] = old_db_name
    del config._Config__dict['kc_postgres_db']
    assert 'postgres_db' in dict_
    assert 'kc_postgres_db' not in dict_
    dict_ = config._Config__get_upgraded_dict()
    assert dict_['kc_postgres_db'] == old_db_name


def test_new_terminology():
    """
    Ensure config uses `primary` instead of `master`
    """
    config = read_config()
    config._Config__dict['backend_server_role'] = 'master'
    dict_ = config._Config__get_upgraded_dict()
    assert dict_['backend_server_role'] == 'primary'
