from prompt_toolkit.widgets import RadioList as _RadioList
from typing import Sequence, Tuple
from prompt_toolkit.widgets.base import _T
from prompt_toolkit.formatted_text import AnyFormattedText


class RadioList(_RadioList):

    def __init__(self, values: Sequence[Tuple[_T, AnyFormattedText]]) -> None:
        super().__init__(values)
        self.handlers = []

    def up(self) -> None:
        self._selected_index = max(0, self._selected_index - 1)

    def down(self) -> None:
        self._selected_index = min(len(self.values) - 1, self._selected_index + 1)

    def get_selected_index(self) -> int:
        return self._selected_index

    def get_selected_item(self) -> Tuple[_T, AnyFormattedText]:
        return self.values[self.get_selected_index()]

    def set_selected_index(self, index: int):
        self._selected_index = index
        self.current_value = self.values[self._selected_index][0]

    def add_enter_handle(self, enter_handler):
        self.handlers.append(enter_handler)

    def _handle_enter(self) -> None:

        old_value = None
        for value in self.values:
            if value[0] == self.current_value:
                old_value = value

        new_value = self.values[self._selected_index]
        for handler in self.handlers:
            ret = handler('enter', old_value, new_value)
            if not ret:
                return
        super()._handle_enter()

        for handler in self.handlers:
            handler('selected', old_value, new_value)
