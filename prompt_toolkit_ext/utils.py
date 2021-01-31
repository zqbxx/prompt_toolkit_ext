from prompt_toolkit.utils import get_cwidth


def fill_right(string, max_len, c=' '):
    str_len = get_cwidth(string)
    fill_count = max_len - str_len
    if fill_count <= 0:
        return string
    return string + c * fill_count
