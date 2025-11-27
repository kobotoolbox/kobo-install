import os
import shutil
from unittest.mock import patch, MagicMock

from helpers.template import Template
from .utils import mock_read_config as read_config


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
