# -*- coding: utf-8 -*-
import subprocess
import sys
import re
import textwrap


class CLI:

    NO_COLOR = '\033[0;0m'
    COLOR_ERROR = '\033[0;31m'  # dark red
    COLOR_SUCCESS = '\033[0;32m'  # dark green
    COLOR_INFO = '\033[1;34m'  # blue
    COLOR_WARNING = '\033[1;31m'  # red
    COLOR_QUESTION = '\033[1;33m'  # dark yellow
    COLOR_DEFAULT = '\033[1;37m'  # white

    EMPTY_CHARACTER = '-'

    DEFAULT_CHOICES = {
        '1': True,
        '2': False,
    }
    # We need an inverted dict version of `DEFAULT_CHOICES` to be able to
    # retrieve keys from the values
    DEFAULT_RESPONSES = dict(zip(DEFAULT_CHOICES.values(),
                                 DEFAULT_CHOICES.keys()))

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
    def colored_print(cls, message, color=NO_COLOR):
        print(cls.colorize(message, color))

    @classmethod
    def colorize(cls, message, color=NO_COLOR):
        return f'{color}{message}{cls.NO_COLOR}'

    @classmethod
    def framed_print(cls, message, color=COLOR_WARNING, columns=70):
        border = '═' * (columns - 2)
        blank_line = ' ' * (columns - 2)
        framed_message = [
            f'╔{border}╗',
            f'║{blank_line}║',
        ]

        if not isinstance(message, list):
            paragraphs = message.split('\n')
        else:
            paragraphs = ''.join(message).split('\n')

        for paragraph in paragraphs:
            if paragraph == '':
                framed_message.append(
                    f'║{blank_line}║'
                )
                continue

            for line in textwrap.wrap(paragraph, columns - 4):
                message_length = len(line)
                spacer = ' ' * (columns - 4 - message_length)
                framed_message.append(
                    f'║ {line}{spacer} ║'
                )

        framed_message.append(f'║{blank_line}║')
        framed_message.append(f'╚{border}╝')
        cls.colored_print('\n'.join(framed_message), color=color)

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
                response = cls.colored_input('', cls.COLOR_QUESTION, default)

                if (
                    response.lower() in map(lambda x: x.lower(), validators)
                    or validators is None
                    or (
                        isinstance(validators, str)
                        and validators.startswith('~')
                        and re.match(validators[1:], response)
                    )
                ):
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
    def get_message_with_default(cls, message, default):
        message = f'{message} ' if message else ''

        if default is None:
            default = ''
        else:
            default = '{white}[{off}{default}{white}]{off}: '.format(
                white=cls.COLOR_DEFAULT,
                off=cls.NO_COLOR,
                default=default
            )

        if message:
            message = f'{message.strip()}: ' if not default else message

        return f'{message}{default}'

    @classmethod
    def run_command(cls, command, cwd=None, polling=False):
        if polling:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=cwd)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
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

    @classmethod
    def yes_no_question(cls, question, default=True,
                        labels=['Yes', 'No']):
        cls.colored_print(question, color=cls.COLOR_QUESTION)
        for index, label in enumerate(labels):
            choice_number = index + 1
            cls.colored_print(f'\t{choice_number}) {label}')
        return cls.get_response(default=default)
