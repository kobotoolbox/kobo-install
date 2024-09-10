# Choose between http or https
PUBLIC_REQUEST_SCHEME=${PUBLIC_REQUEST_SCHEME}
# The publicly-accessible domain where your KoBo Toolbox instance will be reached (e.g. example.com).
PUBLIC_DOMAIN_NAME=${PUBLIC_DOMAIN_NAME}
# The private domain used in docker network. Useful for communication between containers without passing through
# a load balancer. No need to be resolved by a public DNS.
INTERNAL_DOMAIN_NAME=${INTERNAL_DOMAIN_NAME}
# The publicly-accessible subdomain for the KoBoForm form building and management interface (e.g. koboform).
KOBOFORM_PUBLIC_SUBDOMAIN=${KOBOFORM_SUBDOMAIN}
# The publicly-accessible subdomain for the KoBoCAT data collection and project management interface (e.g.kobocat).
KOBOCAT_PUBLIC_SUBDOMAIN=${KOBOCAT_SUBDOMAIN}
# The publicly-accessible subdomain for the Enketo Express web forms (e.g. enketo).
ENKETO_EXPRESS_PUBLIC_SUBDOMAIN=${ENKETO_SUBDOMAIN}
