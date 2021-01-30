from prompt_toolkit.completion import WordCompleter, Completer
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.utils import get_cwidth

from typing import Callable, Dict, Iterable, List, Optional, Pattern, Union

import csv
from io import StringIO
from prompt_toolkit_ext import PromptArgumentParser
from prompt_toolkit_ext.utils import fill_right


class ArgParserCompleter(Completer):

    def __init__(
        self,
        parser: PromptArgumentParser,
        ignore_case: bool = False,
        match_middle: bool = False,
    ) -> None:

        self.parser = parser
        self.ignore_case = ignore_case
        self.match_middle = match_middle

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:

        parser = self.parser

        word_before_cursor = document.get_word_before_cursor()
        text = document.text_before_cursor.lstrip()

        if self.ignore_case:
            text = text.lower()

        buff = StringIO(text)
        reader = csv.reader(buff, delimiter=' ')
        args = None
        for line in reader:
            args = line
            break

        if args is None or len(args) == 0:
            return

        def remove_parent_args(args, parser):
            cur_cmd_pos = -1
            cur_parser = parser
            for i, arg in enumerate(args):
                # 遍历命令行数组，找到最近一个parser
                subparser = parser.get_subparser_by_command(arg, like=False)
                if subparser is not None:
                    cur_cmd_pos = i
                    cur_parser = subparser
                elif cur_cmd_pos == -1:
                    return args, parser
                else:
                    if cur_cmd_pos == len(args) - 1:
                        return [], cur_parser
                    return args[(cur_cmd_pos + 1):], cur_parser
            return args, parser

        # 在当前命令有子命令的时候移除父命令，保留子命令
        current_args, current_parser = remove_parent_args(args, parser)

        if len(current_args) == 0:
            return

        command = current_args[0]

        # 可能是命令
        if len(current_args) == 1:
            subparsers = current_parser.get_subparser_by_command(command, like=True)
            if subparsers is not None:
                for c, _ in subparsers.items():
                    yield Completion(c, -len(word_before_cursor), style='fg:blue', selected_style="fg:white bg:blue")

        # 检查上一次值，如果为参数则提示输入值
        cur_text = current_args[-1]
        if len(current_args) > 1:
            last_text = current_args[-2]
            if last_text.startswith('-'):
                yield Completion('', -len(word_before_cursor), '<input option value>')

        # 获得已经使用过的参数，避免重复出现
        exists_opts = []
        for arg in current_args:
            if arg.startswith('-'):
                exists_opts.append(arg)

        # TODO 判断路径，返回PathCompleter
        # TODO 判断参数类型，显示提示

        # 获取所有可用的参数
        opt_groups = current_parser.get_parser_opts(cur_text)
        completions_dict = []
        max_text_width = 0
        for opt_group in opt_groups:

            opt_strings = opt_group.get('opt_strings')
            help_info = opt_group.get('help_info')
            for opt in opt_strings:
                if opt not in ['-h', '--help'] and opt not in exists_opts:
                    text_width = get_cwidth(opt)
                    if text_width > max_text_width:
                        max_text_width = text_width
                    completions_dict.append({'text': opt, 'display': help_info})
                else:
                    break

        for c in completions_dict:
            text = c.get('text')
            display = fill_right(text, max_text_width) + ' ' + c.get('display')
            yield Completion(text, -len(cur_text),
                             display=display,
                             style='fg:blue',
                             selected_style="fg:white bg:blue")


class PromptCompleter(WordCompleter):

    def __init__(
            self,
            words: Union[List[str], Callable[[], List[str]]],
            ignore_case: bool = False,
            meta_dict: Optional[Dict[str, str]] = None,
            WORD: bool = False,
            sentence: bool = False,
            match_middle: bool = False,
            pattern: Optional[Pattern[str]] = None,
            help_info=None
    ) -> None:
        super(PromptCompleter, self).__init__(words, ignore_case, meta_dict, WORD, sentence, match_middle, pattern)
        self.help_info = help_info

    def set_help_info(self, help_info):
        self.help_info = help_info

    def get_completions(
            self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # Get list of words.
        words = self.words
        if callable(words):
            words = words()

        # Get word/text before cursor.
        if self.sentence:
            word_before_cursor = document.text_before_cursor
        else:
            word_before_cursor = document.get_word_before_cursor(
                WORD=self.WORD, pattern=self.pattern
            )

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word: str) -> bool:
            """ True when the word before the cursor matches. """
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)

        for a in words:
            if word_matches(a):
                text = ''
                if self.help_info:
                    if a in self.help_info:
                        try:
                            text = self.help_info[a]['help']
                        except:
                            # 忽略错误信息
                            pass
                yield Completion(
                    a, -len(word_before_cursor),
                    display=HTML('<b>' + a + '</b>---' + text + ''))
