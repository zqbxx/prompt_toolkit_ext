from pygments.lexer import RegexLexer, bygroups
from pygments.token import *


class ArgParseLexer(RegexLexer):

    BLANK = ' '
    TAB = '\t'
    DOUBLE_QUOTE = '"'

    STATUS_START = 0
    STATUS_BLANK = 1
    STATUS_DQ_START = 2
    STATUS_STRING_IN_QUOTE = 3
    STATUS_DQ_END = 4
    STATUS_STRING = 5

    def get_content_type(self, status, buff):
        if status == self.STATUS_BLANK:
            return Whitespace
        elif status in [self.STATUS_DQ_END, self.STATUS_DQ_START]:
            return Token.Literal.String.Double
        elif status in [self.STATUS_STRING, self.STATUS_STRING_IN_QUOTE]:
            if buff.startswith('-'):
                return String.Symbol
            return String
        elif status == self.STATUS_START:
            return String

    def match_opts(self, match):
        opt_string = match.group()
        start_position = match.start()
        buff = ''
        current_status = self.STATUS_START
        for c in opt_string:

            if current_status == self.STATUS_START:
                if c in [self.BLANK, self.TAB]:
                    buff += c
                    current_status = self.STATUS_BLANK
                elif c == self.DOUBLE_QUOTE:
                    buff += c
                    current_status = self.STATUS_DQ_START
                else:
                    buff += c
                    current_status = self.STATUS_STRING

            elif current_status == self.STATUS_BLANK:
                if c in [self.BLANK, self.TAB]:
                    buff += c
                elif c == self.DOUBLE_QUOTE:
                    if len(buff) > 0:
                        start_position, p, t = self.get_data(buff, current_status, start_position)
                        yield p, t, buff
                    buff = c
                    current_status = self.STATUS_DQ_START
                else:
                    if len(buff) > 0:
                        start_position, p, t = self.get_data(buff, current_status, start_position)
                        yield p, t, buff
                    buff = c
                    current_status = self.STATUS_STRING

            elif current_status == self.STATUS_DQ_START:
                if c != self.DOUBLE_QUOTE:
                    buff += c
                    current_status = self.STATUS_STRING_IN_QUOTE
                else:
                    buff += c
                    current_status = self.STATUS_DQ_END

            elif current_status == self.STATUS_STRING_IN_QUOTE:
                if c != self.DOUBLE_QUOTE:
                    buff += c
                else:
                    buff += c
                    current_status = self.STATUS_DQ_END

            elif current_status == self.STATUS_DQ_END:
                if len(buff) > 0:
                    start_position, p, t = self.get_data(buff, current_status, start_position)
                    yield p, t, buff
                buff = c
                if c in [self.BLANK, self.TAB]:
                    current_status = self.STATUS_BLANK
                elif c == self.DOUBLE_QUOTE:
                    current_status = self.STATUS_DQ_START
                else:
                    current_status = self.STATUS_STRING

            elif current_status == self.STATUS_STRING:
                if c in [self.BLANK, self.TAB]:
                    if len(buff) > 0:
                        start_position, p, t = self.get_data(buff, current_status, start_position)
                        yield p, t, buff
                    buff = c
                    current_status = self.STATUS_BLANK
                else:
                    buff += c

        if len(buff) > 0:
            _, p, t = self.get_data(buff, current_status, start_position)
            yield p, t, buff

    def get_data(self, buff, current_status, start_position):
        p = start_position
        t = self.get_content_type(current_status, buff)
        start_position += len(buff)
        return start_position, p, t

    tokens = {
        'root': [
            (r'(\s+)', Whitespace),
            (r'\w+', Keyword), #普通的命令，例如list
            (r'"(\w+[ \t]*)+"', Keyword), #带双引号，例如"list"
            (r'(-{1,2}\w+)(.*)', match_opts), #剩余部分自己解析
        ]
    }


def print_tokens(csv_lexer, command):
    print('-------start--------')
    print(command)
    tokens = csv_lexer.get_tokens(command)
    for t in tokens:
        print(t)
    print('-------end--------')


if __name__ == '__main__':
    from prompt_toolkit.lexers import PygmentsLexer
    #my_lexer = PygmentsLexer(MyLexer)
    #my_lexer = load_lexer_from_file(__file__, "MyLexer", ensurenl=False)
    my_lexer = ArgParseLexer(ensurenl=False)
    print_tokens(my_lexer, 'list "aaa"')
    #print_tokens(my_lexer, 'list test -f sss -d "fsfds"')
    #print_tokens(my_lexer, '"list" test -f sss -d "fsfds"')
    #print_tokens(my_lexer, '"list test" -f sss -d "fsf\ ds" "aaa" --ds "fsf /ds"')
    #print_tokens(my_lexer, 'list -d "fsf ds"')
    '''
    my_lexer = MyLexer()
    #cmd = '-f sss'
    cmd = '"list test" -f sss -d "fsf\ ds" "aaa" --ds "fsf /ds"'
    print(cmd)
    ret_list = my_lexer.match_opts(cmd)
    for ret in ret_list:
        print(ret)
    '''

