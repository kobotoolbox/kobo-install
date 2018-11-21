# For public, HTTPS servers.
version: '3'

services:

  maintenance:
    image: nginx:latest
    hostname: maintenance
    env_file:
      - ../kobo-deployments/envfile.txt
    environment:
      - TEMPLATED_VAR_REFS=$${PUBLIC_REQUEST_SCHEME} $${INTERNAL_DOMAIN_NAME} $${PUBLIC_DOMAIN_NAME} $${KOBOFORM_PUBLIC_SUBDOMAIN} $${KOBOCAT_PUBLIC_SUBDOMAIN} $${ENKETO_EXPRESS_PUBLIC_SUBDOMAIN}
    ports:
      - ${NGINX_EXPOSED_PORT}:80
    volumes:
      - ./log/nginx:/var/log/nginx
      - ./nginx/:/tmp/kobo_nginx/:ro
    command: "/bin/bash /tmp/kobo_nginx/maintenance/nginx_command.bash"
    restart: on-failure
