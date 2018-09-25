# -*- coding: utf-8 -*-
import os
import subprocess

from helpers.cli import CLI

class Setup:

    KOBO_DOCKER_BRANCH = "multi_compose"

    @classmethod
    def run(cls, config):
        """

        :param config: dict
        """
        if not os.path.isdir("{}/.git".format(config["kobodocker_path"])):
            # clone project
            try:
                git_command = [
                    "git", "clone", "https://github.com/kobotoolbox/kobo-docker",
                    config["kobodocker_path"]
                ]
                subprocess.check_output(git_command, universal_newlines=True,
                                        cwd=os.path.dirname(config["kobodocker_path"]))
            except subprocess.CalledProcessError as cpe:
                CLI.colored_print(cpe.output, CLI.COLOR_ERROR)

        # update project
        if os.path.isdir("{}/.git".format(config["kobodocker_path"])):
            try:
                git_command = ["git", "fetch", "--tags", "--prune"]
                subprocess.check_output(
                    git_command, universal_newlines=True, cwd=config["kobodocker_path"]
                )
                git_command = ["git", "checkout", "--force", Setup.KOBO_DOCKER_BRANCH]
                subprocess.check_output(
                    git_command, universal_newlines=True, cwd=config["kobodocker_path"]
                )
            except subprocess.CalledProcessError as cpe:
                CLI.colored_print(cpe.output, CLI.COLOR_ERROR)