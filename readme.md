The purpose of the script is to install `KoboToolbox` in minutes without messing with configuration files.  
It prompts the user to answer some questions to create configuration files automatically and to start 
docker containers based on `kobo-install` branch of `kobo-docker` [repository](https://github.com/kobotoolbox/kobo-docker "").

It can be run with this simple command

`$kobo-install> python run.py`

First time the command is executed, setup will be launched.   
Subsequent executions will launch docker containers directly.

_The only question which could be asked is:_ `Please choose which network interface you want to use?` if new ip address is detected in for `workstation` installation **only**.

If configuration needs to be changed, please use option `-s`.  
e.g. `$kobo-install> python run.py -s`


**Be aware, this utility is a beta release and still needs improvements**

## Build the configuration
User can choose between 2 types of installations:

- `Workstation`: KoBoToolbox doesn't need to be accessible from anywhere except the computer where it's installed. No DNS needed 
- `Server`: KoBoToolbox needs to be accessible from the local network or from the Internet. DNS are needed

### Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Installation directory| **../kobo-docker**  | ✓ |  |
|SMTP information|  | ✓ | ✓ (frontend only) |
|Public domain name|  |  | ✓ (frontend only) |
|Subdomain names| **kpi, kc, ee**  |  | ✓ (frontend only) |
|Use HTTPS| **No**  |  | ✓ (frontend only) |
|Super user's username| **super_admin** | ✓ | ✓ (frontend only) |
|Super user's password| **Random string**  | ✓ | ✓ (frontend only) |

### Advanced Options

|Option|Default|Workstation|Server
|---|---|---|---|
|Webserver port| **80**  | ✓ |  |
|Network interface|  **Autodetected**  | ✓ | ✓ (frontend only) |
|Use separate servers| **No**  |  | ✓ |
|Use DNS for private routes| **No**  |  | ✓ (frontend only) |
|Backend server IP _(if previous answer is no)_| **Local IP**  |  | ✓ (frontend only) |
|Postgres DB|  **kobo**  | ✓ | ✓ |
|Postgres user|  **kobo**  | ✓ | ✓ |
|Postgres password|  **kobo**  | ✓ | ✓ |
|Use AWS storage|  **No**  | ✓ | ✓ (frontend only) |
|uWGI workers|  **start: 2, max: 4**  | ✓ | ✓ (frontend only) |
|Google UA|  | ✓ | ✓ (frontend only) |
|Google API Key|  | ✓ | ✓ (frontend only) |
|Intercom| | ✓ | ✓ (frontend only) |
|Raven tokens|   | ✓ | ✓ (frontend only) |
|Debug|  **False**  | ✓ | ✓ (frontend only) |
|Developer mode|  **False**  | ✓ | |

## Requirements

- Linux / macOS
- Python 2.7+
- [Docker](https://www.docker.com/get-started "") & [Docker Compose](https://docs.docker.com/compose/install/ "")
- Available TCP Ports:

    1. 80 NginX (or chosen custom port in advanced options)
    2. 5432 PostgreSQL
    3. 5672 RabbitMQ
    4. 6379-6380 redis
    5. 27000 MongoDB

## To-Do

- Handle postgres replication
- Add better input validations
- Stop docker containers with command
- Add option to force update `kobo-docker` repo without rebuilding the config
- Support existing configurations
- Adds comments in the code
- Create command line help
- Tests

## Known issues

- SMTP user is "None" in envfiles when empty
- replication in postgres failed
- script does not work when it's not launched from `kobo-install` repository
