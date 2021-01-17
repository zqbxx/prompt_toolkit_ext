import argparse
import sys


class PromptArgumentParser(argparse.ArgumentParser):

    def parse_args(self, args=None, namespace=None):
        ret = super(PromptArgumentParser, self).parse_args(args, namespace)
        return ret

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        self.has_error = True

    def error(self, message):
        super(PromptArgumentParser, self).error(message)
        self.has_error = True

    def has_error_flag(self):

        if not hasattr(self, 'has_error'):
            self.has_error = False

        if self.has_error:
            return self.has_error

        for sub_action in self._actions:
            if isinstance(sub_action, argparse._SubParsersAction):
                parser_map = sub_action._name_parser_map
                for command, parser in parser_map.items():
                    if isinstance(parser, PromptArgumentParser):
                        if parser.has_error_flag():
                            return True

        return self.has_error

    def clear_error_flag(self):
        self.has_error = False
        for sub_action in self._actions:
            if isinstance(sub_action, argparse._SubParsersAction):
                parser_map = sub_action._name_parser_map
                for command, parser in parser_map.items():
                    if isinstance(parser, PromptArgumentParser):
                        parser.clear_error_flag()
