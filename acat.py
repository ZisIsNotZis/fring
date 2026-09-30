from aring import *
from mmap import mmap, MAP_SHARED, PROT_READ

async def hello():
    sock = await SQE(io_uring_prep_socket, AF_INET, SOCK_STREAM)
    bind(sock, sockaddr(AF_INET,b'127.0.0.1',8123))
    listen(sock, 1024)
    http = b'HTTP/1.0 200 OK\n\n'
    _hello = open('hello', 'rb')
    hello = mmap(_hello.fileno(), 0, MAP_SHARED, PROT_READ)
    _world = open('world', 'rb')
    world = mmap(_world.fileno(), 0, MAP_SHARED, PROT_READ)
    while True:
        fd = await SQE(io_uring_prep_accept, sock)
        SQE(io_uring_prep_write, fd, http, len(http), 0, flag=IOSQE_IO_HARDLINK)
        SQE(io_uring_prep_write, fd, hello, len(hello), 0, flag=IOSQE_IO_HARDLINK)
        SQE(io_uring_prep_write, fd, world, len(world), 0, flag=IOSQE_IO_HARDLINK)
        SQE(io_uring_prep_close, fd)

get_event_loop().run_until_complete(hello())