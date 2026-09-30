from liburing import *
from uvloop import install
from ctypes import CDLL
from asyncio import get_event_loop, Future, Task
from os import strerror

install()
CDLL = CDLL(None)
RING = io_uring()
io_uring_queue_init(8192, RING)
FD = CDLL.eventfd(0, O_NONBLOCK|O_CLOEXEC)
io_uring_register_eventfd(RING, FD)
LOOP = get_event_loop()
SUB = True
CQE = io_uring_cqe()
CB = {}

@lambda _:LOOP.add_reader(FD,_)
def _():
    CDLL.eventfd_read(FD, O_NONBLOCK|O_CLOEXEC)
    while not io_uring_peek_cqe(RING, CQE):
        if CQE.res >= 0:
            CB.pop(CQE.user_data).set_result(CQE.res)
        else:
            CB.pop(CQE.user_data).set_exception(OSError(strerror(-CQE.res)))
        io_uring_cqe_seen(RING, CQE)

def SQE(f, *_, flag=0):
    global SUB
    sqe = io_uring_get_sqe(RING)
    f(sqe, *_)
    sqe.flags = flag
    future = Future()
    sqe.user_data = id(future)
    CB[id(future)] = future
    if SUB:
        LOOP.call_soon(SUBMIT)
        SUB = None
    return future

def SUBMIT():
    global SUB
    io_uring_submit(RING)
    SUB = True