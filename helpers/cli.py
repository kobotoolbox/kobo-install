# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import subprocess
import sys
import re

PY2 = sys.version_info[0] == 2
if PY2:
    input = raw_input
    string_type = unicode
else:
    string_type = str


class CLI(object):

    NO_COLOR = '\033[0m'
    COLOR_ERROR = '\033[91m'
    COLOR_SUCCESS = '\033[92m'
    COLOR_INFO = '\033[94m'
    COLOR_WARNING = '\033[95m'

    EMPTY_CHARACTER = '-'

    DEFAULT_CHOICES = {
        '1': True,
        '2': False,
    }
    DEFAULT_RESPONSES = dict((v, k) for k, v in DEFAULT_CHOICES.items())

    @classmethod
    def get_response(cls, validators=None, default='', to_lower=True,
                     error_msg="Sorry, I didn't understand that!"):

        use_default = False
        # If not validators are provided, let's use default validation
        # "Yes/No", where "Yes" equals 1, and "No" equals 2
        # Example:
        #   Are you sure?
        #       1) Yes
        #       2) No
        if validators is None:
            use_default = True
            default = cls.DEFAULT_RESPONSES[default]
            validators = cls.DEFAULT_CHOICES.keys()

        while True:
            try:
                response = cls.colored_input('', cls.COLOR_WARNING, default)
                print(type(response))
                print(response)

                if (response.lower() in map(lambda x: x.lower(), validators) or
                        validators is None or
                        (isinstance(validators, string_type) and
                         validators.startswith('~') and
                         re.match(validators[1:], response)
                         )):
                    break
                else:
                    cls.colored_print(error_msg,
                                      cls.COLOR_ERROR)
            except ValueError:
                cls.colored_print("Sorry, I didn't understand that.",
                                  cls.COLOR_ERROR)

        if use_default:
            return cls.DEFAULT_CHOICES[response]

        return response.lower() if to_lower else response

    @classmethod
    def colored_print(cls, message, color=NO_COLOR):
        print(cls.colorize(message, color))

    @classmethod
    def colored_input(cls, message, color=NO_COLOR, default=None):
        text = cls.get_message_with_default(message, default)
        input_ = input(cls.colorize(text, color))

        # User wants to delete value previously entered.
        if input_ == '-':
            default = ''
            input_ = ''

        return input_ if input_ is not None and input_ != '' else default

    @classmethod
    def colorize(cls, message, color=NO_COLOR):
        return '{}{}{}'.format(color, message, cls.NO_COLOR)

    @classmethod
    def get_message_with_default(cls, message, default):
        message = '{} '.format(message) if message else ''
        default = '{}[{}]{}: '.format(cls.COLOR_WARNING,
                                      default,
                                      cls.NO_COLOR) \
            if default else ''

        if message:
            message = '{}: '.format(message.strip()) if not default else message

        return '{}{}'.format(message, default)

    @classmethod
    def run_command(cls, command, cwd=None, polling=False):
        if polling:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=cwd)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    if PY2:
                        print(output.strip())
                    else:
                        print(output.decode().strip())
            return process.poll()
        else:
            try:
                stdout = subprocess.check_output(command,
                                                 universal_newlines=True,
                                                 cwd=cwd)
            except subprocess.CalledProcessError as cpe:
                # Error will be display by above command.
                # ^^^ this doesn't seem to be true? let's write it explicitly
                # see https://docs.python.org/3/library/subprocess.html#subprocess.check_output
                sys.stderr.write(cpe.output)
                cls.colored_print('An error has occurred', CLI.COLOR_ERROR)
                sys.exit(1)
            return stdout
