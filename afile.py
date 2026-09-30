from aring import *

async def stat(_):
    stat = statx()
    await SQE(io_uring_prep_statx, stat, _)
    return stat

async def open(*_):
    file = File(await SQE(io_uring_prep_openat, *_))
    file.path = _[0]
    return file

class File(int):    
    offset = 0
    async def read(s, _=0):
        if not _:
            _ = (await stat(s.path)).stx_size
        dat = bytearray(_)
        _ = iovec(dat)
        _ = await SQE(io_uring_prep_readv, s, _, s.offset)
        s.offset += _
        return dat[:_]
    async def write(s, _):
        _ = iovec(_)
        await SQE(io_uring_prep_writev, s, _, len(_), s.offset)
        s.offset += _
        return _
    def __del__(s):
        SQE(io_uring_prep_close, s)