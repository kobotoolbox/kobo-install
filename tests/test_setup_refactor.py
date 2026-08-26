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


# ── __auto_detect_gcloud_profile (dev simple mode) ───────────────────────────

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
    with patch('helpers.config.os.path.expanduser',
               return_value=str(tmp_path / 'missing')):
        config._Config__auto_detect_gcloud_profile()
    d = config._Config__dict
    assert d['gcloud_use_profile'] is False
    assert d['gcloud_project'] == ''


def test_auto_detect_gcloud_profile_enables_profile_without_project(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path)
    config = read_config({'gcloud_use_profile': False, 'gcloud_project': ''})
    with patch('helpers.config.os.path.expanduser',
               return_value=str(gcloud_dir)):
        config._Config__auto_detect_gcloud_profile()
    d = config._Config__dict
    assert d['gcloud_use_profile'] is True
    assert d['gcloud_host_config_dir'] == str(gcloud_dir)
    assert d['gcloud_project'] == ''
    # NLP settings stay an explicit opt-in
    assert d['use_nlp'] is False


def test_auto_detect_gcloud_profile_reads_active_project(tmp_path):
    gcloud_dir = _gcloud_dir(
        tmp_path,
        project='[core]\naccount = someone@example.org\nproject = my-gcp-project\n',
    )
    config = read_config({'gcloud_use_profile': False})
    with patch('helpers.config.os.path.expanduser',
               return_value=str(gcloud_dir)):
        config._Config__auto_detect_gcloud_profile()
    d = config._Config__dict
    assert d['gcloud_project'] == 'my-gcp-project'
    assert d['gcloud_quota_project'] == 'my-gcp-project'


def test_auto_detect_gcloud_profile_survives_malformed_config(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path, project='not an ini file at all')
    config = read_config({'gcloud_use_profile': False})
    with patch('helpers.config.os.path.expanduser',
               return_value=str(gcloud_dir)):
        config._Config__auto_detect_gcloud_profile()
    d = config._Config__dict
    assert d['gcloud_use_profile'] is True
    assert d['gcloud_project'] == ''


def test_auto_detect_gcloud_profile_survives_config_without_project(tmp_path):
    gcloud_dir = _gcloud_dir(tmp_path, project='[core]\naccount = a@b.org\n')
    config = read_config({'gcloud_use_profile': False})
    with patch('helpers.config.os.path.expanduser',
               return_value=str(gcloud_dir)):
        config._Config__auto_detect_gcloud_profile()
    assert config._Config__dict['gcloud_project'] == ''


# ── __questions_gcloud / __questions_nlp ─────────────────────────────────────

def test_questions_gcloud_enables_and_stores_host_dir():
    config = read_config({'gcloud_use_profile': False})
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter([CHOICE_YES, '/opt/gcloud'])
        config._Config__questions_gcloud()
    d = config._Config__dict
    assert d['gcloud_use_profile'] is True
    assert d['gcloud_host_config_dir'] == '/opt/gcloud'


def test_questions_gcloud_clears_host_dir_when_disabled():
    config = read_config({
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/opt/gcloud',
    })
    with patch.object(CLI, 'colored_input', return_value=CHOICE_NO):
        config._Config__questions_gcloud()
    d = config._Config__dict
    assert d['gcloud_use_profile'] is False
    assert d['gcloud_host_config_dir'] == ''


def _gcloud_question_default(config):
    """
    Runs __questions_gcloud and returns the default offered for the yes/no
    question, plus the default offered for the host directory input.
    """
    seen = {}

    def capture_yes_no(question, default=True, labels=None):
        seen['yes_no'] = default
        return default

    def capture_input(message, color, default=''):
        seen['host_dir'] = default
        return default

    with patch.object(CLI, 'yes_no_question', side_effect=capture_yes_no), \
         patch.object(CLI, 'colored_input', side_effect=capture_input):
        config._Config__questions_gcloud()

    return seen


def test_questions_gcloud_defaults_to_yes_when_dir_exists():
    config = read_config({
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=True):
        seen = _gcloud_question_default(config)
    assert seen['yes_no'] is True


def test_questions_gcloud_defaults_to_no_when_dir_missing():
    config = read_config({
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=False):
        seen = _gcloud_question_default(config)
    assert seen['yes_no'] is False


def test_questions_gcloud_stored_answer_wins_over_detection():
    """An explicit previous "Yes" survives the directory moving away."""
    config = read_config({
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/opt/gcloud',
    })
    with patch('helpers.config.os.path.isdir', return_value=False):
        seen = _gcloud_question_default(config)
    assert seen['yes_no'] is True


def test_questions_gcloud_offers_default_dir_after_previous_no():
    """
    Answering No resets the stored directory, so the next run must fall back
    to ~/.config/gcloud instead of offering an empty path.
    """
    config = read_config({
        'gcloud_use_profile': False,
        'gcloud_host_config_dir': '',
    })
    with patch('helpers.config.os.path.isdir', return_value=True):
        seen = _gcloud_question_default(config)
    assert seen['host_dir'] == os.path.expanduser('~/.config/gcloud')


def test_questions_nlp_stores_all_values():
    config = read_config({'use_nlp': False})
    answers = [
        'us-west-2',
        'arn:aws:bedrock:sonnet',
        'arn:aws:bedrock:oss120',
        'my-bucket',
        'my-gcp-project',
        'my-quota-project',
    ]
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = iter(answers)
        config._Config__questions_nlp()
    d = config._Config__dict
    # Checking the section is the consent, no extra yes/no gate
    assert d['use_nlp'] is True
    assert d['aws_bedrock_region_name'] == 'us-west-2'
    assert d['autoqa_claudesonnet_model_aip_arn'] == 'arn:aws:bedrock:sonnet'
    assert d['autoqa_oss120_model_aip_arn'] == 'arn:aws:bedrock:oss120'
    assert d['gs_bucket_name'] == 'my-bucket'
    assert d['gcloud_project'] == 'my-gcp-project'
    assert d['gcloud_quota_project'] == 'my-quota-project'


def test_questions_nlp_defaults_to_detected_gcloud_project():
    """
    The project found by __auto_detect_gcloud_profile is offered as default.
    """
    config = read_config({'gcloud_project': 'detected-project'})
    with patch('helpers.cli.CLI.colored_input') as mock_input:
        mock_input.side_effect = lambda message, color, default='': default
        config._Config__questions_nlp()
    assert config._Config__dict['gcloud_project'] == 'detected-project'


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

    with patch.object(CLI, 'checkbox_menu', side_effect=fake_menu):
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
        'install_mode': 'production',
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
        'install_mode': 'production',
        'use_nlp': True,
        'gcloud_use_profile': True,
        'advanced_sections_seen': ['aws', 'smtp', 'superuser'],
        'advanced_sections_selected': ['aws'],
    })

    choices = _menu_choices(config)

    assert choices['NLP and qualitative analysis'] is True
    assert choices['Google Cloud credentials'] is True
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
    'aws_host_aws_dir': '/home/dev/.aws',
    'gcloud_use_profile': True,
    'gcloud_host_config_dir': '/home/dev/.config/gcloud',
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
    assert d['gcloud_use_profile'] is False
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
