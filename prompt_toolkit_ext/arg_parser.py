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

    def get_subparser_by_command(self, command, like=False):

        subparsers = {}

        for sub_action in self._actions:
            if isinstance(sub_action, argparse._SubParsersAction):
                if like:
                    for c, p in sub_action._name_parser_map.items():
                        if command in c:
                            subparsers[c] = p
                else:
                    parser_map = sub_action._name_parser_map
                    if parser_map.get(command):
                        return parser_map.get(command)

        if like:
            if len(subparsers) > 0:
                return subparsers

        return None

    def get_parser_opts(self, opt):
        opt_list = []
        for action in self._actions:
            if isinstance(action, argparse.Action) and not isinstance(action, argparse._SubParsersAction):
                opt_strings = action.option_strings
                if opt in ['--', '-']:
                    opt_list.append(opt_strings)
                else:
                    matched_opt_strings = []
                    for opt_str in opt_strings:
                        if opt in opt_str:
                            matched_opt_strings.append(opt_str)
                    opt_list.append(matched_opt_strings)

        return opt_list

    def get_subparsers(self):
        subparser_list = []
        for sub_action in self._actions:
            if isinstance(sub_action, argparse._SubParsersAction):
                parser_map = sub_action._name_parser_map
                subparser_list.append(parser_map)
        return subparser_list
