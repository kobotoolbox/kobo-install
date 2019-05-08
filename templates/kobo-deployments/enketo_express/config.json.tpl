{
    "app name": "Enketo Express for KoBo Toolbox",
    "linked form and data server": {
        "name": "KoBo Toolbox",
        "server url": ""
    },
    "widgets": [
        "note", "select-desktop", "select-mobile", "autocomplete", "geo", "textarea",
        "table", "radio", "date", "time", "datetime", "compact", "file", "draw",
        "likert", "distress", "horizontal", "image-view", "comment", "image-map", "date-mobile",
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
