{
    "app name": "Enketo Express for KoBo Toolbox",
    "linked form and data server": {
        "name": "KoBo Toolbox",
        "server url": "",
        "encryption key": "${ENKETO_ENCRYPTION_KEY}"
    },
    "widgets": [
        "note",
        "select-desktop",
        "select-mobile",
        "autocomplete",
        "geo",
        "geo-esri",
        "textarea",
        "table",
        "radio",
        "date",
        "time",
        "datetime",
        "select-media",
        "file",
        "draw",
        "likert",
        "range",
        "rank",
        "columns",
        "analog-scale",
        "image-view",
        "comment",
        "image-map",
        "date-native",
        "date-mobile",
        "url",
        "text-max",
        "../../../node_modules/enketo-image-customization-widget/image-customization",
        "../../../node_modules/enketo-literacy-test-widget/literacywidget"
    ],
    "redis": {
        "cache": {
            "host": "redis-cache.${PRIVATE_DOMAIN_NAME}",
            "port": "${REDIS_CACHE_PORT}"
        },
        "main": {
            "host": "redis-main.${PRIVATE_DOMAIN_NAME}",
            "port": "${REDIS_MAIN_PORT}"
        }
    },
     "google": {
        "api key": "${GOOGLE_API_KEY}",
        "analytics": {
            "ua": "${GOOGLE_UA}",
            "domain": "${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}"
        }
    }
}
