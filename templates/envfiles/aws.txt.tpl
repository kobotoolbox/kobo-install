####################
# Account settings #
####################

${USE_AWS}AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
${USE_AWS}AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}


####################
# Storage settings #
####################

# To use S3, the specified buckets must already exist and the owner of your `AWS_ACCESS_KEY_ID` must have the appropriate S3 permissions.

${USE_AWS}KOBOCAT_DEFAULT_FILE_STORAGE=storages.backends.s3boto.S3BotoStorage
${USE_AWS}KOBOCAT_AWS_STORAGE_BUCKET_NAME=${AWS_BUCKET_NAME}

${USE_AWS}KPI_DEFAULT_FILE_STORAGE=storages.backends.s3boto.S3BotoStorage
${USE_AWS}KPI_AWS_STORAGE_BUCKET_NAME=${AWS_BUCKET_NAME}

${USE_AWS}BACKUP_AWS_STORAGE_BUCKET_NAME=${AWS_BACKUP_BUCKET_NAME}
