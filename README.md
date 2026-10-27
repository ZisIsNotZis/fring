<p align="center">
  <img src="assets/logo.svg" width="112" alt="fring logo">
</p>

<p align="center">
  English | <a href="README.zh-CN.md">简体中文</a>
</p>

<h1 align="center">fring</h1>

<p align="center"><strong>io_uring event loops in Python — three generations, from raw SQEs to a hand-rolled coroutine scheduler.</strong></p>

**Three complete io_uring event loops in plain Python — raw CQE dispatch, an asyncio bridge, and a from-scratch coroutine scheduler — each paired with an HTTP server and a stress client.**

fring is a small archive of hand-written experiments that drive Linux `io_uring` directly from Python through `liburing`'s ctypes bindings. Every generation answers the same question — how much Python event loop do you need once the kernel already queues your I/O? — with the same pair of programs: an HTTP "Hello" or file server and a client that hammers it.

> **Status: archived.** These are scratch scripts, not a library: no package metadata, no pinned versions, no test suite, no CI. Kept because the techniques are still worth reading on current kernels. Linux only; the multishot-accept and `send_zc_fixed` paths need a 6.x kernel.

## Quick start

Requires Linux with `io_uring`, Python 3, and the `liburing` ctypes bindings. The `a*` series also needs `uvloop`.

```bash
python3 -m pip install liburing uvloop

# terminal 1 — the from-scratch scheduler generation
python3 zhellosvr.py 8123

# terminal 2
python3 zstress.py 8123
```

Swap in the other generations without changing the pattern:

```bash
# raw ring, no Python event loop
python3 rhellosvr.py 8123
python3 rstress.py 8123

# asyncio bridge (client and server both use port 8123, hard-coded)
python3 ahellosvr.py
python3 astress.py
```

Servers run until interrupted. `zfilesvr.py` serves files on port 8122; `rhellosvr2.py` is the SQPOLL/multishot-accept variant on port 8080.

## What it can do now

- **Bare-metal ring loops (`r*`)** — prepare SQEs in C-style functions, tag them with `user_data`, dispatch completions by tag. No futures, no event loop, no allocations per request.
- **`io_uring` → asyncio bridge (`a*`)** — one `eventfd` registered with the ring turns CQEs into `asyncio.Future` results, so servers read like ordinary `async`/`await` code on top of `uvloop`.
- **A scheduler that replaces asyncio (`z*`)** — futures, tasks, and a single `run()` loop that alternates CQE reaping, task stepping, and SQ submission; `stat()` reports ring depth and task counts.
- **Kernel features exercised** — `IOSQE_IO_LINK` / `IOSQE_IO_HARDLINK` chaining (send → close), multishot accept, `IORING_SETUP_SQPOLL` with `IORING_ENTER_SQ_WAKEUP`, multishot timeouts, ring-full backpressure, `statx`-based file sizing, and mmap'd response payloads.

## Architecture

Three thin layers, one per generation:

| Generation | Loop | Server entry | Client |
| --- | --- | --- | --- |
| `r` | Raw CQE loop, `user_data` tags | `rhellosvr.py`, `rhellosvr2.py` | `rstress.py` |
| `a` | `uvloop` + registered `eventfd` | `ahellosvr.py`, `acat.py` | `astress.py` |
| `z` | `zring.run()` coroutine scheduler | `zhellosvr.py`, `zfilesvr.py` | `zstress.py` |

The ring is created once at import time; the difference is only what sits between a completion and the code that wanted it.

- **`r*`** — functions such as `accept()`, `send()`, `close()` call `io_uring_get_sqe`, set `user_data`, and the main loop inspects `CQE.user_data` to decide what to do next.
- **`aring.py`** — registers an `eventfd` with `io_uring_register_eventfd`; `uvloop` watches that fd and resolves a `Future` per `user_data`. `SQE()` returns the future and schedules a batched submit. `aring2.py` adds a pending-SQE queue when the ring is full, plus submit/reap counters.
- **`zring.py`** — the whole event loop in one file: awaitable `Sqe`/`Task` objects, a dictionary of live tasks, and a `run()` loop that reaps CQEs, steps coroutines, and submits when the SQ is ready. `zring2.py` is a variant that also reports submit/reap rates.

### Repository map

| Path | What it is |
| --- | --- |
| `aring.py` | asyncio/uvloop bridge: eventfd, `SQE` → `Future`, batched submit |
| `aring2.py` | Bridge with ring-full backpressure and counters |
| `filesvr.py` | Near-duplicate of `aring2.py` with `install()` moved to the top |
| `afile.py` | File helper on the bridge: `stat`/`open`/`read`/`write` |
| `afilesvr.py` | File-server fragment; expects `aring` and `afile` names in scope |
| `ahellosvr.py`, `acat.py`, `astress.py` | asyncio-generation hello server, mmap'd hello server, stress client |
| `zring.py`, `zring2.py` | From-scratch scheduler and its stats variant |
| `zfile.py`, `zfilesvr.py`, `zhellosvr.py`, `zstress.py` | Scheduler-generation file layer, file server, hello server, stress client |
| `rhellosvr.py`, `rhellosvr2.py`, `rstress.py` | Raw ring hello servers and stress client |
| `hellosvc.gpt.c` | AI-drafted C reference sketch for fixed buffers / `send_zc_fixed` / multishot accept; kept for comparison |
| `hello`, `world` | Payload files mmap'd by `acat.py` |

## How to develop

There is nothing to build or install. Edit a script and run it; the files are independent programs, not a package.

- **Stay on the script level.** These files are intentionally flat and import each other with `from aring import *` / `from zring import *`. Keep that convention when adding an experiment.
- **Use the prefix to place a file.** `r*` is raw ring code, `a*` is asyncio-based, `z*` is scheduler-based; helpers (`afile.py`, `zfile.py`) follow their generation.
- **Test against a real kernel.** Start a server, run the matching stress client, and watch the printed counters. There is no test suite and no CI.
- **Ports.** `r*` and `z*` clients take the port as `argv[1]`; `a*` scripts and `zfilesvr.py` hard-code theirs.
- **Kernel requirements.** Multishot accept and the fixed-buffer `send_zc_fixed` sketch need a 6.x kernel; the rest works on any kernel with `io_uring`.

## How to contribute

Issues and pull requests are welcome, especially bug reports from newer kernels. Keep changes small and in the spirit of the archive: plain scripts, no packaging, no CI, no generated code. If you add an experiment, give it the right generation prefix and a matching server/client pair where it makes sense. Documentation lives in the READMEs; update both language versions when behavior changes.

## Roadmap

**Implemented**

- Raw CQE loops with linked send → close, outstanding accepts, SQPOLL wakeups, and multishot accept.
- asyncio bridge over a registered `eventfd`, with batched submission and ring-full backpressure.
- From-scratch coroutine scheduler with futures, tasks, a single run loop, and ring/task statistics.
- HTTP hello and file servers plus stress clients for all three generations.
- `statx` file sizing, mmap'd payloads, multishot timeouts, and a C reference sketch for fixed buffers.

**Planned**

- Nothing. This repository is archived and has no maintained release, test suite, or package.
- If revived, the first useful step would be one side-by-side benchmark harness that runs all three generations under identical load; packaging and tests would follow only if the comparison proved worth keeping. None of that is started.

**Future vision.** The interesting result here is not a faster server — it is how little machinery survives once the kernel owns the queue. A future version would make that visible: the same workload run through the raw ring, the asyncio bridge, and the hand-rolled scheduler, with the Python layers stripped away one at a time until only CQEs and tagged completions remain.

## License

GNU Affero General Public License v3.0 — see [`LICENSE`](LICENSE).

<sub>Archive note: copied from the private `~/my/fring` collection on 2026-09-30; credentials and datasets were dropped during the copy, and the source was not modified. Last touched 2026-02.</sub>
