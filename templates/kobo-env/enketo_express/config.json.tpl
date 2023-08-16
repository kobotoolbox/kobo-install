{
    "app name": "Enketo Express for KoboToolbox",
    "linked form and data server": {
        "name": "KoboToolbox",
        "server url": "",
        "api key": "${ENKETO_API_KEY}"
    },
    "ip filtering": {
        "allowPrivateIPAddress": ${ENKETO_ALLOW_PRIVATE_IP_ADDRESS},
        "allowMetaIPAddress": false,
        "allowIPAddressList": [],
        "denyAddressList": []
    },
    "encryption key": "${ENKETO_ENCRYPTION_KEY}",
    "less secure encryption key": "${ENKETO_LESS_SECURE_ENCRYPTION_KEY}",
    "support": {
        "email": "${DEFAULT_FROM_EMAIL}"
    },
    "widgets": [
        "note",
        "select-desktop",
        "select-mobile",
        "autocomplete",
        "geo",
        "textarea",
        "url",
        "table",
        "radio",
        "date",
        "time",
        "datetime",
        "select-media",
        "file",
        "draw",
        "rank",
        "likert",
        "range",
        "columns",
        "image-view",
        "comment",
        "image-map",
        "date-native",
        "date-native-ios",
        "date-mobile",
        "text-max",
        "text-print",
        "rating",
        "thousands-sep",
        "integer",
        "decimal",
        "../../../node_modules/enketo-image-customization-widget/image-customization",
        "../../../node_modules/enketo-literacy-test-widget/literacywidget"
    ],
    "redis": {
        "cache": {
            "host": "redis-cache.${PRIVATE_DOMAIN_NAME}",
            "port": "${REDIS_CACHE_PORT}"{% if REDIS_PASSWORD %},{% endif REDIS_PASSWORD %}
            {% if REDIS_PASSWORD %}
            "password": ${REDIS_PASSWORD_JS_ENCODED}
            {% endif REDIS_PASSWORD %}
        },
        "main": {
            "host": "redis-main.${PRIVATE_DOMAIN_NAME}",
            "port": "${REDIS_MAIN_PORT}"{% if REDIS_PASSWORD %},{% endif REDIS_PASSWORD %}
            {% if REDIS_PASSWORD %}
            "password": ${REDIS_PASSWORD_JS_ENCODED}
            {% endif REDIS_PASSWORD %}
        }
    },
    "google": {
        "api key": "${GOOGLE_API_KEY}",
        "analytics": {
            "ua": "${GOOGLE_UA}",
            "domain": "${ENKETO_SUBDOMAIN}.${PUBLIC_DOMAIN_NAME}"
        }
    },
    "logo": {
        "source": "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIGlkPSJhIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHg9IjBweCIgeT0iMHB4IiB3aWR0aD0iMjQzLjYyNCIgaGVpZ2h0PSI2MS44MDYiIHZpZXdCb3g9IjAgMCA0MzQuNDEgNTYuODUiPjxkZWZzPjxzdHlsZT4uYntmaWxsOiMyMDk1ZjM7fS5je2ZpbGw6IzU2NWU3Njt9PC9zdHlsZT48L2RlZnM+PHBhdGggY2xhc3M9ImMiIGQ9Ik0xMTIuODQsMTMuNzNjLTEwLjgsMC0xOS4yLDguNy0xOS4yLDE5LjJzOC43LDE5LjIsMTkuMiwxOS4yLDE5LjItOC43LDE5LjItMTkuMmMuMy0xMC44LTguNC0xOS4yLTE5LjItMTkuMlptMCwzMC45Yy02LjMsMC0xMS40LTUuMS0xMS40LTExLjRzNS4xLTExLjQsMTEuNC0xMS40LDExLjQsNS4xLDExLjQsMTEuNGMuMyw2LTUuMSwxMS40LTExLjQsMTEuNFoiLz48cGF0aCBjbGFzcz0iYyIgZD0iTTE1Ny44NCwxMy43M2MtNS40LS45LTEwLjUsLjYtMTQuNCwzLjZWNy40M2MwLTMtMi40LTUuMS01LjEtNS4xaDBjLTEuNSwwLTIuNCwxLjItMi40LDIuNFY0Ni43M2MwLDMsMi40LDUuMSw1LjEsNS4xaDBjMS41LDAsMi40LTEuMiwyLjQtMi40di0uOWMzLjMsMi40LDcuMiwzLjksMTEuNCwzLjksMTEuNCwwLDIwLjQtOS45LDE5LjItMjEuNi0uOS04LjctNy44LTE1LjYtMTYuMi0xNy4xWm0tNS40LDMwLjZjLTUuNC0xLjItOS02LjMtOS0xMS43aDBjMC00LjIsMi4xLTcuOCw1LjctOS42LDguNy00LjIsMTcuMSwyLjEsMTcuMSwxMC4yLC4zLDYuOS02LjMsMTIuNi0xMy44LDExLjFaIi8+PHBhdGggY2xhc3M9ImMiIGQ9Ik0xOTYuNTQsMTMuNzNjLTEwLjgsMC0xOS4yLDguNy0xOS4yLDE5LjJzOC43LDE5LjIsMTkuMiwxOS4yLDE5LjItOC43LDE5LjItMTkuMmMuMy0xMC44LTguNC0xOS4yLTE5LjItMTkuMlptMCwzMC45Yy02LjMsMC0xMS40LTUuMS0xMS40LTExLjRzNS4xLTExLjQsMTEuNC0xMS40LDExLjQsNS4xLDExLjQsMTEuNGMuMyw2LTUuMSwxMS40LTExLjQsMTEuNFoiLz48Zz48cGF0aCBjbGFzcz0iYiIgZD0iTTI1Ni44NCwxNi4xM2MtOS45LDAtMTgsOC4xLTE4LDE4czguMSwxOCwxOCwxOCwxOC04LjEsMTgtMTgtOC4xLTE4LTE4LTE4Wm0wLDMwLjZjLTYuOSwwLTEyLjYtNS43LTEyLjYtMTIuNnM1LjctMTIuNiwxMi42LTEyLjYsMTIuNiw1LjcsMTIuNiwxMi42LTUuNywxMi42LTEyLjYsMTIuNloiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTI5NS41NCwxNi4xM2MtOS45LDAtMTgsOC4xLTE4LDE4czguMSwxOCwxOCwxOCwxOC04LjEsMTgtMTgtOC4xLTE4LTE4LTE4Wm0wLDMwLjZjLTYuOSwwLTEyLjYtNS43LTEyLjYtMTIuNnM1LjctMTIuNiwxMi42LTEyLjYsMTIuNiw1LjcsMTIuNiwxMi42LTUuNywxMi42LTEyLjYsMTIuNloiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTM0Ni44NCwxNi4xM2MtNC44LDAtOS4zLDEuOC0xMi42LDUuMVY5LjUzYzAtMi4xLTEuOC0zLjYtMy42LTMuNi0uOSwwLTEuOCwuOS0xLjgsMS44VjQ4LjUzYzAsMi4xLDEuOCwzLjYsMy42LDMuNiwuOSwwLDEuOC0uOSwxLjgtMS44di0zYzMuMywzLDcuNSw1LjEsMTIuNiw1LjEsOS45LDAsMTgtOC4xLDE4LTE4cy03LjgtMTguMy0xOC0xOC4zWm0wLDMwLjZjLTYuOSwwLTEyLjYtNS43LTEyLjYtMTIuNnM1LjctMTIuNiwxMi42LTEyLjYsMTIuNiw1LjcsMTIuNiwxMi42LTUuNywxMi42LTEyLjYsMTIuNloiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTM4NS44NCwxNi4xM2MtOS45LDAtMTgsOC4xLTE4LDE4czguMSwxOCwxOCwxOCwxOC04LjEsMTgtMTgtOC4xLTE4LTE4LTE4Wm0wLDMwLjZjLTYuOSwwLTEyLjYtNS43LTEyLjYtMTIuNnM1LjctMTIuNiwxMi42LTEyLjYsMTIuNiw1LjcsMTIuNiwxMi42LTUuNywxMi42LTEyLjYsMTIuNloiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTMxOS4yNCw1LjYzYy0uOSwwLTEuOCwuOS0xLjgsMS44VjQ4LjIzYzAsMi4xLDEuOCwzLjYsMy42LDMuNiwuOSwwLDEuOC0uOSwxLjgtMS44VjkuNTNjLjMtMi4xLTEuNS0zLjktMy42LTMuOVoiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTQyMC45NCwzNC4xM2wxMC4yLTE1LjljLjYtLjksMC0yLjQtMS4yLTIuNGgwYy0yLjQsMC00LjgsMS4yLTYsMy4zbC02LDkuNi02LTkuNmMtMS4yLTIuMS0zLjYtMy4zLTYtMy4zLTEuMiwwLTEuOCwxLjItMS4yLDIuNGwxMC4yLDE1LjktMTAuMiwxNS45Yy0uNiwuOSwwLDIuNCwxLjIsMi40aDBjMi40LDAsNC44LTEuMiw2LTMuM2w2LTkuNiw2LDkuNmMxLjIsMi4xLDMuNiwzLjMsNiwzLjNoMGMxLjIsMCwxLjgtMS4yLDEuMi0yLjRsLTEwLjItMTUuOVoiLz48cGF0aCBjbGFzcz0iYiIgZD0iTTI0Mi43NCwxMy43M2MyLjEsMCwzLjYtMS44LDMuNi0zLjYsMC0uOS0uOS0xLjgtMS44LTEuOGgtMjcuM2MtMi4xLDAtMy42LDEuOC0zLjYsMy42LDAsLjksLjksMS44LDEuOCwxLjhoMTEuN1Y0OC41M2MwLDIuMSwxLjgsMy42LDMuNiwzLjYsLjksMCwxLjgtLjksMS44LTEuOFYxMy43M2gxMC4yWiIvPjwvZz48cGF0aCBjbGFzcz0iYyIgZD0iTTk2LjY0LDQ5LjEzbC0yMS4zLTIxLjMsMTcuNy0xNy43Yy45LS45LC4zLTIuNC0uOS0yLjRoLTMuM2MtMi43LDAtNS40LDEuMi03LjIsM2wtMTUuOSwxNS45VjEyLjgzYzAtMy0yLjQtNS4xLTUuMS01LjFoMGMtMS4yLDAtMi40LDEuMi0yLjQsMi40VjQ2LjczYzAsMywyLjQsNS4xLDUuMSw1LjFoMGMxLjIsMCwyLjQtMS4yLDIuNC0yLjR2LTcuOGMwLTIuNCwuOS00LjUsMi40LTZsMi4xLTIuMSwxNSwxNWMxLjgsMS44LDQuNSwzLDcuMiwzaDMuM2MxLjIsMCwxLjgtMS41LC45LTIuNFoiLz48Zz48cGF0aCBjbGFzcz0iYiIgZD0iTTMxLjU0LDM4LjAzdjUuMWMwLDMtMi40LDUuMS01LjEsNS4xSDE1LjM0Yy0zLDAtNS4xLTIuNC01LjEtNS4xVjE0LjMzYzAtMywyLjQtNS4xLDUuMS01LjFoMTEuMWMzLDAsNS4xLDIuNCw1LjEsNS4xdi42Yy45LS4zLDIuMS0uNiwzLS42LDEuMiwwLDIuNCwuMywzLjYsLjZ2LS45YzAtNi42LTUuNC0xMi0xMi0xMkgxNS4wNEM4LjQ0LDIuMDMsMy4wNCw3LjQzLDMuMDQsMTQuMDN2MjguOGMwLDYuNiw1LjQsMTIsMTIsMTJoMTEuMWM2LjYsMCwxMi01LjQsMTItMTJ2LTEyLjlsLTYuNiw4LjFaIi8+PHBhdGggY2xhc3M9ImIiIGQ9Ik0yNi4xNCwzNi4yM2wxMi0xMy44Yy4zLS4zLC4zLTEuMiwwLTEuNWgwYy0yLjEtMS44LTUuNC0xLjUtNy4yLC42bC03LjUsOC43Yy0uMywuMy0uNiwuMy0uNiwwbC0yLjctMy4zYy0uNi0uNi0xLjUtLjYtMi4xLDBoMGMtMS44LDEuOC0xLjgsNC44LS4zLDYuOWwyLjQsMi43YzEuMiwxLjgsNC4yLDEuOCw2LS4zWiIvPjwvZz48L3N2Zz4K",
        "href": ""
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
