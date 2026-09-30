from zring import *

async def stat(_):
    stat = statx()
    await Sqe(io_uring_prep_statx, stat, _)
    return stat

async def open(*_):
    file = File(await Sqe(io_uring_prep_openat, *_))
    file.path = _[0]
    return file

class File(int):
    offset = 0
    async def read(s, _=0):
        if not _:
            _ = (await stat(s.path)).stx_size
        _ = bytearray(_)
        __ = await Sqe(io_uring_prep_read, s, _, len(_), s.offset)
        s.offset += __
        return _[:__]
    async def write(s, _):
        _ = await Sqe(io_uring_prep_writev, s, _, len(_), s.offset)
        s.offset += _
        return _
    def __del__(s):
        Sqe(io_uring_prep_close, s)