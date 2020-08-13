# -*- coding: utf-8 -*-
#
# Copyright 2018-2020 by Vinay Sajip. All Rights Reserved.
#
from __future__ import unicode_literals

from string import digits
import sys

unichr = chr
is_printable = lambda c: c.isprintable()
text_type = str

WORD = 'a'
INTEGER = '0'
FLOAT = '1'
COMPLEX = 'j'
STRING = '"'
EOF = ''
NEWLINE = '\n'
LCURLY = '{'
RCURLY = '}'
LBRACK = '['
RBRACK = ']'
LPAREN = '('
RPAREN = ')'
LT = '<'
GT = '>'
LE = '<='
GE = '>='
EQ = '=='
ASSIGN = '='
NEQ = '!='
ALT_NEQ = '<>'
LSHIFT = '<<'
RSHIFT = '>>'
DOT = '.'
COMMA = ','
COLON = ':'
AT = '@'
PLUS = '+'
MINUS = '-'
STAR = '*'
POWER = '**'
SLASH = '/'
TILDE = '~'
SLASHSLASH = '//'
MODULO = '%'
BACKTICK = '`'
DOLLAR = '$'
TRUE = 'true'
FALSE = 'false'
NONE = 'null'
PYTRUE = 'True'
PYFALSE = 'False'
PYNONE = 'None'
IS = 'is'
IN = 'in'
NOT = 'not'
AND = 'and'
OR = 'or'
BITAND = '&'
BITOR = '|'
BITXOR = '^'
BITNOT = TILDE

WORDCHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
KEYWORDS = {TRUE, FALSE, NONE, IS, IN, NOT, AND, OR}
PUNCT = ':-+*/%,.{}[]()@$<>!~&|^'

PYKEYWORDS = {PYTRUE: TRUE, PYFALSE: FALSE, PYNONE: NONE}

KEYWORD_VALUES = {
    TRUE: True,
    PYTRUE: True,
    FALSE: False,
    PYFALSE: False,
    NONE: None,
    PYNONE: None,
}

SCALAR_TOKENS = {STRING, INTEGER, FLOAT, COMPLEX, FALSE, TRUE, NONE}


class RecognizerError(Exception):
    pass


class TokenizerError(RecognizerError):
    location = None


class Token(object):

    start = end = None

    def __init__(self, kind, text, value=None):
        self.kind = kind
        self.text = text
        self.value = value

    def __repr__(self):
        return 'Token(%s:%s:%s)' % (self.kind, self.text, self.value)

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return (self.kind == other.kind) and (self.value == other.value)


ESCAPES = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
    '\\': '\\',
    '\"': '\"',
    '\'': '\'',
    '/': '/',  # http://api.nobelprize.org/v1/prize.json escapes these
}


class Tokenizer(object):

    whitespace = ' \t\r\n'
    quotes = '\'"'
    punct = PUNCT
    wordchars = WORDCHARS
    identchars = WORDCHARS + digits

    def __init__(self, stream):
        self.stream = stream
        self.lineno = self.charline = 1
        self.colno = self.charcol = 1
        # self.lastc = None
        self.filename = getattr(stream, 'filename', '<unknown filename>')
        self.pbchars = []
        self.pbtokens = []

    @property
    def remaining(self):  # for debugging
        s = self.stream.getvalue()
        p = self.stream.tell()
        return s[p:]

    def push_back(self, c):
        if c and ((c == '\n') or (c not in self.whitespace)):
            self.pbchars.append((c, self.charline, self.charcol))

    def get_char(self):
        """
        Get the next char from the stream. Update line and column numbers
        appropriately.

        :return: The next character from the stream.
        :rtype: str
        """
        if self.pbchars:
            t = self.pbchars.pop()
            c = t[0]
            self.charline = self.lineno = t[1]
            self.charcol = self.colno = t[2]
        else:
            self.charline = self.lineno
            self.charcol = self.colno
            c = self.stream.read(1)
        if c:
            if c != '\n':
                self.colno += 1
            else:
                self.lineno += 1
                self.colno = 1
        return c

    def get_token(self):
        """
        Get a token from the stream. The return value is (token_type, token_value).

        Multiline string tokenizing is thanks to David Janes (BlogMatrix)

        :return: The next token.
        :rtype: A token tuple.
        """
        if self.pbtokens:  # pragma: no cover
            return self.pbtokens.pop()
        stream = self.stream
        token = quoter = ''
        tt = EOF
        get_char = self.get_char

        # noinspection PyShadowingNames
        def get_number(token):
            tt = INTEGER
            in_exponent = False
            radix = 0
            dot_seen = token.find('.') >= 0
            last_was_digit = token[-1].isdigit()
            endline, endcol = self.charline, self.charcol
            while True:
                c = get_char()
                if c == '.':
                    dot_seen = True
                if not c:
                    break
                if c == '_':
                    if last_was_digit:
                        token += c
                        last_was_digit = False
                        endline, endcol = self.charline, self.charcol
                        continue
                    e = TokenizerError('Invalid \'_\' in number: %s' % token + c)
                    e.location = (self.charline, self.charcol)
                    raise e
                last_was_digit = False  # unless set in one of the clauses below
                if (radix == 0) and ('0' <= c <= '9'):
                    token += c
                    last_was_digit = True
                    endline, endcol = self.charline, self.charcol
                elif (radix == 2) and ('0' <= c <= '1'):
                    token += c
                    last_was_digit = True
                    endline, endcol = self.charline, self.charcol
                elif (radix == 8) and ('0' <= c <= '7'):
                    token += c
                    last_was_digit = True
                    endline, endcol = self.charline, self.charcol
                elif (radix == 16) and (
                    ('0' <= c <= '9') or ('a' <= c <= 'f') or ('A' <= c <= 'F')
                ):
                    token += c
                    last_was_digit = True
                    endline, endcol = self.charline, self.charcol
                elif c in 'OXoxBb' and token == '0':
                    if c in 'Oo':
                        radix = 8
                    elif c in 'Xx':
                        radix = 16
                    else:
                        radix = 2
                    token += c
                    endline, endcol = self.charline, self.charcol
                elif c == '.':
                    if (radix != 0) or token.find('.') >= 0 or in_exponent:
                        e = TokenizerError('Invalid character in number: %c' % c)
                        e.location = (self.charline, self.charcol)
                        raise e
                    else:
                        token += c
                        endline, endcol = self.charline, self.charcol
                elif (
                    (radix == 0)
                    and (c == '-')
                    and token.find('-', 1) < 0
                    and in_exponent
                ):
                    token += c
                    endline, endcol = self.charline, self.charcol
                elif (
                    (radix == 0)
                    and (c in 'eE')
                    and (token.find('e') < 0)
                    and (token.find('E') < 0)
                    and (token[-1] != '_')
                ):
                    token += c
                    endline, endcol = self.charline, self.charcol
                    in_exponent = True
                else:
                    break
            # reached the end of any actual number part. Before checking
            # for complex, ensure that the last char wasn't an underscore.
            if token[-1] == '_':
                e = TokenizerError('Invalid \'_\' at end of number: %s' % token)
                e.location = (self.charline, self.charcol - 1)
                raise e
            if c:
                if (radix == 0) and c in 'jJ':
                    token += c
                    endline, endcol = self.charline, self.charcol
                    tt = COMPLEX
                else:
                    if c != '.' and not c.isalnum():
                        self.push_back(c)
                    else:
                        e = TokenizerError('Invalid character in number: %c' % c)
                        e.location = (self.charline, self.charcol)
                        raise e
            try:
                s = token.replace('_', '')
                if radix:
                    value = int(s[2:], radix)
                elif token[-1] in 'jJ':
                    value = complex(s)
                elif in_exponent or dot_seen:
                    value = float(s)
                    tt = FLOAT
                else:
                    radix = 8 if s[0] == '0' else 10
                    value = int(s, radix)
            except ValueError:
                # str(token) so Unicode doesn't show u'prefix in repr
                e = TokenizerError('Badly-formed number: %r' % str(token))
                e.location = (startline, startcol)
                raise e
            return tt, token, value, endline, endcol

        # noinspection PyShadowingNames
        def parse_escapes(s):
            i = s.find('\\')
            if i < 0:
                result = s
            else:
                result = []
                failed = False
                while i >= 0:
                    n = len(s)
                    if i > 0:
                        result.append(s[:i])
                    c = s[i + 1]
                    # import pdb; pdb.set_trace()
                    if c in ESCAPES:
                        result.append(ESCAPES[c])
                        i += 2
                    elif c in 'xXuU':
                        if c in 'xX':
                            slen = 4
                        else:
                            slen = 6 if c == 'u' else 10
                        if (i + slen) > n:
                            failed = True
                            break
                        p = s[i + 2 : i + slen]
                        try:
                            d = int(p, 16)
                            if (0xD800 <= d <= 0xDFFF) or d >= 0x110000:
                                failed = True
                                break
                            result.append(unichr(d))
                            i += slen
                        except ValueError:
                            failed = True
                            break
                    else:
                        failed = True
                        break
                    s = s[i:]
                    i = s.find('\\')
                if failed:
                    e = TokenizerError(
                        'Invalid escape sequence at index %d: %s' % (i, s)
                    )
                    e.location = (startline, startcol)
                    raise e
                result.append(s)
                result = ''.join(result)
            return result

        value = None

        while True:
            c = get_char()
            startline = endline = self.charline
            startcol = endcol = self.charcol

            if not c:
                break
            elif c == '#':
                stream.readline()
                self.lineno += 1
                self.colno = 1
                endline, endcol = self.lineno, self.colno - 1
                tt = token = NEWLINE
                break
            elif c == '\n':
                endline, endcol = self.lineno, self.colno - 1
                tt = token = NEWLINE
                break
            elif c == '\r':
                c = get_char()
                if c != '\n':
                    self.push_back(c)
                tt = token = NEWLINE
                endline, endcol = self.charline, self.charcol
                break
            elif c == '\\':
                c = get_char()
                if c != '\n':
                    e = TokenizerError('Unexpected character: \\')
                    e.location = self.charline, self.charcol
                    raise e
                endline, endcol = self.charline, self.charcol
                continue
            elif c in self.whitespace:
                continue
            elif c == '`':
                token = quoter = c
                tt = BACKTICK
                endline, endcol = self.charline, self.charcol
                while True:
                    c = get_char()
                    if not c:
                        break
                    if not is_printable(c):
                        e = TokenizerError(
                            'Invalid char %c in `-string: \'%s\'' % (c, token)
                        )
                        e.location = (self.charline, self.charcol)
                        raise e
                    token += c
                    endline, endcol = self.charline, self.charcol
                    if c == quoter:
                        break
                if not c:
                    e = TokenizerError('Unterminated `-string: \'%s\'' % token)
                    e.location = (startline, startcol)
                    raise e
                break
            elif c in self.quotes:
                token = c
                endline, endcol = self.charline, self.charcol
                quote = c
                tt = STRING
                escaped = False
                multiline = False
                c1 = get_char()
                c1loc = (self.charline, self.charcol)
                if c1 != quote:
                    self.push_back(c1)
                else:
                    c2 = get_char()
                    if c2 != quote:
                        self.push_back(c2)
                        if not c2:
                            self.charline, self.charcol = c1loc
                        self.push_back(c1)
                    else:
                        multiline = True
                        token += quote
                        token += quote
                # Keep the quoting string around for later
                quoter = token
                while True:
                    c = get_char()
                    if not c:
                        break
                    token += c
                    endline, endcol = self.charline, self.charcol
                    if (c == quote) and not escaped:
                        if not multiline or (
                            len(token) >= 6
                            and token.endswith(token[:3])
                            and token[-4] != '\\'
                        ):
                            break
                    if c == '\\':
                        nc = get_char()
                        if nc == '\n':
                            token = token[:-1]  # lose the backslash we added
                            continue
                        else:
                            self.push_back(nc)
                            escaped = not escaped
                    else:
                        escaped = False
                if not c:
                    e = TokenizerError('Unterminated quoted string: %r' % token)
                    e.location = (startline, startcol)
                    raise e
                break
            elif c in self.wordchars:
                token = c
                endline, endcol = self.charline, self.charcol
                tt = WORD
                c = get_char()
                while c and (c in self.identchars):
                    token += c
                    endline, endcol = self.charline, self.charcol
                    c = get_char()
                self.push_back(c)
                if token in PYKEYWORDS:
                    token = PYKEYWORDS[token]
                if token in KEYWORDS:
                    value = KEYWORD_VALUES.get(token)
                    tt = token
                else:
                    value = token
                break
            elif c in digits:
                tt, token, value, endline, endcol = get_number(c)
                break
            elif c == '=':
                nc = get_char()
                if nc == '=':
                    token = c + nc
                    endline, endcol = self.charline, self.charcol
                    tt = token
                else:
                    tt = token = c
                    self.push_back(nc)
                break
            elif c in self.punct:
                token = tt = c
                endline, endcol = self.charline, self.charcol
                if c == '.':
                    c = get_char()
                    if c:
                        if c not in digits:
                            self.push_back(c)
                        else:
                            token += c
                            tt, token, value, endline, endcol = get_number(token)
                            break
                elif c == '-':
                    c = get_char()
                    if c:
                        if c in digits or c == '.':
                            token += c
                            tt, token, value, endline, endcol = get_number(token)
                        else:
                            self.push_back(c)
                elif token in ('<', '>', '!', '*', '/', '&', '|'):
                    c = get_char()
                    pb = True
                    if token == '<':
                        if c in '<>=':
                            token += c
                            endline, endcol = self.charline, self.charcol
                            tt = token if token != ALT_NEQ else NEQ
                            pb = False
                    elif token in ('&', '|') and c == token:
                        token += c
                        endline, endcol = self.charline, self.charcol
                        if c == '&':
                            tt = AND
                        else:
                            tt = OR
                        pb = False
                    elif token == '>':
                        if c in '>=':
                            token += c
                            endline, endcol = self.charline, self.charcol
                            tt = token
                            pb = False
                    elif token == '!':
                        if c == '=':
                            token += c
                            endline, endcol = self.charline, self.charcol
                            tt = token
                            pb = False
                        else:
                            tt = NOT
                    elif token in '*/=':
                        if c == token:
                            token += c
                            endline, endcol = self.charline, self.charcol
                            tt = token
                            pb = False
                    if pb:
                        self.push_back(c)
                break
            else:
                e = TokenizerError('Unexpected character: %r' % str(c))
                e.location = (self.charline, self.charcol)
                raise e
        if tt in (STRING, BACKTICK):
            n = len(quoter)
            assert n in (1, 3)
            assert token.startswith(quoter)
            assert token.endswith(quoter)
            try:
                value = parse_escapes(token[n:-n])
            except TokenizerError as e:
                e.location = (startline, startcol)
                raise e
        result = Token(tt, token, value)
        result.start = (startline, startcol)
        result.end = (endline, endcol)
        return result

    def __iter__(self):
        return self

    def next(self):
        result = self.get_token()
        if result.kind == EOF:
            raise StopIteration
        return result

    __next__ = next
