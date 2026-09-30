from liburing import *
from types import CoroutineType
from time import time
RING = io_uring()
io_uring_queue_init(256, RING)
CQE = io_uring_cqe()
SUB = RCV = 0
T = time()
class Future:
    __slots__ = '_'
    def __await__(s):
        if not hasattr(s, '_'):
            yield s
        if isinstance(s._, Exception):
            raise s._
        return s._
TASK = {}
class Task(Future):
    __slots__ = ()
    def __init__(s, _):
        s._ = _ if hasattr(_, '__await__') else _()
        TASK[s] = None
    def __await__(s):
        if isinstance(s._, CoroutineType):
            yield s
        if isinstance(s._, Exception):
            raise s._
        return s._
SQE = {}
class Sqe(Future):
    __slots__ = ()
    def __init__(s, f, *_, flag=0):
        sqe = io_uring_get_sqe(RING)
        f(sqe, *_)
        sqe.flags = flag
        sqe.user_data = id(s)
        SQE[id(s)] = s
def main():
    global SUB, RCV
    while TASK:
        if io_uring_peek_cqe(RING, CQE) == 0:
            if _ := SQE.pop(CQE.user_data, None):
                _._ = CQE.res
            io_uring_cqe_seen(RING, CQE)
            RCV += 1
        elif _ := next((i for i, _ in TASK.items() if not _ or hasattr(_, '_')), None):
            try:
                TASK[_] = _._.send(None)
            except StopIteration as e:
                del TASK[_]
                _._ = e.value
        elif io_uring_sq_space_left(RING) < 256:
            io_uring_submit_and_wait(RING, 1)
            SUB += 1
def stat():
    global SUB, RCV, T
    _ = {'sq':io_uring_sq_ready(RING), 'cq':io_uring_cq_ready(RING), 'task':len(TASK), 'sqe':len(SQE), 'sub':SUB/(time()-T), 'rcv':RCV/(time()-T)}
    SUB = RCV = 0
    T = time()
    return _