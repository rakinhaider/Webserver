import os
import platform
from datetime import datetime
import re


class HTTPResponse:
    BASE_FOLDER = 'Upload'
    DEFAULT_HTTP_VERSION = 'HTTP/1.1'
    SUPPORTED_VERSIONS = ['HTTP/1.0', 'HTTP/1.1']
    ACCEPT = 'Accept'
    LINE_SEPARATOR = '\r\n'
    CONTENT_DESPOSITION = 'Content-Desposition'
    BIG_FILE_SIZE = 20000000

    def __init__(self, request=None, response_str=None):
        self.request = request
        self.response_str = response_str
        self.status_code = None
        self.method = None
        self.url = None
        self.header_items = None
        self.body = None

    def __str__(self):
        if self.response_str is not None:
            return self.response_str
        else:
            pass

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
            size = os.path.getsize(self.BASE_FOLDER + request.url)
            header += 'Content-Length: ' + str(size) + self.LINE_SEPARATOR
            content_type = self.get_content_type(request.url, request.header_items[self.ACCEPT])
            header += 'Content-Type: ' + content_type +\
                      self.LINE_SEPARATOR
            if content_type not in ['text/html', 'text/plain'] or size > self.BIG_FILE_SIZE:
                header += self.CONTENT_DESPOSITION + ': attachment' + self.LINE_SEPARATOR
        header += 'Connection: closed' + self.LINE_SEPARATOR
        header += self.LINE_SEPARATOR
        return header

    def check_error(self):
        status_code = 200
        if self.request.is_bad():
            status_code = 400
        elif self.request.version not in self.SUPPORTED_VERSIONS:
            status_code = 505
        elif self.request.method == 'GET':
            file_path = self.BASE_FOLDER + self.request.url
            if not os.path.exists(file_path):
                status_code = 404
            elif (os.stat(file_path).st_mode & (1 << 8)) == 0:
                status_code = 403
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
        header = self.get_response_header()
        print header
        success = client_sock.sendall(header)
        # if success is None:
            # print 'header sent successfully'

    def send_response_body(self, client_sock):
        if self.status_code == 404:
            url = '/404_not_found.html'
        elif self.status_code == 403:
            url = '/403_forbidden.html'
        elif self.status_code == 400:
            url = '/400_bad_request.html'
        elif self.status_code == 505:
            url = '/505_http_version_not_supported.html'
        elif self.status_code == 500:
            url = '/500_internal_server_error.html'
        elif self.status_code == 200:
            if self.request.url == '/':
                url = '/index.html'
            else:
                url = self.request.url
        else:
            return ''
        f = open(self.BASE_FOLDER + url)
        while True:
            buffer = f.read(1024)
            success = client_sock.send(buffer)
            if len(buffer) < 1024:
                break

    def send_response(self, client_sock):
        self.check_error()
        self.send_response_line(client_sock)
        self.send_response_header(client_sock)
        self.send_response_body(client_sock)

    def parse_response(self):
        try:
            segments = self.response_str.split('\r\n\r\n')
            self.body = segments[1]
            index = segments[0].index('\r\n')
            self.response_line = segments[0][:index]
            self.header_items = self.parse_header(segments[0][index + 2:])
        except:
            self.body = None
            self.response_line = None
            self.header_items = None

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

    def get_header_by_name(self, key):
        if self.header_items is None:
            return None
        return self.header_items.get(key)

    def receive(self, client_sock, file_name):
        response = ''
        while True:
            buffer = client_sock.recv(1024)
            response += buffer
            if '\r\n' in response:
                break
            elif len(buffer) == 0:
                print 'Remote Socket Closed'
                break
                return

        index = response.index('\r\n')
        self.response_line = response[:index]
        self.response_str = self.response_line + self.LINE_SEPARATOR
        response = response[index + 2:]
        print self.response_line
        while True:
            buffer = client_sock.recv(1024)
            response += buffer
            if '\r\n\r\n' in response:
                break
            elif len(buffer) == 0:
                print 'Remote Socket Closed'
                break
                return

        index = response.index('\r\n\r\n')
        self.header_items = self.parse_header(response[:index])
        self.response_str += response[:index] + self.LINE_SEPARATOR * 2
        response = response[index + 4:]
        print self.header_items

        base_folder = 'Download/'
        if os.path.exists(base_folder + file_name):
            root, ext = os.path.splitext(file_name)
            i = 1
            while os.path.exists(base_folder + root + ' (' + str(i) + ')' + ext):
                i += 1
            file_name = root + ' (' + str(i) + ')' + ext

        if self.get_header_by_name(self.CONTENT_DESPOSITION) == 'attachment':
            file_size = int(self.get_header_by_name('Content-Length'))
            downloaded = 0
            f = open(base_folder + file_name, 'w')
            f.write(response)
            downloaded += len(response)
            print 'Downloading', downloaded * 100.0 / file_size, '%',
            while True:
                buffer = client_sock.recv(1024)
                f.write(buffer)
                downloaded += len(buffer)
                print '\rDownloading', downloaded * 100.0 / file_size, '%',
                if len(buffer) == 0:
                    break

            print '\rDownloading', 100, '%'
            self.response_str += '<VERY BIG FILE. NOT SHOWN. OPEN ' + file_name + ' TO VIEW>'
        else:
            while True:
                buffer = client_sock.recv(1024)
                response += buffer
                if len(buffer) == 0:
                    break
            self.body = response
            self.response_str += self.body