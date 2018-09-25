# -*- coding: utf-8 -*-
import os

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
            git_command = [
                "git", "clone", "https://github.com/kobotoolbox/kobo-docker",
                config["kobodocker_path"]
            ]
            CLI.run_command(git_command, cwd=os.path.dirname(config["kobodocker_path"]))

        if os.path.isdir("{}/.git".format(config["kobodocker_path"])):
            # update code
            git_command = ["git", "fetch", "--tags", "--prune"]
            CLI.run_command(git_command, cwd=config["kobodocker_path"])

            # checkout branch
            git_command = ["git", "checkout", "--force", Setup.KOBO_DOCKER_BRANCH]
            CLI.run_command(git_command, cwd=config["kobodocker_path"])