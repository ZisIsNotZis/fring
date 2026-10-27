# Contributing to fring

fring is an archive of hand-written Linux `io_uring` experiments in Python, not a
library. Contributions are welcome as long as they keep it that way.

## Scope

**In scope**

- Bug reports, especially ones from kernels newer than the scripts.
- New experiment scripts that follow the existing generation prefixes: `r*` for
  raw ring code, `a*` for the asyncio bridge, `z*` for the hand-rolled
  scheduler. Give an experiment a matching server/client pair where it makes
  sense.
- Corrections to the READMEs, including kernel-version and port details.

**Out of scope**

- Packaging (`pyproject.toml`, wheels, a published `fring` package), pinned
  dependencies, CI, and generated code. The archive is deliberately flat.
- Refactors that touch every generation at once. Each file is a snapshot of an
  idea; leave the old ones as they are.

## How to check a change

There is no test suite and no CI. The check is the one the project has always
used: start the server, run the matching stress client, watch the counters.

```bash
# generation you touched, e.g. the scheduler
python3 zhellosvr.py 8123   # terminal 1
python3 zstress.py 8123     # terminal 2 — prints completions once per interval

# the other generations, for comparison
python3 rhellosvr.py 8123 & python3 rstress.py 8123
python3 ahellosvr.py & python3 astress.py
```

Exit criteria: the server survives the run, the client keeps printing a
non-zero count, and no traceback appears in either terminal. Say in your pull
request which generation you ran and on which kernel (`uname -r`).

## Pull requests

- One experiment or one fix per pull request; small diffs review quickly.
- Do not reformat files you did not otherwise change.
- If behavior changes, update `README.md` and `README.zh-CN.md` in the same
  pull request — both language versions describe the same tree.

## Issues

Include the kernel version (`uname -r`), distro, Python version, the exact
command you ran, and the full traceback. `io_uring` behavior changes between
kernel releases, so the version is the single most useful line in a report.
