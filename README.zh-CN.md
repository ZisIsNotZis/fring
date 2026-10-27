<p align="center">
  <img src="assets/logo.svg" width="112" alt="fring logo">
</p>

<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

<h1 align="center">fring</h1>

<p align="center"><strong>Python 里的 io_uring 事件循环 —— 三个世代，从裸 SQE 到自研协程调度器。</strong></p>

**三套用纯 Python 写成的 io_uring 事件循环 —— 直接分发 CQE、桥接 asyncio、以及从零实现的协程调度器 —— 每一套都配有 HTTP 服务器和压力测试客户端。**

fring 是一组手写实验的归档：通过 `liburing` 的 ctypes 绑定，在 Python 里直接驱动 Linux `io_uring`。三个世代回答的是同一个问题 —— 内核已经替你排队了，Python 这边到底还需要多少事件循环？—— 每一代都配了一对程序：一个 HTTP "Hello" 或文件服务器，外加一个不断打它的客户端。

> **状态：已归档。** 这些是实验脚本，不是库：没有包元数据、没有锁版本、没有测试、没有 CI。保留下来是因为其中的手法在当代内核上仍有阅读价值。仅支持 Linux；multishot accept 和 `send_zc_fixed` 相关路径需要 6.x 内核。

## 快速开始

需要带 `io_uring` 的 Linux、Python 3，以及 `liburing` 的 ctypes 绑定。`a*` 系列还需要 `uvloop`。

```bash
python3 -m pip install liburing uvloop

# 终端 1 —— 自研调度器世代
python3 zhellosvr.py 8123

# 终端 2
python3 zstress.py 8123
```

换一代只需替换脚本，模式不变：

```bash
# 裸环，没有 Python 事件循环
python3 rhellosvr.py 8123
python3 rstress.py 8123

# asyncio 桥（客户端和服务器都写死 8123 端口）
python3 ahellosvr.py
python3 astress.py
```

服务器会一直跑到手动中断。`zfilesvr.py` 在 8122 端口提供文件服务；`rhellosvr2.py` 是 SQPOLL + multishot accept 的变体，监听 8080。

## 现在能做什么

- **直接操作环（`r*`）** —— 用 C 风格的函数准备 SQE，打上 `user_data` 标签，再按标签分发完成事件。没有 future、没有事件循环、每个请求不额外分配对象。
- **`io_uring` → asyncio 桥（`a*`）** —— 把一个 `eventfd` 注册进环，CQE 就变成 `asyncio.Future` 的结果；服务器因此可以写成普通的 `async`/`await`，跑在 `uvloop` 上。
- **取代 asyncio 的调度器（`z*`）** —— 自己实现 future、task，以及一个 `run()` 循环，在收割 CQE、推进任务、提交 SQ 之间轮转；`stat()` 报告环深度和任务数。
- **用到的内核特性** —— `IOSQE_IO_LINK` / `IOSQE_IO_HARDLINK` 链式操作（send → close）、multishot accept、`IORING_SETUP_SQPOLL` 配合 `IORING_ENTER_SQ_WAKEUP`、multishot 超时、环满时的背压、基于 `statx` 的文件大小读取，以及 mmap 响应数据。

## 架构

三代人，三层很薄的封装：

| 世代 | 循环 | 服务器入口 | 客户端 |
| --- | --- | --- | --- |
| `r` | 裸 CQE 循环，靠 `user_data` 标签分发 | `rhellosvr.py`、`rhellosvr2.py` | `rstress.py` |
| `a` | `uvloop` + 注册的 `eventfd` | `ahellosvr.py`、`acat.py` | `astress.py` |
| `z` | `zring.run()` 协程调度器 | `zhellosvr.py`、`zfilesvr.py` | `zstress.py` |

环在 import 时创建一次；区别只在于“完成事件”和“想要结果的那段代码”之间隔了什么。

- **`r*`** —— `accept()`、`send()`、`close()` 这类函数直接调 `io_uring_get_sqe`、设置 `user_data`，主循环再看 `CQE.user_data` 决定下一步做什么。
- **`aring.py`** —— 用 `io_uring_register_eventfd` 把 `eventfd` 注册进环；`uvloop` 监听这个 fd，按 `user_data` 找到对应的 `Future` 并设结果。`SQE()` 返回 future，同时安排一次批量提交。`aring2.py` 增加了环满时的待提交队列，以及提交/收割计数。
- **`zring.py`** —— 整个事件循环就在一个文件里：可 await 的 `Sqe`/`Task`、一张存活任务表，以及 `run()` 循环，在收割 CQE、推进协程、SQ 就绪时提交这三件事之间轮转。`zring2.py` 是额外统计提交/收割速率的变体。

### 仓库导览

| 路径 | 说明 |
| --- | --- |
| `aring.py` | asyncio/uvloop 桥：eventfd、`SQE` → `Future`、批量提交 |
| `aring2.py` | 带环满背压和计数器的桥 |
| `filesvr.py` | 与 `aring2.py` 几乎相同，只是把 `install()` 提到文件开头 |
| `afile.py` | 桥上的文件辅助层：`stat`/`open`/`read`/`write` |
| `afilesvr.py` | 文件服务器片段；假定 `aring` 和 `afile` 的名字已在作用域里 |
| `ahellosvr.py`、`acat.py`、`astress.py` | asyncio 世代的 hello 服务器、mmap 版 hello 服务器、压力客户端 |
| `zring.py`、`zring2.py` | 自研调度器及其统计变体 |
| `zfile.py`、`zfilesvr.py`、`zhellosvr.py`、`zstress.py` | 调度器世代的文件层、文件服务器、hello 服务器、压力客户端 |
| `rhellosvr.py`、`rhellosvr2.py`、`rstress.py` | 裸环 hello 服务器和压力客户端 |
| `hellosvc.gpt.c` | AI 起草的 C 参考片段，示范固定缓冲区 / `send_zc_fixed` / multishot accept，仅供对照 |
| `hello`、`world` | 被 `acat.py` mmap 的响应数据文件 |

## 如何开发

没有构建或安装步骤。改完脚本直接跑；这些文件是各自独立的程序，不是包。

- **停留在脚本层面。** 文件刻意保持扁平，靠 `from aring import *` / `from zring import *` 互相引用。新增实验时沿用这个习惯。
- **用前缀决定位置。** `r*` 是裸环代码，`a*` 基于 asyncio，`z*` 基于自研调度器；辅助文件（`afile.py`、`zfile.py`）跟随各自的世代。
- **在真实内核上验证。** 先起服务器，再跑对应的压力客户端，观察打印出的计数。这里没有测试套件，也没有 CI。
- **端口。** `r*` 和 `z*` 的客户端从 `argv[1]` 取端口；`a*` 脚本和 `zfilesvr.py` 把端口写死在代码里。
- **内核要求。** multishot accept 和固定缓冲区 `send_zc_fixed` 示例需要 6.x 内核；其余部分在任何支持 `io_uring` 的内核上都能跑。

## 如何参与

欢迎提 issue 和 pull request，尤其欢迎新内核上的 bug 报告。改动请保持小而符合归档的气质：纯脚本，不引入打包、CI 或生成代码。新增实验时给它正确的前缀，并在合适的情况下补上配套的服务器/客户端。文档就是两份 README；行为变化时请同步更新两个语言版本。

## 路线图

**已实现**

- 裸 CQE 循环：send → close 链式操作、多路待处理的 accept、SQPOLL 唤醒、multishot accept。
- 基于注册 `eventfd` 的 asyncio 桥：批量提交，以及环满时的背压。
- 从零实现的协程调度器：future、task、单一 run 循环，外加环与任务的统计。
- 三个世代各自的 HTTP hello/文件服务器和压力客户端。
- `statx` 读文件大小、mmap 响应数据、multishot 超时，以及固定缓冲区的 C 参考片段。

**计划中**

- 没有。这个仓库已归档，没有维护中的发布、测试或包。
- 如果重启，第一步应该是写一个并排压测工具，让三代在同一负载下跑同一种工作；只有对比结果值得保留时，才轮到打包和测试。这些都没有开始。

**未来设想。** 这里最有意思的结果并不是“更快的服务器”，而是内核接管队列之后，Python 这一层还能剩下多少东西。如果继续做，应该把这件事直接展示出来：同一份负载分别跑过裸环、asyncio 桥和手写调度器，一层一层剥掉 Python，直到只剩 CQE 和按标签分发的完成事件。

## 许可证

GNU Affero 通用公共许可证 v3.0 —— 见 [`LICENSE`](LICENSE)。

<sub>归档说明：2026-09-30 从私有 `~/my/fring` 集合复制而来，复制时丢弃了凭据和数据集，源目录未改动。最后一次修改是 2026-02。</sub>
