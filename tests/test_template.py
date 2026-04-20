import os
import shutil
from unittest.mock import patch, MagicMock

from helpers.template import Template
from .utils import mock_read_config as read_config


def _get_template_vars(overrides=None):
    config = read_config(overrides)
    with patch(
        'helpers.template.Template._Template__read_unique_id',
        MagicMock(return_value='123456789')
    ):
        return Template._Template__get_template_variables(config)


WORK_DIR = '/tmp/kobo-install-tests'

@patch(
    'helpers.template.Template._Template__read_unique_id',
    MagicMock(return_value='123456789')
)
@patch(
    'helpers.template.Template._Template__write_unique_id',
    MagicMock(return_value='123456789')
)
@patch(
    'helpers.template.Template._get_templates_path_parent',
    MagicMock(return_value=f'{WORK_DIR}/templates/')
)
@patch(
    'helpers.config.Config.get_env_files_path',
    MagicMock(return_value=f'{WORK_DIR}/kobo-env/')
)
@patch(
    'helpers.config.Config.get_letsencrypt_repo_path',
    MagicMock(return_value=f'{WORK_DIR}/nginx-certbot/')
)
def test_render_templates():
    config = read_config()
    config._Config__dict['unique_id'] = '123456789'
    config._Config__dict['kobodocker_path'] = f'{WORK_DIR}/kobo-docker/'
    try:
        _copy_templates()
        assert not os.path.exists(
            f'{WORK_DIR}/kobo-docker/docker-compose.frontend.override.yml'
        )
        assert not os.path.exists(
            f'{WORK_DIR}/kobo-docker/docker-compose.backend.override.yml'
        )
        assert not os.path.exists(f'{WORK_DIR}/kobo-env/envfiles/django.txt')
        Template.render(config)
        assert os.path.exists(
            f'{WORK_DIR}/kobo-docker/docker-compose.frontend.override.yml'
        )
        assert os.path.exists(
            f'{WORK_DIR}/kobo-docker/docker-compose.backend.override.yml'
        )
        assert os.path.exists(f'{WORK_DIR}/kobo-env/envfiles/django.txt')
    finally:
        shutil.rmtree(WORK_DIR)


def test_aws_template_tokens_credentials_mode():
    vars_ = _get_template_vars({
        'use_aws': True,
        'aws_use_profile': False,
        'aws_access_key': 'key',
        'aws_secret_key': 'secret',
        'aws_profile_name': '',
        'aws_host_aws_dir': '',
    })
    assert vars_['USE_AWS_CREDENTIALS'] == ''
    assert vars_['USE_AWS_PROFILE'] == '#'
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == '#'


def test_aws_template_tokens_profile_mode():
    vars_ = _get_template_vars({
        'use_aws': True,
        'aws_use_profile': True,
        'aws_access_key': '',
        'aws_secret_key': '',
        'aws_profile_name': 'my_profile',
        'aws_host_aws_dir': '/home/user/.aws',
    })
    assert vars_['USE_AWS_CREDENTIALS'] == '#'
    assert vars_['USE_AWS_PROFILE'] == ''
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == ''
    assert vars_['AWS_PROFILE'] == 'my_profile'
    assert vars_['AWS_HOST_AWS_DIR'] == '/home/user/.aws'


def test_aws_template_tokens_aws_disabled():
    vars_ = _get_template_vars({'use_aws': False, 'aws_use_profile': False})
    assert vars_['USE_AWS_CREDENTIALS'] == '#'
    assert vars_['USE_AWS_PROFILE'] == '#'
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == '#'


def test_cloud_profile_volumes_active_in_kpi_dev_mode():
    vars_ = _get_template_vars({
        'use_aws': False,
        'aws_use_profile': False,
        'kpi_path': '/path/to/kpi',
    })
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == ''
    assert vars_['USE_AWS_PROFILE'] == '#'


def _copy_templates(src: str = None, dst: str = None):
    if not src:
        src = os.path.dirname(os.path.realpath(__file__)) + '/../templates/'
    if not dst:
        dst = f'{WORK_DIR}/templates/'

    # Create the destination directory if needed
    os.makedirs(dst, exist_ok=True)

    for entry in os.listdir(src):
        src_path = os.path.join(src, entry)
        dst_path = os.path.join(dst, entry)

        if os.path.isdir(src_path):
            # Recursively copy subdirectories
            _copy_templates(src_path, dst_path)
        else:
            # Copy files (overwrite if exists)
            shutil.copy2(src_path, dst_path)
