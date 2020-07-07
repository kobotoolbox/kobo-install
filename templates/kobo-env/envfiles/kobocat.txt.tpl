KOBOCAT_DJANGO_DEBUG=${DEBUG}
TEMPLATE_DEBUG=${DEBUG}
${USE_X_FORWARDED_HOST}USE_X_FORWARDED_HOST=True

DJANGO_SETTINGS_MODULE=onadata.settings.kc_environ
ENKETO_VERSION=Express

KOBOCAT_BROKER_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD_URL_ENCODED}@{% endif REDIS_PASSWORD %}redis-main.${PRIVATE_DOMAIN_NAME}:${REDIS_MAIN_PORT}/2
KOBOCAT_CELERY_LOG_FILE=/srv/logs/celery.log

# Default KoBoCAT media backup schedule is weekly at 12:00 AM UTC on Sunday.
${USE_MEDIA_BACKUP}KOBOCAT_MEDIA_BACKUP_SCHEDULE=${KOBOCAT_MEDIA_BACKUP_SCHEDULE}

KOBOCAT_MONGO_HOST=mongo.${PRIVATE_DOMAIN_NAME}
KOBOCAT_MONGO_PORT=${MONGO_PORT}
KOBOCAT_MONGO_NAME=formhub
KOBOCAT_MONGO_USER=${MONGO_USER_USERNAME}
KOBOCAT_MONGO_PASS=${MONGO_USER_PASSWORD}


# Dev: One or more mappings from PyDev remote debugging machine file paths to `kobocat` container
#   file paths (see https://github.com/kobotoolbox/kobocat/blob/master/docker/setup_pydev.bash).
#KOBOCAT_PATH_FROM_ECLIPSE_TO_PYTHON_PAIRS=~/devel/kobocat -> /srv/src/kobocat | ~/.virtualenvs/kobocat/lib/python2.7/site-packages -> /usr/local/lib/python2.7/dist-packages
