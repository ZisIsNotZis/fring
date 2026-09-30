from liburing import *
from uvloop import install
install()
from ctypes import CDLL
from asyncio import get_event_loop, Future, Task
from socket import socket


CDLL = CDLL(None)
RING = io_uring()
io_uring_queue_init(8192, RING)
FD = CDLL.eventfd(0, O_NONBLOCK|O_CLOEXEC)
io_uring_register_eventfd(RING, FD)
LOOP = get_event_loop()
SQN = 0
SQL = []
CQE = io_uring_cqe()
CQL = {}

@lambda _:LOOP.add_reader(FD,_)
def _():
    CDLL.eventfd_read(FD, O_NONBLOCK|O_CLOEXEC)
    _ = 0
    while not io_uring_peek_cqe(RING, CQE):
        if CQE.res >= 0:
            CQL.pop(CQE.user_data).set_result(CQE.res)
        else:
            CQL.pop(CQE.user_data).set_exception(OSError(CQE.res))
        io_uring_cqe_seen(RING, CQE)
        _ += 1
    print('complete', _, 'pend', len(CQL))
    while SQL and io_uring_sq_space_left(RING):
        SQE_(*SQL.pop())

def SQE_(f, _, flag, future):
    global SQN
    sqe = io_uring_get_sqe(RING)
    f(sqe, *_)
    sqe.flags = flag
    sqe.user_data = id(future)
    CQL[id(future)] = future
    if not SQN:
        LOOP.call_soon(SUBMIT)
    SQN += 1

def SQE(f, *_, flag=0):
    future = Future()
    if io_uring_sq_space_left(RING):
        SQE_(f, _, flag, future)
    else:
        SQL.append((f, _, flag, future))
    return future

def SUBMIT():
    global SQN
    io_uring_submit(RING)
    print('submit', SQN, 'pend', len(SQL))
    SQN = 0