from webclient import run_client

import unittest

class TestServerClient(unittest.TestCase):

    SERVER_NAME = 'xinu1.cs.purdue.edu'
    SERVER_PORT = 3000

    def test_200(self):
        error_code = 200
        file_name = 'index.html'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = '/'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'Upload/'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = '/Upload/'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'Upload/webserver.pdf'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = '/upload/webserver.pdf'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'test/webserver'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'upload/image'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        request = 'GET /' + file_name + ' HTTP/1.1\r\n' \
                  + '\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code

    def test_404(self):
        error_code = 404
        file_name = '/abc.html'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = '/Download/'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'test/'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = 'test/webserver.pdf'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code


    def test_403(self):
        error_code = 403
        file_name = 'read_only.html'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code
        file_name = '/upload/read_only.txt'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name) == error_code

    def test_400(self):
        error_code = 400
        file_name = 'read_me.txt'
        request = 'GET /' + ' HTTP/1.1\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code
        request = 'GET /' + file_name + ' HTTP/1.1\r\n' \
                  + 'Host: 127.0.1.1:3000\r\n' \
                  + ''
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code
        request = 'GET /' + file_name + ' HTTP/1.1\r\n' \
                  + 'Host: 127.0.1.1:3000' \
                  + 'Accept-Language: en-US,en;q=0.5\r\n' \
                  + '\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code
        request = 'GET /' + file_name + ' HTTP/1.1\r\n' \
                  + 'abcdefg\r\n' \
                  + 'Accept-Language: en-US,en;q=0.5\r\n' \
                  + '\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code
        request = 'POST /' + file_name + ' HTTP/1.1\r\n' \
                  + 'abcdefg\r\n' \
                  + 'Accept-Language: en-US,en;q=0.5\r\n' \
                  + '\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code

    def test_505(self):
        error_code = 505
        file_name = 'read_me.txt'
        request = 'GET /' + ' HTTP/2.0\r\n\r\n'
        assert run_client(self.SERVER_NAME, self.SERVER_PORT, file_name, request) == error_code


if __name__ == '__main__':
    unittest.main()