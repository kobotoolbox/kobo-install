#######################
# Mandatory variables #
#######################

# Choose between http or https
PUBLIC_REQUEST_SCHEME=${PROTOCOL}
# The publicly-accessible domain where your KoBo Toolbox instance will be reached (e.g. example.com).
PUBLIC_DOMAIN_NAME=${PUBLIC_DOMAIN_NAME}
# The private domain used in docker network. Useful for communication between containers without passing through
# a load balancer. No need to be resolved by a public DNS.
INTERNAL_DOMAIN_NAME=${INTERNAL_DOMAIN_NAME}
# The publicly-accessible subdomain for the KoBoForm form building and management interface (e.g. koboform).
KOBOFORM_PUBLIC_SUBDOMAIN=${KOBOFORM_SUBDOMAIN}
# The publicly-accessible subdomain for the KoBoCAT data collection and project management interface (e.g.kobocat).
KOBOCAT_PUBLIC_SUBDOMAIN=${KOBOCAT_SUBDOMAIN}
# The publicly-accessible subdomain for the Enketo Express web forms (e.g. enketo).
ENKETO_EXPRESS_PUBLIC_SUBDOMAIN=${ENKETO_SUBDOMAIN}
# See "api key" here: https://github.com/kobotoolbox/enketo-express/tree/master/config#linked-form-and-data-server.
ENKETO_API_KEY=${ENKETO_API_KEY}
# Keep `ENKETO_API_TOKEN` for retro-compatibility with KPI and KoBoCAT. ToDo Remove when KPI and KC read correct env variable
ENKETO_API_TOKEN=${ENKETO_API_KEY}
# See "https://github.com/enketo/enketo-express/blob/master/setup/docker/create_config.py#L14
ENKETO_ENCRYPTION_KEY=${ENKETO_ENCRYPTION_KEY}
# Canonically a 50-character random string. For Django 1.8.13, see https://docs.djangoproject.com/en/1.8/ref/settings/#secret-key and https://github.com/django/django/blob/4022b2c306e88a4ab7f80507e736ce7ac7d01186/django/core/management/commands/startproject.py#L29-L31.
# To generate a secret key in the same way as `django-admin startproject` you can run:
# docker-compose run --rm kpi python -c 'from django.utils.crypto import get_random_string; print(get_random_string(50, "abcdefghijklmnopqrstuvwxyz0123456789!@#$$%^&*(-_=+)"))'
DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
# The initial superuser's username.
KOBO_SUPERUSER_USERNAME=${KOBO_SUPERUSER_USERNAME}
# The initial superuser's password.
KOBO_SUPERUSER_PASSWORD=${KOBO_SUPERUSER_PASSWORD}
# The e-mail address where your users can contact you.
KOBO_SUPPORT_EMAIL=${DEFAULT_FROM_EMAIL}
