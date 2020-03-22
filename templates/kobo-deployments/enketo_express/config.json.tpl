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
    },
    "payload limit": "1mb",
    "text field character limit": 1000000,
    "maps": [
        {
            "name": "humanitarian",
            "tiles": [ "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png" ],
            "attribution": "&copy; <a href=\"http://openstreetmap.org\">OpenStreetMap</a> & <a href=\"https://www.hotosm.org/updates/2013-09-29_a_new_window_on_openstreetmap_data\">Yohan Boniface & Humanitarian OpenStreetMap Team</a> | <a href=\"https://www.openstreetmap.org/copyright\">Terms</a>"
        }, {
            "name": "satellite",
            "tiles": [ "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" ],
            "attribution": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        }, {
            "name": "terrain",
            "tiles": [ "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" ],
            "attribution": "&copy; <a href=\"https://openstreetmap.org\">OpenStreetMap</a> | <a href=\"https://www.openstreetmap.org/copyright\">Terms</a>"
        }, {
            "name": "streets",
            "tiles": [ "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" ],
            "attribution": "&copy; <a href=\"https://openstreetmap.org\">OpenStreetMap</a> | <a href=\"https://www.openstreetmap.org/copyright\">Terms</a>"
        }
    ]
}
