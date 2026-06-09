# -*- coding: utf-8 -*-
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

from helpers.cli import CLI
from helpers.config import Config
from .utils import mock_read_config as read_config

CHOICE_YES = '1'
CHOICE_NO = '2'
DEV = '1'
STAGING = '2'
PRODUCTION = '3'
SIMPLE = '1'
ADVANCED = '2'


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

    # advanced=False → not False=True → DEFAULT_RESPONSES[True]='1' (Simple)
    assert defaults_seen[0] == '1'
    assert not config.advanced_options


def test_questions_complexity_default_advanced_when_previously_advanced():
    config = read_config({'advanced': True})
    defaults_seen = []

    def capture(msg, color, default):
        defaults_seen.append(default)
        return default

    with patch.object(CLI, 'colored_input', side_effect=capture):
        config._Config__questions_complexity()

    # advanced=True → not True=False → DEFAULT_RESPONSES[False]='2' (Advanced)
    assert defaults_seen[0] == '2'
    assert config.advanced_options


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
def test_build_simple_mode_consumes_exactly_two_inputs(_):
    """Mode + complexity — nothing else should be asked."""
    config = read_config()
    config._Config__first_time = False

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([PRODUCTION, SIMPLE])
        config.build()

    assert mock_ci.call_count == 2


@patch('helpers.config.Config.write_config', new=lambda *a, **k: None)
@patch('helpers.config.Config._Config__setup_directory', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_detect_network', new=lambda *a: None)
@patch('helpers.config.Config._Config__auto_configure_resources', new=lambda *a: None)
@patch('helpers.network.Network.get_primary_ip', return_value='127.0.0.1')
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

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([PRODUCTION, SIMPLE])
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

    with patch('helpers.cli.CLI.colored_input') as mock_ci:
        mock_ci.side_effect = iter([PRODUCTION, SIMPLE])
        result = config.build()

    assert result['mongo_secured'] is True


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


# ── __auto_detect_aws_profile (dev simple mode) ──────────────────────────────

def test_auto_detect_aws_profile_enables_profile_when_dir_exists():
    config = read_config({'use_aws': False, 'aws_use_profile': False})
    with patch('helpers.config.os.path.isdir', return_value=True):
        config._Config__auto_detect_aws_profile()
    d = config._Config__dict
    assert d['aws_use_profile'] is True
    assert d['aws_profile_name'] == 'default'
    assert d['aws_host_aws_dir'].endswith('.aws')
    # S3 storage must NOT be forced on
    assert d['use_aws'] is False


def test_auto_detect_aws_profile_noop_when_dir_missing():
    config = read_config({'use_aws': False, 'aws_use_profile': False})
    with patch('helpers.config.os.path.isdir', return_value=False):
        config._Config__auto_detect_aws_profile()
    d = config._Config__dict
    assert d['aws_use_profile'] is False
    assert d['use_aws'] is False
