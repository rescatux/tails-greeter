def unicode_to_utf8(self, string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string
