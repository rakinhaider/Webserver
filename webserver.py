import socket
import sys
import os
import platform
import re
from datetime import datetime


class HTTPRequest():
    def __init__(self, request):
        self.method, self.url, self.version, self.header_items, self.body = self.parse_http_request(request)

    def parse_request_line(self, request_line):
        try:
            line_splits = request_line.split(' ')
            method = line_splits[0]
            url = line_splits[1]
            if url == '/':
                url = '/index.html'
            version = line_splits[2]
        except:
            return None, None, None
        return method, url, version

    def parse_header(self, header):
        try:
            header_lines = header.split('\r\n')
            header_items = {}
            for line in header_lines:
                splits = line.split(': ')
                header_items[splits[0]] = splits[1]
            for header_item in header_items:
                value = header_items[header_item]
                if ',' in value:
                    value = re.split(',[\s]*', value)
                header_items[header_item] = value
        except:
            return None
        return header_items

    def split_request_segments(self, request):
        try:
            request_splits = request.split('\r\n\r\n')
            body = request_splits[1]
            index = request_splits[0].index('\r\n')
            request_line = request_splits[0][:index]
            header = request_splits[0][index + 2:]
        except:
            return None, None, None
        return request_line, header, body

    def parse_http_request(self, request):
        request_line, header, body = self.split_request_segments(request)
        # print 'request_line', request_line
        method, url, version = self.parse_request_line(request_line)
        # print method, url, version
        # print 'header', header
        header_items = self.parse_header(header)
        # print header_items
        # print 'body', body
        return method, url, version, header_items, body

    def is_bad(self):
        if self.method is None or self.url is None:
            return True
        elif self.method not in ['GET', 'POST', 'HEAD', 'PUT', 'DELETE']:
            return True
        elif self.header_items is None or self.body is None:
            return True

    def __str__(self):
        return 'Method ' + http_request.method + ' ' +\
               'Url ' + http_request.url + ' ' +\
               'Version ' + http_request.version + ' ' +\
               'Header ' + str(http_request.header_items) + ' ' +\
               'Body ' + http_request.body

    def __repr__(self):
        return 'Method ' + http_request.method, ' ', 'Url', http_request.url, \
               ' ', 'Version', http_request.version, ' ', 'Header', http_request.header_items, \
               ' ', 'Body', http_request.body


class HTTPResponse():
    BASE_FOLDER = 'Upload'
    DEFAULT_HTTP_VERSION = 'HTTP/1.1'
    SUPPORTED_VERSIONS = ['HTTP/1.0', 'HTTP/1.1']
    ACCEPT = 'Accept'
    LINE_SEPARATOR = '\r\n'

    def __init__(self, request):
        self.request = request
        self.status_code = None

    def get_status_message(self, status_code):
        # print status_code
        if status_code == 200:
            return 'OK'
        elif status_code == 301:
            return 'Moved Parmanently'
        elif status_code == 400:
            return 'Bad Request'
        elif status_code == 403:
            return 'Forbidden'
        elif status_code == 404:
            return 'Not Found'
        elif status_code == 500:
            return 'Internal Server Error'
        elif status_code == 505:
            return 'HTTP Version Not Supported'

    def get_content_type(self, url, accepts):
        _, file_extension = os.path.splitext(url)
        file_extension = file_extension[1:]
        # print(file_extension)
        subtype = file_extension
        if file_extension in ['txt']:
            type = 'text/'
            subtype = 'plain'
        elif file_extension in ['html', 'csv']:
            type = 'text/'
        elif file_extension in ['jpg', 'jpeg', 'png', 'bmp']:
            type = 'image/'
        elif file_extension in ['gif']:
            type = 'image/'
        elif file_extension in ['pdf']:
            type = 'application/'
        # print(accepts)
        return type + subtype

    def get_response_line(self, status_code):
        return self.request.version + ' ' + str(status_code) + ' ' + self.get_status_message(status_code) + '\r\n'

    def get_response_header(self):
        header = 'Date: ' + str(datetime.now()) + self.LINE_SEPARATOR
        header += 'Server: ' + os.name + '/' + platform.release() + ' (' + platform.system() + ')' + self.LINE_SEPARATOR
        request = self.request
        if self.status_code == 200:
            header += 'Last-Modified: ' + str(os.path.getmtime(self.BASE_FOLDER + request.url)) + self.LINE_SEPARATOR
            header += 'Content-Length: ' + str(os.path.getsize(self.BASE_FOLDER + request.url)) + self.LINE_SEPARATOR
            header += 'Content-Type: ' + self.get_content_type(request.url, request.header_items[self.ACCEPT]) +\
                      self.LINE_SEPARATOR
        header += 'Connection: closed' + self.LINE_SEPARATOR
        header += self.LINE_SEPARATOR
        return header

    def check_error(self):
        status_code = 200
        if self.request.is_bad():
            status_code = 400
        elif self.request.method == 'GET':
            file_path = self.BASE_FOLDER + self.request.url
            if not os.path.exists(file_path):
                status_code = 404
            elif (os.stat(file_path).st_mode & (1 << 8)) == 0:
                status_code = 403
        elif self.request.version not in self.SUPPORTED_VERSIONS:
            status_code = 505
        self.status_code = status_code
        print self.status_code

    def send_response_line(self, client_sock):
        if self.status_code == None:
            self.check_error()
        # print 'sending request line'
        success = client_sock.sendall(self.request.version + ' ' + str(self.status_code)
                            + ' ' + self.get_status_message(self.status_code) + '\r\n')

        # if success is None:
            # print 'request line sent successfully'

    def send_response_header(self, client_sock):
        success = client_sock.sendall(self.get_response_header())
        # if success is None:
            # print 'header sent successfully'

    def send_response_body(self, client_sock):
        if self.status_code == 404:
            url = '/404_not_found.html'
        elif self.status_code == 403:
            url = '/403_forbidden.html'
        elif self.status_code == 400:
            url = '/400_bad_request.html'
        elif self.request.url == '/':
            url = '/index.html'
        else:
            url = self.request.url
        f = open(self.BASE_FOLDER + url)
        # print 'sending body'
        # overall_success = True
        for line in f:
            success = client_sock.sendall(line)
            # if success is not None:
                # overall_success = False
        # if overall_success:
            # print 'Body sent successfully'


if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    port = 3000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((ip, port))

    server_sock.listen(5)

    is_parent = 1

    # if True:
    while True:
        # print 'parent accepting'
        client_sock, addr = server_sock.accept()
        is_parent = os.fork()
        if is_parent == 0:
            request = ''
            while True:
                buffer = client_sock.recv(1024)
                print buffer
                request += buffer
                if len(buffer) < 1024:
                    break

            http_request = HTTPRequest(request)
            print 'child_pid', os.getpid(), ' serving ', http_request.url
            print http_request
            response = HTTPResponse(http_request)
            response.check_error()
            response.send_response_line(client_sock)
            response.send_response_header(client_sock)
            response.send_response_body(client_sock)
            client_sock.shutdown(socket.SHUT_RDWR)
            client_sock.close()
            break


    if is_parent != 0:
        server_sock.close()
    if is_parent == 0:
        print 'Child PID ', os.getpid(), ' served ', http_request.url