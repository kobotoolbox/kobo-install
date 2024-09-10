# Override for primary back-end server
version: '3'

services:

  postgres:
    volumes:
      - ../kobo-env/postgres/conf/postgres.conf:/kobo-docker-scripts/conf/postgres.conf
    ${EXPOSE_BACKEND_PORTS}ports:
    ${EXPOSE_BACKEND_PORTS}  - ${POSTGRES_PORT}:5432
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - postgres.${PRIVATE_DOMAIN_NAME}

  mongo:
    ${EXPOSE_BACKEND_PORTS}ports:
    ${EXPOSE_BACKEND_PORTS}  - ${MONGO_PORT}:27017
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - mongo.${PRIVATE_DOMAIN_NAME}

  redis_main:
    ${EXPOSE_BACKEND_PORTS}ports:
    ${EXPOSE_BACKEND_PORTS}  - ${REDIS_MAIN_PORT}:6379
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - redis-main.${PRIVATE_DOMAIN_NAME}

  redis_cache:
    ${EXPOSE_BACKEND_PORTS}ports:
    ${EXPOSE_BACKEND_PORTS}  - ${REDIS_CACHE_PORT}:6380
    ${USE_BACKEND_NETWORK}networks:
    ${USE_BACKEND_NETWORK}  kobo-be-network:
    ${USE_BACKEND_NETWORK}    aliases:
    ${USE_BACKEND_NETWORK}      - redis-cache.${PRIVATE_DOMAIN_NAME}

${USE_BACKEND_NETWORK}networks:
${USE_BACKEND_NETWORK}  kobo-be-network:
${USE_BACKEND_NETWORK}    driver: bridge
