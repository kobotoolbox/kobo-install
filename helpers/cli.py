# -*- coding: utf-8 -*-
import re
import subprocess
import sys

if sys.version_info.major < 3:
    input = raw_input


class CLI(object):

    NO_COLOR = "\033[0m"
    COLOR_ERROR = "\033[91m"
    COLOR_SUCCESS = "\033[92m"
    COLOR_INFO = "\033[94m"
    COLOR_WARNING = "\033[95m"

    @classmethod
    def get_response(cls, validators=None, default=""):
    
        response = None
    
        while True:
            try:
                response = cls.colored_input("", cls.COLOR_WARNING, default)
                if response.lower() in map(lambda x:x.lower(), validators) or validators is None or \
                    (isinstance(validators, str) and validators.startswith("~") and re.match(validators[1:], response)):
                    break
                else:
                    cls.colored_print("Sorry, I didn't understand that!", cls.COLOR_ERROR)
                    continue
            except ValueError:
                cls.colored_print("Sorry, I didn't understand that.", cls.COLOR_ERROR)
                continue
            else:
                break
    
        return response.lower()

    @classmethod
    def colored_print(cls, message, color=NO_COLOR):
        print(cls.colorize(message, color))

    @classmethod
    def colored_input(cls, message, color=NO_COLOR, default=None):
        text = cls.get_message_with_default(message, default)
        input_ = input(cls.colorize(text, color))
        return input_ if input_ is not None and input_ != "" else default

    @classmethod
    def colorize(cls, message, color=NO_COLOR):
        return "{}{}{}".format(color, message, cls.NO_COLOR)

    @classmethod
    def get_message_with_default(cls, message, default):
        message = "{} ".format(message) if message else ""
        default = "{}[{}]{}: ".format(cls.COLOR_WARNING, default, cls.NO_COLOR) if default else ""

        if message:
            message = "{}: ".format(message.strip()) if not default else message

        return "{}{}".format(message, default)

    @classmethod
    def run_command(cls, command, cwd=None):
        try:
            subprocess.check_output(command, universal_newlines=True, cwd=cwd)
        except subprocess.CalledProcessError as cpe:
            cls.colored_print(cpe.output, CLI.COLOR_ERROR)
            return False
        return True
