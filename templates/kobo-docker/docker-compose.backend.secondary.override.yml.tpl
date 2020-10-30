# For public, HTTPS servers.
version: '2.2'

services:
  postgres:
    extends:
      file: docker-compose.backend.template.yml
      service: postgres
    volumes:
      - ../kobo-env/postgres/secondary/postgres.conf:/kobo-docker-scripts/secondary/postgres.conf
    ports:
      - ${POSTGRES_PORT}:5432
    ${ADD_BACKEND_EXTRA_HOSTS}extra_hosts:
      ${ADD_BACKEND_EXTRA_HOSTS}- postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
      ${ADD_BACKEND_EXTRA_HOSTS}- primary.postgres.${PRIVATE_DOMAIN_NAME}:${PRIMARY_BACKEND_IP}
