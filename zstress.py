from zring import *
from sys import argv
from os import strerror
ADDR = sockaddr(AF_INET, b'127.0.0.1', int(argv[1]))
RSP = bytearray(256)
TS = timespec(5)
N = 0

@lambda _:[Task(_())for i in range(10)]
async def _():
    global N, E
    while True:
        if (fd:=await Sqe(io_uring_prep_socket,AF_INET,SOCK_STREAM))>0 and await Sqe(io_uring_prep_connect,fd,ADDR)>=0:
            if await Sqe(io_uring_prep_recv, fd, RSP, len(RSP)) > 0:
                N += 1
            Sqe(io_uring_prep_close, fd)

@lambda _:Task(_())
async def _():
    global N
    while True:
        await Sqe(io_uring_prep_timeout, TS, 0, 0)
        print(N, stat())
        N = 0

run()