from liburing import *
from socket import socket, AF_INET, SOCK_STREAM
SOCK = socket(AF_INET, SOCK_STREAM)
SOCK.bind(('127.0.0.1', 8080))
SOCK.listen()
CQE = io_uring_cqe()
RING = io_uring()
io_uring_queue_init(256, RING, IORING_SETUP_SQPOLL)
_ = io_uring_get_sqe(RING)
_.user_data = 1
io_uring_prep_multishot_accept(_, SOCK.fileno())
while True:
    if RING.sq_ring.flags & IORING_SQ_NEED_WAKEUP:
        io_uring_enter(RING, 0, 0, IORING_ENTER_SQ_WAKEUP)
    while not io_uring_wait_cqe(RING, CQE):
        if CQE.user_data:
            _ = io_uring_get_sqe(RING)
            _.flags = IOSQE_IO_HARDLINK
            io_uring_prep_send(_, CQE.res, b'HTTP/1.0 200 OK\n\nHello World', 28)
            io_uring_prep_close(io_uring_get_sqe(RING), CQE.res)
        io_uring_cqe_seen(RING, CQE)
