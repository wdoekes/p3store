#!/usr/bin/env python
from wsgiref import simple_server

from p3store.server import application


def main():
    # TODO: logging?
    addr, port = '127.0.0.1', 8000
    print('Running simple WSGI server on {addr}:{port}.'.format(
        addr=addr, port=port))
    httpd = simple_server.make_server(addr, port, application)
    httpd.serve_forever()

if __name__ == '__main__':
    main()
