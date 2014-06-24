"""
Output and Ansi art unicode helpers for x/84, https://github.com/jquast/x84
"""
import warnings
import re

from x84.bbs.session import getterminal, getsession

from blessed.sequences import Sequence, measure_length

__all__ = ['echo', 'timeago', 'encode_pipe', 'decode_pipe']

def syncterm_setfont(fontname):
    fontname = fontname.lower()
    if fontname == 'topaz':
        ansicode = '\x1b[0;40 D'
    if fontname == 'microknight':
        ansicode = '\x1b[0;39 D'
    if fontname == 'potnoodle':
        ansicode = '\x1b[0;37 D'
    if fontname == 'mosoul':
        ansicode = '\x1b[0;38 D'
    if fontname == 'cp437thin':
        ansicode = '\x1b[0;26 D'
    if fontname == 'cp437':
        ansicode = '\x1b[0;0 D'
    return ansicode

def echo(ucs):
    """
    Display unicode terminal sequence.
    """
    session = getsession()
    if not isinstance(ucs, unicode):
        warnings.warn('non-unicode: %r' % (ucs,), UnicodeWarning, 2)
        return session.write(ucs.decode('iso8859-1'))
    return session.write(ucs)


def timeago(secs, precision=0):
    """
    timago(float[,int])

    Pass a duration of time and return human readable shorthand, fe.

    asctime(126.32) -> ' 2m 6s',
    asctime(70.9999, 2) -> ' 1m 10.99s'
    """
    # split by days, mins, hours, secs
    years = weeks = days = mins = hours = 0
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    years, weeks = divmod(weeks, 52)
    ((num1, num2), (label1, label2)) = (
        ((years, weeks), (u'y', u'w')) if years >= 1.0 else
        ((weeks, days), (u'w', u'd')) if weeks >= 1.0 else
        ((days, hours), (u'd', u'h')) if days >= 1.0 else
        ((hours, mins), (u'h', u'm')) if hours >= 1.0 else
        ((mins, secs), (u'm', u's')))
    return (u'%2d%s%2.*f%s' % (num1, label1, precision, num2, label2,))


def decode_pipe(ucs):
    """
    decode_pipe(ucs) -> unicode

    Return new terminal sequence, replacing 'pipe codes', such as u'|03'
    with this terminals equivalent attribute sequence.
    """
    # simple optimization, no '|' ? exit early!
    if not u'|' in ucs:
        return ucs
    term = getterminal()
    outp = u''
    ptr = 0
    match = None
    ANSI_PIPE = re.compile(r'\|(\d{2,3})')

    for match in ANSI_PIPE.finditer(ucs):
        val = match.group(1)
        # allow escaping using a second pipe
        if match.start() and ucs[match.start() - 1] == '|':
            continue
        # 07 -> 7
        while val.startswith('0'):
            val = val[1:]
        int_value = 0 if 0 == len(val) else int(val, 10)
        assert int_value >= 0 and int_value <= 256
        # colors 0-7 and 16-256 are as-is term.color()
        # special accomidations for 8-15, some termcaps are ok
        # with term.color(11), whereas others have trouble, help
        # out by using dim color and bold attribute instead.
        attr = u''
        if int_value <= 7 or int_value >= 16:
            attr = term.normal + term.color(int_value)
        elif int_value <= 15:
            attr = term.normal + term.color(int_value - 8) + term.bold
        outp += ucs[ptr:match.start()] + attr
        ptr = match.end()

    outp = ucs if match is None else u''.join((outp, ucs[match.end():]))
    return u''.join((outp, term.normal))
_decode_pipe = decode_pipe

def encode_pipe(ucs):
    """
    encode_pipe(ucs) -> unicode

    Return new unicode terminal sequence, replacing EMCA-48 ANSI
    color sequences with their pipe-equivalent values.
    """
    # TODO: Support all kinds of terminal color sequences,
    # such as kermit or avatar or some such .. something non-emca
    outp = u''
    nxt = 0
    term = getterminal()
    ANSI_COLOR = re.compile(r'\033\[(\d{2,3})m')
    for idx in range(0, len(ucs)):
        if idx == nxt:
            # at sequence, point beyond it,
            match = ANSI_COLOR.match(ucs[idx:])
            if match:
                #nxt = idx + measure_length(ucs[idx:], term)
                nxt = idx + len(match.group(0))
                # http://wiki.mysticbbs.com/mci_codes
                value = int(match.group(1)) - 30
                if value >= 0 and value <= 60:
                    outp += u'|%02d' % (value,)
        if nxt <= idx:
            # append non-sequence to outp,
            outp += ucs[idx]
            # point beyond next sequence, if any,
            # otherwise point to next character
            nxt = idx + 1 #measure_length(ucs[idx:], term) + 1
    return outp
_encode_pipe = encode_pipe


##### Deprecated (will be removed in v2.0) #############

def ansiwrap(ucs, width=70, **kwargs):
    """Wrap a single paragraph of Unicode Ansi sequences,
    returning a list of wrapped lines.
    """
    warnings.warn('ansiwrap() deprecated, getterminal() now'
                  'supplies an equivalent .wrap() API')
    return getterminal().wrap(text=ucs, width=width, **kwargs)


class Ansi(Sequence):
    def __new__(cls, object):
        warnings.warn('Ansi() deprecated, getterminal() now provides '
                      '.length(), .rjust(), .wrap(), etc.')
        new = Sequence.__new__(cls, object, getterminal())
        return new

    def __len__(self):
        warnings.warn('Ansi().__len__() deprecated, getterminal() now '
                      'provides an equivalent .length() API')
        return self._term.length(text=self)

    def wrap(self, width, **kwargs):
        warnings.warn('Ansi().wrap() deprecated, getterminal() now '
                      'provides a similar .wrap() API')
        if 'indent' in kwargs:
            indent = kwargs.pop('indent')
        else:
            indent = u''
        lines = []
        for line in unicode(self).splitlines():
            if line.strip():
                for wrapped in ansiwrap(line, width, subsequent_indent=indent):
                    lines.append(wrapped)
            else:
                lines.append(u'')
        return '\r\n'.join(lines)

    def seqfill(self, _encode_pipe=False):
        warnings.warn('Ansi().seqfill() deprecated, getterminal() now '
                      'provides an equivalent .padd() API')
        val = self.padd()
        if _encode_pipe:
            return encode_pipe(unicode(val))
        return val

    def decode_pipe(self):
        warnings.warn('Ansi().decode_pipe() deprecated, use decode_pipe()')
        return _decode_pipe(unicode(self))

    def encode_pipe(self):
        warnings.warn('Ansi().decode_pipe() deprecated, use decode_pipe()')
        return _encode_pipe(unicode(self))
