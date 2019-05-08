# For public, HTTPS servers.
version: '2.1'

services:
  postgres:
    extends:
      file: docker-compose.backend.template.yml
      service: postgres
    ${OVERRIDE_POSTGRES_SETTINGS}volumes:
    ${OVERRIDE_POSTGRES_SETTINGS}  - ../kobo-deployments/postgres/slave/postgres.conf:/kobo-docker-scripts/slave/postgres.conf
    ports:
      - ${POSTGRES_PORT}:5432
