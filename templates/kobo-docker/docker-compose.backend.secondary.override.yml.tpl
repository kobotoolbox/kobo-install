# For public, HTTPS servers.
version: '2.2'

services:
  postgres:
    extends:
      file: docker-compose.backend.template.yml
      service: postgres
    ${OVERRIDE_POSTGRES_SETTINGS}volumes:
    ${OVERRIDE_POSTGRES_SETTINGS}  - ../kobo-env/postgres/secondary/postgres.conf:/kobo-docker-scripts/secondary/postgres.conf
    ports:
      - ${POSTGRES_PORT}:5432
    ${USE_EXTRA_HOSTS}extra_hosts:
      ${ADD_BACKEND_EXTRA_HOSTS}- postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
      ${ADD_BACKEND_EXTRA_HOSTS}- primary.postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
