# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import shutil
import sys
import tempfile

from helpers.cli import CLI
from helpers.config import Config


class Setup:
    KOBO_DOCKER_BRANCH = "master"

    @classmethod
    def run(cls, config):
        """
        Clone or pull `kobo-docker` project in installation directory
        :param config: dict
        """

        if not os.path.isdir(os.path.join(config["kobodocker_path"], ".git")):
            # Move unique id file to /tmp in order to clone without errors
            # (e.g. not empty directory)
            tmp_dirpath = tempfile.mkdtemp()
            os.rename(os.path.join(config["kobodocker_path"], Config.UNIQUE_ID_FILE),
                      os.path.join(tmp_dirpath, Config.UNIQUE_ID_FILE))

            # clone project
            git_command = [
                "git", "clone", "https://github.com/kobotoolbox/kobo-docker",
                config["kobodocker_path"]
            ]
            CLI.run_command(git_command, cwd=os.path.dirname(config["kobodocker_path"]))

            os.rename(os.path.join(tmp_dirpath, Config.UNIQUE_ID_FILE),
                      os.path.join(config["kobodocker_path"], Config.UNIQUE_ID_FILE))
            shutil.rmtree(tmp_dirpath)

        if os.path.isdir(os.path.join(config["kobodocker_path"], ".git")):
            # checkout branch
            git_command = ["git", "checkout", "--force", Setup.KOBO_DOCKER_BRANCH]
            CLI.run_command(git_command, cwd=config["kobodocker_path"])

            # update code
            git_command = ["git", "pull", "origin", Setup.KOBO_DOCKER_BRANCH]
            CLI.run_command(git_command, cwd=config["kobodocker_path"])

    @classmethod
    def update_hosts(cls, config):

        if config.get("local_installation") == Config.TRUE:
            start_sentence = "### (BEGIN) KoBoToolbox local routes"
            end_sentence = "### (END) KoBoToolbox local routes"

            with open("/etc/hosts", "r") as f:
                tmp_host = f.read()

            start_position = tmp_host.find(start_sentence)
            end_position = tmp_host.find(end_sentence)

            if start_position > -1:
                tmp_host = tmp_host[0: start_position] + tmp_host[end_position + len(end_sentence) + 1:]

            routes = "{ip_address}  " \
                     "{kpi_subdomain}.{public_domain_name} " \
                     "{kc_subdomain}.{public_domain_name} " \
                     "{ee_subdomain}.{public_domain_name}".format(
                        ip_address=config.get("local_interface_ip"),
                        public_domain_name=config.get("public_domain_name"),
                        kpi_subdomain=config.get("kpi_subdomain"),
                        kc_subdomain=config.get("kc_subdomain"),
                        ee_subdomain=config.get("ee_subdomain")
            )

            tmp_host = ("{bof}"
                        "\n{start_sentence}"
                        "\n{routes}"
                        "\n{end_sentence}"
                        ).format(
                bof=tmp_host.strip(),
                start_sentence=start_sentence,
                routes=routes,
                end_sentence=end_sentence
            )

            with open("/tmp/etchosts", "w") as f:
                f.write(tmp_host)

            if config.get("review_host") != Config.FALSE:
                CLI.colored_print("╔═══════════════════════════════════════════════════════════════════╗",
                                  CLI.COLOR_WARNING)
                CLI.colored_print("║ Administrative privileges are required to update your /etc/hosts. ║",
                                  CLI.COLOR_WARNING)
                CLI.colored_print("╚═══════════════════════════════════════════════════════════════════╝",
                                  CLI.COLOR_WARNING)
                CLI.colored_print("Do you want to review your /etc/hosts file before overwriting it?",
                                  CLI.COLOR_SUCCESS)
                CLI.colored_print("\t1) Yes")
                CLI.colored_print("\t2) No")
                config["review_host"] = CLI.get_response([Config.TRUE, Config.FALSE],
                                                         config.get("review_host", Config.FALSE))
                if config["review_host"] == Config.TRUE:
                    print(tmp_host)
                    CLI.colored_input("Press any keys when ready")

                # Save 'review_host'
                config_ = Config()
                config_.write_config()

            return_value = os.system("sudo mv /etc/hosts /etc/hosts.old && sudo mv /tmp/etchosts /etc/hosts")
            if return_value != 0:
                sys.exit()
