# Spire2Lab 项目转接文档

更新时间：2026-10-22

项目地址：<https://github.com/Lidz-abel/Spire2Lab>

本地目录：`/user/chenzk/sts2-lab`

当前 Git 检查点：本地 `main` 已包含 README、转接文档和远程 LICENSE 的合并提交。

上次已确认推送检查点：`0a5c869`（包含平台代码、README、转接文档和来源说明）。历史 TLS 故障之后已成功推送；每次接手仍须核对远程实际状态。
项目目标：**完成第一阶段**

## 新会话启动指令

把下面这段连同本文件一起交给新的会话：

> 你正在继续开发 Spire2Lab。先阅读仓库根目录的 `AGENTS.md`、`PROJECT-HANDOFF.md`、`CODE-PROVENANCE.md`、`PHASE1-STATUS.json`、`ARCHITECTURE-PLAN.txt` 和 `README.md`，再检查当前 `git status`、测试结果和 `artifacts`。用户要求平台尽可能原创、允许参考开源实现：优先自行实现平台与研究核心，按来源文档逐步替换绑定、Mod 和有限战斗引擎；当前运行路径仍有上游依赖。保留第一阶段的完整目标：建立可实时观察、可复现、可训练、能与 Windows Steam 原版逐步对照的强化学习环境。不要把模拟器测试或合成 HTTP 测试当作原版一致性证据。每次新增要求或实质进展都更新本文件，按需同步状态、来源和 README，并创建一个说明清楚的 commit。

## 项目定位

Spire2Lab 面向《杀戮尖塔 2》的自主强化学习研究，目标是支持：

1. 受玩家可见信息约束的策略；
2. 隐藏状态一致的搜索分支；
3. 分层决策，从整局目标连接到战斗原子动作；
4. Linux 服务器上的高效并行采样和训练；
5. Windows Steam 原版执行、实时决策可视化和逐步一致性验证。

当前架构是 Linux 计算服务器 + 低配置 Windows Steam PC。Linux 运行模拟器、策略、搜索、训练、日志和面板；Windows 运行游戏及轻量 Mod。两个后端共享语义观测/动作协议。

## 已确认的不可变要求

- 原创优先：平台尽可能自行设计和实现，开源项目可以参考。具体来源与迁移顺序见 `CODE-PROVENANCE.md` 的 O-01 至 O-05；当前依赖仍是上游实现，不追溯改称原创。
- 第一阶段必须包含真实原版游戏接入，不得用模拟器自测替代。
- 面板要能实时显示智能体看到的状态、候选动作、选中动作和执行结果。
- 后续加入原版画面时，画面必须能通过 `run_id`、`decision_id` 和帧信息与决策记录对应。
- 策略不能读取隐藏抽牌顺序、内部 RNG 或其他玩家无法获得的信息。
- 动作执行要区分建议、提交、确认和结果未知；网络响应丢失时禁止盲重发。
- 原版版本、Mod、模拟器和协议发生变化后，相关结论必须重新验证。
- “通过”只适用于明确声明的有限场景和字段，不扩张为全游戏完全一致。

## 第一阶段固定范围

配置文件：`config/phase1.json`

- 铁甲战士，A0；
- `Strike ×5`、`Defend ×4`、`Bash ×1`；
- `Burning Blood`，无药水；
- 80/80 HP、99 金币、第 2 层；
- `nibbits-weak`、`slimes-weak`、`sludge-spinner`；
- 开发种子 1–10，保留评测种子 1001–1010；
- 基线策略：`random`、`heuristic`；
- 不在第一阶段训练 RL 模型。

原版参考验收配置：`config/acceptance.json`

- 3 个遭遇 × 10 个开发种子 × 2 个策略 = 60 条独立参考战斗；
- 额外边界探针覆盖失败等基线策略未覆盖的情况；
- 必须覆盖：出牌、结束回合、回合推进、状态牌意图、状态牌入场、能力效果、敌人移除、胜利、失败；
- 一个原始捕获不能重复计数为多个 case；
- 合成传输、手工伪造轨迹、未决动作都不能通过验收。

## 当前实现

### 已经存在

- 协议 `0.2.0`：`sts2lab/contracts.py`
- C# NativeAOT 模拟器和只读观测导出：`native/`
- Linux 模拟器、snapshot/restore、`sample_world`：`sts2lab/simulator.py`
- Gymnasium `combat-entities-v2`：`sts2lab/gym_env.py`
- 随机和可解释启发式策略：`sts2lab/policies.py`
- FastAPI + 无构建步骤浏览器面板：`sts2lab/server.py`、`web/`
- Windows 原版异步适配器与桥接：`sts2lab/original.py`、`sts2lab/bridge.py`
- 轨迹哈希链、语义重执行和比较器：`sts2lab/traces.py`、`sts2lab/parity.py`
- 参考重放与验收矩阵：`sts2lab/reference_replay.py`、`sts2lab/acceptance.py`
- Windows 接入和安装脚本：`scripts/Connect-Windows.ps1`、`scripts/Install-Windows-Mod.ps1`
- 原版异常动作归档、断线确认、暂停和回放
- `ARCHITECTURE-PLAN.txt`：完整架构、路线和阶段边界

### 当前可核查证据

最近一次本地检查：

| 证据 | 结果 | 说明 |
| --- | --- | --- |
| Python 测试 | 43 passed | `artifacts/lab-tests.xml` |
| 模拟器面板浏览器检查 | 6 passed | `artifacts/browser-checks.json` |
| 合成原版接口面板检查 | 5 passed | `artifacts/original-dashboard-synthetic/report.json` |
| 开发集模拟器基准 | 60 episodes / 980 decisions | `artifacts/benchmark-development.json` |
| 验收矩阵 | incomplete | Windows report 缺失，60 条原版 case 全部缺失 |
| 原版实机 | 未验证 | 尚无 Windows DLL、Mod 编译运行和真实捕获 |

运行验收状态：

```bash
cd /user/chenzk/sts2-lab
.venv/bin/python scripts/audit_acceptance.py
```

目前预期返回非零，因为 `artifacts/windows/report.json` 尚未存在。这是正确的安全状态。

## 当前阻塞与下一项动作

真正的关键路径是 Windows 实机接入。需要用户在安装 Steam 游戏的 Windows PC 上执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Connect-Windows.ps1 `
  -Server 用户@服务器 -SshPort 22
```

脚本会：

1. 找到 Steam 的《杀戮尖塔 2》安装目录；
2. 记录 Steam Build ID 和 `sts2.dll`、`GodotSharp.dll`、`0Harmony.dll` 的版本/哈希；
3. 把报告和编译引用上传到 Linux 的 `artifacts/windows/`；
4. 建立 Windows → Linux 面板转发和 Linux → Windows 游戏 Mod 的反向隧道。

收到 Windows 文件后，在 Linux 执行：

```bash
cd /user/chenzk/sts2-lab
.venv/bin/python scripts/build_bridge.py
```

构建成功后，在 Windows 关闭游戏并执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Windows-Mod.ps1 `
  -Server 用户@服务器 -SshPort 22
```

然后启动 Steam 游戏、启用 Mod、保持连接窗口运行，打开 `http://127.0.0.1:8765`，先完成一次稳定战斗状态读取和单步动作。之后再处理原版场景初始化、随机对齐和 60 条参考集。

## Git 提交规则

远程仓库：`https://github.com/Lidz-abel/Spire2Lab.git`

历史推送曾遇到 TLS 错误，后来已成功推送至 `0a5c869`。下一次提交前读取当前远程状态；推送结果需要核实，不根据缓存或旧日志推断成功。

每个 commit 只表达一个可核查进度，推荐顺序：

1. `docs: add Spire2Lab README and project handoff`
2. `chore: record Windows game fingerprint`
3. `feat: compile bridge for verified game build`
4. `feat: verify original-game one-step control`
5. `test: add finite original reference cases`
6. `feat: complete phase-one acceptance gate`

每个提交前检查格式与工作区：

```bash
git diff --check
git status --short
```

文档变更检查链接和 JSON 等结构化文件；代码变更运行相关测试，涉及跨模块行为时执行 `.venv/bin/python -m pytest -q`。

提交正文要说明：改动、验证命令、证据路径、仍然缺少的证据。不要把 `artifacts/windows/assemblies`、游戏 DLL、存档或原版原始捕获放进 Git。

## 文件导航

- [`README.md`](README.md)：GitHub 首页，面向研究者和开发者；
- [`CODE-PROVENANCE.md`](CODE-PROVENANCE.md)：本项目代码、上游代码和许可证边界；
- [`AGENTS.md`](AGENTS.md)：原创优先与持续记录的执行约定；
- [`README.txt`](README.txt)：详细 Linux/Windows 运维步骤；
- [`ARCHITECTURE-PLAN.txt`](ARCHITECTURE-PLAN.txt)：总体架构和后续路线；
- [`PHASE1-STATUS.json`](PHASE1-STATUS.json)：机器可读的状态与证据；
- [`config/phase1.json`](config/phase1.json)：第一阶段环境范围；
- [`config/acceptance.json`](config/acceptance.json)：原版参考集验收规则；
- `artifacts/`：本地证据目录，默认被 Git 忽略；
- `vendor/*.json`：固定上游提交和归档校验值。

## 更新本转接文档的方法

每次实质进展后更新四处：

1. 本文件的“当前实现”“当前可核查证据”“当前阻塞与下一项动作”；
2. `PHASE1-STATUS.json` 的状态、requirements、evidence；
3. `README.md` 中面向外部读者的状态描述；
4. commit message 和测试/证据路径。

不要删除失败记录。失败的编译、首个差异、未决动作和版本变化都是复现所需的信息。

## 决策与进度记录

| 日期 | 来源 | 要求或变化 | 当前落实情况 |
| --- | --- | --- | --- |
| 2026-10-20 | 用户 | 新仓库 `Lidz-abel/Spire2Lab`，科研风格 README，按进度 commit | README、转接文档和许可证已提交，见历史 |
| 2026-10-21 | 用户询问与来源检查 | 明确新增代码和上游模拟器/Mod 的边界 | `CODE-PROVENANCE.md`；已推送 `0a5c869` |
| 2026-10-22 | 用户明确要求 | 平台尽可能原创，允许参考开源实现 | 本轮记录原创原则、O-01 至 O-05 迁移计划及 `AGENTS.md`；独立引擎/Mod 尚未实现；第一阶段仍待 Windows 实机输入 |
