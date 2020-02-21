import os
import platform
from datetime import datetime
import re

class HTTPResponse:
    SERVER_ROOT = 'Upload'
    CLIENT_ROOT = 'Download/'
    DEFAULT_HTTP_VERSION = 'HTTP/1.1'
    SUPPORTED_VERSIONS = ['HTTP/1.0', 'HTTP/1.1']
    ACCEPT = 'Accept'
    LINE_SEPARATOR = '\r\n'
    CONTENT_DISPOSITION = 'Content-Disposition'
    BIG_FILE_SIZE = 20000000
    ERROR_HTML = '<!doctype html><html><head><title><status_code> <status_msg>!</title></head><body><p><status_code> <status_msg></p></body></html>'

    def __init__(self, request=None, response_str=None):
        self.request = request
        self.response_str = response_str
        self.status_code = None
        self.header_items = None
        self.body = None

    def __str__(self):
        if self.response_str is not None:
            return self.response_str
        else:
            pass

    def get_status_message(self, status_code):
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
        # Split the file name and extension.
        # Based on the extension return the content type
        # If no extension is found, use 'application/octet-stream'
        _, file_extension = os.path.splitext(url)
        file_extension = file_extension[1:]
        subtype = file_extension
        if subtype is None or subtype == '':
            return 'application/octet-stream'
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
        return type + subtype

    def get_response_header(self):
        header = 'Date: ' + str(datetime.now()) + self.LINE_SEPARATOR
        header += 'Server: ' + os.name + '/' + platform.release() + ' (' + platform.system() + ')' + self.LINE_SEPARATOR
        request = self.request
        # If the status code is 200
        # Append Last-Modified, Content-Length and Content-Type with the header.
        if self.status_code == 200:
            header += 'Last-Modified: ' + str(os.path.getmtime(self.SERVER_ROOT + request.url)) + self.LINE_SEPARATOR
            size = os.path.getsize(self.SERVER_ROOT + request.url)
            header += 'Content-Length: ' + str(size) + self.LINE_SEPARATOR
            content_type = self.get_content_type(self.resolve_url(), request.header_items.get(self.ACCEPT))
            header += 'Content-Type: ' + content_type +\
                      self.LINE_SEPARATOR
            if (content_type not in ['text/html', 'text/plain']) or size > self.BIG_FILE_SIZE:
                header += self.CONTENT_DISPOSITION + ': attachment' + self.LINE_SEPARATOR
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
            file_path = self.resolve_url()
            if not os.path.exists(file_path):
                status_code = 404
            # Testing whether the real permission not set. In that case the file is forbidden.
            elif (os.stat(file_path).st_mode & (1 << 8)) == 0:
                status_code = 403
        self.status_code = status_code

    def resolve_url(self):
        file_path = self.SERVER_ROOT + self.request.url

        if os.path.isdir(file_path):
            if file_path.endswith('/'):
                file_path += 'index.html'
            else:
                file_path += '/index.html'

        return file_path

    def get_response_line(self, status_code):
        return self.request.version + ' ' + str(self.status_code) +\
               ' ' + self.get_status_message(self.status_code) + self.LINE_SEPARATOR

    def send_response_line(self, client_sock):
        if self.status_code == None:
            self.check_error()
        if self.request.version is None:
            self.request.version = self.DEFAULT_HTTP_VERSION

        response_line = self.get_response_line(self.status_code)
        print response_line
        success = client_sock.sendall(response_line)

    def send_response_header(self, client_sock):
        header = self.get_response_header()
        print header
        success = client_sock.sendall(header)

    def send_response_body(self, client_sock):
        # If the status code is 200
        # the corresponding file is read
        # Otherwise and html containing the error message is sent.
        if self.status_code == 200:
            url = self.request.url
        else:
            error_msg = self.ERROR_HTML.replace('<status_code>', str(self.status_code))
            error_msg = error_msg.replace('<status_msg>', self.get_status_message(self.status_code))
            client_sock.sendall(error_msg)
            return

        file_path = self.resolve_url()
        f = open(file_path, 'r')
        while True:
            buffer = f.read(1024)
            success = client_sock.send(buffer)
            if len(buffer) < 1024:
                break

    def send_response(self, client_sock):
        # Check error and then send the response_line, header and the body sequentially
        self.check_error()
        self.send_response_line(client_sock)
        self.send_response_header(client_sock)
        self.send_response_body(client_sock)

    def parse_response(self):
        # This is used by the client to parse the received response.
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

    def parse_response_line(self):
        # Parse the response line to get the version and status_code sent by the server.
        response_line_segments = self.response_line.split(' ')
        self.version = response_line_segments[0]
        self.status_code = int(response_line_segments[1])

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
            return header_items
        return header_items

    def get_header_by_name(self, key):
        if self.header_items is None:
            return None
        return self.header_items.get(key)

    def receive(self, client_sock, file_name):
        # This function is used by the client to recieve each segment of the response
        response = ''
        while True:
            buffer = client_sock.recv(1024)
            response += buffer
            # Receive until first \r\n is received
            if '\r\n' in response:
                break
            elif len(buffer) == 0:
                print 'Remote Socket Closed'
                break
                return

        index = response.index('\r\n')
        self.response_line = response[:index]
        self.response_str = self.response_line + self.LINE_SEPARATOR
        # After the response_line,
        # the rest of the received response will contain the header and the body
        response = response[index + 2:]
        # print self.response_line
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

        file_name = os.path.basename(file_name)
        # Resolve naming conflict.
        # If file_name = a.txt and it already exists, try 'a (1).txt', 'a (2).txt' and so on.
        if os.path.exists(self.CLIENT_ROOT + file_name):
            root, ext = os.path.splitext(file_name)
            i = 1
            while os.path.exists(self.CLIENT_ROOT + root + ' (' + str(i) + ')' + ext):
                i += 1
            file_name = root + ' (' + str(i) + ')' + ext

        # If the file is very big or the file is not text,
        # it is saved as a file and not shown in console.
        # Otherwise, it is just shown in the console.
        if self.get_header_by_name(self.CONTENT_DISPOSITION) == 'attachment':
            file_size = int(self.get_header_by_name('Content-Length'))
            downloaded = 0
            f = open(self.CLIENT_ROOT + file_name, 'w')
            f.write(response)
            f.flush()
            downloaded += len(response)
            print 'Downloading', downloaded * 100.0 / file_size, '%',
            while True:
                buffer = client_sock.recv(1024)
                f.write(buffer)
                f.flush()
                downloaded += len(buffer)
                print '\rDownloading', downloaded * 100.0 / file_size, '%',
                if len(buffer) == 0:
                    break

            print '\rDownloading', 100, '%'
            if int(self.get_header_by_name('Content-Length')) > self.BIG_FILE_SIZE:
                self.response_str += '<VERY BIG FILE. NOT SHOWN. OPEN ' + file_name + ' TO VIEW>'
            else:
                self.response_str += '<NON-Text FILE NOT SHOWN. OPEN ' + file_name + ' TO VIEW>'
        else:
            while True:
                buffer = client_sock.recv(1024)
                response += buffer
                if len(buffer) == 0:
                    break
            self.body = response
            self.response_str += self.body