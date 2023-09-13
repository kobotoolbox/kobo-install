#!/bin/bash

function join_by { local d=$$1; shift; echo -n "$$1"; shift; printf "%s" "$${@/#/$$d}"; }

DOMAINS=(${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME})
DOMAINS_CSV=$$(join_by , "$${DOMAINS[@]}")
RSA_KEY_SIZE=4096
DATA_PATH="./data/certbot"
EMAIL="" # Adding a valid address is strongly recommended
STAGING=0 # Set to 1 if you're testing your setup to avoid hitting request limits
MKDIR_CMD=$$(which mkdir)
DOCKER_COMPOSE_CMD="$$(which ${DOCKER_COMPOSE_CMD})"
CURL_CMD=$$(which curl)


if [ -d "$$DATA_PATH/conf/live/$$DOMAINS" ]; then
  read -p "Existing data found for $$DOMAINS_CSV. Continue and replace existing certificate? (y/N) " decision
  if [ "$$decision" != "Y" ] && [ "$$decision" != "y" ]; then
    exit
  fi
fi

if [ ! -e "$$DATA_PATH/conf/options-ssl-nginx.conf" ] || [ ! -e "$$DATA_PATH/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  $$MKDIR_CMD -p "$$DATA_PATH/conf"
  $$CURL_CMD -s https://raw.githubusercontent.com/kobotoolbox/nginx-certbot/master/certbot/options-ssl-nginx.conf > "$$DATA_PATH/conf/options-ssl-nginx.conf"
  $$CURL_CMD -s https://raw.githubusercontent.com/kobotoolbox/nginx-certbot/master/certbot/ssl-dhparams.pem > "$$DATA_PATH/conf/ssl-dhparams.pem"
  echo
fi

echo "### Creating dummy certificate for $${DOMAINS_CSV} ..."
DOMAINS_PATH="/etc/letsencrypt/live/$$DOMAINS"
$$MKDIR_CMD -p "$$DATA_PATH/conf/live/$$DOMAINS"
$$DOCKER_COMPOSE_CMD ${DOCKER_COMPOSE_SUFFIX} run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:1024 -days 1\
    -keyout '$$DOMAINS_PATH/privkey.pem' \
    -out '$$DOMAINS_PATH/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo


echo "### Starting nginx ..."
$$DOCKER_COMPOSE_CMD ${DOCKER_COMPOSE_SUFFIX} up --force-recreate -d nginx_ssl_proxy
echo

echo "### Deleting dummy certificate for $${DOMAINS_CSV} ..."
$$DOCKER_COMPOSE_CMD ${DOCKER_COMPOSE_SUFFIX} run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$$DOMAINS && \
  rm -Rf /etc/letsencrypt/archive/$$DOMAINS && \
  rm -Rf /etc/letsencrypt/renewal/$$DOMAINS.conf" certbot
echo


echo "### Requesting Let's Encrypt certificate for $${DOMAINS_CSV} ..."
#Join $$DOMAINS to -d args
DOMAIN_ARGS=""
for DOMAIN in "$${DOMAINS[@]}"; do
  DOMAIN_ARGS="$$DOMAIN_ARGS -d $$DOMAIN"
done

# Select appropriate EMAIL arg
case "$$EMAIL" in
  "") EMAIL_ARG="--register-unsafely-without-email" ;;
  *) EMAIL_ARG="--email $$EMAIL" ;;
esac

# Enable staging mode if needed
if [ $$STAGING != "0" ]; then STAGING_ARG="--staging"; fi

$$DOCKER_COMPOSE_CMD ${DOCKER_COMPOSE_SUFFIX} run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $$STAGING_ARG \
    $$EMAIL_ARG \
    $$DOMAIN_ARGS \
    --rsa-key-size $$RSA_KEY_SIZE \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### Reloading nginx ..."
$$DOCKER_COMPOSE_CMD ${DOCKER_COMPOSE_SUFFIX} exec nginx_ssl_proxy nginx -s reload
