# fring — io_uring event loops in Python, three generations

**What:** A small set of hand-written Python experiments that drive Linux
`io_uring` directly from Python via the `liburing` ctypes bindings, at three
levels of abstraction: raw ring loops (`r*`), an `asyncio`/`uvloop` integration
(`a*`), and a from-scratch coroutine scheduler that replaces `asyncio` entirely
(`zring.py`, `z*`).

**Why it exists:** To find out how much of an event loop you actually need when
the kernel already queues your I/O. Each generation answers the same question —
an HTTP "Hello" / file server plus a client stress harness — with a different
amount of Python machinery between the request and the SQE.

- `r*` — no Python event loop at all; SQEs are prepared in C-style loops and
  results dispatched off `user_data` tags. Smallest and fastest to reason about.
- `aring.py` — bridges the ring to `uvloop` through an `eventfd` registered with
  `io_uring_register_eventfd`; CQEs become `asyncio.Future`s, so servers are
  written with plain `async`/`await`.
- `zring.py` / `zring2.py` — drops `asyncio` and hand-rolls a coroutine
  scheduler: futures, tasks, a `run()` loop that alternates CQE reaping,
  task stepping and SQ submission, plus a `stat()` that reports SQ/CQ depth and
  submit/reap rates. `z*` servers and stress clients are built on it.

Notable techniques exercised across the set: `IOSQE_IO_LINK` /
`IOSQE_IO_HARDLINK` chaining (send→close), multishot accept, `IORING_SETUP_SQPOLL`
with `IORING_ENTER_SQ_WAKEUP`, multishot timeouts, ring-size backpressure with a
pending-SQE queue, mmap'd response payloads, and `statx`-based file sizing.

**How to run:** Linux only (the `io_uring` syscalls must exist; the multishot
accept / `send_zc_fixed` paths need a 6.x kernel). Requires `python-liburing`
(the `liburing` module used by every file) and, for the `a*` series, `uvloop`.
There is no packaging, no pinning and no test suite — these are scratch scripts;
run a server in one terminal and the matching stress client in another, e.g.:

```bash
# terminal 1
python3 -m pip install liburing uvloop
python3 zhellosvr.py 8123
# terminal 2
python3 zstress.py 8123
```

**Status:** Prototype / personal experiments, written Dec 2024 – Feb 2026 and
last touched 2026-02. Kept as an archive of the io_uring investigations rather
than as a usable library: no package metadata, no versions pinned, no docs, and
`filesvr.py` is a near-duplicate of `aring2.py` (only the position of the
`install()` call differs). `hellosvc.gpt.c` is an AI-drafted C reference
snippet, not working local code — it is a sketch of the
fixed-buffer/`send_zc_fixed`/multishot-accept approach, and is kept for
comparison only. The `io_uring` API surface used here is still current on 2026
kernels (not a TensorFlow-1-style dead end), but nothing here is maintained.

**License:** No LICENSE file, no README, no copyright headers anywhere in the
directory. Treat as the author's own unpublished experiments (all rights
reserved by default); a license must be chosen explicitly before this is
published as a repo.
