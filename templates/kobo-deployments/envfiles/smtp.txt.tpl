##################################
# For sending e-mail using SMTP. #
##################################

# NOTE: To send from GMail, the sending account must enable "Allowing less secure apps to access your account" (https://support.google.com/accounts/answer/6010255).
# NOTE: To send from AWS EC2 instances, SNS must be used instead of SMTP. These and the SNS e-mail settings from `envfiles/aws.txt` are mutually exclusive; do not use both.
# See https://docs.djangoproject.com/en/1.8/topics/email/#smtp-backend.

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=${SMTP_HOST}
EMAIL_PORT=${SMTP_PORT}
EMAIL_HOST_USER=${SMTP_USER}
EMAIL_HOST_PASSWORD=${SMTP_PASSWORD}
EMAIL_USE_TLS=${SMTP_USE_TLS}
DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL}