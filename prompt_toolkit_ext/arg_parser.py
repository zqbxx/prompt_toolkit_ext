import argparse


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
        return self.has_error

    def clear_error_flag(self):
        self.has_error = False