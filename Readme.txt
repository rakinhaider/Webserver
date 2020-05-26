- A webserver and a webclient are implemented.
- If / is requested,
    The server tries find the file Upload/index.html
- If webserver.pdf is requested,
    The server tries find the file Upload/webserver.pdf
- If upload/webserver.pdf is requested,
    The server tries find the file Upload/upload/webserver.pdf

- The server and client is tested using test_server_client.py file.
    It takes two parameters. The server_name and the server_port
    Run 'python test_server_client.py <server_name> <server_port>' to run the test
    The test program tests status codes 200, 400, 403, 404, 505
    It also test sending multiple big files.

- The server is also tested with both Firefox and Chrome.
