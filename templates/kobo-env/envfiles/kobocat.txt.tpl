KOBOCAT_DJANGO_DEBUG=${DEBUG}
TEMPLATE_DEBUG=${DEBUG}
${USE_X_FORWARDED_HOST}USE_X_FORWARDED_HOST=True

DJANGO_SESSION_COOKIE_AGE=${DJANGO_SESSION_COOKIE_AGE}
DJANGO_SETTINGS_MODULE=onadata.settings.prod
ENKETO_VERSION=Express

KOBOCAT_BROKER_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD}@{% endif REDIS_PASSWORD %}redis-main.${PRIVATE_DOMAIN_NAME}:${REDIS_MAIN_PORT}/2
KOBOCAT_CELERY_LOG_FILE=/srv/logs/celery.log

# Default KoBoCAT media backup schedule is weekly at 12:00 AM UTC on Sunday.
${USE_MEDIA_BACKUP}KOBOCAT_MEDIA_BACKUP_SCHEDULE=${KOBOCAT_MEDIA_BACKUP_SCHEDULE}

# Dev: One or more mappings from PyDev remote debugging machine file paths to `kobocat` container
#   file paths (see https://github.com/kobotoolbox/kobocat/blob/master/docker/setup_pydev.bash).
#KOBOCAT_PATH_FROM_ECLIPSE_TO_PYTHON_PAIRS=~/devel/kobocat -> /srv/src/kobocat | ~/.virtualenvs/kobocat/lib/python2.7/site-packages -> /usr/local/lib/python2.7/dist-packages

# Comma separated domains
${USE_SERVICE_ACCOUNT_WHITELISTED_HOSTS}SERVICE_ACCOUNT_WHITELISTED_HOSTS=${KOBOCAT_SUBDOMAIN}.${INTERNAL_DOMAIN_NAME}
