async def filereq(fd):
    buf = bytearray(256)
    await SQE(io_uring_prep_read, fd, buf, len(buf))
    buf = b'HTTP/1.0 200 OK\n\n' + await(await open(buf[5:].partition(b' ')[0])).read(256)
    SQE(io_uring_prep_write, fd, buf, len(buf), 0, flag=IOSQE_IO_LINK)
    SQE(io_uring_prep_close, fd)
async def file():
    while True:
        Task(filereq(await SQE(io_uring_prep_accept, SOCK.fileno())))