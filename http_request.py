import re

class HTTPRequest:
    def __init__(self, request):
        # parse the string request and initiate the member variables.
        self.method, self.url, self.version, self.header_items, self.body = self.parse_http_request(request)

    def parse_request_line(self, request_line):
        # Parse request line into three segments.
        # method, url and version
        # If any of the segments is not found None is returned
        method = None
        url = None
        version = None
        try:
            line_splits = request_line.split(' ')
            method = line_splits[0]
            url = line_splits[1]
            version = line_splits[2]
        except:
            return method, url, version
        return method, url, version

    def parse_header(self, header):
        # Parse the header segment into key value pairs
        # If the header is a empty string,  return empty dictionary
        # Otherwise, parse each line of the header into key-value pairs.
        if header == '':
            return {}
        try:
            header_lines = header.split('\r\n')
            header_items = {}
            for line in header_lines:
                splits = line.split(': ')
                header_items[splits[0]] = splits[1]
                # If there are more than two key value pairs in a single line
                # then the request is not well formed.
                if len(splits) > 2:
                    return None
            # some header items have multiple comma seperated values
            # these values are parsed and converted into a list.
            for header_item in header_items:
                value = header_items[header_item]
                if ',' in value:
                    value = re.split(',[\s]*', value)
                header_items[header_item] = value
        except:
            return None
        return header_items

    def split_request_segments(self, request):
        # Parse the request string into three segments.
        # request_line, header_lines and body.
        request_line = None
        header = None
        body = None
        try:
            index = request.index('\r\n')
            request_line = request[:index]
            request = request[index + 2:]
            # If there are no header lines then
            # the header string should be exactly equal to '\r\n'
            # Otherwise there will be atleast one '\r\n\r\n' separating the header from the body
            if request == '\r\n':
                header = ''
                body = ''
            else:
                index = request.index('\r\n\r\n')
                header = request[:index]
                body = request[index + 4:]
        except:
            return request_line, header, body
        return request_line, header, body

    def parse_http_request(self, request):
        # Parse the request string
        request_line, header, body = self.split_request_segments(request)
        method, url, version = self.parse_request_line(request_line)
        header_items = self.parse_header(header)
        return method, url, version, header_items, body

    def is_bad(self):
        # Check whether the request is a bad request
        if self.method is None or self.url is None:
            return True
        # Since only GET is implemented other methods('POST', 'HEAD', 'PUT', 'DELETE') are considered Bad Request
        elif self.method not in ['GET']:
            return True
        elif self.header_items is None or self.body is None:
            return True

    def __str__(self):
        try:
            string = 'Method ' + self.method + ' ' + \
                    'Url ' + self.url + ' ' + \
                    'Version ' + self.version + ' '
            if self.header_items is None:
                string += 'Header ' + str(self.header_items) + ' '
            if self.body is not None:
                string += 'Body ' + self.body
        except:
            return 'Bad Request'
        return string

    def __repr__(self):
        return self.__str__()
