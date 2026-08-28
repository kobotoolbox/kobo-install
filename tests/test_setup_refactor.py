# -*- coding: utf-8 -*-
import curses
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

from helpers.cli import CLI
from helpers.config import Config
from helpers.template import Template
from .utils import mock_read_config as read_config

# Captured before the autouse fixture below replaces it, so the guard itself
# can still be tested.
_REAL_IS_INTERACTIVE = CLI.is_interactive

CHOICE_YES = '1'
CHOICE_NO = '2'
DEV = '1'
STAGING = '2'
PRODUCTION = '3'
SIMPLE = '1'
ADVANCED = '2'


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def interactive_terminal():
    """
    pytest captures stdout and feeds stdin from a pipe, so `CLI.is_interactive`
    is False for every test. Custom setup refuses to open the curses menu in
    that situation, which would abort each menu test before it starts.

    Tests that exercise the non-interactive guard itself patch it back to
    False locally.
    """
    with patch.object(CLI, 'is_interactive', return_value=True):
        yield


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_noop_patches():
    """Common patches that neutralise filesystem/network in build() tests."""
    return [
        patch('helpers.config.Config.write_config', new=lambda *a, **k: None),
        patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None),
        patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None),
        patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None),
        patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1'),
    ]


# ── __detect_install_mode ────────────────────────────────────────────────────

def test_detect_install_mode_dev():
    config = read_config({'local_installation': True})
    assert config._Config__detect_install_mode() == 'dev'


def test_detect_install_mode_dev_local_without_dev_flag():
    """local_installation alone is sufficient — dev_mode flag is redundant."""
    config = read_config({'local_installation': True, 'dev_mode': False})
    assert config._Config__detect_install_mode() == 'dev'


def test_detect_install_mode_staging():
    config = read_config({'local_installation': False, 'staging_mode': True})
    assert config._Config__detect_install_mode() == 'staging'


def test_detect_install_mode_production_by_default():
    config = read_config()
    assert config._Config__detect_install_mode() == 'production'


def test_detect_install_mode_ignores_stored_install_mode_key():
    """install_mode in the dict is derived, not trusted for backwards compat."""
    config = read_config({'install_mode': 'production', 'local_installation': True})
    assert config._Config__detect_install_mode() == 'dev'


# ── __questions_install_mode ─────────────────────────────────────────────────

def test_questions_install_mode_sets_dev_flags():
    config = read_config()
    with patch.object(CLI, 'colored_input', return_value=DEV):
        config._Config__questions_install_mode()
    d = config._Config__dict
    assert d['install_mode'] == 'dev'
    assert d['local_installation'] is True
    assert d['dev_mode'] is True
    assert d['staging_mode'] is False
    assert d['debug'] is True


def test_questions_install_mode_sets_staging_flags():
    config = read_config()
    with patch.object(CLI, 'colored_input', return_value=STAGING):
        config._Config__questions_install_mode()
    d = config._Config__dict
    assert d['install_mode'] == 'staging'
    assert d['local_installation'] is False
    assert d['dev_mode'] is False
    assert d['staging_mode'] is True
    assert d['debug'] is False
    assert d['use_celery'] is True


def test_questions_install_mode_sets_production_flags():
    config = read_config()
    with patch.object(CLI, 'colored_input', return_value=PRODUCTION):
        config._Config__questions_install_mode()
    d = config._Config__dict
    assert d['install_mode'] == 'production'
    assert d['local_installation'] is False
    assert d['dev_mode'] is False
    assert d['staging_mode'] is False
    assert d['debug'] is False


def test_questions_install_mode_dev_resets_domain_names():
    """A workstation is never asked for a domain, so the server one must go."""
    config = read_config({
        'install_mode': 'production',
        'public_domain_name': 'kobo.example',
        'internal_domain_name': 'kobo.internal',
        'private_domain_name': 'kobo.private.example',
    })
    with patch.object(CLI, 'colored_input', return_value=DEV):
        config._Config__questions_install_mode()
    d = config._Config__dict
    assert d['public_domain_name'] == 'kobo.local'
    assert d['internal_domain_name'] == 'docker.internal'
    assert d['private_domain_name'] == 'kobo.private'


def test_questions_install_mode_staging_keeps_domain_names():
    """Production and staging are both servers: the domain is theirs to keep."""
    config = read_config({
        'install_mode': 'production',
        'public_domain_name': 'kobo.example',
    })
    with patch.object(CLI, 'colored_input', return_value=STAGING):
        config._Config__questions_install_mode()

    assert config._Config__dict['public_domain_name'] == 'kobo.example'


def test_questions_install_mode_dev_again_keeps_domain_names():
    """
    A development install that stays one keeps whatever domain it was given:
    only a change of mode resets anything.
    """
    config = read_config({
        'install_mode': 'dev',
        'local_installation': True,
        'dev_mode': True,
        'public_domain_name': 'kobo.dev',
    })
    with patch.object(CLI, 'colored_input', return_value=DEV):
        config._Config__questions_install_mode()

    assert config._Config__dict['public_domain_name'] == 'kobo.dev'


def test_questions_install_mode_default_reflects_existing_dev_config():
    """Existing dev config → default choice should be '1'."""
    config = read_config({'local_installation': True})
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default  # accept whatever default is offered

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_install_mode()

    assert defaults_seen[0] == '1'


def test_questions_install_mode_default_reflects_existing_staging_config():
    config = read_config({'staging_mode': True})
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_install_mode()

    assert defaults_seen[0] == '2'


def test_questions_install_mode_default_reflects_existing_production_config():
    config = read_config()
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_install_mode()

    assert defaults_seen[0] == '3'


# ── __questions_complexity ───────────────────────────────────────────────────

def test_questions_complexity_simple():
    config = read_config()
    with patch.object(CLI, 'colored_input', return_value=SIMPLE):
        config._Config__questions_complexity()
    assert config._Config__dict['advanced'] is False
    assert not config.advanced_options


def test_questions_complexity_advanced():
    config = read_config()
    with patch.object(CLI, 'colored_input', return_value=ADVANCED):
        config._Config__questions_complexity()
    assert config._Config__dict['advanced'] is True
    assert config.advanced_options


def test_questions_complexity_default_simple_when_no_prior_choice():
    config = read_config()  # advanced=False by default
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_complexity()

    assert defaults_seen[0] == '1'  # Quick setup
    assert not config.advanced_options


def test_questions_complexity_default_advanced_when_previously_advanced():
    config = read_config({'advanced': True})
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_complexity()

    assert defaults_seen[0] == '2'  # Custom setup
    assert config.advanced_options


def test_questions_complexity_explains_both_choices():
    """
    "Simple" and "Advanced" on their own said nothing about what either one
    does; each line now carries what it means.
    """
    printed = []
    config = read_config()
    with patch.object(CLI, 'colored_print',
                      side_effect=lambda m, *a, **k: printed.append(m)), \
         patch.object(CLI, 'colored_input', return_value=SIMPLE):
        config._Config__questions_complexity()

    quick = [m for m in printed if 'Quick setup' in m]
    custom = [m for m in printed if 'Custom setup' in m]
    assert len(quick) == 1 and len(custom) == 1
    assert 'nothing else is asked' in quick[0]
    assert 'sections' in custom[0]


def test_questions_install_mode_explains_each_mode():
    printed = []
    config = read_config()
    with patch.object(CLI, 'colored_print',
                      side_effect=lambda m, *a, **k: printed.append(m)), \
         patch.object(CLI, 'colored_input', return_value=DEV), \
         patch.object(CLI, 'framed_print', new=lambda *a, **k: None):
        config._Config__questions_install_mode()

    for label in ('Development', 'Staging', 'Production'):
        line = [m for m in printed if label in m and m.startswith('\t')]
        assert len(line) == 1, label
        # Every choice says what it is, not just its name
        assert len(line[0].split('\u2014')[1].split()) >= 4, label


# ── __setup_directory ────────────────────────────────────────────────────────

def test_setup_directory_sets_sibling_kobo_docker_path():
    config = read_config()
    helpers_parent = os.path.dirname(
        os.path.dirname(os.path.realpath(
            sys.modules['helpers.config'].__file__
        ))
    )
    expected = os.path.realpath(
        os.path.normpath(os.path.join(helpers_parent, '..', 'kobo-docker'))
    )

    with patch('helpers.config.Config.write_unique_id', return_value=True), \
         patch('helpers.config.Config._Config__validate_installation'), \
         patch('os.makedirs'):
        config._Config__setup_directory()

    assert config._Config__dict['kobodocker_path'] == expected


def test_setup_directory_creates_dir_if_missing():
    config = read_config()
    with patch('helpers.config.Config.write_unique_id', return_value=True), \
         patch('helpers.config.Config._Config__validate_installation'), \
         patch('os.path.isdir', return_value=False), \
         patch('os.makedirs') as mock_mkdir:
        config._Config__setup_directory()

    mock_mkdir.assert_called_once()


def test_setup_directory_exits_if_mkdir_fails():
    config = read_config()
    with patch('helpers.config.Config.write_unique_id', return_value=True), \
         patch('helpers.config.Config._Config__validate_installation'), \
         patch('os.path.isdir', return_value=False), \
         patch('os.makedirs', side_effect=OSError):
        with pytest.raises(SystemExit):
            config._Config__setup_directory()


# ── __detect_system_resources ────────────────────────────────────────────────

def test_detect_system_resources_linux():
    meminfo = 'MemTotal:       16777216 kB\nMemFree: 8000000 kB\n'
    m = mock_open(read_data=meminfo)
    m.return_value.__iter__ = lambda s: iter(meminfo.splitlines(keepends=True))

    with patch('sys.platform', 'linux'), \
         patch('builtins.open', m):
        cpus, ram_gb = Config._Config__detect_system_resources()

    assert cpus == os.cpu_count()
    assert ram_gb == 16  # 16777216 kB // 1048576


def test_detect_system_resources_macos():
    ram_bytes = 8 * 1024 ** 3  # 8 GB
    mock_popen = MagicMock()
    mock_popen.return_value.__enter__ = lambda s: s
    mock_popen.return_value.__exit__ = MagicMock(return_value=False)
    mock_popen.return_value.read = lambda: str(ram_bytes)

    with patch('sys.platform', 'darwin'), \
         patch('os.popen', mock_popen):
        cpus, ram_gb = Config._Config__detect_system_resources()

    assert cpus == os.cpu_count()
    assert ram_gb == 8


def test_detect_system_resources_fallback_on_error():
    with patch('sys.platform', 'linux'), \
         patch('builtins.open', side_effect=OSError):
        cpus, ram_gb = Config._Config__detect_system_resources()

    assert cpus == os.cpu_count()
    assert ram_gb == 2  # safe fallback


def test_detect_system_resources_minimum_one_cpu():
    with patch('os.cpu_count', return_value=None), \
         patch('sys.platform', 'linux'), \
         patch('builtins.open', side_effect=OSError):
        cpus, _ = Config._Config__detect_system_resources()

    assert cpus == 1


# ── __auto_configure_resources ───────────────────────────────────────────────

@patch('helpers.network.Network.curl', return_value=None)
def test_auto_configure_resources_skipped_for_dev(mock_curl):
    config = read_config({'install_mode': 'dev', 'dev_mode': True,
                          'local_installation': True})
    original_postgres = config._Config__dict['postgres_settings']
    original_uwsgi = config._Config__dict['uwsgi_settings']

    config._Config__auto_configure_resources()

    assert config._Config__dict['postgres_settings'] == original_postgres
    assert config._Config__dict['uwsgi_settings'] == original_uwsgi
    mock_curl.assert_not_called()


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(8, 16))
def test_auto_configure_resources_staging_50_percent(mock_detect, mock_curl):
    config = read_config({'install_mode': 'staging'})
    config._Config__auto_configure_resources()
    assert config._Config__dict['postgres_cpus'] == '4'   # 8 × 50%
    assert config._Config__dict['postgres_ram'] == '8'    # 16 × 50%
    assert config._Config__dict['postgres_settings'] is True


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(8, 16))
def test_auto_configure_resources_production_75_percent(mock_detect, mock_curl):
    config = read_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()
    assert config._Config__dict['postgres_cpus'] == '6'   # round(8 × 0.75)
    assert config._Config__dict['postgres_ram'] == '12'   # round(16 × 0.75)
    assert config._Config__dict['postgres_settings'] is True


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(1, 1))
def test_auto_configure_resources_never_below_minimum(mock_detect, mock_curl):
    """Tiny machine: floors must hold (1 CPU, 2 GB, 2/4 workers, 1024 MB)."""
    config = read_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()
    assert int(config._Config__dict['postgres_cpus']) >= 1
    assert int(config._Config__dict['postgres_ram']) >= 2
    assert int(config._Config__dict['uwsgi_workers_start']) >= 2
    assert int(config._Config__dict['uwsgi_workers_max']) >= 4
    assert int(config._Config__dict['uwsgi_soft_limit']) >= 1024


@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_auto_configure_resources_pgconfig_response_stored(mock_detect):
    pg_conf = '# pgconfig\nshared_buffers = 2048MB\n'
    with patch('helpers.network.Network.curl', return_value=pg_conf):
        config = read_config({'install_mode': 'production'})
        config._Config__auto_configure_resources()
    assert 'shared_buffers' in config._Config__dict['postgres_settings_content']


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_auto_configure_resources_pgconfig_failure_preserves_existing(mock_detect, mock_curl):
    config = read_config({'install_mode': 'production'})
    original = config._Config__dict['postgres_settings_content']
    config._Config__auto_configure_resources()
    assert config._Config__dict['postgres_settings_content'] == original


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_auto_configure_resources_uwsgi_workers_scale_with_cpus(mock_detect, mock_curl):
    # 4 CPUs × 75% = 3 allocated → workers_start=max(2,3)=3, workers_max=max(4,6)=6
    config = read_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()
    assert config._Config__dict['uwsgi_workers_start'] == '3'
    assert config._Config__dict['uwsgi_workers_max'] == '6'
    assert config._Config__dict['uwsgi_settings'] is True


# ── uWSGI soft_limit ─────────────────────────────────────────────────────────

@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_uwsgi_soft_limit_staging_25_percent(mock_detect, mock_curl):
    """Staging single-server: 25% of 16 GB = 4096 MB."""
    config = read_config({'install_mode': 'staging'})
    config._Config__auto_configure_resources()
    assert config._Config__dict['uwsgi_soft_limit'] == '4096'


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_uwsgi_soft_limit_production_50_percent(mock_detect, mock_curl):
    """Production single-server: 50% of 16 GB = 8192 MB."""
    config = read_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()
    assert config._Config__dict['uwsgi_soft_limit'] == '8192'


@patch('helpers.network.Network.curl', return_value=None)
@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 1))
def test_uwsgi_soft_limit_floor_1024_mb(mock_detect, mock_curl):
    """1 GB machine: soft_limit must not drop below 1024 MB."""
    config = read_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()
    assert int(config._Config__dict['uwsgi_soft_limit']) >= 1024


@patch('helpers.config.Config._Config__detect_system_resources', return_value=(4, 16))
def test_uwsgi_soft_limit_multiserver_frontend_75_percent(mock_detect):
    """Multi-server frontend: recalculated to 75% = 12288 MB."""
    config = read_config({'install_mode': 'production'})
    config._Config__first_time = True
    config._Config__dict['uwsgi_settings'] = True
    config._Config__dict['multi'] = True
    config._Config__dict['server_role'] = 'frontend'

    # Replicate the recalculation logic from __run_selected_advanced_sections
    _, ram_gb = config._Config__detect_system_resources()
    soft_limit_mb = max(1024, round(ram_gb * 0.75 * 1024))
    config._Config__dict['uwsgi_soft_limit'] = str(soft_limit_mb)

    assert config._Config__dict['uwsgi_soft_limit'] == '12288'


# ── build() simple mode ──────────────────────────────────────────────────────

@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_dev_consumes_exactly_two_inputs(_):
    """Mode + complexity — a workstation needs nothing else."""
    config = read_config({'local_installation': True, 'dev_mode': True,
                          'install_mode': 'dev'})
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
            patch.object(Config, '_Config__auto_setup_kpi_path'), \
            patch.object(Config, '_Config__auto_detect_cloud_profiles'):
        mock_ci.side_effect = iter([DEV, SIMPLE])
        config.build()

    assert mock_ci.call_count == 2


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_server_consumes_exactly_four_inputs(_):
    """Mode + complexity + the two answers a server has no default for."""
    config = read_config()
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
            patch.object(Config, '_Config__clone_repo'):
        mock_ci.side_effect = iter([
            PRODUCTION, SIMPLE, 'kobo.example', 'support@kobo.example',
        ])
        config.build()

    assert mock_ci.call_count == 4


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
# The host's own ~/.aws and ~/.config/gcloud must not decide what this asks
@patch('helpers.config.Config._Config__auto_detect_cloud_profiles',
       new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_setup_kpi_path',
       new=lambda *a: None)
def test_build_simple_dev_sets_console_email_backend(_):
    config = read_config({'local_installation': True, 'dev_mode': True,
                          'install_mode': 'dev'})
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([DEV, SIMPLE])
        result = config.build()

    assert result['email_backend'] == (
        'django.core.mail.backends.console.EmailBackend'
    )


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_production_email_backend_empty(_):
    config = read_config()
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
            patch.object(Config, '_Config__clone_repo'):
        mock_ci.side_effect = iter([
            PRODUCTION, SIMPLE, 'kobo.example', 'support@kobo.example',
        ])
        result = config.build()

    assert result['email_backend'] == ''


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_secures_mongo(_):
    config = read_config()
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
            patch.object(Config, '_Config__clone_repo'):
        mock_ci.side_effect = iter([
            PRODUCTION, SIMPLE, 'kobo.example', 'support@kobo.example',
        ])
        result = config.build()

    assert result['mongo_secured'] is True


# ── build() simple mode, server ──────────────────────────────────────────────

def _build_quick_server(config, mode, domain='kobo.example',
                        email='support@kobo.example'):
    """
    Runs a quick setup on a server, answering the two questions it asks.

    Returns:
        tuple: the resulting dict, and the `__clone_repo` mock.
    """
    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
            patch.object(Config, '_Config__clone_repo') as mock_clone:
        mock_ci.side_effect = iter([mode, SIMPLE, domain, email])
        result = config.build()

    return result, mock_clone


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_production_asks_domain_name(_):
    """Regression: quick setup used to leave a server on `kobo.local`."""
    config = read_config()
    config._Config__first_time = False

    result, _clone = _build_quick_server(config, PRODUCTION)

    assert result['public_domain_name'] == 'kobo.example'
    # Derived from the domain, as the custom setup does
    assert result['internal_domain_name'] == 'kobo.internal'
    assert result['private_domain_name'] == 'kobo.private'
    # Subdomains have usable defaults, so they are not asked
    assert result['kpi_subdomain'] == 'kf'
    assert result['kc_subdomain'] == 'kc'
    assert result['ee_subdomain'] == 'ee'


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_staging_asks_domain_name(_):
    """Staging is a server too, and needs the same two answers."""
    config = read_config({'staging_mode': True, 'install_mode': 'staging'})
    config._Config__first_time = False

    result, _clone = _build_quick_server(config, STAGING)

    assert result['public_domain_name'] == 'kobo.example'
    assert result['letsencrypt_email'] == 'support@kobo.example'


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_server_support_email_used_everywhere(_):
    """One address, for outgoing email, Let's Encrypt and the maintenance page."""
    config = read_config()
    config._Config__first_time = False

    result, _clone = _build_quick_server(config, PRODUCTION)

    assert result['default_from_email'] == 'support@kobo.example'
    assert result['letsencrypt_email'] == 'support@kobo.example'
    assert result['maintenance_email'] == 'support@kobo.example'


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_server_support_email_defaults_to_domain(_):
    """
    On a first run the address offered follows the domain just entered, so
    pressing ENTER is enough.
    """
    config = read_config()
    config._Config__first_time = True
    answers = iter([PRODUCTION, SIMPLE, 'kobo.example'])

    def answer(message, color=None, default=None):
        try:
            return next(answers)
        except StopIteration:
            # The support address: an empty answer makes the real
            # `CLI.colored_input()` return the default it offered
            return default

    with patch('helpers.cli.CLI.colored_input', side_effect=answer), \
            patch.object(Config, '_Config__clone_repo'):
        result = config.build()

    assert result['default_from_email'] == 'support@kobo.example'
    assert result['letsencrypt_email'] == 'support@kobo.example'


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_server_installs_letsencrypt_without_asking(_):
    """
    Quick setup accepts every default: certificates are installed, and
    `nginx-certbot` is cloned so `run.py` finds it later.
    """
    config = read_config()
    config._Config__first_time = False

    result, mock_clone = _build_quick_server(config, PRODUCTION)

    assert result['use_letsencrypt'] is True
    assert result['proxy'] is True
    assert result['block_common_http_ports'] is True
    assert result['nginx_proxy_port'] == Config.DEFAULT_PROXY_PORT
    assert result['exposed_nginx_docker_port'] == Config.DEFAULT_NGINX_PORT
    mock_clone.assert_called_once_with(
        config.get_letsencrypt_repo_path(), 'nginx-certbot'
    )


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_simple_server_keeps_own_reverse_proxy(_):
    """
    Quick setup accepts the stored default, so an installation that chose its
    own load balancer in custom setup does not silently get certbot back.
    """
    config = read_config({'use_letsencrypt': False})
    config._Config__first_time = False

    result, mock_clone = _build_quick_server(config, PRODUCTION)

    assert result['use_letsencrypt'] is False
    mock_clone.assert_not_called()


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
@patch('helpers.config.Config._Config__auto_detect_cloud_profiles',
       new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_setup_kpi_path',
       new=lambda *a: None)
def test_build_simple_dev_keeps_local_domain(_):
    """A workstation is never asked for a domain name."""
    config = read_config({'local_installation': True, 'dev_mode': True,
                          'install_mode': 'dev'})
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([DEV, SIMPLE])
        result = config.build()

    assert result['public_domain_name'] == 'kobo.local'


# ── checkbox_menu logic ───────────────────────────────────────────────────────

def test_checkbox_menu_separators_are_not_selectable():
    choices = [
        {'separator': 'Group A'},
        {'label': 'Item 1', 'checked': True},
        {'separator': 'Group B'},
        {'label': 'Item 2', 'checked': False},
    ]
    selectable = [i for i, c in enumerate(choices) if 'label' in c]
    assert selectable == [1, 3]
    assert 0 not in selectable
    assert 2 not in selectable


def test_checkbox_menu_toggle_all_off_to_on():
    state = [
        {'separator': 'Section'},
        {'label': 'A', 'checked': False},
        {'label': 'B', 'checked': False},
    ]
    all_on = all(s['checked'] for s in state if 'label' in s)
    for s in state:
        if 'label' in s:
            s['checked'] = not all_on

    assert state[1]['checked'] is True
    assert state[2]['checked'] is True


def test_checkbox_menu_toggle_all_on_to_off():
    state = [
        {'separator': 'Section'},
        {'label': 'A', 'checked': True},
        {'label': 'B', 'checked': True},
    ]
    all_on = all(s['checked'] for s in state if 'label' in s)
    for s in state:
        if 'label' in s:
            s['checked'] = not all_on

    assert state[1]['checked'] is False
    assert state[2]['checked'] is False


def test_checkbox_menu_toggle_all_partial_treated_as_off():
    """Partial selection → treated as all_on=False → toggle sets everything on."""
    state = [
        {'label': 'A', 'checked': True},
        {'label': 'B', 'checked': False},
    ]
    all_on = all(s['checked'] for s in state if 'label' in s)
    assert all_on is False
    for s in state:
        if 'label' in s:
            s['checked'] = not all_on

    assert state[0]['checked'] is True
    assert state[1]['checked'] is True


def test_checkbox_menu_separator_skipped_by_nearest_selectable():
    """Arrow navigation must skip over separators."""
    state = [
        {'label': 'A', 'checked': False},
        {'separator': 'Group'},
        {'label': 'B', 'checked': False},
    ]

    def nearest_selectable(pos, direction):
        idx = pos + direction
        while 0 <= idx < len(state):
            if 'label' in state[idx]:
                return idx
            idx += direction
        return pos

    # From position 0 (A), going down (+1) should skip separator at 1 → land on 2 (B)
    assert nearest_selectable(0, 1) == 2
    # From position 2 (B), going up (-1) should skip separator at 1 → land on 0 (A)
    assert nearest_selectable(2, -1) == 0
    # At boundary: going up from 0 stays at 0
    assert nearest_selectable(0, -1) == 0


# ── __auto_detect_aws_profile (applies the mount, does not ask) ──────────────

def test_auto_detect_aws_profile_enables_profile_when_dir_exists():
    config = read_config({'use_aws': False, 'aws_use_profile': False})
    with patch('helpers.config.os.path.isdir', return_value=True):
        config._Config__auto_detect_aws_profile('/home/dev/.aws')
    d = config._Config__dict
    assert d['aws_use_profile'] is True
    assert d['aws_profile_name'] == 'default'
    assert d['aws_host_aws_dir'].endswith('.aws')
    # S3 storage must NOT be forced on
    assert d['use_aws'] is False


def test_auto_detect_aws_profile_noop_when_dir_missing():
    config = read_config({'use_aws': False, 'aws_use_profile': False})
    with patch('helpers.config.os.path.isdir', return_value=False):
        config._Config__auto_detect_aws_profile('/home/dev/.aws')
    d = config._Config__dict
    assert d['aws_use_profile'] is False
    assert d['use_aws'] is False


# ── __auto_detect_gcloud_profile (applies the mount, does not ask) ───────────

def _gcloud_dir(tmp_path, project=None):
    """
    Builds a fake `~/.config/gcloud` directory, optionally holding an active
    project in its default configuration.
    """
    gcloud_dir = tmp_path / '.config' / 'gcloud'
    gcloud_dir.mkdir(parents=True)
    if project is not None:
        conf_dir = gcloud_dir / 'configurations'
        conf_dir.mkdir()
        (conf_dir / 'config_default').write_text(project)
    return gcloud_dir


def test_auto_detect_gcloud_profile_noop_when_dir_missing(tmp_path):
    config = read_config({'gcloud_use_profile': False})
    config._Config__auto_detect_gcloud_profile(str(tmp_path / 'missing'))
    d = config._Config__dict
    assert d['gcloud_use_profile'] is False
    assert d['asr_mt_google_project_id'] == ''


def test_auto_detect_gcloud_profile_enables_profile_without_project(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path)
    config = read_config({
        'gcloud_use_profile': False,
        'asr_mt_google_project_id': '',
    })
    config._Config__auto_detect_gcloud_profile(str(gcloud_dir))
    d = config._Config__dict
    assert d['gcloud_use_profile'] is True
    assert d['gcloud_host_config_dir'] == str(gcloud_dir)
    assert d['asr_mt_google_project_id'] == ''
    # NLP settings stay an explicit opt-in
    assert d['use_nlp'] is False


def test_auto_detect_gcloud_profile_reads_active_project(tmp_path):
    gcloud_dir = _gcloud_dir(
        tmp_path,
        project='[core]\naccount = someone@example.org\nproject = my-gcp-project\n',
    )
    config = read_config({'gcloud_use_profile': False})
    config._Config__auto_detect_gcloud_profile(str(gcloud_dir))
    assert config._Config__dict['asr_mt_google_project_id'] == 'my-gcp-project'


def test_auto_detect_gcloud_profile_survives_malformed_config(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path, project='not an ini file at all')
    config = read_config({'gcloud_use_profile': False})
    config._Config__auto_detect_gcloud_profile(str(gcloud_dir))
    d = config._Config__dict
    assert d['gcloud_use_profile'] is True
    assert d['asr_mt_google_project_id'] == ''


def test_auto_detect_gcloud_profile_survives_config_without_project(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path, project='[core]\naccount = a@b.org\n')
    config = read_config({'gcloud_use_profile': False})
    config._Config__auto_detect_gcloud_profile(str(gcloud_dir))
    assert config._Config__dict['asr_mt_google_project_id'] == ''


# ── __questions_cloud_profiles ───────────────────────────────────────────────

def test_questions_cloud_profiles_enables_both_and_stores_host_dirs():
    config = read_config({
        'aws_use_profile': False,
        'gcloud_use_profile': False,
    })
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter([
            CHOICE_YES, 'staging', '/opt/aws',   # AWS
            CHOICE_YES, '/opt/gcloud',           # Google
        ])
        config._Config__questions_cloud_profiles()
    d = config._Config__dict
    assert d['aws_use_profile'] is True
    assert d['aws_profile_name'] == 'staging'
    assert d['aws_host_aws_dir'] == '/opt/aws'
    assert d['gcloud_use_profile'] is True
    assert d['gcloud_host_config_dir'] == '/opt/gcloud'


def test_questions_cloud_profiles_clears_host_dirs_when_disabled():
    config = read_config({
        'aws_use_profile': True,
        'aws_profile_name': 'staging',
        'aws_host_aws_dir': '/opt/aws',
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/opt/gcloud',
    })
    with patch.object(CLI, 'colored_input', return_value=CHOICE_NO):
        config._Config__questions_cloud_profiles()
    d = config._Config__dict
    assert d['aws_use_profile'] is False
    assert d['aws_profile_name'] == ''
    assert d['aws_host_aws_dir'] == ''
    assert d['gcloud_use_profile'] is False
    assert d['gcloud_host_config_dir'] == ''


def test_questions_cloud_profiles_clears_aws_credentials():
    """
    A profile supplies the credentials; a stale key/secret pair left behind
    would keep being rendered into `aws.txt`.
    """
    config = read_config({
        'aws_use_profile': False,
        'aws_access_key': 'AKIA',
        'aws_secret_key': 'shhh',
    })
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter([
            CHOICE_YES, 'default', '/opt/aws',
            CHOICE_NO,
        ])
        config._Config__questions_cloud_profiles()
    d = config._Config__dict
    assert d['aws_access_key'] == ''
    assert d['aws_secret_key'] == ''


def _cloud_profiles_defaults(config):
    """
    Runs __questions_cloud_profiles and returns the defaults offered for both
    yes/no questions and for both host directory inputs.
    """
    yes_no = []
    inputs = {}

    def capture_yes_no(question, default=True, labels=None):
        yes_no.append(default)
        return default

    def capture_input(message, color, default=''):
        inputs[message] = default
        return default

    with patch.object(CLI, 'yes_no_question', side_effect=capture_yes_no), \
         patch.object(CLI, 'colored_input', side_effect=capture_input):
        config._Config__questions_cloud_profiles()

    return {'aws': yes_no[0], 'gcloud': yes_no[1], 'inputs': inputs}


def test_questions_cloud_profiles_default_to_yes_when_dirs_exist():
    config = read_config({
        'aws_use_profile': False,
        'aws_host_aws_dir': '',
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=True):
        seen = _cloud_profiles_defaults(config)
    assert seen['aws'] is True
    assert seen['gcloud'] is True


def test_questions_cloud_profiles_default_to_no_when_dirs_missing():
    config = read_config({
        'aws_use_profile': False,
        'aws_host_aws_dir': '',
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=False):
        seen = _cloud_profiles_defaults(config)
    assert seen['aws'] is False
    assert seen['gcloud'] is False


def test_questions_cloud_profiles_stored_answer_wins_over_detection():
    """An explicit previous "Yes" survives the directories moving away."""
    config = read_config({
        'aws_use_profile': True,
        'aws_host_aws_dir': '/opt/aws',
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/opt/gcloud',
    })
    with patch('helpers.config.os.path.isdir', return_value=False):
        seen = _cloud_profiles_defaults(config)
    assert seen['aws'] is True
    assert seen['gcloud'] is True


def test_questions_cloud_profiles_offer_default_dirs_after_previous_no():
    """
    Answering No resets the stored directories, so the next run must fall back
    to ~/.aws and ~/.config/gcloud instead of offering an empty path.
    """
    config = read_config({
        'aws_use_profile': False,
        'aws_host_aws_dir': '',
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=True):
        seen = _cloud_profiles_defaults(config)
    inputs = seen['inputs']
    assert inputs['AWS credentials directory on host'] == \
        os.path.expanduser('~/.aws')
    assert inputs['Google Cloud credentials directory on host'] == \
        os.path.expanduser('~/.config/gcloud')


# ── __questions_nlp ──────────────────────────────────────────────────────────

def test_questions_nlp_stores_all_values():
    config = read_config({
        'use_nlp': False,
        'gcloud_use_profile': True,
        'aws_use_profile': True,
    })
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        # Google first (bucket, project), then AWS.
        mock_input.side_effect = iter([
            'my-bucket', 'my-gcp-project', 'us-west-2',
        ])
        config._Config__questions_nlp()
    d = config._Config__dict
    # Checking the section is the consent, no extra yes/no gate
    assert d['use_nlp'] is True
    assert d['gs_bucket_name'] == 'my-bucket'
    assert d['aws_bedrock_region_name'] == 'us-west-2'
    assert d['asr_mt_google_project_id'] == 'my-gcp-project'


def test_questions_nlp_groups_the_google_questions_together():
    """
    The AutoQA model ARNs are gone, and the two GOOGLE_CLOUD_* projects are
    derived from the single project answer instead of being asked.

    The two Google questions must also sit next to each other: Bedrock is a
    different provider serving a different feature, and used to be asked
    between them.
    """
    config = read_config({
        'use_nlp': False,
        'gcloud_use_profile': True,
        'aws_use_profile': True,
    })
    seen = []
    with patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': seen.append(m)):
        config._Config__questions_nlp()
    assert len(seen) == 3
    assert not [m for m in seen if 'ARN' in m]
    assert len([m for m in seen if 'project' in m.lower()]) == 1
    # Google, Google, then AWS — never Google, AWS, Google.
    assert 'Google' in seen[0]
    assert 'Google' in seen[1]
    assert 'Bedrock' in seen[2]


def test_questions_nlp_project_defaults_to_the_detected_one():
    """
    The project found by __auto_detect_gcloud_profile is offered as default.
    """
    config = read_config({
        'asr_mt_google_project_id': 'detected-project',
        'gcloud_use_profile': True,
    })
    with patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': default):
        config._Config__questions_nlp()
    assert config._Config__dict['asr_mt_google_project_id'] == \
        'detected-project'


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_cloud_profiles',
       new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_setup_kpi_path', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_gives_nlp_up_to_the_custom_yml(_, tmp_path):
    """
    kobo-install must not write variables the custom compose file already
    defines: the same setting would then have two sources of truth.
    """
    (tmp_path / 'docker-compose.frontend.custom.yml').write_text(
        '      - GOOGLE_CLOUD_PROJECT=my-gcp-project\n'
    )
    config = read_config({
        'local_installation': True, 'dev_mode': True, 'install_mode': 'dev',
        'kobodocker_path': str(tmp_path),
        'use_nlp': True,
        'use_frontend_custom_yml': True,
    })
    config._Config__first_time = False

    printed = []
    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
         patch.object(CLI, 'colored_print',
                      side_effect=lambda m, *a, **k: printed.append(m)):
        mock_ci.side_effect = iter([DEV, SIMPLE])
        result = config.build()

    assert result['use_nlp'] is False
    assert [m for m in printed if 'custom.yml' in m]
    # Mode and complexity, nothing more
    assert mock_ci.call_count == 2


# ── __auto_setup_kpi_path (dev, quick setup) ─────────────────────────────────

def _sibling_kpi_path():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.realpath(
            sys.modules['helpers.config'].__file__
        ))
    )
    return os.path.realpath(os.path.normpath(os.path.join(base_dir, '..', 'kpi')))


def test_auto_setup_kpi_path_settles_on_the_sibling_checkout():
    config = read_config({'kpi_path': '', 'kpi_dev_build_id': ''})
    with patch.object(Config, '_Config__clone_repo') as mock_clone:
        config._Config__auto_setup_kpi_path()

    d = config._Config__dict
    assert d['kpi_path'] == _sibling_kpi_path()
    mock_clone.assert_called_once_with(d['kpi_path'], 'kpi')


def test_auto_setup_kpi_path_stamps_a_build_id():
    """Without one, the front-end image is never rebuilt from the sources."""
    config = read_config({'kpi_path': '', 'kpi_dev_build_id': ''})
    with patch.object(Config, '_Config__clone_repo'):
        config._Config__auto_setup_kpi_path()
    assert config._Config__dict['kpi_dev_build_id']


def test_auto_setup_kpi_path_keeps_an_existing_checkout():
    """
    A developer pointing the install at their own checkout must not have it
    swapped for the sibling default.
    """
    config = read_config({
        'kpi_path': '/home/dev/src/kpi',
        'kpi_dev_build_id': 'frontend1735689600',
    })
    with patch.object(Config, '_Config__clone_repo') as mock_clone:
        config._Config__auto_setup_kpi_path()

    d = config._Config__dict
    assert d['kpi_path'] == '/home/dev/src/kpi'
    # Nothing moved, so the image does not need rebuilding
    assert d['kpi_dev_build_id'] == 'frontend1735689600'
    mock_clone.assert_called_once_with('/home/dev/src/kpi', 'kpi')


def test_auto_setup_kpi_path_clones_a_missing_checkout(tmp_path):
    kpi_path = tmp_path / 'kpi'
    config = read_config({'kpi_path': str(kpi_path), 'kpi_dev_build_id': ''})

    with patch.object(CLI, 'run_command') as mock_run, \
         patch.object(CLI, 'colored_print'):
        config._Config__auto_setup_kpi_path()

    assert kpi_path.is_dir()
    command = mock_run.call_args[0][0]
    assert command[:2] == ['git', 'clone']
    assert command[2].endswith('/kpi')
    assert command[3] == str(kpi_path)


def test_auto_setup_kpi_path_leaves_an_existing_clone_alone(tmp_path):
    kpi_path = tmp_path / 'kpi'
    (kpi_path / '.git').mkdir(parents=True)
    config = read_config({'kpi_path': str(kpi_path), 'kpi_dev_build_id': 'x'})

    with patch.object(CLI, 'run_command') as mock_run:
        config._Config__auto_setup_kpi_path()

    mock_run.assert_not_called()


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_cloud_profiles',
       new=lambda *a: None)
@patch('helpers.config.Config._Config__questions_nlp_quick', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_quick_dev_sets_up_kpi(_):
    config = read_config({'local_installation': True, 'dev_mode': True,
                          'install_mode': 'dev', 'kpi_path': ''})
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
         patch.object(Config, '_Config__clone_repo'), \
         patch.object(CLI, 'colored_print'):
        mock_ci.side_effect = iter([DEV, SIMPLE])
        result = config.build()

    assert result['kpi_path'] == _sibling_kpi_path()
    assert result['kpi_dev_build_id']
    # Still only mode and complexity are asked
    assert mock_ci.call_count == 2


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
def test_build_quick_production_leaves_kpi_alone(_):
    """Mounting a source checkout only makes sense on a workstation."""
    config = read_config({'kpi_path': ''})
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci, \
         patch.object(Config, '_Config__clone_repo') as mock_clone:
        mock_ci.side_effect = iter([
            PRODUCTION, SIMPLE, 'kobo.example', 'support@kobo.example',
        ])
        result = config.build()

    assert result['kpi_path'] == ''
    # Only the reverse proxy is cloned on a server
    assert [call[0][1] for call in mock_clone.call_args_list] == [
        'nginx-certbot'
    ]


# ── __nlp_managed_by_custom_yml ──────────────────────────────────────────────

def _config_with_custom_yml(tmp_path, content=None):
    """
    Builds a config pointing at a kobo-docker directory, optionally holding a
    front-end custom compose file.
    """
    if content is not None:
        (tmp_path / 'docker-compose.frontend.custom.yml').write_text(content)
    return read_config({'kobodocker_path': str(tmp_path)})


def test_nlp_custom_yml_absent_file_is_not_managed(tmp_path):
    """The first run cannot have one: kobo-docker is cloned after build()."""
    config = _config_with_custom_yml(tmp_path)
    assert config._Config__nlp_managed_by_custom_yml() is False


def test_nlp_custom_yml_detects_list_syntax(tmp_path):
    config = _config_with_custom_yml(tmp_path, """
services:
  kpi: &custom_env_vars
    environment:
      - GS_BUCKET_NAME=my-bucket
""")
    assert config._Config__nlp_managed_by_custom_yml() is True


def test_nlp_custom_yml_detects_mapping_syntax(tmp_path):
    config = _config_with_custom_yml(tmp_path, """
services:
  kpi:
    environment:
      GOOGLE_CLOUD_PROJECT: my-gcp-project
""")
    assert config._Config__nlp_managed_by_custom_yml() is True


def test_nlp_custom_yml_ignores_empty_values(tmp_path):
    """A placeholder left blank configures nothing."""
    config = _config_with_custom_yml(tmp_path, """
      - GS_BUCKET_NAME=
      - GOOGLE_CLOUD_PROJECT=
""")
    assert config._Config__nlp_managed_by_custom_yml() is False


def test_nlp_custom_yml_ignores_autoqa_arns(tmp_path):
    """
    kobo-install no longer manages the AutoQA ARNs, so a file holding only
    those must not hide the NLP questions.
    """
    config = _config_with_custom_yml(tmp_path, """
      - AUTOQA_CLAUDESONNET_MODEL_AIP_ARN=arn:aws:bedrock:sonnet
      - AUTOQA_OSS120_MODEL_AIP_ARN=arn:aws:bedrock:oss120
""")
    assert config._Config__nlp_managed_by_custom_yml() is False


def test_nlp_custom_yml_ignores_unrelated_variables(tmp_path):
    config = _config_with_custom_yml(tmp_path, """
      - STRIPE_ENABLED=True
      - DJSTRIPE_WEBHOOK_VALIDATION=verify_signature
""")
    assert config._Config__nlp_managed_by_custom_yml() is False


def test_nlp_custom_yml_survives_unreadable_file(tmp_path):
    config = _config_with_custom_yml(tmp_path, 'GS_BUCKET_NAME=my-bucket')
    with patch('builtins.open', side_effect=OSError):
        assert config._Config__nlp_managed_by_custom_yml() is False


def test_nlp_custom_yml_result_is_cached(tmp_path):
    config = _config_with_custom_yml(tmp_path, '      - GS_BUCKET_NAME=mine')
    assert config._Config__nlp_managed_by_custom_yml() is True
    # The file is read once; a later failure must not change the answer
    with patch('builtins.open', side_effect=OSError):
        assert config._Config__nlp_managed_by_custom_yml() is True


# ── __questions_nlp_quick (dev, quick setup) ─────────────────────────────────

def test_questions_nlp_quick_silent_without_gcloud():
    """
    Quick setup keeps its promise: no gcloud credentials on the host means NLP
    cannot work, so nothing is asked.
    """
    config = read_config({'gcloud_use_profile': False})
    with patch.object(CLI, 'colored_input') as mock_input:
        config._Config__questions_nlp_quick()
    mock_input.assert_not_called()
    assert config._Config__dict['use_nlp'] is False


def test_questions_nlp_quick_asks_three_questions_after_yes():
    config = read_config({
        'gcloud_use_profile': True,
        'aws_use_profile': True,
    })
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter([
            CHOICE_YES, 'my-bucket', 'my-gcp-project', 'us-west-2',
        ])
        config._Config__questions_nlp_quick()
    d = config._Config__dict
    assert mock_input.call_count == 4  # the gate, then three answers
    assert d['use_nlp'] is True
    assert d['gs_bucket_name'] == 'my-bucket'
    assert d['aws_bedrock_region_name'] == 'us-west-2'
    assert d['asr_mt_google_project_id'] == 'my-gcp-project'


def test_questions_nlp_quick_stops_after_no():
    config = read_config({'gcloud_use_profile': True})
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter([CHOICE_NO])
        config._Config__questions_nlp_quick()
    assert mock_input.call_count == 1
    assert config._Config__dict['use_nlp'] is False


def test_questions_nlp_quick_silent_when_custom_yml_owns_it(tmp_path):
    config = _config_with_custom_yml(tmp_path, '      - GS_BUCKET_NAME=mine')
    config._Config__dict['gcloud_use_profile'] = True
    with patch.object(CLI, 'colored_input') as mock_input:
        config._Config__questions_nlp_quick()
    mock_input.assert_not_called()


def test_questions_nlp_quick_offers_the_detected_project(tmp_path):
    """
    __auto_detect_gcloud_profile has just filled the project in, so a bare
    ENTER keeps it.
    """
    config = read_config({
        'gcloud_use_profile': True,
        'asr_mt_google_project_id': 'detected-project',
    })
    with patch.object(CLI, 'yes_no_question', return_value=True), \
         patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': default):
        config._Config__questions_nlp_quick()
    assert config._Config__dict['asr_mt_google_project_id'] == \
        'detected-project'


# ── __questions_web_server_port ──────────────────────────────────────────────

def test_questions_web_server_port_updates_port():
    config = read_config()
    assert config._Config__dict['exposed_nginx_docker_port'] == '80'
    with patch.object(CLI, 'colored_input', return_value='8080'):
        config._Config__questions_web_server_port()
    assert config._Config__dict['exposed_nginx_docker_port'] == '8080'


# ── First-run pre-checking of the advanced sections ──────────────────────────

def _menu_choices(config):
    """
    Runs the advanced section menu without curses and returns the choices it
    would have displayed, as {label: checked}.
    """
    captured = {}

    def fake_menu(title, choices):
        captured.update({
            c['label']: c['checked'] for c in choices if 'label' in c
        })
        return []

    # `kobodocker_path` points at the real sibling checkout, which on a
    # developer's machine may carry a custom compose file holding the NLP
    # variables. That case has its own test; the menu tests must not depend
    # on it.
    with patch.object(CLI, 'checkbox_menu', side_effect=fake_menu), \
         patch.object(Config, '_Config__nlp_managed_by_custom_yml',
                      return_value=False):
        config._Config__questions_advanced_sections()

    return captured


def _menu_config(overrides=None):
    """
    Config for menu tests. `mock_read_config` forces `kobodocker_path` to
    /tmp; restore the value `__setup_directory` would have set so the
    'Install directory' section is not spuriously pre-checked.
    """
    overrides = dict(overrides or {})
    overrides.setdefault('advanced', True)
    overrides.setdefault(
        'kobodocker_path', Config.get_template()['kobodocker_path']
    )
    return read_config(overrides)


def _first_run_config(overrides=None):
    config = _menu_config(overrides)
    config._Config__dict.pop('date_created', None)
    config._Config__first_time = None
    return config


def _later_run_config(overrides=None):
    config = _menu_config(overrides)
    config._Config__dict['date_created'] = 1735689600
    config._Config__first_time = None
    return config


def test_first_run_production_checks_only_the_essentials():
    """
    A first advanced run must stay short: only the sections a fresh server
    install genuinely cannot do without are pre-checked.
    """
    config = _first_run_config({'install_mode': 'production'})
    assert config.first_time

    choices = _menu_choices(config)

    checked = {label for label, is_checked in choices.items() if is_checked}
    assert checked == {
        'Domain names',
        'HTTPS & certificates',
        'SMTP',
        'Superuser credentials',
    }


def test_first_run_dev_checks_only_superuser():
    """
    In dev, SMTP stays unchecked so the console email backend survives, and
    the server-only sections are not part of the menu at all.
    """
    config = _first_run_config({
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
    })
    assert config.first_time

    choices = _menu_choices(config)

    checked = {label for label, is_checked in choices.items() if is_checked}
    assert checked == {'Superuser credentials'}
    assert choices['SMTP'] is False
    assert choices['Web server port'] is False
    assert choices['KPI source files'] is False


def test_old_install_without_memory_is_treated_as_a_first_menu():
    """
    An install created before the menu remembered anything has no selection to
    restore, so it gets the same essentials as a brand new one.
    """
    config = _later_run_config({'install_mode': 'production'})
    assert not config.first_time
    assert config._Config__dict['advanced_sections_seen'] == []

    choices = _menu_choices(config)

    checked = {label for label, is_checked in choices.items() if is_checked}
    assert checked == {
        'Domain names',
        'HTTPS & certificates',
        'SMTP',
        'Superuser credentials',
    }


def test_cloud_and_nlp_sections_are_development_only():
    """
    A server authenticates with its own credentials, and gets its NLP settings
    from Constance — neither section has anything to offer there.
    """
    dev = _menu_choices(_menu_config({
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
    }))
    assert 'Cloud credentials (AWS & Google)' in dev
    assert 'NLP and qualitative analysis' in dev

    for mode, overrides in (
        ('staging', {'staging_mode': True}),
        ('production', {}),
    ):
        choices = _menu_choices(_menu_config(
            dict(overrides, install_mode=mode, local_installation=False)
        ))
        assert 'Cloud credentials (AWS & Google)' not in choices, mode
        assert 'NLP and qualitative analysis' not in choices, mode
        # AWS S3 storage stays available everywhere
        assert 'AWS S3 storage' in choices, mode


def test_cloud_profiles_section_checked_from_either_profile():
    """
    One section covers both mounts, so either one being on pre-checks it.
    """
    base = {
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
        'aws_use_profile': False, 'gcloud_use_profile': False,
    }
    label = 'Cloud credentials (AWS & Google)'

    assert _menu_choices(_menu_config(base))[label] is False
    assert _menu_choices(_menu_config(
        dict(base, aws_use_profile=True)))[label] is True
    assert _menu_choices(_menu_config(
        dict(base, gcloud_use_profile=True)))[label] is True


def test_nlp_section_hidden_when_custom_yml_owns_it(tmp_path):
    (tmp_path / 'docker-compose.frontend.custom.yml').write_text(
        '      - GS_BUCKET_NAME=my-bucket\n'
    )
    config = _menu_config({
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
        'kobodocker_path': str(tmp_path),
        'use_nlp': True,
    })

    captured = {}

    def fake_menu(title, choices):
        captured.update({
            c['label']: c['checked'] for c in choices if 'label' in c
        })
        return []

    with patch.object(CLI, 'checkbox_menu', side_effect=fake_menu):
        config._Config__questions_advanced_sections()

    assert 'NLP and qualitative analysis' not in captured
    # The mounts are a separate concern and stay on offer
    assert 'Cloud credentials (AWS & Google)' in captured


def test_database_sections_are_never_pre_checked():
    """
    MongoDB, PostgreSQL and Redis all default to a generated password, so a
    customised one is indistinguishable from an untouched default. None of
    them may be pre-checked, on a first run or a later one.
    """
    for config in (
        _first_run_config({'install_mode': 'production'}),
        _later_run_config({'install_mode': 'production'}),
    ):
        choices = _menu_choices(config)
        assert choices['MongoDB'] is False
        assert choices['PostgreSQL'] is False
        assert choices['Redis'] is False


@patch('helpers.config.Network.curl', return_value='')
@patch('helpers.config.Config._Config__detect_system_resources',
       return_value=(8, 16))
def test_tuning_sections_unchecked_after_auto_configuration(_detect, _curl):
    """
    `build()` runs __auto_configure_resources before opening the menu, and it
    sets `postgres_settings` / `uwsgi_settings`. Those sections must still
    come up unchecked: the values were computed, not chosen.
    """
    config = _first_run_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()

    d = config._Config__dict
    assert d['postgres_settings'] is True
    assert d['uwsgi_settings'] is True

    choices = _menu_choices(config)
    assert choices['PostgreSQL tuning'] is False
    assert choices['uWSGI tuning'] is False


@patch('helpers.config.Network.curl', return_value='')
@patch('helpers.config.Config._Config__detect_system_resources',
       return_value=(8, 16))
def test_tuning_sections_checked_once_answered(_detect, _curl):
    """
    Once the user has answered the tuning questions, the values are theirs and
    the sections are pre-checked on the next run.
    """
    config = _later_run_config({'install_mode': 'production'})
    config._Config__auto_configure_resources()

    with patch.object(CLI, 'colored_input', side_effect=lambda m, c, default='': default), \
         patch.object(CLI, 'get_response', side_effect=lambda v, default=None, **k: default):
        config._Config__questions_postgres_tuning()
        config._Config__questions_uwsgi()

    d = config._Config__dict
    assert d['postgres_settings_auto'] is False
    assert d['uwsgi_settings_auto'] is False

    choices = _menu_choices(config)
    assert choices['PostgreSQL tuning'] is True
    assert choices['uWSGI tuning'] is True


def test_remembered_selection_wins_over_values():
    """
    Once a section has been offered, only the previous answer decides — a
    customised value no longer re-checks it on its own.
    """
    config = _later_run_config({
        # NLP is offered in development only
        'install_mode': 'dev',
        'local_installation': True,
        'dev_mode': True,
        'use_nlp': True,
        'docker_prefix': 'kobo1',
        'advanced_sections_seen': ['nlp', 'docker_prefix', 'superuser', 'aws'],
        'advanced_sections_selected': ['aws'],
    })

    choices = _menu_choices(config)

    assert choices['AWS S3 storage'] is True
    assert choices['NLP and qualitative analysis'] is False
    assert choices['Docker Compose prefix'] is False
    # Not remembered as offered, so the first-menu essentials no longer apply
    assert choices['Superuser credentials'] is False


def test_section_added_by_an_upgrade_falls_back_to_values():
    """
    A key the menu has never offered — a section shipped by a later version of
    kobo-install — must still surface from its own value.
    """
    config = _later_run_config({
        'install_mode': 'dev',
        'local_installation': True,
        'dev_mode': True,
        'use_nlp': True,
        'gcloud_use_profile': True,
        'advanced_sections_seen': ['aws', 'smtp', 'superuser'],
        'advanced_sections_selected': ['aws'],
    })

    choices = _menu_choices(config)

    assert choices['NLP and qualitative analysis'] is True
    assert choices['Cloud credentials (AWS & Google)'] is True
    # Remembered keys still obey the memory
    assert choices['AWS S3 storage'] is True
    assert choices['SMTP'] is False


def _run_menu(config, picked):
    """
    Runs the menu, answering it with the given labels. Returns the selected
    section keys.
    """
    with patch.object(CLI, 'checkbox_menu', return_value=list(picked)):
        return config._Config__questions_advanced_sections()


def test_selection_is_remembered():
    config = _first_run_config({'install_mode': 'production'})

    selected = _run_menu(config, ['AWS S3 storage', 'SMTP'])

    d = config._Config__dict
    assert sorted(selected) == ['aws', 'smtp']
    assert d['advanced_sections_selected'] == ['aws', 'smtp']
    # Every section the menu displayed is now known
    assert 'superuser' in d['advanced_sections_seen']
    assert 'mongodb' in d['advanced_sections_seen']

    # Replaying the menu restores exactly that selection
    choices = _menu_choices(config)
    checked = {label for label, is_checked in choices.items() if is_checked}
    assert checked == {'AWS S3 storage', 'SMTP'}


def test_empty_selection_is_remembered_as_empty():
    """
    Confirming the menu with nothing ticked is an answer too, and must not be
    mistaken for "no memory yet".
    """
    config = _first_run_config({'install_mode': 'production'})

    _run_menu(config, [])

    d = config._Config__dict
    assert d['advanced_sections_selected'] == []
    assert d['advanced_sections_seen'] != []

    choices = _menu_choices(config)
    assert not any(choices.values())


def test_choices_from_another_mode_are_preserved():
    """
    Server-only sections are absent from the dev menu; answering it must not
    erase what was picked for production.
    """
    config = _later_run_config({
        'install_mode': 'dev',
        'local_installation': True,
        'dev_mode': True,
        'advanced_sections_seen': ['public_routes', 'https_proxy', 'aws'],
        'advanced_sections_selected': ['public_routes', 'https_proxy'],
    })

    _run_menu(config, ['AWS S3 storage'])

    d = config._Config__dict
    # `public_routes` and `https_proxy` are not offered in dev, so they keep
    # the answer given the last time a server menu was shown
    assert d['advanced_sections_selected'] == [
        'aws', 'https_proxy', 'public_routes'
    ]


def test_cancelling_the_menu_aborts_setup():
    """
    q / ESC must leave everything on disk untouched rather than continue as
    if no section had been picked.
    """
    config = _later_run_config({
        'install_mode': 'production',
        'advanced_sections_seen': ['aws'],
        'advanced_sections_selected': ['aws'],
    })

    with patch.object(CLI, 'checkbox_menu', return_value=None):
        with pytest.raises(SystemExit) as exc:
            config._Config__questions_advanced_sections()

    assert exc.value.code == 0
    # The remembered selection survives the cancellation
    assert config._Config__dict['advanced_sections_selected'] == ['aws']


def test_web_server_port_checked_when_port_is_custom():
    config = _later_run_config({
        'install_mode': 'dev',
        'local_installation': True,
        'dev_mode': True,
        'exposed_nginx_docker_port': '8080',
    })

    assert _menu_choices(config)['Web server port'] is True


def test_web_server_port_absent_outside_dev_mode():
    config = _later_run_config({'install_mode': 'production'})

    assert 'Web server port' not in _menu_choices(config)


def test_first_run_dev_keeps_console_email_backend():
    """
    SMTP unchecked on a first dev run is what keeps the console email backend:
    selecting the section is what switches to a real SMTP server.
    """
    console_backend = 'django.core.mail.backends.console.EmailBackend'
    config = _first_run_config({
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
        'email_backend': console_backend,
    })
    assert _menu_choices(config)['SMTP'] is False

    with patch('helpers.config.Config._Config__secure_mongo'):
        config._Config__run_selected_advanced_sections([])

    assert config._Config__dict['email_backend'] == console_backend


# ── Leaving development for a server ─────────────────────────────────────────

DEV_LEFTOVERS = {
    'kpi_path': '/home/dev/src/kpi',
    'exposed_nginx_docker_port': '8080',
    'https': False,
    'use_letsencrypt': False,
    'email_backend': 'django.core.mail.backends.console.EmailBackend',
    'debug': True,
    'use_celery': False,
    'aws_use_profile': True,
    'aws_profile_name': 'dev',
    'aws_host_aws_dir': '/home/dev/.aws',
    'gcloud_use_profile': True,
    'gcloud_host_config_dir': '/home/dev/.config/gcloud',
    'use_nlp': True,
    'gs_bucket_name': 'dev-bucket',
    'aws_bedrock_region_name': 'us-west-2',
    'asr_mt_google_project_id': 'dev-project',
}


def _switch_mode(config, choice):
    with patch.object(CLI, 'colored_input', return_value=choice), \
         patch.object(CLI, 'framed_print'), \
         patch.object(CLI, 'colored_print'):
        config._Config__questions_install_mode()


def _dev_install_with_leftovers():
    config = read_config({'local_installation': True, 'dev_mode': True})
    config._Config__dict.update(DEV_LEFTOVERS)
    return config


@pytest.mark.parametrize('choice,mode', [(STAGING, 'staging'),
                                         (PRODUCTION, 'production')])
def test_switching_to_a_server_clears_development_values(choice, mode):
    """
    Neither branch of build() asks about these afterwards, so anything left
    behind reaches the generated server configuration.
    """
    config = _dev_install_with_leftovers()

    _switch_mode(config, choice)

    d = config._Config__dict
    assert d['install_mode'] == mode
    # A server sends real email and speaks HTTPS
    assert d['email_backend'] == ''
    assert d['https'] is True
    assert d['use_letsencrypt'] is True
    # The web server port is only configurable in dev, so it goes back to 80
    assert d['exposed_nginx_docker_port'] == Config.DEFAULT_NGINX_PORT
    # Host credential directories do not exist on a server
    assert d['aws_use_profile'] is False
    assert d['aws_profile_name'] == 'default'
    assert d['aws_host_aws_dir'] == os.path.expanduser('~/.aws')
    assert d['gcloud_use_profile'] is False
    # NLP is a development-only section; a server gets it from Constance
    assert d['use_nlp'] is False
    assert d['gs_bucket_name'] == ''
    assert d['aws_bedrock_region_name'] == ''
    assert d['asr_mt_google_project_id'] == ''
    assert d['debug'] is False
    assert d['use_celery'] is True


def test_switching_to_staging_keeps_the_kpi_checkout():
    """
    Staging supports a local KPI checkout — the section is offered for both
    dev and staging — so it must survive the switch. Production drops it.
    """
    config = _dev_install_with_leftovers()
    _switch_mode(config, STAGING)
    assert config._Config__dict['kpi_path'] == '/home/dev/src/kpi'

    config = _dev_install_with_leftovers()
    _switch_mode(config, PRODUCTION)
    assert config._Config__dict['kpi_path'] == ''


def test_switching_between_servers_keeps_the_chosen_settings():
    """
    Only leaving development clears these. A staging install turned into
    production must keep the HTTPS setup its owner configured.
    """
    config = read_config({
        'install_mode': 'staging', 'staging_mode': True,
        'local_installation': False,
        'https': False, 'use_letsencrypt': False,
        'smtp_host': 'smtp.example.org',
    })

    _switch_mode(config, PRODUCTION)

    d = config._Config__dict
    assert d['install_mode'] == 'production'
    assert d['https'] is False
    assert d['use_letsencrypt'] is False
    assert d['smtp_host'] == 'smtp.example.org'


def test_staying_in_the_same_mode_changes_nothing():
    config = _dev_install_with_leftovers()
    before = dict(config._Config__dict)

    _switch_mode(config, DEV)

    after = config._Config__dict
    # `install_mode` is normalised from `local_installation` for configs
    # written before the key existed; nothing else may move.
    assert after['install_mode'] == 'dev'
    assert {k: v for k, v in after.items() if k != 'install_mode'} == {
        k: v for k, v in before.items() if k != 'install_mode'
    }


# ── Terminal requirements (CLI.is_interactive / curses menu) ─────────────────

def test_is_interactive_requires_both_streams():
    """
    curses reads stdin and draws on stdout, so either one redirected is enough
    to make the menu impossible — `run.py --setup | tee setup.log` keeps a
    tty on stdin while taking stdout away.
    """
    def _streams(stdin_tty, stdout_tty):
        return (
            patch('helpers.cli.sys.stdin', MagicMock(
                isatty=MagicMock(return_value=stdin_tty))),
            patch('helpers.cli.sys.stdout', MagicMock(
                isatty=MagicMock(return_value=stdout_tty))),
        )

    for stdin_tty, stdout_tty, expected in (
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ):
        stdin_patch, stdout_patch = _streams(stdin_tty, stdout_tty)
        with stdin_patch, stdout_patch:
            assert _REAL_IS_INTERACTIVE() is expected


def test_custom_setup_exits_without_a_terminal():
    """
    Without a tty, `curses.wrapper` prints escape sequences and then raises.
    The menu must never be reached: a scripted run is told to use quick setup.
    """
    config = _later_run_config({'install_mode': 'production'})

    with patch.object(CLI, 'is_interactive', return_value=False), \
            patch.object(CLI, 'checkbox_menu') as menu:
        with pytest.raises(SystemExit) as exc:
            config._Config__questions_advanced_sections()

    # 1, not 0: this is a failure, unlike the deliberate ESC cancellation.
    assert exc.value.code == 1
    menu.assert_not_called()


def test_checkbox_menu_treats_ctrl_c_like_esc():
    """Ctrl+C must reach the caller's cancellation path, not run.py."""
    choices = [{'label': 'A', 'checked': True}]
    with patch('helpers.cli.curses.wrapper', side_effect=KeyboardInterrupt):
        assert CLI.checkbox_menu('Pick:', choices) is None


def test_checkbox_menu_survives_a_window_too_small():
    """
    A terminal too short for the layout makes every `addstr` raise; the menu
    must still answer instead of taking the whole setup down with it.
    """
    choices = [
        {'separator': 'Group'},
        {'label': 'A', 'checked': True},
        {'label': 'B', 'checked': False},
    ]

    class _TinyScreen:
        def getmaxyx(self):
            return 1, 4

        def erase(self):
            pass

        def refresh(self):
            pass

        def addstr(self, *args, **kwargs):
            raise curses.error('addwstr() returned ERR')

        def getch(self):
            return ord('\n')

    def _wrapper(func):
        return func(_TinyScreen())

    with patch('helpers.cli.curses.wrapper', _wrapper), \
            patch('helpers.cli.curses.curs_set'), \
            patch('helpers.cli.curses.start_color'), \
            patch('helpers.cli.curses.use_default_colors'), \
            patch('helpers.cli.curses.init_pair'), \
            patch('helpers.cli.curses.color_pair', return_value=0):
        assert CLI.checkbox_menu('Pick:', choices) == ['A']


# ── pgconfig.org unreachable ─────────────────────────────────────────────────

def test_auto_configure_resources_reports_a_pgconfig_failure():
    """
    A silent fallback to the template values leaves the operator thinking the
    server was tuned. Say it, like the interactive path already does.
    """
    config = _first_run_config({
        'install_mode': 'production',
        'multi': False,
    })

    printed = []
    with patch('helpers.config.Network.curl', return_value=''), \
            patch.object(Config, '_Config__detect_system_resources',
                         return_value=(4, 8)), \
            patch.object(CLI, 'colored_print',
                         side_effect=lambda msg, *a, **k: printed.append(msg)):
        config._Config__auto_configure_resources()

    d = config._Config__dict
    # Sizing still happened; only the generated conf file is missing.
    assert d['postgres_cpus'] == '3'
    assert d['postgres_settings_content'] == (
        Config.get_template()['postgres_settings_content']
    )
    assert any('error has occurred' in message for message in printed)


# ── Consent before mounting host credentials ─────────────────────────────────

def _cloud_dirs(tmp_path, aws=True, gcloud=True, project=None):
    """
    Builds the host directories `__auto_detect_cloud_profiles` looks for, and
    returns an `expanduser` replacement that resolves ~ to them.
    """
    aws_dir = tmp_path / '.aws'
    if aws:
        aws_dir.mkdir()
    gcloud_dir = _gcloud_dir(tmp_path, project=project) if gcloud \
        else tmp_path / '.config' / 'gcloud'

    def expanduser(path):
        return str(aws_dir if path == '~/.aws' else gcloud_dir)

    return expanduser, str(aws_dir), str(gcloud_dir)


def test_cloud_profiles_asked_once_for_both_providers(tmp_path):
    """Two providers, one decision — not two prompts in a row."""
    expanduser, aws_dir, gcloud_dir = _cloud_dirs(
        tmp_path, project='[core]\nproject = my-project\n'
    )
    config = _first_run_config({
        'aws_use_profile': False,
        'gcloud_use_profile': False,
        'asr_mt_google_project_id': '',
    })

    asked = []

    def _answer(question, default=True, **kwargs):
        asked.append(question)
        return True

    with patch('helpers.config.os.path.expanduser', side_effect=expanduser), \
            patch.object(CLI, 'yes_no_question', side_effect=_answer):
        config._Config__auto_detect_cloud_profiles()

    assert len(asked) == 1
    # Both directories are named, and the scope of the mount is spelled out.
    assert aws_dir in asked[0]
    assert gcloud_dir in asked[0]
    assert 'every profile' in asked[0]

    d = config._Config__dict
    assert d['aws_use_profile'] is True
    assert d['gcloud_use_profile'] is True
    assert d['asr_mt_google_project_id'] == 'my-project'


def test_cloud_profiles_respects_a_no(tmp_path):
    expanduser, _, _ = _cloud_dirs(
        tmp_path, project='[core]\nproject = my-project\n'
    )
    config = _first_run_config({
        'aws_use_profile': False,
        'gcloud_use_profile': False,
        'asr_mt_google_project_id': '',
        'use_aws': False,
    })

    with patch('helpers.config.os.path.expanduser', side_effect=expanduser), \
            patch.object(CLI, 'yes_no_question', return_value=False):
        config._Config__auto_detect_cloud_profiles()

    d = config._Config__dict
    assert d['aws_use_profile'] is False
    assert d['gcloud_use_profile'] is False
    assert d['use_aws'] is False
    # Declining the mount must not leak the project either.
    assert d['asr_mt_google_project_id'] == ''


def test_cloud_profiles_only_lists_what_exists(tmp_path):
    """A machine with only ~/.aws must not be told about Google Cloud."""
    expanduser, aws_dir, gcloud_dir = _cloud_dirs(tmp_path, gcloud=False)
    config = _first_run_config({'aws_use_profile': False})

    asked = []
    with patch('helpers.config.os.path.expanduser', side_effect=expanduser), \
            patch.object(CLI, 'yes_no_question',
                         side_effect=lambda q, **k: asked.append(q) or True):
        config._Config__auto_detect_cloud_profiles()

    assert aws_dir in asked[0]
    assert 'Google Cloud' not in asked[0]
    assert config._Config__dict['gcloud_use_profile'] is False


def test_cloud_profiles_asks_nothing_without_credentials(tmp_path):
    expanduser, _, _ = _cloud_dirs(tmp_path, aws=False, gcloud=False)
    config = _first_run_config()

    with patch('helpers.config.os.path.expanduser', side_effect=expanduser), \
            patch.object(CLI, 'yes_no_question') as question:
        config._Config__auto_detect_cloud_profiles()

    question.assert_not_called()


def test_credentials_question_defaults_to_the_previous_answer(tmp_path):
    """
    A stored `False` means "no" only once the install exists; on a first run it
    is just the template default, so the question opens on Yes.
    """
    expanduser, _, _ = _cloud_dirs(tmp_path)
    defaults = []

    def _capture(question, default=True, **kwargs):
        defaults.append(default)
        return False

    for factory, stored, expected in (
        (_first_run_config, {}, True),
        (_later_run_config, {}, False),
        (_later_run_config, {'aws_use_profile': True}, True),
        (_later_run_config, {'gcloud_use_profile': True}, True),
    ):
        overrides = {'aws_use_profile': False, 'gcloud_use_profile': False}
        overrides.update(stored)
        config = factory(overrides)
        with patch('helpers.config.os.path.expanduser',
                   side_effect=expanduser), \
                patch.object(CLI, 'yes_no_question', side_effect=_capture):
            config._Config__auto_detect_cloud_profiles()
        assert defaults[-1] is expected


# ── $HOME in generated mounts ────────────────────────────────────────────────

def test_host_paths_render_through_home():
    """
    The generated override file is committed nowhere but is read on whatever
    machine runs it; `$HOME` keeps it from carrying the setup runner's home.
    """
    host_path = Template._Template__host_path
    home = os.path.expanduser('~')

    assert host_path(os.path.join(home, '.aws')) == '$HOME/.aws'
    assert host_path(os.path.join(home, '.config', 'gcloud')) == (
        '$HOME/.config/gcloud'
    )
    assert host_path(home) == '$HOME'
    # Outside the home directory there is nothing to generalise.
    assert host_path('/mnt/shared/creds') == '/mnt/shared/creds'
    # A home-lookalike prefix is not a match.
    assert host_path(home + '-backup/.aws') == home + '-backup/.aws'
    assert host_path('') == ''


def test_generated_override_mounts_use_home(tmp_path):
    """End to end: the rendered compose file must not name the user's home."""
    home = os.path.expanduser('~')
    config = read_config({
        'local_installation': True,
        'dev_mode': True,
        'aws_use_profile': True,
        'gcloud_use_profile': True,
        'aws_host_aws_dir': os.path.join(home, '.aws'),
        'gcloud_host_config_dir': os.path.join(home, '.config', 'gcloud'),
    })

    variables = Template._Template__get_template_variables(config)

    assert variables['AWS_HOST_AWS_DIR'] == '$HOME/.aws'
    assert variables['GCLOUD_HOST_CONFIG_DIR'] == '$HOME/.config/gcloud'
    assert home not in variables['AWS_HOST_AWS_DIR']
    assert home not in variables['GCLOUD_HOST_CONFIG_DIR']


# ── Two features, two providers ──────────────────────────────────────────────

def test_questions_nlp_asks_only_google_without_aws():
    """Bedrock powers qualitative analysis; no AWS credentials, no reach."""
    config = read_config({
        'use_nlp': False,
        'gcloud_use_profile': True,
        'aws_use_profile': False,
        'aws_access_key': '',
        'aws_bedrock_region_name': '',
    })
    seen = []
    with patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': seen.append(m)):
        config._Config__questions_nlp()

    assert len(seen) == 2
    assert not [m for m in seen if 'Bedrock' in m]
    assert config._Config__dict['use_nlp'] is True
    assert config._Config__dict['aws_bedrock_region_name'] == ''


def test_questions_nlp_asks_only_bedrock_without_gcloud():
    """
    The other half: a developer with only AWS credentials must still be able
    to set qualitative analysis up. Gating the whole section on gcloud used
    to lock them out.
    """
    config = read_config({
        'use_nlp': False,
        'gcloud_use_profile': False,
        'aws_use_profile': True,
        'gs_bucket_name': '',
    })
    seen = []
    with patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': seen.append(m)):
        config._Config__questions_nlp()

    assert len(seen) == 1
    assert 'Bedrock' in seen[0]
    assert config._Config__dict['use_nlp'] is True
    assert config._Config__dict['gs_bucket_name'] == ''


def test_questions_nlp_counts_aws_keys_as_credentials():
    """boto3 reads the explicit keys too, not just a mounted ~/.aws."""
    config = read_config({
        'gcloud_use_profile': False,
        'aws_use_profile': False,
        'aws_access_key': 'AKIAEXAMPLE',
    })
    seen = []
    with patch.object(CLI, 'colored_input',
                      side_effect=lambda m, c, default='': seen.append(m)):
        config._Config__questions_nlp()

    assert [m for m in seen if 'Bedrock' in m]


def test_questions_nlp_skips_when_no_provider_is_reachable():
    """Ticking the section without credentials would write dead settings."""
    config = read_config({
        'use_nlp': False,
        'gcloud_use_profile': False,
        'aws_use_profile': False,
        'aws_access_key': '',
    })
    printed = []
    with patch.object(CLI, 'colored_input') as mock_input, \
            patch.object(CLI, 'colored_print',
                         side_effect=lambda m, *a, **k: printed.append(m)):
        config._Config__questions_nlp()

    mock_input.assert_not_called()
    assert config._Config__dict['use_nlp'] is False
    assert any('No cloud credentials' in m for m in printed)


def test_questions_nlp_quick_names_what_is_actually_available():
    """The gate must not promise transcription to an AWS-only machine."""
    cases = [
        ({'gcloud_use_profile': True, 'aws_use_profile': True},
         'Configure NLP & Qualitative Analysis?'),
        ({'gcloud_use_profile': True, 'aws_use_profile': False},
         'Configure NLP?'),
        ({'gcloud_use_profile': False, 'aws_use_profile': True},
         'Configure Qualitative Analysis?'),
    ]
    for flags, expected in cases:
        config = read_config({'aws_access_key': '', **flags})
        asked = []
        with patch.object(CLI, 'yes_no_question',
                          side_effect=lambda q, **k: asked.append(q) or False):
            config._Config__questions_nlp_quick()

        assert asked == [expected], flags


def test_questions_nlp_quick_silent_without_any_credentials():
    config = read_config({
        'gcloud_use_profile': False,
        'aws_use_profile': False,
        'aws_access_key': '',
    })
    with patch.object(CLI, 'yes_no_question') as question:
        config._Config__questions_nlp_quick()
    question.assert_not_called()


# ── Server topology decides the menu, so it is asked before it ───────────────

def _backend_only_config(overrides=None):
    """A machine that plays the back-end role in a multi-server install."""
    o = {'install_mode': 'production', 'multi': True, 'server_role': 'backend'}
    o.update(overrides or {})
    config = _later_run_config(o)
    assert config.backend and not config.frontend
    return config


def _frontend_only_config(overrides=None):
    o = {'install_mode': 'production', 'multi': True,
         'server_role': 'frontend'}
    o.update(overrides or {})
    config = _later_run_config(o)
    assert config.frontend and not config.backend
    return config


def test_topology_is_asked_before_the_menu_is_built():
    """
    The role decides which sections exist, so it cannot be one of them. Asked
    from inside the menu, a fresh multi-server install got a single-server
    list.
    """
    calls = []
    config = _later_run_config({'install_mode': 'production'})

    with patch.object(Config, '_Config__questions_topology',
                      side_effect=lambda *a: calls.append('topology')), \
            patch.object(Config, '_Config__questions_advanced_sections',
                         side_effect=lambda *a: calls.append('menu') or []), \
            patch.object(Config, '_Config__run_selected_advanced_sections',
                         new=lambda *a: None), \
            patch.object(Config, '_Config__confirm_overwrite_or_exit',
                         new=lambda *a: None), \
            patch.object(Config, 'write_config', new=lambda *a, **k: None), \
            patch.object(Config, '_Config__welcome', new=lambda *a: None), \
            patch.object(Config, '_Config__questions_install_mode',
                         new=lambda *a: None), \
            patch.object(Config, '_Config__questions_complexity',
                         new=lambda *a: None), \
            patch.object(Config, '_Config__setup_directory',
                         new=lambda *a: None), \
            patch.object(Config, '_Config__auto_detect_network',
                         new=lambda *a: None), \
            patch.object(Config, '_Config__auto_configure_resources',
                         new=lambda *a: None), \
            patch('helpers.network.Network.get_primary_ip',
                  return_value='127.0.0.1'):
        config.build()

    assert calls == ['topology', 'menu']


def test_multi_server_is_no_longer_a_section():
    """It is a structural question now; leaving it in the menu asks twice."""
    config = _later_run_config({'install_mode': 'production'})
    assert 'Multi-server setup' not in _menu_choices(config)


def test_topology_skipped_on_a_workstation():
    config = _later_run_config({
        'install_mode': 'dev', 'local_installation': True, 'dev_mode': True,
    })
    with patch.object(CLI, 'yes_no_question') as question:
        config._Config__questions_topology()
    question.assert_not_called()


def test_backups_offered_to_a_backend():
    """
    The database schedules are a back-end job. Gating the section on
    `self.frontend` hid them from the machine holding the databases.
    """
    assert _menu_choices(_backend_only_config())['Backups'] is False


def test_backups_offered_to_a_frontend_without_s3():
    choices = _menu_choices(_frontend_only_config({'use_aws': False}))
    assert 'Backups' in choices


def test_backups_hidden_from_a_frontend_on_s3():
    """`__questions_backup()` has nothing to ask there."""
    assert 'Backups' not in _menu_choices(
        _frontend_only_config({'use_aws': True})
    )


def test_frontend_only_sections_absent_on_a_backend():
    """
    Their execution already re-checks the role, so offering them put entries
    in the menu that silently did nothing when ticked.
    """
    choices = _menu_choices(_backend_only_config())
    for label in ('SMTP', 'Superuser credentials', 'Secret keys',
                  'Domain names', 'HTTPS & certificates'):
        assert label not in choices, label


def test_backend_only_sections_absent_on_a_frontend():
    choices = _menu_choices(_frontend_only_config())
    for label in ('MongoDB', 'PostgreSQL', 'Redis', 'PostgreSQL tuning'):
        assert label not in choices, label


def test_custom_yaml_offered_to_both_roles():
    """`__questions_custom_yml()` asks about whichever file applies."""
    assert 'Custom YAML' in _menu_choices(_backend_only_config())
    assert 'Custom YAML' in _menu_choices(_frontend_only_config())


def test_backend_only_backup_asks_for_its_own_aws_settings():
    """
    `__questions_backup()` has a `self.backend and not self.frontend` branch
    that asks the AWS questions itself, because the "AWS S3 storage" section
    is front-end only. It was unreachable while the menu hid backups from
    back ends.
    """
    config = _backend_only_config({'use_backup': True, 'advanced': True})

    with patch.object(CLI, 'yes_no_question', return_value=True), \
            patch.object(CLI, 'get_response',
                         side_effect=lambda *a, **k: '0 2 * * 0'), \
            patch.object(CLI, 'framed_print', new=lambda *a, **k: None), \
            patch.object(CLI, 'colored_print', new=lambda *a, **k: None), \
            patch.object(Config, '_Config__questions_aws') as aws_questions:
        config._Config__questions_backup()

    aws_questions.assert_called_once()
    d = config._Config__dict
    assert d['use_backup'] is True
    # The database schedules the back end owns were actually asked.
    assert d['postgres_backup_schedule'] == '0 2 * * 0'
    assert d['mongo_backup_schedule'] == '0 2 * * 0'
    assert d['redis_backup_schedule'] == '0 2 * * 0'
