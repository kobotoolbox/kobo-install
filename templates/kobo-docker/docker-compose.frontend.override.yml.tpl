# For public, HTTPS servers.
version: '3'

services:
  kobocat:
  ${USE_KC_DEV_MODE}  build: ${KC_PATH}
  ${USE_KC_DEV_MODE}  image: kobocat:dev.${KC_DEV_BUILD_ID}
  ${USE_KC_DEV_MODE}  volumes:
  ${USE_KC_DEV_MODE}    - ${KC_PATH}:/srv/src/kobocat
    environment:
      - ENKETO_PROTOCOL=${PROTOCOL}
      - KC_UWSGI_WORKERS_COUNT=${UWSGI_WORKERS_MAX}
      - KC_UWSGI_CHEAPER_WORKERS_COUNT=${UWSGI_WORKERS_START}
      - NGINX_PUBLIC_PORT=${NGINX_PUBLIC_PORT}
      - KC_UWSGI_MAX_REQUESTS=${UWSGI_MAX_REQUESTS}
      - KC_UWSGI_CHEAPER_RSS_LIMIT_SOFT=${UWSGI_SOFT_LIMIT}
      - KC_UWSGI_HARAKIRI=${UWSGI_HARAKIRI}
      - KC_UWSGI_WORKER_RELOAD_MERCY=${UWSGI_WORKER_RELOAD_MERCY}
      ${USE_DEV_MODE}- DJANGO_SETTINGS_MODULE=onadata.settings.dev
      ${USE_CELERY}- SKIP_CELERY=True
    ${USE_EXTRA_HOSTS}extra_hosts:
    ${USE_FAKE_DNS}  - ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - mongo.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-main.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-cache.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - kobocat
    ${USE_BACKEND_NETWORK}      - kobocat.docker.container

  kpi:
  ${USE_KPI_DEV_MODE}  build: ${KPI_PATH}
  ${USE_KPI_DEV_MODE}  image: kpi:dev.${KPI_DEV_BUILD_ID}
  ${USE_KPI_DEV_MODE}  volumes:
  ${USE_KPI_DEV_MODE}    - ${KPI_PATH}:/srv/src/kpi
    environment:
      - KPI_UWSGI_WORKERS_COUNT=${UWSGI_WORKERS_MAX}
      - KPI_UWSGI_CHEAPER_WORKERS_COUNT=${UWSGI_WORKERS_START}
      - NGINX_PUBLIC_PORT=${NGINX_PUBLIC_PORT}
      - KPI_UWSGI_MAX_REQUESTS=${UWSGI_MAX_REQUESTS}
      - KPI_UWSGI_CHEAPER_RSS_LIMIT_SOFT=${UWSGI_SOFT_LIMIT}
      - KPI_UWSGI_HARAKIRI=${UWSGI_HARAKIRI}
      - KPI_UWSGI_WORKER_RELOAD_MERCY=${UWSGI_WORKER_RELOAD_MERCY}
    ${USE_CELERY}  - SKIP_CELERY=True
    ${USE_DEV_MODE}  - DJANGO_SETTINGS_MODULE=kobo.settings.dev
    ${USE_HTTPS}  - SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
    ${USE_NPM_FROM_HOST}  - FRONTEND_DEV_MODE=host
    ${USE_EXTRA_HOSTS}extra_hosts:
    ${USE_FAKE_DNS}  - ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - mongo.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-main.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-cache.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - kpi
    ${USE_BACKEND_NETWORK}      - kpi.docker.container

  nginx:
    environment:
      - NGINX_PUBLIC_PORT=${NGINX_PUBLIC_PORT}
      - UWSGI_PASS_TIMEOUT=${UWSGI_PASS_TIMEOUT}
    ${USE_LETSENSCRYPT}ports:
    ${USE_LETSENSCRYPT}  - ${NGINX_EXPOSED_PORT}:80
    ${USE_EXTRA_HOSTS}extra_hosts:
    ${USE_FAKE_DNS}  - ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - mongo.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-main.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-cache.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    networks:
      kobo-fe-network:
        aliases:
          - ${KOBOFORM_SUBDOMAIN}.${INTERNAL_DOMAIN_NAME}
          - ${KOBOCAT_SUBDOMAIN}.${INTERNAL_DOMAIN_NAME}
          - ${ENKETO_SUBDOMAIN}.${INTERNAL_DOMAIN_NAME}
          - nginx.internal

  enketo_express:
    # `DUMMY_ENV` is only there to avoid extra complex condition to override
    # `enketo_express` section or not. It allows to always this section whatever
    # `USE_EXTRA_HOSTS` and `USE_BACKEND_NETWORK` values are.
    environment:
      - DUMMY_ENV=True
    ${USE_EXTRA_HOSTS}extra_hosts:
    ${USE_FAKE_DNS}  - ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${USE_FAKE_DNS}  - ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}:${LOCAL_INTERFACE_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - mongo.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-main.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - redis-cache.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - enketo_express

${USE_BACKEND_NETWORK}networks:
${USE_BACKEND_NETWORK}  kobo-be-network:
${USE_BACKEND_NETWORK}    external:
${USE_BACKEND_NETWORK}      name: ${DOCKER_NETWORK_BACKEND_PREFIX}_kobo-be-network
