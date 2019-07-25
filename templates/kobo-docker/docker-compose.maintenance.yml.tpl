# For public, HTTPS servers.
version: '3'

services:

  maintenance:
    image: nginx:latest
    hostname: maintenance
    env_file:
      - ../kobo-deployments/envfile.txt
    environment:
      - ETA=2 hours
      - DATE_STR=Monday,&nbsp;November&nbsp;26&nbsp;at&nbsp;02:00&nbsp;GMT
      - DATE_ISO=20181126T02
    ports:
      - 80:80
    volumes:
        - ./log/nginx:/var/log/nginx
        - ./nginx/:/tmp/kobo_nginx/:ro
    command: "/bin/bash /tmp/kobo_nginx/maintenance/nginx_command.bash"
    restart: on-failure
