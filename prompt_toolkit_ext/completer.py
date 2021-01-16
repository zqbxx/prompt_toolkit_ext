from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completion
from prompt_toolkit.formatted_text import HTML
from typing import Callable, Dict, Iterable, List, Optional, Pattern, Union


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
