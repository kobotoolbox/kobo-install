The purpose of the script is to install `KoBoToolbox ` in minutes without messing with configuration files.  
It prompts the user to answer some questions to create configuration files automatically and to start docker containers based on `kobo-install` branch of `kobo-docker` [repository](https://github.com/kobotoolbox/kobo-docker "").

## Warning
If you have already installed `KoBoToolbox` with `kobo-docker` from `master` branch,
databases are not compatible and and docker images (`PostgreSQL`, `MongoDB`) are not the same.  
`kobo-install` won't be able to start the app.  



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
|Subdomain names| **kpi, kc, ee**  |  | ✓ (frontend only) |
|Use HTTPS| **No**  |  | ✓ (frontend only) |
|Super user's username| **super_admin** | ✓ | ✓ (frontend only) |
|Super user's password| **Random string**  | ✓ | ✓ (frontend only) |

### Advanced Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Webserver port| **80**  | ✓ |  |
|Reverse proxy interal port| **80**  |  | ✓ (frontend only) |
|Network interface|  **Autodetected**  | ✓ | ✓ (frontend only) |
|Use separate servers| **No**  |  | ✓ |
|Use DNS for private routes| **No**  |  | ✓ (frontend only) |
|Master backend IP _(if previous answer is no)_| **Local IP**  |  | ✓ (frontend only) |
|Postgres DB|  **kobo**  | ✓ | ✓ |
|Postgres user|  **kobo**  | ✓ | ✓ |
|Postgres password|  **kobo**  | ✓ | ✓ |
|Postgres number of connections|  **100**  | ✓ | ✓ (backend only) |
|Postgres RAM|  **8**  | ✓ | ✓ (backend only) |
|Use AWS storage|  **No**  | ✓ | ✓ (frontend only) |
|uWGI workers|  **start: 2, max: 4**  | ✓ | ✓ (frontend only) |
|uWGI memory limit|  **128 MB**  | ✓ | ✓ (frontend only) |
|Google UA|  | ✓ | ✓ (frontend only) |
|Google API Key|  | ✓ | ✓ (frontend only) |
|Intercom| | ✓ | ✓ (frontend only) |
|Raven tokens|   | ✓ | ✓ (frontend only) |
|Debug|  **False**  | ✓ |  |
|Developer mode|  **False**  | ✓ | |
|Staging mode|  **False**  |  | ✓ (frontend only) |

## Requirements

- Linux / macOS
- Python 2.7+/3.4+
- [Docker](https://www.docker.com/get-started "") & [Docker Compose](https://docs.docker.com/compose/install/ "")
- Available TCP Ports:

    1. 80 NginX
    2. 5432 PostgreSQL
    3. 5672 RabbitMQ
    4. 6379-6380 redis
    5. 27017 MongoDB
    
    _N.B.: Ports can be customized in advanced options._

## Tests

Tests can be run with `pytest`.

- virtualenv for python2 can be created with `requirements_py2_tests.txt`
- virtualenv for python3 can be created with `requirements_py3_tests.txt`

## To-Do

- Handle secondary backend
- Validate users' input
