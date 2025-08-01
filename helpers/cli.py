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
    def run_command(cls, command, cwd=None, polling=False, verbose=0, show_command=False):
        """
        Run a command with optional verbosity levels
        
        Args:
            command: Command list to execute
            cwd: Working directory
            polling: If True, show real-time output and return exit code
            verbose: Verbosity level (0=minimal, 1=normal, 2=detailed)
            show_command: If True, show the command being executed
        """
        import time
        
        # Only show verbose output if explicitly requested
        if show_command or verbose >= 1:
            command_str = ' '.join(command) if isinstance(command, list) else command
            cls.colored_print(f"🔧 Executing: {command_str}", cls.COLOR_INFO)
        
        start_time = time.time()
        
        if polling:
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                cwd=cwd,
                universal_newlines=True
            )
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if verbose >= 2:
                        # Show detailed output with timestamps
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] {line}")
                    else:
                        print(line)
            
            exit_code = process.poll()
            elapsed_time = time.time() - start_time
            
            # Only show timing info if verbose
            if verbose >= 1:
                if exit_code == 0:
                    cls.colored_print(f"✅ Command completed in {elapsed_time:.2f}s", cls.COLOR_SUCCESS)
                else:
                    cls.colored_print(f"❌ Command failed with exit code {exit_code} after {elapsed_time:.2f}s", cls.COLOR_ERROR)
            
            return exit_code
        else:
            try:
                stdout = subprocess.check_output(command,
                                                 universal_newlines=True,
                                                 stderr=subprocess.STDOUT,
                                                 cwd=cwd)
                elapsed_time = time.time() - start_time
                
                # Only show timing info if verbose
                if verbose >= 1:
                    cls.colored_print(f"✅ Command completed in {elapsed_time:.2f}s", cls.COLOR_SUCCESS)
                
                return stdout
            except subprocess.CalledProcessError as cpe:
                elapsed_time = time.time() - start_time
                sys.stderr.write(cpe.output)
                
                if verbose >= 1:
                    cls.colored_print(f"❌ Command failed after {elapsed_time:.2f}s", cls.COLOR_ERROR)
                else:
                    cls.colored_print('An error has occurred', cls.COLOR_ERROR)
                sys.exit(1)

    @classmethod
    def yes_no_question(cls, question, default=True,
                        labels=['Yes', 'No']):
        cls.colored_print(question, color=cls.COLOR_QUESTION)
        for index, label in enumerate(labels):
            choice_number = index + 1
            cls.colored_print(f'\t{choice_number}) {label}')
        return cls.get_response(default=default)

    @classmethod
    def progress_message(cls, message, status="info"):
        """
        Display a progress message with appropriate emoji and color
        
        Args:
            message: The message to display
            status: 'info', 'success', 'error', 'warning'
        """
        icons = {
            'info': '🔧',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        }
        
        colors = {
            'info': cls.COLOR_INFO,
            'success': cls.COLOR_SUCCESS,
            'error': cls.COLOR_ERROR,
            'warning': cls.COLOR_WARNING
        }
        
        icon = icons.get(status, '🔧')
        color = colors.get(status, cls.COLOR_INFO)
        
        cls.colored_print(f"{icon} {message}", color)

    @classmethod
    def print_step(cls, step_number, total_steps, message, verbose=0):
        """
        Print a numbered step with progress indication
        
        Args:
            step_number: Current step number
            total_steps: Total number of steps
            message: Step description
            verbose: Verbosity level
        """
        if verbose >= 1:
            progress = f"[{step_number}/{total_steps}]"
            cls.colored_print(f"{progress} {message}", cls.COLOR_INFO)
        else:
            cls.progress_message(message, "info")
