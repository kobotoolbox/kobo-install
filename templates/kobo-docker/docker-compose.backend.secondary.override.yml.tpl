# For public, HTTPS servers.
version: '2.2'

services:
  postgres:
    volumes:
      - ../kobo-env/postgres/secondary/postgres.conf:/kobo-docker-scripts/secondary/postgres.conf
    ports:
      - ${POSTGRES_PORT}:5432
    ${ADD_BACKEND_EXTRA_HOSTS}extra_hosts:
    ${ADD_BACKEND_EXTRA_HOSTS}  - postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
    ${ADD_BACKEND_EXTRA_HOSTS}  - primary.postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}

  ${RUN_REDIS_CONTAINERS}redis_main:
  ${RUN_REDIS_CONTAINERS}  extends:
  ${RUN_REDIS_CONTAINERS}    file: docker-compose.backend.template.yml
  ${RUN_REDIS_CONTAINERS}    service: redis_main
  ${RUN_REDIS_CONTAINERS}  ports:
  ${RUN_REDIS_CONTAINERS}    - ${REDIS_MAIN_PORT}:6379

  ${RUN_REDIS_CONTAINERS}redis_cache:
  ${RUN_REDIS_CONTAINERS}  extends:
  ${RUN_REDIS_CONTAINERS}    file: docker-compose.backend.template.yml
  ${RUN_REDIS_CONTAINERS}    service: redis_cache
  ${RUN_REDIS_CONTAINERS}  ports:
  ${RUN_REDIS_CONTAINERS}    - ${REDIS_CACHE_PORT}:6380

