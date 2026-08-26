############################################################################
# GOOGLE_ANALYTICS_TOKEN must be changed in enketo_express/config.json too #
############################################################################
GOOGLE_ANALYTICS_TOKEN=${GOOGLE_UA}

SENTRY_DSN=${KPI_RAVEN_DSN}
SENTRY_JS_DSN=${KPI_RAVEN_JS_DSN}

###############################
# Google Cloud authentication #
###############################

${USE_GCLOUD_PROFILE}GOOGLE_APPLICATION_CREDENTIALS=/home/kobo/.config/gcloud/application_default_credentials.json

##############################
# NLP / Qualitative analysis #
##############################

${USE_NLP}AWS_BEDROCK_REGION_NAME=${AWS_BEDROCK_REGION_NAME}
${USE_NLP}AUTOQA_CLAUDESONNET_MODEL_AIP_ARN=${AUTOQA_CLAUDESONNET_MODEL_AIP_ARN}
${USE_NLP}AUTOQA_OSS120_MODEL_AIP_ARN=${AUTOQA_OSS120_MODEL_AIP_ARN}
${USE_NLP}GS_BUCKET_NAME=${GS_BUCKET_NAME}
${USE_NLP}GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
${USE_NLP}GOOGLE_CLOUD_QUOTA_PROJECT=${GOOGLE_CLOUD_QUOTA_PROJECT}
