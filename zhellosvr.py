from zring import *
from socket import socket
from sys import argv
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('127.0.0.1', int(argv[1])))
sock.listen(32768)
RSP = b'HTTP/1.0 200 OK\n\nHello'
TS = timespec(5)
N = 0

async def con(fd):
    global N
    if await Sqe(io_uring_prep_send, fd, RSP, len(RSP)) > 0:
        N += 1
    Sqe(io_uring_prep_close, fd)

@lambda _: [Task(_()) for i in range(10)]
async def _():
    while True:
        if (fd := await Sqe(io_uring_prep_accept, sock.fileno())) > 0:
            Task(con(fd))

@lambda _: Task(_())
async def _():
    global N
    while True:
        await Sqe(io_uring_prep_timeout, TS, 0, 0)
        print(N, stat())
        N = 0

run()