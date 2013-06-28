def unicode_to_utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string
