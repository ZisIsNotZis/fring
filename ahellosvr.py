from aring import *

async def hello():
    sock = await SQE(io_uring_prep_socket, AF_INET, SOCK_STREAM)
    bind(sock, sockaddr(AF_INET,b'127.0.0.1',8123))
    listen(sock, 1024)
    hello = b'HTTP/1.0 200 OK\n\nHello'
    while True:
        fd = await SQE(io_uring_prep_accept, sock)
        SQE(io_uring_prep_write, fd, hello, len(hello), 0, flag=IOSQE_IO_LINK)
        SQE(io_uring_prep_close, fd)

get_event_loop().run_until_complete(hello())