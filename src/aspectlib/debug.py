import logging
import os
import socket
import sys
from itertools import islice
import string

import wrapt
import aspectlib

logger = logging.getLogger(__name__)


def _frames(frame):
    while frame:
        yield frame
        frame = frame.f_back


def _make_stack(skip=0, length=6, _sep=os.path.sep):
    return ' < '.join("%s:%s:%s" % (
        '/'.join(f.f_code.co_filename.split(_sep)[-2:]),
        f.f_lineno,
        f.f_code.co_name
    ) for f in islice(_frames(sys._getframe(1 + skip)), length))

ASCII_ONLY = ''.join(i if i in string.printable else '.' for i in (chr(c) for c in range(256)))


def log(func=None, stacktrace=10, align_stacktrace=60, arguments=True, result=True, trim_result=False, strip_non_ascii=True, use_logging=False,
        instance_attributes=(), print_to=sys.stderr):
    def dump(buf):
        if strip_non_ascii:
            buf = buf.translate(ASCII_ONLY)
        try:
            if use_logging:
                logger.debug(buf)
            elif print_to:
                buf += '\n'
                print_to.write(buf)
        except Exception as exc:
            logger.critical('Failed to log a message: %s', exc, exc_info=True)

    @wrapt.decorator
    def logged(func, instance, args, kwargs, _missing=object()):
        name = func.__name__
        if instance:
            instance_type = type(instance)
            info = []
            for key in instance_attributes:
                if key.endswith('()'):
                    call = key = key.rstrip('()')
                else:
                    call = False
                val = getattr(instance, key, _missing)
                if val is not _missing and key != name:
                    info.append(' %s=%r' % (
                        key, val() if call else val
                    ))
            sig = buf = '<%s%s>.%s' % (instance_type.__name__, ''.join(info), name)
            #print('>>>', instance, sig)
        else:
            sig = buf = func.__name__
        if arguments:
            buf += '(%s%s)' % (
                ', '.join(repr(i) for i in args),
                (', ' + ', '.join('%s=%r' % i for i in kwargs.items())) if kwargs else '',
            )
        if stacktrace:
            buf = ("%%-%ds  <<< %%s" % align_stacktrace) % (buf, _make_stack(length=stacktrace))
        dump(buf)
        try:
            res = func(*args, **kwargs)
        except Exception as exc:
            dump(buf + ' ~ raised %s' % exc)
            raise

        if result:
            dump(sig + ' => %s' % res)
        return res

    if func:
        return logged(func)
    else:
        return logged

#_recv = socket._socketobject.recv
#_recvfrom = socket._socketobject.recvfrom
#_recv_into = socket._socketobject.recv_into
#_recvfrom_into = socket._socketobject.recvfrom_into
#
#def wrap_meth(self, name):
#    meth = getattr(self, name)
#    name = name.upper()
#    def wrapper(*args):
#        logging.critical('fd%s.%s%s < %s' % (self.fileno(), name, args, quick_stack(1, 10)))
#        ret = meth(*args)
#        logging.critical('  ==> returns: %r', ret)
#        return ret
#    return wrapper
#
#class DebugSocket(socket._socketobject):
#    def __init__(self, *args, **kwargs):
#        super(DebugSocket, self).__init__(*args, **kwargs)
#        for name in ('recv', 'recvfrom', 'recvfrom_into', 'recv_into'):
#            setattr(self, name, wrap_meth(self, name))
#
#socket.socket = socket.SocketType = socket._socketobject = DebugSocket

if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    import socket
    aspectlib.weave(socket.socket, log(use_logging=True, print_to=None, instance_attributes=('fileno()',)), patch_on_init=True, skip_methods=('fileno',))
    s = socket.socket()
    s.connect(('127.0.0.1', 80))
    s.send('GET / HTTP/1.0\r\n\r\n')
    repr(s.recv(10000))
    s.close()

    #import test_aspectlib
    #aspectlib.weave(test_aspectlib.SlotsTestSubClass, log(use_logging=True, print_to=None), patch_on_init=True)
    #x = test_aspectlib.SlotsTestSubClass('bubu')
    #x.foobar('tete')
    #x.class_foobar('tete')
    #x.static_foobar('tete')
