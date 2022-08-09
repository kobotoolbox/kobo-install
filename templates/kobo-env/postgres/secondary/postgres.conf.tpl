#####################################################################################
# SECONDARY SPECIFIC
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

#------------------------------------------------------------------------------------
# REPLICATION
#------------------------------------------------------------------------------------
hot_standby_feedback = on

# https://stackoverflow.com/a/33282856
# https://stackoverflow.com/a/34404303
max_standby_streaming_delay = -1
max_standby_archive_delay = -1
