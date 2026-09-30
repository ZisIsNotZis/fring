from liburing import *

CQE = io_uring_cqe()

class Ring(io_uring):
    __slots__ = 'task', 'sqe'
    def __init__(s):
        io_uring_queue_init(256, s)
        s.task = {}
        s.sqe = {}
RING = Ring()

class Future:
    __slots__ = '_'
    def __await__(s):
        yield s
        if isinstance(s._, Exception):
            raise s._
        return s._
DONE = Future()
DONE._ = None

class Task(Future):
    __slots__ = ()
    def __init__(s, _, ring=RING):
        s._ = _
        ring.task[s] = DONE

class Sqe(Future):
    __slots__ = ()
    def __init__(s, f, *_, flag=0, ring=RING):
        sqe = io_uring_get_sqe(ring)
        f(sqe, *_)
        sqe.flags = flag
        sqe.user_data = id(s)
        ring.sqe[id(s)] = s

def run(ring=RING):
    while ring.task:
        if not io_uring_peek_cqe(ring, CQE):
            ring.sqe.pop(CQE.user_data)._ = CQE.res
            io_uring_cqe_seen(ring, CQE)
        elif _ := [i for i, _ in ring.task.items() if hasattr(_, '_')]:
            for _ in _:
                try:
                    ring.task[_] = _._.send(None)
                except StopIteration as e:
                    del ring.task[_]
                    _._ = e.value
        elif io_uring_sq_ready(ring):
            io_uring_submit_and_wait(ring, 1)

def stat(ring=RING):
    return {'sq':io_uring_sq_ready(ring), 'cq':io_uring_cq_ready(ring), 'task':len(ring.task), 'sqe':len(ring.sqe)}