# For public, HTTPS servers.
version: '3'

services:

  maintenance:
    image: nginx:latest
    hostname: maintenance
    env_file:
      - ../kobo-deployments/envfile.txt
    environment:
      - ETA=${MAINTENANCE_ETA}
      - DATE_STR=${MAINTENANCE_DATE_STR}
      - DATE_ISO=${MAINTENANCE_DATE_ISO}
      - EMAIL=${MAINTENANCE_EMAIL}
    ports:
      - ${NGINX_EXPOSED_PORT}:80
    volumes:
        - ./log/nginx:/var/log/nginx
        - ./nginx/:/tmp/kobo_nginx/:ro
    command: "/bin/bash /tmp/kobo_nginx/maintenance/nginx_command.bash"
    restart: on-failure
    networks:
      - kobo-maintenance-network

networks:
  kobo-maintenance-network:
    driver: bridge
