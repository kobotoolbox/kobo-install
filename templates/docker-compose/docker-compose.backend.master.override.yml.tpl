# For public, HTTPS servers.
version: '2.1'

${OVERRIDE_MASTER_BACKEND}services:

${OVERRIDE_MASTER_BACKEND}  postgres:
${OVERRIDE_MASTER_BACKEND}    volumes:
${OVERRIDE_MASTER_BACKEND}      - ../kobo-deployments/postgres/master/postgres.conf:/kobo-docker-scripts/master/postgres.conf