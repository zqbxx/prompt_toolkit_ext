import functools
import os
import signal
import threading
import traceback
from asyncio import get_event_loop, new_event_loop, set_event_loop
from typing import (
    TYPE_CHECKING,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Sized,
    TextIO,
    TypeVar,
    cast,
)

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app_session
from prompt_toolkit.filters import Condition, is_done, renderer_height_is_known
from prompt_toolkit.formatted_text import (
    AnyFormattedText,
    StyleAndTextTuples,
    to_formatted_text,
)
from prompt_toolkit.input import Input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout import (
    ConditionalContainer,
    FormattedTextControl,
    HSplit,
    Layout,
    VSplit,
    Window,
    FloatContainer)
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.layout.dimension import AnyDimension, D
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.utils import in_main_thread

from prompt_toolkit.shortcuts.progress_bar.formatters import Formatter, Text

try:
    import contextvars
except ImportError:
    from prompt_toolkit.eventloop import dummy_contextvars

    contextvars = dummy_contextvars  # type: ignore


"""
从prompt_toolkit直接复制后修改

"""


__all__ = ["Progress"]

E = KeyPressEvent

_SIGWINCH = getattr(signal, "SIGWINCH", None)


def create_key_bindings() -> KeyBindings:
    """
    Key bindings handled by the progress bar.
    (The main thread is not supposed to handle any key bindings.)
    """
    kb = KeyBindings()

    @kb.add("c-l")
    def _clear(event: E) -> None:
        event.app.renderer.clear()

    @kb.add("c-c")
    def _interrupt(event: E) -> None:
        # Send KeyboardInterrupt to the main thread.
        os.kill(os.getpid(), signal.SIGINT)

    return kb


_T = TypeVar("_T")


class Progress:
    """
    Progress bar context manager.

    Usage ::

        with ProgressBar(...) as pb:
            for item in pb(data):
                ...

    :param title: Text to be displayed above the progress bars. This can be a
        callable or formatted text as well.
    :param formatters: List of :class:`.Formatter` instances.
    :param bottom_toolbar: Text to be displayed in the bottom toolbar. This
        can be a callable or formatted text.
    :param style: :class:`prompt_toolkit.styles.BaseStyle` instance.
    :param key_bindings: :class:`.KeyBindings` instance.
    :param file: The file object used for rendering, by default `sys.stderr` is used.

    :param color_depth: `prompt_toolkit` `ColorDepth` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance.
    :param input: :class:`~prompt_toolkit.input.Input` instance.
    """

    def __init__(
        self,
        title: AnyFormattedText = None,
        formatters: Optional[Sequence[Formatter]] = [Text(' ')],
        bottom_toolbar: AnyFormattedText = None,
        style: Optional[BaseStyle] = None,
        key_bindings: Optional[KeyBindings] = None,
        file: Optional[TextIO] = None,
        color_depth: Optional[ColorDepth] = None,
        output: Optional[Output] = None,
        input: Optional[Input] = None,
    ) -> None:

        self.title = title
        self.formatters = formatters
        self.bottom_toolbar = bottom_toolbar
        self.models: List[ProgressModel] = []
        self.style = style
        self.key_bindings = key_bindings

        # Note that we use __stderr__ as default error output, because that
        # works best with `patch_stdout`.
        self.color_depth = color_depth
        self.output = output or get_app_session().output
        self.input = input or get_app_session().input

        self._thread: Optional[threading.Thread] = None

        self._loop = get_event_loop()
        self._app_loop = new_event_loop()

        self._previous_winch_handler = None
        self._has_sigwinch = False

        if TYPE_CHECKING:
            # Infer type from getsignal result, as defined in typeshed. Too
            # complex to repeat here.
            self._previous_winch_handler = signal.getsignal(_SIGWINCH)

        self.root = None

    def create_ui(self):

        self._create_app()

        # Run application in different thread.
        def run() -> None:
            set_event_loop(self._app_loop)
            try:
                self.app.run()
            except BaseException as e:
                traceback.print_exc()
                print(e)

        ctx: contextvars.Context = contextvars.copy_context()

        self._thread = threading.Thread(target=ctx.run, args=(run,))
        self._thread.start()

        # Attach WINCH signal handler in main thread.
        # (Interrupt that we receive during resize events.)
        self._has_sigwinch = _SIGWINCH is not None and in_main_thread()
        if self._has_sigwinch:
            self._previous_winch_handler = signal.getsignal(_SIGWINCH)
            self._loop.add_signal_handler(_SIGWINCH, self.invalidate)

    def _create_app(self):
        # Create UI Application.
        title_toolbar = ConditionalContainer(
            Window(
                FormattedTextControl(lambda: self.title),
                height=1,
                style="class:progressbar,title",
            ),
            filter=Condition(lambda: self.title is not None),
        )

        bottom_toolbar = ConditionalContainer(
            Window(
                FormattedTextControl(
                    lambda: self.bottom_toolbar, style="class:bottom-toolbar.text"
                ),
                style="class:bottom-toolbar",
                height=1,
            ),
            filter=~is_done
                   & renderer_height_is_known
                   & Condition(lambda: self.bottom_toolbar is not None),
        )

        def width_for_formatter(formatter: Formatter) -> AnyDimension:
            # Needs to be passed as callable (partial) to the 'width'
            # parameter, because we want to call it on every resize.
            return formatter.get_width(progress_bar=self)

        progress_controls = [
            Window(
                content=_ProgressControl(self, f),
                width=functools.partial(width_for_formatter, f),
            )
            for f in self.formatters
        ]

        body = self.create_content(progress_controls)

        self.root = FloatContainer(
            content=HSplit(
                    [
                        title_toolbar,
                        body,
                        bottom_toolbar,
                    ]
                ),
            floats=[]
        )

        if self.key_bindings is None:
            self.create_key_bindings()

        self.app: Application[None] = Application(
            min_redraw_interval=0.05,
            layout=Layout(self.root),
            style=self.style,
            key_bindings=self.key_bindings,
            refresh_interval=0.3,
            color_depth=self.color_depth,
            output=self.output,
            input=self.input,
            full_screen=True,
        )

        return self.app

    def create_content(self, progress_controls):
        return VSplit(
            progress_controls,
            height=lambda: D(
                preferred=len(self.models), max=len(self.models)
            ),
        )

    def create_key_bindings(self):
        pass

    def exit(self):
        # Quit UI application.
        if self.app.is_running:
            self.app.exit()

        # Remove WINCH handler.
        if self._has_sigwinch:
            self._loop.remove_signal_handler(_SIGWINCH)
            signal.signal(_SIGWINCH, self._previous_winch_handler)

    def clear(self):
        # 不能在self._thread线程中调用
        if self._thread is not None:
            self._thread.join()

        if self._app_loop.is_running():
            self._app_loop.close()

    def destroy(self):
        # 不能在self._thread线程中调用
        self.exit()
        self.clear()

    def create_model(
        self,
        remove_when_done: bool = False,
    ) -> "ProgressModel":
        model = ProgressModel(self, remove_when_done=remove_when_done)
        self.models.append(model)
        return model

    def invalidate(self) -> None:
        self._app_loop.call_soon_threadsafe(self.app.invalidate)


class _ProgressControl(UIControl):
    """
    User control for the progress bar.
    """

    def __init__(self, progress_bar: Progress, formatter: Formatter) -> None:
        self.progress_bar = progress_bar
        self.formatter = formatter
        self._key_bindings = create_key_bindings()

    def create_content(self, width: int, height: int) -> UIContent:
        items: List[StyleAndTextTuples] = []

        for pr in self.progress_bar.models:
            try:
                text = self.formatter.format(self.progress_bar, pr, width)
            except BaseException:
                traceback.print_exc()
                text = "ERROR"

            items.append(to_formatted_text(text))

        def get_line(i: int) -> StyleAndTextTuples:
            return items[i]

        return UIContent(get_line=get_line, line_count=len(items), show_cursor=False)

    def is_focusable(self) -> bool:
        return True  # Make sure that the key bindings work.

    def get_key_bindings(self) -> KeyBindings:
        return self._key_bindings


class ProgressModel:

    def __init__(self, progress: Progress, remove_when_done: bool = False,):
        self.progress = progress
        self.remove_when_done = remove_when_done
        self._done = False

    def invalidate(self):
        self.progress.invalidate()

    @property
    def done(self) -> bool:
        return self._done

    @done.setter
    def done(self, value: bool) -> None:
        self._done = value

        if value and self.remove_when_done:
            self.progress.models.remove(self)
