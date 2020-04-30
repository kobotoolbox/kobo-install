The purpose of the script is to install `KoBoToolbox ` in minutes without messing with configuration files.  
It prompts the user to answer some questions to create configuration files automatically and to start docker containers based on [`kobo-docker`](https://github.com/kobotoolbox/kobo-docker "").

## Important notice when upgrading from any release older than [`2.020.18`](https://github.com/kobotoolbox/kobo-install/releases/tag/2.020.18)

Prior to release `2.020.18`(https://github.com/kobotoolbox/kobo-install/releases/tag/2.020.18), [KPI](https://github.com/kobotoolbox/kpi) and [KoBoCAT](https://github.com/kobotoolbox/kobocat) both shared a common Postgres database. They now each have their own. **If you are upgrading an existing single-database installation, you must follow [these instructions](https://community.kobotoolbox.org/t/upgrading-to-separate-databases-for-kpi-and-kobocat/7202)** to migrate the KPI tables to a new database and adjust your configuration appropriately.

If you do not want to upgrade at this time, please use the [`shared-database-obsolete`](https://github.com/kobotoolbox/kobo-install/tree/shared-database-obsolete) branch instead.

## Warning for `kobo-docker` installations made prior to March 2019

If you have already installed `KoBoToolbox` with `kobo-docker` prior March 2019,
you **must** complete [a manual upgrade process](https://github.com/kobotoolbox/kobo-docker/#important-notice-when-upgrading-from-commit-5c2ef02-march-4-2019-or-earlier)
before using this repository. **If you do not, `kobo-install` will not be able to start.**

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
`$kobo-install> python3 run.py --update`

Stop KoBoToolbox:  
`$kobo-install> python3 run.py --stop`

Get help:  
`$kobo-install> python3 run.py --help`

Get version:  
`$kobo-install> python3 run.py --version`

Build kpi and kobocat (dev mode):  
`$kobo-install> python3 run.py --build`

Run docker commands on frontend containers:
`$kobo-install> python run.py --compose-frontend [docker-compose arguments]`

Run docker commands on backend containers:
`$kobo-install> python run.py --compose-backend [docker-compose arguments]`

Start maintenance mode:
`$kobo-install> python run.py --maintenance`

Stop maintenance mode:
`$kobo-install> python run.py --stop-maintenance`

## Build the configuration
User can choose between 2 types of installations:

- `Workstation`: KoBoToolbox doesn't need to be accessible from anywhere except the computer where it's installed. No DNS needed 
- `Server`: KoBoToolbox needs to be accessible from the local network or from the Internet. DNS are needed

### Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Installation directory| **../kobo-docker**  | ✓ | ✓ |
|SMTP information|  | ✓ | ✓ (frontend only) |
|Public domain name| **kobo.local** |  | ✓ (frontend only) |
|Subdomain names| **kf, kc, ee**  |  | ✓ (frontend only) |
|Use HTTPS<sup>1</sup>| **False** (Workstation)<br>**True** (Server)  |  | ✓ (frontend only) |
|Super user's username| **super_admin** | ✓ | ✓ (frontend only) |
|Super user's password| **Random string**  | ✓ | ✓ (frontend only) |

### Advanced Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Webserver port| **80**  | ✓ |  |
|Reverse proxy interal port| **8080**  |  | ✓ (frontend only) |
|Network interface|  **Autodetected**  | ✓ | ✓ (frontend only) |
|Use separate servers| **No**  |  | ✓ |
|Use DNS for private routes| **No**  |  | ✓ (frontend only) |
|Master backend IP _(if previous answer is no)_| **Local IP**  |  | ✓ (frontend only) |
|PostgreSQL DB|  **kobo**  | ✓ | ✓ |
|PostgreSQL user|  **kobo**  | ✓ | ✓ |
|PostgreSQL password|  **Autogenerate**  | ✓ | ✓ |
|PostgreSQL number of connections<sup>2</sup>|  **100**  | ✓ | ✓ (backend only) |
|PostgreSQL RAM<sup>2</sup>|  **2**  | ✓ | ✓ (backend only) |
|PostgreSQL Application Profile<sup>2</sup>|  **Mixed**  | ✓ | ✓ (backend only) |
|PostgreSQL Storage<sup>2</sup>|  **HDD**  | ✓ | ✓ (backend only) |
|Use AWS storage|  **No**  | ✓ | ✓ (frontend only) |
|uWGI workers|  **start: 2, max: 4**  | ✓ | ✓ (frontend only) |
|uWGI memory limit|  **128 MB**  | ✓ | ✓ (frontend only) |
|Google UA|  | ✓ | ✓ (frontend only) |
|Google API Key|  | ✓ | ✓ (frontend only) |
|Raven tokens|   | ✓ | ✓ (frontend only) |
|Debug|  **False**  | ✓ |  |
|Developer mode|  **False**  | ✓ | |
|Staging mode|  **False**  |  | ✓ (frontend only) |

<sup>1)</sup> _HTTPS certificates must be installed on a Reverse Proxy. 
`KoBoInstall` can install one and use `Let's Encrypt` to generate certificates thanks to [nginx-certbot project](https://github.com/wmnnd/nginx-certbot "")_

<sup>2)</sup> _Custom settings are provided by [PostgreSQL Configuration Tool API](https://github.com/sebastianwebber/pgconfig-api "")_

ℹ  Intercom App ID [must now](https://github.com/kobotoolbox/kpi/pull/2285) be configured through "Per user settings" in the Django admin interface of KPI.

## Requirements

- Linux / macOS
- Python 2.7/3.5+ <sup>Python2 support will be dropped in a future release</sup>
- [Docker](https://www.docker.com/get-started "") & [Docker Compose](https://docs.docker.com/compose/install/ "")
- Available TCP Ports:

    1. 80 NginX
    2. 5432 PostgreSQL
    3. 5672 RabbitMQ
    4. 6379-6380 redis
    5. 27017 MongoDB
    
    _N.B.: Ports can be customized in advanced options._

## Tests

Tests can be run with `tox`.  
Be sure it's install before running the tests

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


## To-Do

- Handle secondary backend
