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
    server_sock.bind((ip, port))

    server_sock.listen(5)

    is_parent = 1

    # if True:
    while True:
        # print 'parent accepting'
        client_sock, addr = server_sock.accept()
        # Creating child process to handle requests
        is_parent = os.fork()
        # If the process is child recieve request and respond.
        if is_parent == 0:
            # Receiving request as string.
            request = ''
            while True:
                buffer = client_sock.recv(1024)
                print buffer
                request += buffer
                if len(buffer) < 1024:
                    break

            http_request = HTTPRequest(request=request)
            # Preparing a HTTP Response with the request and send the response to the client
            response = HTTPResponse(http_request)
            response.send_response(client_sock)
            client_sock.shutdown(socket.SHUT_RDWR)
            client_sock.close()
            # If the client have responded to the request then terminate the client process.
            # This break will break the while loop and the client process will terminate.
            break


    if is_parent != 0:
        server_sock.close()
    # For testing purpose chile process id can be printed to show that the child has been terminated.
    if is_parent == 0:
        # print 'Child PID ', os.getpid(), ' served ', http_request.url
        pass