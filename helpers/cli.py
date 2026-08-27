# -*- coding: utf-8 -*-
import curses
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

    @staticmethod
    def is_interactive():
        """
        Checks whether a real terminal is attached on both ends.

        `curses` reads from stdin and draws on stdout, so a run with either one
        redirected (a pipe, a file, a CI step, an agent shell) has nowhere to
        put the menu.

        Returns:
            bool
        """
        return sys.stdin.isatty() and sys.stdout.isatty()

    @staticmethod
    def checkbox_menu(question, choices):
        """
        Interactive checkbox menu navigable with the keyboard.

        Args:
            question (str): Title displayed at the top.
            choices (list): List of dicts, either:
                {'label': str, 'checked': bool, 'description': str (optional)}
                                                 — selectable item
                {'separator': str}               — non-selectable section header

            The optional 'description' is shown in a help line at the bottom
            while the item is highlighted.

        Returns:
            list: Labels of selected items, or None if cancelled (Esc/q).
        """
        state = [dict(c) for c in choices]
        selectable = [i for i, s in enumerate(state) if 'label' in s]

        def _init_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_YELLOW, -1)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, -1, -1)
            curses.init_pair(5, curses.COLOR_CYAN, -1)
            curses.init_pair(6, curses.COLOR_BLUE, -1)

        def _list_height(height, show_info):
            # Reserve two bottom rows for the description only when info is shown.
            return max(1, height - 3 - (2 if show_info else 0))

        def _safe_addstr(stdscr, y, x, text, attr=0):
            # A window too small for the layout makes `addstr` raise. Drawing
            # only what fits keeps the menu usable instead of killing setup.
            height, _ = stdscr.getmaxyx()
            if not 0 <= y < height:
                return
            try:
                stdscr.addstr(y, x, text, attr)
            except curses.error:
                pass

        def _draw(stdscr, current, scroll_offset, show_info):
            stdscr.erase()
            height, width = stdscr.getmaxyx()

            _safe_addstr(stdscr, 0, 0, question[:width - 1],
                         curses.color_pair(1) | curses.A_BOLD)
            hint = ('↑↓ navigate   SPACE toggle   A all/none   '
                    'i info   ENTER confirm   q cancel')
            _safe_addstr(stdscr, 1, 0, hint[:width - 1],
                         curses.color_pair(5))
            _safe_addstr(stdscr, 2, 0, '─' * min(width - 1, 60),
                         curses.color_pair(4))

            list_height = _list_height(height, show_info)
            for i, item in enumerate(state[scroll_offset:scroll_offset + list_height]):
                row = i + 3
                idx = i + scroll_offset
                if 'separator' in item:
                    _safe_addstr(stdscr, row, 0,
                                 f"  {item['separator']}"[:width - 1],
                                 curses.color_pair(6) | curses.A_BOLD)
                else:
                    checkbox = '[x]' if item['checked'] else '[ ]'
                    line = f'  {checkbox}  {item["label"]}'
                    if idx == current:
                        attr = curses.color_pair(2) | curses.A_BOLD
                    elif item['checked']:
                        attr = curses.color_pair(3)
                    else:
                        attr = curses.color_pair(4)
                    _safe_addstr(stdscr, row, 0, line[:width - 1], attr)

            # Description help line for the highlighted item (toggled with 'i').
            if show_info:
                description = state[current].get('description', '') \
                    if 'label' in state[current] else ''
                description = description or '(no description)'
                _safe_addstr(stdscr, height - 2, 0,
                             '─' * min(width - 1, 60),
                             curses.color_pair(4))
                _safe_addstr(stdscr, height - 1, 0,
                             description[:width - 1],
                             curses.color_pair(5))

            stdscr.refresh()

        def _nearest_selectable(pos, direction):
            idx = pos + direction
            while 0 <= idx < len(state):
                if 'label' in state[idx]:
                    return idx
                idx += direction
            return pos

        def _run(stdscr):
            curses.curs_set(0)
            _init_colors()
            current = selectable[0] if selectable else 0
            scroll_offset = 0
            show_info = False

            while True:
                height, _ = stdscr.getmaxyx()
                list_height = _list_height(height, show_info)

                if current < scroll_offset:
                    scroll_offset = current
                elif current >= scroll_offset + list_height:
                    scroll_offset = current - list_height + 1

                _draw(stdscr, current, scroll_offset, show_info)
                key = stdscr.getch()

                if key == curses.KEY_UP:
                    current = _nearest_selectable(current, -1)
                elif key == curses.KEY_DOWN:
                    current = _nearest_selectable(current, 1)
                elif key in (ord('i'), ord('I')):
                    show_info = not show_info
                elif key == ord(' ') and 'label' in state[current]:
                    state[current]['checked'] = not state[current]['checked']
                elif key in (ord('a'), ord('A')):
                    all_on = all(s['checked'] for s in state if 'label' in s)
                    for s in state:
                        if 'label' in s:
                            s['checked'] = not all_on
                elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                    return [s['label'] for s in state if 'label' in s and s['checked']]
                elif key in (27, ord('q')):
                    return None

        try:
            return curses.wrapper(_run)
        except KeyboardInterrupt:
            # Same outcome as ESC/`q`: nothing selected, nothing written.
            # `wrapper` has already restored the terminal by the time we land
            # here, so the caller's message prints on a clean screen.
            return None
