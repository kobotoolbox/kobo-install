# For public, HTTPS servers.
version: '2.1'

${OVERLOAD_BACKEND}services:

  ${OVERLOAD_BACKEND}postgres:
    ${OVERLOAD_BACKEND}image: mdillon/postgis:9.4

  ${OVERLOAD_BACKEND}mongo:
    ${OVERLOAD_BACKEND}image: kobotoolbox/mongo:latest
    ${OVERLOAD_BACKEND}environment:
      ${OVERLOAD_BACKEND}- MONGO_DATA=/srv/db
    ${OVERLOAD_BACKEND}volumes:
      ${OVERLOAD_BACKEND}- ./.vols/mongo:/srv/db