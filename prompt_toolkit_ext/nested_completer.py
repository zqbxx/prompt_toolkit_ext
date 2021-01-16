from prompt_toolkit.completion import NestedCompleter

from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completer, Completion
from typing import Dict, Iterable, Optional

from prompt_toolkit_ext import PromptCompleter


class PromptNestedCompleter(NestedCompleter):

    def set_help_info(self, help_info):
        self.help_info = help_info

    @classmethod
    def from_nested_dict(cls, data, help):

        options: Dict[str, Optional[Completer]] = {}
        for key, value in data.items():
            if isinstance(value, Completer):
                options[key] = value
            elif isinstance(value, dict):
                options[key] = cls.from_nested_dict(value, help[key])
                options[key].set_help_info(help[key])
            elif isinstance(value, set):
                options[key] = cls.from_nested_dict({item: None for item in value}, help[key])
                options[key].set_help_info(help[key])
            else:
                assert value is None
                options[key] = None

        return cls(options)

    def get_completions(
            self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a space, check for the first term, and use a
        # subcompleter.
        # 检查字符串是否以-开头，处理平级的参数（多个参数会进行递归调用）
        if " " in text and not text.startswith('-'):
            first_term = text.split()[0]
            completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term):].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                for c in completer.get_completions(new_document, complete_event):
                    yield c

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = PromptCompleter(
                list(self.options.keys()), ignore_case=self.ignore_case, match_middle=True
            )
            completer.set_help_info(self.help_info)
            for c in completer.get_completions(document, complete_event):
                yield c

