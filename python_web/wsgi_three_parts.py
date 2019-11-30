#! /usr/bin/python3

"""
This is a relatively complete WSGI snippt for three parts.

It shows us how to design server, middleware and application.

For more info and Code Source(Changed slightly at Middleware part):
    https://www.python.org/dev/peps/pep-3333/
"""

# --------------------------------------------------
# The Server/Gateway Side
# --------------------------------------------------

import os, sys


enc, esc = sys.getfilesystemencoding(), 'surrogateescape'


def unicode_to_wsgi(u):
    return u.encode(enc, esc).decode('iso-8859-1')


def wsgi_to_bytes(s):
    return s.encode('iso-8859-1')


def run_with_cgi(application):
    environ = {k: unicode_to_wsgi(v) for k, v in os.environ.items()}
    environ['wsgi.input']        = sys.stdin.buffer
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1, 0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']     = True

    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    def write(data):
        out = sys.stdout.buffer

        if not headers_set:
            raise AssertionError("write() before start_response()")
        elif not headers_sent:
            status, response_headers = headers_sent[:] = headers_set
            out.write(wsgi_to_bytes('Status: %s\r\n' % status))
            for header in response_headers:
                out.write(wsgi_to_bytes('%s: %s\r\n' % header))
            out.write(wsgi_to_bytes('\r\n'))
        out.write(data) 
        out.flush()

    def start_response(status, response_headers, exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]

        return write

    result = application(environ, start_response)
    try:
        for data in result:
            if data:
                write(data)
        if not headers_sent:
            write('')
    finally:
        if hasattr(result, 'close'):
            result.close()

# --------------------------------------------------
# Middleware: Components that Play Both Sides
# --------------------------------------------------


def back_one_char(string: bytes):
    """ Convert char to another char
    which's ascii is one greater than previous one
    """
    return ''.join([chr(char+1) for char in string]).encode('ascii')


class ChangeIter:
    def __init__(self, result, transform_ok):
        if hasattr(result, 'close'):
            self.close = result.close
        self._next = iter(result).__next__
        self.transform_ok = transform_ok

    def __iter__(self):
        return self

    def __next__(self):
        if self.transform_ok:
            return back_one_char(self._next())  # Acting on response body
        else:
            return self._next()


class Changetor:
    transform = False

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):

        transform_ok = [True]   # for 'back_one_char()'

        def start_change(status, response_headers, exc_info=None):
            
            del transform_ok[:]

            for name, value in response_headers:
                if name.lower() == 'content-type' and value == 'text/plain':
                    transform_ok.append(True)
                    response_headers = [(name, value)
                        for name, value in response_headers
                            if name.lower() != 'content-length'
                        ]
                    break
            write = start_response(status, response_headers, exc_info)
 
            if transform_ok:
                def write_change(data):
                    write(back_one_char(data))
                return write_change
            else:
                return write

        return ChangeIter(self.application(environ, start_change),
                           transform_ok)
                        

# --------------------------------------------------
# The Application/Framework Side
# --------------------------------------------------


class Application:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        self.start(status, response_headers)
        yield b'Hello World\n'


run_with_cgi(Changetor(Application))

