# For public, HTTPS servers.
version: '3'

services:

  maintenance:
    environment:
      - ETA=${MAINTENANCE_ETA}
      - DATE_STR=${MAINTENANCE_DATE_STR}
      - DATE_ISO=${MAINTENANCE_DATE_ISO}
      - EMAIL=${MAINTENANCE_EMAIL}
    ports:
      - ${NGINX_EXPOSED_PORT}:80
