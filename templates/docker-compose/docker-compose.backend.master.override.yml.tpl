# For public, HTTPS servers.
version: '2.1'

services:

  rabbit:
    ports:
      - ${RABBIT_MQ_PORT}:5672

  postgres:
    ${OVERRIDE_POSTGRES_MASTER}volumes:
    ${OVERRIDE_POSTGRES_MASTER}  - ../kobo-deployments/postgres/master/postgres.conf:/kobo-docker-scripts/master/postgres.conf
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
