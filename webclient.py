import socket
import sys
from http_response import HTTPResponse

def run_client(server_name, server_port, file_name, request=None):
    client_sock = socket.socket(socket.AF_INET,
                                socket.SOCK_STREAM)
    client_sock.connect((socket.gethostbyname(server_name),
                         server_port))
    # Remove / prefix from file_name
    # If the given file_name is of the form /index.html,
    # it will convert it to index.html
    if file_name.startswith('/'):
        file_name = file_name[1:]

    # If request is not passed as the parameter,
    # the default request will be used.
    if request is None:
        request = 'GET /' + file_name + ' HTTP/1.1\r\n' \
                  + 'Host: 127.0.1.1:3000\r\n' \
                  + 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0\r\n' \
                  + 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n' \
                  + 'Accept-Language: en-US,en;q=0.5\r\n' \
                  + 'Accept-Encoding: gzip, deflate\r\n' \
                  + '\r\n'

    client_sock.sendall(request)

    response = HTTPResponse()
    response.receive(client_sock, file_path=file_name)
    print response
    client_sock.close()
    return response.status_code


if __name__ == "__main__":

    server_name = socket.gethostname()
    server_port = 3000
    file_name = 'big_text.txt'
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
        server_port = int(sys.argv[2])
        file_name = sys.argv[3]

    run_client(server_name, server_port, file_name)