# See "api key" here: https://github.com/kobotoolbox/enketo-express/tree/master/config#linked-form-and-data-server.
ENKETO_API_KEY=${ENKETO_API_KEY}
# Keep `ENKETO_API_TOKEN` for retro-compatibility with KPI and KoBoCAT. ToDo Remove when KPI and KC read correct env variable
ENKETO_API_TOKEN=${ENKETO_API_KEY}
# See "https://github.com/enketo/enketo-express/blob/master/setup/docker/create_config.py#L14
ENKETO_ENCRYPTION_KEY=${ENKETO_ENCRYPTION_KEY}
