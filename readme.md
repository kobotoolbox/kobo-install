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
[ ] Advanced options on macOS
[ ] Fix postgres replication user creation
[ ] Local configuration with ip address (is it necessary?)
[ ] Support existing configurations
[ ] Handle backend and frontend env

### Known issues

- SMTP user is "None" in envfiles when empty
- replication in postgres failed
- script does not work when it's not launched from `kobo-install` repository