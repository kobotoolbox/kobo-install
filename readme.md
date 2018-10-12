The purpose of the repo is to install `KoboToolbox` in minutes without messing with configuration files.
It prompts the user to answer some questions to create configuration files automatically.

It can be run with simple command

`$kobo-install> python run.py`

**This utility is an beta release**

## Requirements

- Linux / macOS
- Python 2.7+/3.4+
- [Docker](https://www.docker.com/get-started "") & [Docker Compose](https://docs.docker.com/compose/install/ "")

### To-Do

[ ] Add better documentation
[x] Block start when user is not connected to network
[x] Add summary before starting env
[x] Autodetect network changes in local env  
[x] Automatically start env  
[ ] Tests  
[x] Developer mode. Add paths to kobocat and kpi in override composer file  
[x] Advanced network on macOS. Use `netiface`?  
[ ] Fix postgres replication user creation  
[x] Handle multi environments (frontend on one server and backend on another)  
[ ] Better input validations  
[ ] Stop docker containers with command  
[ ] Support existing configurations  
[ ] Local configuration with ip address (is it necessary?)
[ ] Developer mode: Add watcher to reload uWSGI

### Known issues

- replication in postgres failed
- script does not work when it's not launched from `kobo-install` repository
- sometimes frontend containers can not communicate with backend containers. Restarting all containers fixes it.
- Using same NginX port crashes
- Re-use existing folder gives permission denied
