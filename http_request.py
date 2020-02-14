import re

class HTTPRequest:
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
        string = 'Method ' + self.method + ' ' + \
                'Url ' + self.url + ' ' + \
                'Version ' + self.version + ' ' + \
                'Header ' + str(self.header_items) + ' '
        if self.body is not None:
            string += 'Body ' + self.body
        return string

    def __repr__(self):
        return self.__str__()
