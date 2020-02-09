import socket
import sys
if __name__ == "__main__":

    server_name = socket.gethostname()
    server_port = 3000
    file_name = '\\index.html'
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
        server_port = int(sys.argv[2])

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_sock.connect((server_name, server_port))
    client_sock.send('hello')
    client_sock.close()
