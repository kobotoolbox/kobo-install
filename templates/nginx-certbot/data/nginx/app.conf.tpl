server {
    listen 80;
    server_name ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME};
    server_tokens off;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$$host$$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${KOBOCAT_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME} ${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME};
    server_tokens off;

    ssl_certificate /etc/letsencrypt/live/${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${KOBOFORM_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Allow 100M upload
    client_max_body_size 100M;

    location / {
        proxy_pass  http://nginx;
        proxy_set_header    Host                $$http_host;
        proxy_set_header    X-Real-IP           $$remote_addr;
        proxy_set_header    X-Forwarded-For     $$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto   https;
    }
}
