version: '3'

services:
  nginx_ssl_proxy:
    image: nginx:1.21-alpine
    restart: unless-stopped
    volumes:
      - ./data/nginx:/etc/nginx/conf.d
      - ./data/certbot/conf:/etc/letsencrypt
      - ./data/certbot/www:/var/www/certbot
    ports:
      - "80:80"
      - "443:443"
    command: "/bin/sh -c 'while :; do sleep 6h & wait $$$${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"
    networks:
      kobo-fe-network:
        aliases:
          - nginx_ssl_proxy
  certbot:
    image: certbot/certbot
    restart: unless-stopped
    volumes:
      - ./data/certbot/conf:/etc/letsencrypt
      - ./data/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $$$${!}; done;'"

networks:
  kobo-fe-network:
    name: ${DOCKER_NETWORK_FRONTEND_PREFIX}_kobo-fe-network
