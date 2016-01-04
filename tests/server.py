import io
import unittest

from p3store.server import application


class ServerResponse(object):
    def __init__(self, status, headers, data_list):
        self._status = status
        self._headers = headers
        self._data_list = data_list

    @property
    def status_code(self):
        return int(self._status.split(' ', 1)[0])

    @property
    def headers(self):
        return dict(self._headers)

    @property
    def raw_content(self):
        return b''.join(self._data_list)


class ServerTestCase(unittest.TestCase):
    def default_env(self):
        return {
            'wsgi.errors': None,
            'wsgi.input': io.BytesIO(),
        }

    def call(self, method='GET', uri='/', extra_env={}):
        out_status = []
        out_headers = []
            
        def respond(status, headers):
            out_status.append(status)
            out_headers.extend(headers)

        env = self.default_env()
        env.update({
            'REQUEST_METHOD': method,
            'PATH_INFO': uri,
        })
        env.update(extra_env)
        
        out = list(application(env=env, start_response=respond))
        return ServerResponse(out_status[0], out_headers, out)
