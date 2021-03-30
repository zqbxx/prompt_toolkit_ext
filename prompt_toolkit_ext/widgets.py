from typing import Sequence, Tuple, List
import qrcode
from axel import Event

from prompt_toolkit.widgets import RadioList as _RadioList
from prompt_toolkit.widgets.base import _T
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.formatted_text import (
    AnyFormattedText,
    StyleAndTextTuples,
    to_formatted_text,
)


class RadioList(_RadioList):

    def __init__(self, values: Sequence[Tuple[_T, AnyFormattedText]]) -> None:
        super().__init__(values)
        self.handlers = []
        self.check_event = Event()

    def up(self) -> None:
        self._selected_index = max(0, self._selected_index - 1)

    def down(self) -> None:
        self._selected_index = min(len(self.values) - 1, self._selected_index + 1)

    def get_selected_index(self) -> int:
        return self._selected_index

    def get_selected_item(self) -> Tuple[_T, AnyFormattedText]:
        return self.values[self.get_selected_index()]

    def get_selected_value(self):
        return self.get_selected_item()[0]

    def get_checked_index(self):
        for idx, value in enumerate(self.values):
            if value[0] == self.current_value:
                return idx
        return -1

    def get_checked_value(self):
        return self.current_value

    def get_checked_item(self):
        return self.values[self.get_checked_index()]

    def set_checked_index(self, index: int):
        self._selected_index = index
        self.current_value = self.values[self._selected_index][0]

    def set_selected_index(self, index: int):
        self._selected_index = index

    def _handle_enter(self) -> None:

        old_value = None
        for value in self.values:
            if value[0] == self.current_value:
                old_value = value
        new_value = self.values[self._selected_index]
        super()._handle_enter()
        self.check_event.fire(old_value, new_value)


'''
@author: ‘wang_pc‘
@site: 
@software: PyCharm
@file: qrcode_terminal.py
@time: 2017/2/10 16:38
@Update: 2018/2/6 21:58

https://github.com/alishtory/qrcode-terminal/blob/master/qrcode_terminal/qrcode_terminal.py
'''


class BarCode(UIControl):

    def __init__(self, text: str) -> None:
        self._text = text
        self._items = self._qr_terminal_str()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._items = self._qr_terminal_str()

    def create_content(self, width: int, height: int) -> UIContent:

        def get_line(i: int) -> StyleAndTextTuples:
            return self._items[i]

        return UIContent(get_line=get_line, line_count=len(self._items), show_cursor=False)

    def _qr_terminal_str(self, version=1) -> List[StyleAndTextTuples]:

        white_block = '▇'
        black_block = '  '

        qr = qrcode.QRCode(version)
        qr.add_data(self.text)
        qr.make()

        lines: List[StyleAndTextTuples] = []
        text: StyleAndTextTuples = to_formatted_text(white_block*(qr.modules_count+2))
        lines.append(text)
        for mn in qr.modules:
            output = white_block
            for m in mn:
                if m:
                    output += black_block
                else:
                    output += white_block
            output += white_block
            text: StyleAndTextTuples = to_formatted_text(output)
            lines.append(text)
        text: StyleAndTextTuples = to_formatted_text(white_block*(qr.modules_count+2))
        lines.append(text)
        return lines


if __name__ == '__main__':
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl
    from prompt_toolkit.layout.layout import Layout

    kb = KeyBindings()

    @kb.add('c-q')
    def exit_(event):
        event.app.exit()

    buffer1 = Buffer()  # Editable buffer.

    root_container = VSplit([
        Window(content=BufferControl(buffer=buffer1)),
        Window(width=1, char='|'),
        Window(content=BarCode('Hello world')),
    ])

    layout = Layout(root_container)

    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    app.run()
