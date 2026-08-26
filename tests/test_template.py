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


def test_aws_profile_decoupled_from_s3_storage():
    """Profile auth can be enabled (mount ~/.aws, set AWS_PROFILE) without
    turning on S3 storage."""
    vars_ = _get_template_vars({
        'use_aws': False,
        'aws_use_profile': True,
        'aws_profile_name': 'default',
        'aws_host_aws_dir': '/home/user/.aws',
    })
    # Profile auth + volume mount active
    assert vars_['USE_AWS_PROFILE'] == ''
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == ''
    assert vars_['AWS_PROFILE'] == 'default'
    # S3 storage stays off, no static credentials
    assert vars_['USE_AWS_S3'] == '#'
    assert vars_['USE_AWS_CREDENTIALS'] == '#'


def test_aws_upgrade_without_profile_keys():
    """Config loaded from old .run.conf without aws_use_profile keys should
    fall back to credentials mode without raising KeyError."""
    config = read_config({'use_aws': True, 'aws_access_key': 'key', 'aws_secret_key': 'secret'})
    del config._Config__dict['aws_use_profile']
    del config._Config__dict['aws_profile_name']
    del config._Config__dict['aws_host_aws_dir']
    with patch(
        'helpers.template.Template._Template__read_unique_id',
        MagicMock(return_value='123456789')
    ):
        vars_ = Template._Template__get_template_variables(config)
    assert vars_['USE_AWS_CREDENTIALS'] == ''
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


# ── Google Cloud authentication ──────────────────────────────────────────────

def test_gcloud_template_tokens_profile_enabled():
    vars_ = _get_template_vars({
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/home/user/.config/gcloud',
    })
    assert vars_['USE_GCLOUD_PROFILE'] == ''
    assert vars_['GCLOUD_HOST_CONFIG_DIR'] == '/home/user/.config/gcloud'


def test_gcloud_template_tokens_profile_disabled():
    vars_ = _get_template_vars({'gcloud_use_profile': False})
    assert vars_['USE_GCLOUD_PROFILE'] == '#'


def test_gcloud_profile_alone_opens_volumes_key():
    """
    A gcloud-only mount must still uncomment the `volumes:` key, otherwise the
    mount lines land under a key that does not exist.
    """
    vars_ = _get_template_vars({
        'kpi_path': '',
        'aws_use_profile': False,
        'gcloud_use_profile': True,
        'gcloud_host_config_dir': '/home/user/.config/gcloud',
    })
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == ''
    assert vars_['USE_AWS_PROFILE'] == '#'


def test_gcloud_profile_independent_from_nlp():
    """
    Mounting the credentials directory must not enable the NLP settings.
    """
    vars_ = _get_template_vars({
        'gcloud_use_profile': True,
        'gcloud_project': 'my-gcp-project',
        'use_nlp': False,
    })
    assert vars_['USE_GCLOUD_PROFILE'] == ''
    assert vars_['USE_NLP'] == '#'
    # The detected project is still carried over, just commented out
    assert vars_['GOOGLE_CLOUD_PROJECT'] == 'my-gcp-project'


# ── NLP / qualitative analysis ───────────────────────────────────────────────

def test_nlp_template_tokens_enabled():
    vars_ = _get_template_vars({
        'use_nlp': True,
        'aws_bedrock_region_name': 'us-west-2',
        'autoqa_claudesonnet_model_aip_arn': 'arn:aws:bedrock:sonnet',
        'autoqa_oss120_model_aip_arn': 'arn:aws:bedrock:oss120',
        'gs_bucket_name': 'my-bucket',
        'gcloud_project': 'my-gcp-project',
        'gcloud_quota_project': 'my-quota-project',
    })
    assert vars_['USE_NLP'] == ''
    assert vars_['AWS_BEDROCK_REGION_NAME'] == 'us-west-2'
    assert vars_['AUTOQA_CLAUDESONNET_MODEL_AIP_ARN'] == 'arn:aws:bedrock:sonnet'
    assert vars_['AUTOQA_OSS120_MODEL_AIP_ARN'] == 'arn:aws:bedrock:oss120'
    assert vars_['GS_BUCKET_NAME'] == 'my-bucket'
    assert vars_['GOOGLE_CLOUD_PROJECT'] == 'my-gcp-project'
    assert vars_['GOOGLE_CLOUD_QUOTA_PROJECT'] == 'my-quota-project'


def test_nlp_template_tokens_disabled_by_default():
    vars_ = _get_template_vars()
    assert vars_['USE_NLP'] == '#'
    assert vars_['GS_BUCKET_NAME'] == ''


def test_gcloud_and_nlp_tokens_tolerate_old_config():
    """
    A `.run.conf` written before these keys existed must not raise.
    """
    config = read_config()
    for key in (
        'gcloud_use_profile',
        'gcloud_host_config_dir',
        'gcloud_project',
        'gcloud_quota_project',
        'gs_bucket_name',
        'use_nlp',
        'aws_bedrock_region_name',
        'autoqa_claudesonnet_model_aip_arn',
        'autoqa_oss120_model_aip_arn',
    ):
        del config._Config__dict[key]

    with patch(
        'helpers.template.Template._Template__read_unique_id',
        MagicMock(return_value='123456789')
    ):
        vars_ = Template._Template__get_template_variables(config)

    assert vars_['USE_GCLOUD_PROFILE'] == '#'
    assert vars_['USE_NLP'] == '#'
    assert vars_['USE_CLOUD_PROFILE_VOLUMES'] == '#'
