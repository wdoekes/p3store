from tests.server import ServerTestCase


class ServerTest(ServerTestCase):
    def test_example(self):
        response = self.call()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['location'],
                         '/v1/:/obj/myserver.tld')
        self.assertEqual(response.raw_content, b'')
