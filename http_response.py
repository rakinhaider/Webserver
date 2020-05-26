import os
import platform
from datetime import datetime
import re
import socket

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
        if request is not None:
            self.request_url = self.resolve_url(request)
            self.version = self.get_response_version(request)
            self.status_code = self.check_error(request)
            self.header_items = self.prep_resp_header_items(request)
            self.body = self.prep_resp_body()

        elif self.response_str is not None:
            self.version = None
            self.status_code = None
            self.header_items = None
            self.body = None

    def __str__(self):
        if self.status_code is None:
            return ''
        s = self.prep_response_line()
        s += self.prep_header()
        if not self.is_attachment(self.header_items):
            s += self.body
        else:
            s += 'Attachment Received.' \
                 ' Stored at ' + self.stored_path
        return s

    def is_attachment(self, header_items):
        text_file_types = ['text/html', 'text/plain']
        if self.status_code != 200:
            return False
        if header_items['Content-Type'] not in text_file_types:
            return True
        elif int(header_items['Content-Length']) > self.BIG_FILE_SIZE:
            return True
        else:
            return False

    def get_response_version(self, request):
        if request.version is not None:
            return request.version
        else:
            return self.DEFAULT_HTTP_VERSION

    def get_status_message(self):
        if self.status_code == 200:
            return 'OK'
        elif self.status_code == 301:
            return 'Moved Parmanently'
        elif self.status_code == 400:
            return 'Bad Request'
        elif self.status_code == 403:
            return 'Forbidden'
        elif self.status_code == 404:
            return 'Not Found'
        elif self.status_code == 500:
            return 'Internal Server Error'
        elif self.status_code == 505:
            return 'HTTP Version Not Supported'

    def get_content_type(self, request):
        # Split the file name and extension.
        # Based on the extension return the content type
        # If no extension is found, use 'application/octet-stream'
        url = self.request_url
        accepts = request.header_items.get(self.ACCEPT)

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
        else:
            return 'application/octet-stream'
        return type + subtype

    def get_server_name(self):
        sname = os.name + '/' + platform.release()
        sname += ' (' + platform.system() + ')'
        return sname

    def check_error(self, request):
        status_code = 200
        if request.is_bad():
            status_code = 400
        elif request.version not in self.SUPPORTED_VERSIONS:
            status_code = 505
        elif request.method == 'GET':
            file_path = self.request_url
            if not os.path.exists(file_path):
                status_code = 404
            # Testing whether the real permission not set.
            # In that case the file is forbidden.
            elif (os.stat(file_path).st_mode & (1 << 8)) == 0:
                status_code = 403
        return status_code

    def resolve_url(self, request):
        file_path = self.SERVER_ROOT + request.url

        if os.path.isdir(file_path):
            if file_path.endswith('/'):
                file_path += 'index.html'
            else:
                file_path += '/index.html'

        return file_path

    def prep_response_line(self):
        resp_line = self.version + ' '
        resp_line += str(self.status_code) + ' '
        resp_line += self.get_status_message()
        resp_line += self.LINE_SEPARATOR
        return resp_line

    def prep_resp_header_items(self, request):
        header_items = {}
        header_items['Date'] = datetime.now()
        header_items['Server'] = self.get_server_name()
        # If the status code is 200,
        # append Last-Modified, Content-Length
        # and Content-Type with the header.
        if self.status_code == 200:
            header_items['Last-Modified'] = os.path.getmtime(self.request_url)
            size = os.path.getsize(self.request_url)
            header_items['Content-Length'] = size
            content_type = self.get_content_type(request)
            header_items['Content-Type'] = content_type
            if self.is_attachment(header_items):
                header_items[self.CONTENT_DISPOSITION] = 'attachment'
        header_items['Connection'] = 'closed'
        return header_items

    def prep_header(self):
        header = ''
        for item in self.header_items:
            header += item + ': ' + str(self.header_items[item])
            header += self.LINE_SEPARATOR
        header += self.LINE_SEPARATOR
        return header

    def prep_resp_body(self):
        if self.status_code != 200:
            return self.prep_error_msg()
        elif not self.is_attachment(self.header_items):
            text = ''
            for line in _read_file(self.request_url):
                text += line
            return text
        else:
            return None

    def prep_error_msg(self):
        error_msg = self.ERROR_HTML
        error_msg = error_msg.replace('<status_code>', str(self.status_code))
        status_msg = self.get_status_message()
        error_msg = error_msg.replace('<status_msg>', status_msg)
        return error_msg

    def send_response_line(self, client_sock):
        response_line = self.prep_response_line()
        print response_line
        success = client_sock.sendall(response_line)

    def send_response_header(self, client_sock):
        header = self.prep_header()
        print header
        success = client_sock.sendall(header)

    def send_response_body(self, client_sock):
        # If the body is empty (the file is big or attachment),
        # read the file in chucks and send.
        # Otherwise, send the text in the body.
        if self.body is not None:
            client_sock.sendall(self.body)
        else:
            file_path = self.request_url
            for buffer in _read_file(file_path):
                success = client_sock.send(buffer)

    def send_response(self, client_sock):
        # Send the response_line, header and the body sequentially
        self.send_response_line(client_sock)
        self.send_response_header(client_sock)
        self.send_response_body(client_sock)

    def parse_resp_str(self):
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

    def parse_resp_line(self, response_line):
        # Parse the response line to get the version and status_code sent by the server.
        response_line_segments = response_line.split(' ')
        version = response_line_segments[0]
        status_code = int(response_line_segments[1])
        return version, status_code

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

    def get_header_item(self, key):
        if self.header_items is None:
            return None
        return self.header_items.get(key)

    def read_resp_line(self, client_sock):
        response = ''
        while True:
            buffer = client_sock.recv(1024, socket.MSG_PEEK)
            if '\r\n' in buffer:
                index = buffer.index('\r\n')
                response += buffer[:index]
                client_sock.recv(index + 2)
                break
            elif len(buffer) == 0:
                print 'Remote Socket Closed'
                exit(1)
            else:
                client_sock.recv(1024)
                response += buffer
        return response

    def read_header(self, client_sock):
        header = ''
        while True:
            buffer = client_sock.recv(1024, socket.MSG_PEEK)
            if '\r\n\r\n' in buffer:
                index = buffer.index('\r\n\r\n')
                header += buffer[:index]
                client_sock.recv(index + 4)
                break
            elif len(buffer) == 0:
                print 'Remote Socket Closed'
                return
            else:
                client_sock.recv(1024)
                header += buffer
        return header

    def read_body(self, client_sock, file_path=None):
        response = ''
        file_name = os.path.basename(file_path)
        file_path = self.CLIENT_ROOT
        file_path += file_name
        # Resolve naming conflict.
        # If file_name = a.txt and it already exists,
        # try 'a (1).txt', 'a (2).txt' and so on.
        if os.path.exists(self.CLIENT_ROOT + file_name):
            root, ext = os.path.splitext(file_name)
            i = 1
            while os.path.exists(file_path):
                i += 1
                file_path = self.CLIENT_ROOT
                file_path += root + ' (' + str(i) + ')' + ext

        # If the file is very big or the file is not text,
        # it is saved as a file and not shown in console.
        # Otherwise, it is just shown in the console.
        if self.is_attachment(self.header_items):
            file_size = int(self.get_header_item('Content-Length'))
            downloaded = 0
            f = open(file_path, 'w')
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
            if int(self.get_header_item('Content-Length')) > self.BIG_FILE_SIZE:
                self.body = None
                self.stored_path = file_path
            else:
                self.body = None
                self.stored_path = file_path
            return None
        else:
            while True:
                buffer = client_sock.recv(1024)
                response += buffer
                if len(buffer) == 0:
                    break
            self.body = response
            return response

    def receive(self, client_sock, file_path):
        # This function is used by the client
        # to recieve each segment of the response

        # First response line is read and parsed.
        response_line = self.read_resp_line(client_sock)
        self.version, self.status_code = self.parse_resp_line(response_line)
        # Then header is read and parsed.
        header = self.read_header(client_sock)
        self.header_items = self.parse_header(header)
        # Finally, body is read.
        # If attachment, file is stored returned None.
        self.body = self.read_body(client_sock, file_path)


def _read_file(file_path):
    f = open(file_path, 'r')
    while True:
        buffer = f.read(1024)
        yield buffer
        if len(buffer) < 1024:
            break