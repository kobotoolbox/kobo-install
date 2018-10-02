The purpose of the repo is to install `KoboToolbox` in minutes without messing with configuration files.
It prompts the user to answer some questions to create configuration files automatically.

It can be run with simple command

`$kobo-install> python run.py`

**This utility is an alpha release**

## Requirements

- Linux/macOS
- Python 2.7+

### To-Do

[x] Add summary before starting env
[ ] Autodetect network changes in local env
[x] Automatically start env
[ ] Tests
[ ] Developer mode. Add paths to kobocat and kpi in override composer file
[x] Advanced network on macOS. Use `netiface`?
[ ] Fix postgres replication user creation
[ ] Handle multi environments (frontend on one server and backend on another)
[ ] Better input validations
[ ] Stop docker containers with command
[ ] Support existing configurations
[ ] Local configuration with ip address (is it necessary?)

### Known issues

- SMTP user is "None" in envfiles when empty
- replication in postgres failed
- script does not work when it's not launched from `kobo-install` repository