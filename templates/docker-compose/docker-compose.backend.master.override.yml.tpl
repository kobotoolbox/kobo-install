# For public, HTTPS servers.
version: '2.1'

services:

  postgres:
    ${OVERRIDE_POSTGRES_SETTINGS}volumes:
    ${OVERRIDE_POSTGRES_SETTINGS}  - ../kobo-deployments/postgres/master/postgres.conf:/kobo-docker-scripts/master/postgres.conf
    ${POSTGRES_BACKUP_FROM_SLAVE}environment:
    ${POSTGRES_BACKUP_FROM_SLAVE}  - POSTGRES_BACKUP_FROM_SLAVE=True
    ports:
      - ${POSTGRES_PORT}:5432

  mongo:
    ports:
      - ${MONGO_PORT}:27017

  redis_main:
    ports:
      - ${REDIS_MAIN_PORT}:6379

  redis_cache:
    ports:
      - ${REDIS_CACHE_PORT}:6380
