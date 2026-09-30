from liburing import *
from socket import socket
from sys import argv
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('127.0.0.1',int(argv[1])))
sock.listen(65536*2)
RING = io_uring()
io_uring_queue_init(256, RING)
CQE = io_uring_cqe()
RSP = bytearray(1<<24)

def accept():
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_accept(sqe, sock.fileno())
    sqe.user_data = 2
def send(fd):
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_send(sqe, fd, RSP, len(RSP))
    sqe.user_data = 1
    return sqe
def close(fd):
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_close(sqe, fd)
    sqe.user_data = 1
for _ in range(10):
    accept()
while True:
    io_uring_submit(RING)
    while not io_uring_peek_cqe(RING, CQE):
        if CQE.user_data == 2:
            send(CQE.res).flags = IOSQE_IO_HARDLINK
            close(CQE.res)
            accept()
        io_uring_cqe_seen(RING, CQE)
