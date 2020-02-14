import socket
import sys
import os

from http_request import HTTPRequest
from http_response import HTTPResponse

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    port = 3000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print ip, port
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

            http_request = HTTPRequest(request=request)
            print 'child_pid', os.getpid(), ' serving ', http_request.url
            print http_request
            response = HTTPResponse(http_request)
            response.send_response(client_sock)
            client_sock.shutdown(socket.SHUT_RDWR)
            client_sock.close()
            break


    if is_parent != 0:
        server_sock.close()
    if is_parent == 0:
        print 'Child PID ', os.getpid(), ' served ', http_request.url