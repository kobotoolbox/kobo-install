The purpose of the repo is to install `KoboToolbox` in minutes without messing with configuration files.
It prompts the user to answer some questions to create configuration files automatically.

## Requirements

- Linux/macOS
- Python 2.7+

**This utility is in alpha release.**

### To-Do

[ ] Add summary before starting env
[ ] Automatically start env
[ ] Tests
[ ] Advanced options on macOS
[ ] Fix postgres replication user creation
[ ] Local configuration with ip address (is it necessary?)
[ ] Support existing configurations

### Known issues

- smtp user is "None" in envfiles when empty
- replication in postgres failed