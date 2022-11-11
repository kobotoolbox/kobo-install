#--------------------------------------------------------------------------------
# MONGO
#--------------------------------------------------------------------------------
# These `KOBO_MONGO_` settings only affect the mongo container itself and the
# `wait_for_mongo.bash` init script that runs within the kpi and kobocat.
# Please see kobocat.txt to set container variables
KOBO_MONGO_PORT=${MONGO_PORT}
KOBO_MONGO_HOST=mongo.${PRIVATE_DOMAIN_NAME}
MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USERNAME}
MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
MONGO_INITDB_DATABASE=formhub
KOBO_MONGO_USERNAME=${MONGO_USER_USERNAME}
KOBO_MONGO_PASSWORD=${MONGO_USER_PASSWORD}
MONGO_DB_NAME=formhub
MONGO_DB_URL=mongodb://${MONGO_USER_USERNAME}:${MONGO_USER_PASSWORD}@mongo.${PRIVATE_DOMAIN_NAME}:${MONGO_PORT}/formhub

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
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
KC_POSTGRES_DB=${KC_POSTGRES_DB}
KPI_POSTGRES_DB=${KPI_POSTGRES_DB}

# Postgres database used by kpi and kobocat Django apps
KC_DATABASE_URL=postgis://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres.${PRIVATE_DOMAIN_NAME}:${POSTGRES_PORT}/${KC_POSTGRES_DB}
KPI_DATABASE_URL=postgis://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres.${PRIVATE_DOMAIN_NAME}:${POSTGRES_PORT}/${KPI_POSTGRES_DB}

# Replication
KOBO_POSTGRES_REPLICATION_USER=kobo_replication
KOBO_POSTGRES_REPLICATION_PASSWORD=${POSTGRES_REPLICATION_PASSWORD}
KOBO_POSTGRES_PRIMARY_ENDPOINT=primary.postgres.${PRIVATE_DOMAIN_NAME}

# Default Postgres backup schedule is weekly at 02:00 AM UTC on Sunday.
${USE_BACKUP}POSTGRES_BACKUP_SCHEDULE=${POSTGRES_BACKUP_SCHEDULE}

# WAL-E archiving and backup support
${USE_WAL_E}USE_WAL_E=1

#--------------------------------------------------------------------------------
# REDIS
#--------------------------------------------------------------------------------

# Default Redis backup schedule is weekly at 03:00 AM UTC on Sunday.
${USE_BACKUP}REDIS_BACKUP_SCHEDULE=${REDIS_BACKUP_SCHEDULE}

REDIS_SESSION_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD}@{% endif REDIS_PASSWORD %}redis-cache.${PRIVATE_DOMAIN_NAME}:${REDIS_CACHE_PORT}/2
REDIS_LOCK_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD}@{% endif REDIS_PASSWORD %}redis-cache.${PRIVATE_DOMAIN_NAME}:${REDIS_CACHE_PORT}/3
REDIS_PASSWORD=${REDIS_PASSWORD}
CACHE_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD}@{% endif REDIS_PASSWORD %}redis-cache.${PRIVATE_DOMAIN_NAME}:${REDIS_CACHE_PORT}/5
REDIS_CACHE_MAX_MEMORY=${REDIS_CACHE_MAX_MEMORY}
SERVICE_ACCOUNT_BACKEND_URL=redis://{% if REDIS_PASSWORD %}:${REDIS_PASSWORD}@{% endif REDIS_PASSWORD %}redis-cache.${PRIVATE_DOMAIN_NAME}:${REDIS_CACHE_PORT}/6
