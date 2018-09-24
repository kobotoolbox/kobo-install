# -*- coding: utf-8 -*-
import json
import os
import stat

from helpers.cli import CLI


class Config:

    CONFIG_FILE = ".run.conf"

    @classmethod
    def read_config(cls):
        config = {}
        try:
            with open(cls.CONFIG_FILE, "r") as f:
                config = json.loads(f.read())
        except Exception as e:
            pass

        return config

    @classmethod
    def write_config(cls, config):
        try:
            with open(cls.CONFIG_FILE, "w") as f:
                f.write(json.dumps(config))

            os.chmod(cls.CONFIG_FILE, stat.S_IWRITE | stat.S_IREAD)

        except Exception as e:
            print(str(e))
            CLI.colored_print("Could not write configuration file", CLI.COLOR_ERROR)
            return False

        return True
