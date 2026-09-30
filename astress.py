from aring import *
from asyncio import sleep

ADDR = sockaddr(AF_INET, b'127.0.0.1', 8123)
REQ = b'GET / HTTP/1.0\n\n'
RSP = bytearray(256)

async def loop():
    global N, E
    fd = None
    while True:
        try:
            fd = await SQE(io_uring_prep_socket, AF_INET, SOCK_STREAM)
            SQE(io_uring_prep_connect, fd, ADDR, flag=IOSQE_IO_LINK)
            # SQE(io_uring_prep_write, fd, REQ, len(REQ), 0, flag=IOSQE_IO_LINK)
            await SQE(io_uring_prep_read, fd, RSP, len(RSP))
            N += 1
        except Exception as e:
            E += 1
        finally:
            if fd:
                SQE(io_uring_prep_close, fd)
                fd = None

async def stress():
    global N, E
    for _ in range(9):
        Task(loop())
    while True:
        N = E = 0
        await sleep(1)
        print(N, E)

get_event_loop().run_until_complete(stress())