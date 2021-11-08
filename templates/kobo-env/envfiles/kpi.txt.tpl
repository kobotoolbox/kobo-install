KPI_DJANGO_DEBUG=${DEBUG}
TEMPLATE_DEBUG=${DEBUG}
${USE_X_FORWARDED_HOST}USE_X_FORWARDED_HOST=True

ENKETO_VERSION=Express
KPI_PREFIX=/
KPI_BROKER_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD_URL_ENCODED}@{% endif REDIS_PASSWORD %}redis-main.${PRIVATE_DOMAIN_NAME}:${REDIS_MAIN_PORT}/1

KPI_MONGO_HOST=mongo.${PRIVATE_DOMAIN_NAME}
KPI_MONGO_PORT=${MONGO_PORT}
KPI_MONGO_NAME=formhub
KPI_MONGO_USER=${MONGO_USER_USERNAME}
KPI_MONGO_PASS=${MONGO_USER_PASSWORD}

DJANGO_LANGUAGE_CODES=en ar es de-DE fr hi ku pl pt tr zh-hans
