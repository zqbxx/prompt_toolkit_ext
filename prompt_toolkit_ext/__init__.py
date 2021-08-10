import csv
from argparse import ArgumentParser
from io import StringIO
from typing import List, Callable

from prompt_toolkit.completion import Completer
from prompt_toolkit.history import History
from prompt_toolkit import prompt
from prompt_toolkit.lexers import Lexer

from .file_history import LimitSizeFileHistory
from .arg_parser import PromptArgumentParser
from .completer import PromptCompleter
from .nested_completer import PromptNestedCompleter


def run_prompt(prompt_parser: PromptArgumentParser,
               prompt_history: History = None,
               prompt_completer: Completer = None,
               prompt_lexer: Lexer = None):

    while True:

        user_input = prompt('# ',
                            history=prompt_history,
                            completer=prompt_completer,
                            lexer=prompt_lexer)

        if len(user_input.strip()) == 0:
            continue

        lines = user_input.split('\n')

        for line in lines:
            if line is None or len(line.strip()) == 0:
                continue
            run_line(prompt_parser, line)


def run_line(parser: PromptArgumentParser, line: str):
    buff = StringIO(line)
    reader = csv.reader(buff, delimiter=' ')
    arg_array = None
    for arg_array in reader:
        pass
    try:
        parser.clear_error_flag()
        args = parser.parse_args(arg_array)
        if not parser.has_error_flag():
            if hasattr(args, 'func'):
                args.func(args)
    except TypeError as e:
        print(e)


class ActionNotAllowedException(Exception):

    def __init__(self, msg: str, func: Callable):
        self.msg = msg
        self.func = func

    def __str__(self):
        return self.msg


__all__ = [
    "LimitSizeFileHistory",
    "PromptArgumentParser",
    "PromptCompleter",
    "PromptNestedCompleter",
]



