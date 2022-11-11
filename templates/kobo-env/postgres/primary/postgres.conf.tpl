#####################################################################################
# PRIMARY SPECIFIC
# If file must be appended to shared/postgres.conf
#####################################################################################
#------------------------------------------------------------------------------------
# TUNING
#------------------------------------------------------------------------------------
# These settings are based on server configuration
# https://www.pgconfig.org/#/tuning
# DB Version: 14
# OS Type: linux
# App profile: ${POSTGRES_APP_PROFILE}
# Hard-drive: SSD
# Total Memory (RAM): ${POSTGRES_RAM}GB

${POSTGRES_SETTINGS}

${USE_WAL_E}archive_mode = on
${USE_WAL_E}archive_command = 'envdir $$PGDATA/wal-e.d/env wal-e wal-push %p'
${USE_WAL_E}archive_timeout = 60
