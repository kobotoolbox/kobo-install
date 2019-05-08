#--------------------------------------------------------------------------------
# MONGO
#--------------------------------------------------------------------------------
# These `KOBO_POSTGRES_` settings only affect the postgres container itself and the
# `wait_for_mongo.bash` init script that runs within the kpi and kobocat.
# Please see kobocat.txt to set container variables
KOBO_MONGO_PORT=${MONGO_PORT}
KOBO_MONGO_HOST=mongo.${PRIVATE_DOMAIN_NAME}

# Default MongoDB backup schedule is weekly at 01:00 AM UTC on Sunday.
${USE_BACKUP}MONGO_BACKUP_SCHEDULE=${MONGO_BACKUP_SCHEDULE}

#--------------------------------------------------------------------------------
# POSTGRES
#--------------------------------------------------------------------------------

# These `KOBO_POSTGRES_` settings only affect the postgres container itself and the
# `wait_for_postgres.bash` init script that runs within the kpi and kobocat
# containers. To control Django database connections, please see the
# `DATABASE_URL` environment variable.
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_HOST=postgres.${PRIVATE_DOMAIN_NAME}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Postgres database used by kpi and kobocat Django apps
DATABASE_URL=postgis://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres.${PRIVATE_DOMAIN_NAME}:${POSTGRES_PORT}/${POSTGRES_DB}

# Replication
KOBO_POSTGRES_REPLICATION_USER=kobo_replication
KOBO_POSTGRES_REPLICATION_PASSWORD=${POSTGRES_REPLICATION_PASSWORD}
#KOBO_POSTGRES_MASTER_ENDPOINT=primary.postgres.${PRIVATE_DOMAIN_NAME}

# Default Postgres backup schedule is weekly at 02:00 AM UTC on Sunday.
${USE_BACKUP}POSTGRES_BACKUP_SCHEDULE=${POSTGRES_BACKUP_SCHEDULE}

#--------------------------------------------------------------------------------
# REDIS
#--------------------------------------------------------------------------------

# Default Redis backup schedule is weekly at 03:00 AM UTC on Sunday.
${USE_BACKUP}REDIS_BACKUP_SCHEDULE=${REDIS_BACKUP_SCHEDULE}
