# For public, HTTPS servers.
version: '2.2'

services:
  postgres:
    extends:
      file: docker-compose.backend.template.yml
      service: postgres
    ${OVERRIDE_POSTGRES_SETTINGS}volumes:
    ${OVERRIDE_POSTGRES_SETTINGS}  - ../kobo-deployments/postgres/secondary/postgres.conf:/kobo-docker-scripts/secondary/postgres.conf
    ports:
      - ${POSTGRES_PORT}:5432
