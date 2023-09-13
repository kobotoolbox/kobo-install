The purpose of the script is to install KoboToolbox in minutes without messing with configuration files.
It prompts the user to answer some questions to create configuration files automatically and to start docker containers based on [`kobo-docker`](https://github.com/kobotoolbox/kobo-docker "").

## :warning: You _must observe_ the following when upgrading:

### …from any release older than [`2.022.44`](https://github.com/kobotoolbox/kobo-install/releases/tag/2.022.44) (November 2022)

If you have already installed KoboToolbox between March 2019 and November 2022, you **must** complete [a manual upgrade process](https://github.com/kobotoolbox/kobo-docker/blob/master/doc/November-2022-Upgrade.md) before trying to upgrade. **If you do not, `kobo-install` will not be able to start.**

### …from any release older than [`2.020.18`](https://github.com/kobotoolbox/kobo-install/releases/tag/2.020.18) (May 2020)

Prior to release [`2.020.18`](https://github.com/kobotoolbox/kobo-install/releases/tag/2.020.18), [KPI](https://github.com/kobotoolbox/kpi) and [KoBoCAT](https://github.com/kobotoolbox/kobocat) both shared a common Postgres database. They now each have their own. **If you are upgrading an existing single-database installation, you must follow [these instructions](https://community.kobotoolbox.org/t/upgrading-to-separate-databases-for-kpi-and-kobocat/7202)** to migrate the KPI tables to a new database and adjust your configuration appropriately.

If you do not want to upgrade at this time, please use the [`shared-database-obsolete`](https://github.com/kobotoolbox/kobo-install/tree/shared-database-obsolete) branch instead.

### …installations made prior to March 2019

If you have already installed KoboToolbox with `kobo-docker` prior March 2019,
you **must** complete [a manual upgrade process](https://github.com/kobotoolbox/kobo-docker/#important-notice-when-upgrading-from-commit-5c2ef02-march-4-2019-or-earlier)
before using this repository. **If you do not, `kobo-install` will not be able to start.**

## Versions

Branch `master` is the recommended branch to use `kobo-install` on your production environment. Just run `git checkout master` before your first run.

Branch `beta` is a pre-release of the next version. It contains new features and bug fixes.

Other branches are for development purposes.

## Usage

`$kobo-install> python3 run.py`

First time the command is executed, setup will be launched.  
Subsequent executions will launch docker containers directly.

Rebuild configuration:  
`$kobo-install> python3 run.py --setup`

Get info:  
`$kobo-install> python3 run.py --info`

Get docker logs:  
`$kobo-install> python3 run.py --logs`

Update KoBoToolbox:  
`$kobo-install> python3 run.py --update [branch or tag]`

By default, fetch the latest version of `master` branch


Stop KoBoToolbox:  
`$kobo-install> python3 run.py --stop`

Get help:  
`$kobo-install> python3 run.py --help`

Get version:  
`$kobo-install> python3 run.py --version`

Build kpi and kobocat (dev mode):  
`$kobo-install> python3 run.py --build`

Run docker commands on front-end containers:  
`$kobo-install> python3 run.py --compose-frontend [docker-compose arguments]`

Run docker commands on back-end containers:  
`$kobo-install> python3 run.py --compose-backend [docker-compose arguments]`

Start maintenance mode:  
`$kobo-install> python3 run.py --maintenance`

Stop maintenance mode:  
`$kobo-install> python3 run.py --stop-maintenance`

## Build the configuration
User can choose between 2 types of installations:

- `Workstation`: KoBoToolbox doesn't need to be accessible from anywhere except the computer where it's installed. No DNS needed
- `Server`: KoBoToolbox needs to be accessible from the local network or from the Internet. DNS are needed

### Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Installation directory| **../kobo-docker**  | ✓ | ✓ |
|SMTP information|  | ✓ | ✓ (front end only) |
|Public domain name| **kobo.local** |  | ✓ (front end only) |
|Subdomain names| **kf, kc, ee**  |  | ✓ (front end only) |
|Use HTTPS<sup>1</sup>| **False** (Workstation)<br>**True** (Server)  |  | ✓ (front end only) |
|Super user's username| **super_admin** | ✓ | ✓ (front end only) |
|Super user's password| **Random string**  | ✓ | ✓ (front end only) |
|Activate backups<sup>2</sup>|  **False**  | ✓ | ✓ (back end only) |

### Advanced Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Webserver port| **80**  | ✓ |  |
|Reverse proxy interal port| **8080**  |  | ✓ (front end only) |
|Network interface|  **Autodetected**  | ✓ | ✓ (front end only) |
|Use separate servers| **No**  |  | ✓ |
|Use DNS for private routes| **No**  |  | ✓ (front end only) |
|Primary back end IP _(if previous answer is no)_| **Local IP**  |  | ✓ (front end only) |
|PostgreSQL DB|  **kobo**  | ✓ | ✓ |
|PostgreSQL user's username|  **kobo**  | ✓ | ✓ |
|PostgreSQL user's password|  **Autogenerate**  | ✓ | ✓ |
|PostgreSQL number of connections<sup>3</sup>|  **100**  | ✓ | ✓ (back end only) |
|PostgreSQL RAM<sup>3</sup>|  **2**  | ✓ | ✓ (back end only) |
|PostgreSQL Application Profile<sup>3</sup>|  **Mixed**  | ✓ | ✓ (back end only) |
|PostgreSQL Storage<sup>3</sup>|  **HDD**  | ✓ | ✓ (back end only) |
|MongoDB super user's username|  **root**  | ✓ | ✓ |
|MongoDB super user's password|  **Autogenerate**  | ✓ | ✓ |
|MongoDB user's username|  **kobo**  | ✓ | ✓ |
|MongoDB user's password|  **Autogenerate**  | ✓ | ✓ |
|Redis password<sup>4</sup>|  **Autogenerate**  | ✓ | ✓ |
|Use AWS storage<sup>5</sup>|  **No**  | ✓ | ✓ |
|Use WAL-E PostgreSQL backups<sup>6</sup> |  **No**  | ✓ | ✓ (back end only) |
|uWGI workers|  **start: 2, max: 4**  | ✓ | ✓ (front end only) |
|uWGI memory limit|  **128 MB**  | ✓ | ✓ (front end only) |
|uWGI harakiri timeout |  **120s**  | ✓ | ✓ (front end only) |
|uWGI worker reload timeout |  **120s**  | ✓ | ✓ (front end only) |
|Google UA|  | ✓ | ✓ (front end only) |
|Google API Key|  | ✓ | ✓ (front end only) |
|Raven tokens|   | ✓ | ✓ (front end only) |
|Debug|  **False**  | ✓ |  |
|Developer mode|  **False**  | ✓ | |
|Staging mode|  **False**  |  | ✓ (front end only) |

<sup>1)</sup> _HTTPS certificates must be installed on a Reverse Proxy.
`kobo-install` can install one and use `Let's Encrypt` to generate certificates
 thanks
 to [nginx-certbot project](https://github.com/wmnnd/nginx-certbot "")_

<sup>2)</sup> _If AWS credentials are provided, backups are sent to configured bucket_

<sup>3)</sup> _Custom settings are provided by [PostgreSQL Configuration Tool API](https://github.com/sebastianwebber/pgconfig-api "")_

<sup>4)</sup> _Redis password is optional but **strongly** recommended_

<sup>5)</sup> _If AWS storage is selected, credentials must be provided if backups are activated_

<sup>6)</sup> _WAL-E backups for PostgreSQL are only available when using AWS storage_

ℹ  Intercom App ID [must now](https://github.com/kobotoolbox/kpi/pull/2285) be configured through "Per user settings" in the Django admin interface of KPI.

## Requirements

- Linux <sup>5</sup> / macOS <sup>6</sup>
- Python 3.8+
- [Docker](https://www.docker.com/get-started "") <sup>7</sup>
- Available TCP Ports: <sup>8</sup>

    1. 80 NGINX
    1. 443 NGINX (if you use kobo-install with LetsEncrypt proxy)
    2. Additional ports when `expose ports` advanced option has been selected
        1. 5432 PostgreSQL
        3. 6379-6380 redis
        4. 27017 MongoDB

    _**WARNING:**_

    - _If you use a firewall, be sure to open traffic publicly on NGINX port, otherwise kobo-install cannot work_
    - _By default, additional ports are not exposed except when using multi servers configuration. If you choose to expose them, **be sure to not expose them publicly** (e.g. use a firewall and allow traffic between front-end and back-end containers only. NGINX port still has to stay publicly opened though)._

<sup>5)</sup> _It has been tested with Ubuntu 18.04, 20.04 and 22.04_

<sup>6)</sup> _Docker on macOS is slow. First boot usually takes a while to be ready. You may have to answer `Yes` once or twice to question `Wait for another 600 seconds?` when prompted_

<sup>7)</sup> _Compose V1 is still supported but has reached its EOL from July 2023_

<sup>8)</sup> _These are defaults but can be customized with advanced options_


## Tests

Tests can be run with `tox`.  
Be sure it is installed before running the tests.

```
$kobo-install> sudo apt install python3-pip
$kobo-install> pip3 install tox
$kobo-install> tox
```
or

```
$kobo-install> sudo apt install tox
$kobo-install> tox
```
