from liburing import *
from sys import argv
RING = io_uring()
io_uring_queue_init(256, RING)
CQE = io_uring_cqe()
ADDR = sockaddr(AF_INET, b'127.0.0.1', int(argv[1]))
RSP = bytearray(1<<24)
TS = timespec(1)
N = 0

def socket():
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_socket(sqe, AF_INET, SOCK_STREAM)
    sqe.user_data = 1
def connect(fd):
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_connect(sqe, fd, ADDR)
    sqe.user_data = fd << 3 | 2
def recv(fd):
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_recv(sqe, fd, RSP, len(RSP))
    sqe.user_data = 3
    return sqe
def close(fd):
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_close(sqe, fd)
    sqe.user_data = 4
def timeout():
    sqe = io_uring_get_sqe(RING)
    io_uring_prep_timeout(sqe, TS, 0, IORING_TIMEOUT_MULTISHOT)
    sqe.user_data = 5
for _ in range(10):
    socket()
timeout()
while True:
    io_uring_submit_and_wait(RING, 1)
    while not io_uring_peek_cqe(RING, CQE):
        if CQE.user_data == 1:
            if CQE.res <= 0:
                socket()
            else:
                connect(CQE.res)
        elif CQE.user_data & 3 == 2:
            if CQE.res < 0:
                connect(CQE.user_data >> 3)
            else:
                recv(CQE.user_data >> 3).flags = IOSQE_IO_HARDLINK
                close(CQE.user_data >> 3)
                socket()
        elif CQE.user_data == 3:
            if CQE.res > 0:
                N += 1
        elif CQE.user_data == 5:
            print(N)
            N = 0
        io_uring_cqe_seen(RING, CQE)
