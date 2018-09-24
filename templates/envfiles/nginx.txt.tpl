# Options for the following are "uWSGI" or "runserver_plus" (for debugging).
KPI_WEB_SERVER=uWSGI
KOBOCAT_WEB_SERVER=uWSGI

# Options for the following are "Nginx" or "Django".
# NOTE: In order to serve static files from Django, the corresponding 
#   `..._DJANGO_DEBUG` environment variable must be set to "True"
#   in `envfiles/kobocat.txt` and/or `envfiles/kpi.txt`.
KOBOCAT_STATIC_FILES_SERVER=Nginx
KPI_STATIC_FILES_SERVER=Nginx
