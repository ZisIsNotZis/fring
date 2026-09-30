from zfile import *
from socket import socket
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('127.0.0.1', 8122))
sock.listen(32768)
buf = bytearray(256)

async def con(fd):
    await Sqe(io_uring_prep_recv, fd, buf, len(buf))
    _ = b'HTTP/1.0 200 OK\n\n' + await(await open(buf[5:].partition(b' ')[0])).read()
    await Sqe(io_uring_prep_send, fd, _, len(_))
    Sqe(io_uring_prep_close, fd)

@lambda _:Task(_())
async def svr():
    while True:
        Task(con(await Sqe(io_uring_prep_accept, sock.fileno())))

run()