from prompt_toolkit.history import History
from typing import Iterable, List
import os


class LimitSizeFileHistory(History):
    """
    :class:`.History` class that stores all strings in a file.
    """

    def __init__(self, filename: str, size: int) -> None:
        self.filename = filename
        self.size = size
        super(LimitSizeFileHistory, self).__init__()

    def load_history_strings(self) -> Iterable[str]:
        strings: List[str] = []
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                for line_bytes in f:
                    line = line_bytes.decode("utf-8")
                    strings.append(line.strip())

        # 截取最后一段数据
        strings = strings[-self.size:]
        # 清除数据
        with open(self.filename, "wb") as f:
            pass

        with open(self.filename, "ab") as f:
            for s in strings:
                self.write_string(s, f)

        # Reverse the order, because newest items have to go first.
        return reversed(strings)

    def store_string(self, string: str) -> None:
        # Save to file.
        with open(self.filename, "ab") as f:
            self.write_string(string, f)

    def write_string(self, string, f) -> None:
        def write(t: str) -> None:
            f.write(t.encode("utf-8"))

        for line in string.split("\n"):
            write(line + os.linesep)
