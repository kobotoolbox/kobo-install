#--------------------------------------------------------------------------------
# MONGO
#--------------------------------------------------------------------------------
# These `KOBO_POSTGRES_` settings only affect the postgres container itself and the
# `wait_for_mongo.bash` init script that runs within the kpi and kobocat.
# Please see kobocat.txt to set container variables
KOBO_MONGO_PORT=27017
KOBO_MONGO_HOST=mongo.${PRIVATE_DOMAIN_NAME}


#--------------------------------------------------------------------------------
# POSTGRES
#--------------------------------------------------------------------------------

# These `KOBO_POSTGRES_` settings only affect the postgres container itself and the
# `wait_for_postgres.bash` init script that runs within the kpi and kobocat
# containers. To control Django database connections, please see the
# `DATABASE_URL` environment variable.
POSTGRES_PORT=5432
POSTGRES_HOST=postgres.${PRIVATE_DOMAIN_NAME}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Postgres database used by kpi and kobocat Django apps
DATABASE_URL=postgis://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres.${PRIVATE_DOMAIN_NAME}:5432/${POSTGRES_DB}

# Replication
#KOBO_POSTGRES_REPLICATION_USER=kobo_replication
#KOBO_POSTGRES_REPLICATION_PASSWORD=
#KOBO_POSTGRES_MASTER_ENDPOINT=primary.postgres.${PRIVATE_DOMAIN_NAME}
#KOBO_POSTGRES_SLAVE_ENDPOINT=secondary.postgres.${PRIVATE_DOMAIN_NAME}


#--------------------------------------------------------------------------------
# RABBIT
#--------------------------------------------------------------------------------

KOBO_RABBIT_PORT=5672
KOBO_RABBIT_HOST=rabbit.${PRIVATE_DOMAIN_NAME}
