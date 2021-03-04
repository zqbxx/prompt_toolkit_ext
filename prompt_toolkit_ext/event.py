from axel import Event


class KeyEvent(Event):

    def __init__(self, key: str):
        super().__init__()
        self.key = key

