The purpose of the script is to install `KoBoToolbox ` in minutes without messing with configuration files.  
It prompts the user to answer some questions to create configuration files automatically and to start docker containers based on [`kobo-docker`](https://github.com/kobotoolbox/kobo-docker "").

## Warning
If you have already installed `KoBoToolbox` with `kobo-docker` prior March 2019,
databases are not compatible and and docker images (`PostgreSQL`, `MongoDB`) are not the same.  
**`KoBoInstall` won't be able to start the app.**

## Usage

`$kobo-install> python run.py`

First time the command is executed, setup will be launched.   
Subsequent executions will launch docker containers directly.

Rebuild configuration:  
`$kobo-install> python run.py --setup`

Get info:  
`$kobo-install> python run.py --info`

Get docker logs:  
`$kobo-install> python run.py --logs`

Upgrade KoBoToolbox:  
`$kobo-install> python run.py --upgrade`

Stop KoBoToolbox:  
`$kobo-install> python run.py --stop`

Get help:  
`$kobo-install> python run.py --help`

Get version:  
`$kobo-install> python run.py --version`

Build kpi and kobocat (dev mode):  
`$kobo-install> python run.py --build`


**Be aware, this utility is a beta release and may still have bugs.**

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
- Python 2.7+/3.5+
- [Docker](https://www.docker.com/get-started "") & [Docker Compose](https://docs.docker.com/compose/install/ "")
- Available TCP Ports:

    1. 80 NginX
    2. 5432 PostgreSQL
    3. 5672 RabbitMQ
    4. 6379-6380 redis
    5. 27017 MongoDB
    
    _N.B.: Ports can be customized in advanced options._

## Rebuild static files (for frontend development)

To immediately see your changes (in the `kpi` repository) live you need to run `npm run watch` to rebuild static files on the fly:

```
$kodo-docker> docker-compose -f docker-compose.frontend.yml -f docker-compose.frontend.override.yml run -p 3000:3000 --rm kpi npm run watch
```

Keep in mind that you need to continue running `npm run watch` to have static files be served continuously. Once stopped, static files won't be found anymore until you restart the `npm watch` or rebuild the container using 

```
$kobo-install> python run.py --build-kpi
```

## Tests

Tests can be run with `tox`.  
Be sure it's install before running the tests

```
$kobo-install> sudo apt install python-pip
$kobo-install> pip install tox
$kobo-install> tox
```
or 

```
$kobo-install> sudo apt install tox
$kobo-install> tox
```


## To-Do

- Handle secondary backend
