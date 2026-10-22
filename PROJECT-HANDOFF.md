# Spire2Lab 项目转接文档

更新时间：2026-10-22

项目地址：<https://github.com/Lidz-abel/Spire2Lab>

本地目录：`/user/chenzk/sts2-lab`

当前 Git 检查点：本地 `main` 已包含 README、转接文档和远程 LICENSE 的合并提交。

上次已确认推送检查点：`0a5c869`（包含平台代码、README、转接文档和来源说明）。历史 TLS 故障之后已成功推送；每次接手仍须核对远程实际状态。

2026-10-22 原创优先进度提交：`6629068`（原创优先原则与依赖迁移规划）。该次推送失败：
VS Code Git 凭据服务连接被拒绝，GitHub 返回 `No anonymous write access` / `Authentication failed`。
文件与提交均在本地保留；三阶段规划时只读远程核对仍为 `0a5c869`。恢复本机 GitHub 认证后再推送，
不在聊天或仓库中保存令牌。此项阻塞远程同步，独立于 Windows 实机接入阻塞。
三阶段规划已提交为 `5e7f24b`；提交后重试 `git push origin main`，仍因同一凭据服务
故障及 GitHub 认证失败退出（128）。格式、JSON、三个阶段/八个任务及 14 个本地链接
检查通过。远程尚未收到本次规划，后续认证恢复后应推送并核对远程 HEAD。
最新品牌与 README 提交：`9cc73a7`。提交后执行 `git push origin main` 仍退出 128：
VS Code Git 凭据服务连接被拒绝，GitHub 拒绝匿名写入。远程核对仍为 `0a5c869`；
本次 Logo 和 README 尚未上传。已请用户在本机 Git 客户端恢复登录，未索取令牌。
项目目标：**完成第一阶段**

2026-10-22 Windows 安装与首次启用：用户回传四个文件下载完成及安装成功输出，
备份目录已创建；首次 SSH 密码失败后重试成功，未阻止安装。随后用户说明游戏在
点击“加载模块”后退出，目前未运行。只读检查收到的 `sts2.dll` 方法调用元数据：
`NConfirmModLoadingPopup.OnYesButtonPressed` 调用同意标记设置、`SaveSettings`，
随后调用 `NGame.Quit`。因此这次现象符合首次启用后主动退出流程，不能据此报崩溃；
更不能据此确认 Mod 已成功加载。证据：`artifacts/windows/mod-startup-calls.json`；
检查工具在同目录 `mod-startup-check/`，只读 IL 调用目标，未加载或执行游戏代码，
游戏 DLL 与元数据检查产物均不进入 Git。
安装后的根路径及状态 GET 探测均超时，记录于 `post-install-greeting-probe.json`
与 `post-install-probe.json`；当时游戏未运行，不据此判断 Mod 或 SSH 转发故障。
已请用户保留隧道、从 Steam 再启动游戏并停留主菜单，提供显示版本号；游戏启动后
再读 Windows 本机 15526 与 Linux 反向 18526。未发送任何游戏动作，原版仍为 0/60。
当前状态：安装成功来自用户终端证据，Mod 加载、语义版本及状态读取仍待实测。

2026-10-22 安装命令反馈：用户已在 Windows PowerShell 中，但调用 `powershell`
启动命令时得到 CommandNotFoundException，安装脚本尚未执行。操作说明已改成在
当前会话执行 `Set-ExecutionPolicy -Scope Process Bypass -Force` 后直接调用
`.\Install-Windows-Mod.ps1`，另一个接入窗口保持打开。无需修改 PATH 或重装 shell。
同步修改接入包说明及运维命令；服务器 Mod 产物不变，Windows 安装仍待用户执行。

2026-10-22 最新实机接入进展：已实际收到 Windows `report.json` 和三份 DLL，
Steam build `23811903`、分支 `public`；所有文件大小与 SHA-256 匹配报告。
`sts2.dll` SHA-256 为 `a1f9e653f1e28e4076558fee1e60d218619cb7e057b887c6417f62c62c6d7a52`。
文件/程序集版本为 `0.1.0.0`，产品版本为 `0.1.0+59260271157f76a2896f0eab5bc6ea1245d8b314`，
不能据此确认游戏语义版本 v0.107.1；原版验收门已准确拒绝这个尚未核对的版本。
SDK 9.0.319 使用收到的引用编译桥接成功，0 错误、1 项上游 CS8602 警告。
产物位于 `artifacts/windows/mod`；DLL/manifest 指纹、许可证与构建来源已核对，
产物目录不包含三份游戏引用 DLL。`build.json` 记录实际 Steam build、分支、配置目标
及 `semantic_game_version_verified: false`，不把编译成功改称原版运行通过。
只读 PE 元数据确认 `CardModel.Enchantment` 存在公开实例 getter，未执行游戏代码；
实际读值仍待运行。证据：`reference-verification.json`、`assembly-metadata-check.json`、
`bridge-build-first.log`、`bridge-build.log`，均位于被忽略的 `artifacts/windows/`。
服务器 18526 反向监听已出现，但只读桥接 HTTP 请求超时，尚未取得原版状态。
下一项用户操作：保留接入窗口，关闭游戏，在另一窗口运行安装脚本，然后启用 Mod，
停留主菜单并提供游戏显示的版本号；我们先读状态，再进入受控实验。原版仍为 0/60。
本轮针对传输、原版适配和安装脚本的 16 项测试通过（1 项现有依赖弃用警告）；证据为
`artifacts/windows/bridge-integration-tests.xml`，其合成/上游素材不计实机证据。
GitHub 认证阻塞未收到恢复确认，本轮提交保留在本地，不重复触发失败的凭据服务。

2026-10-22 SSH 诊断后续：用户从 Windows 执行简单远程命令，得到
`SPIRE2LAB_SSH_OK`；客户端日志显示 `exec request accepted` 和 `Exit status 0`。
这是用户提供的实际客户端记录，确认该次登录与远程命令成功；此前连接关闭的根因
仍未确定，不把一次成功推广为文件传输、端口转发或原版桥接已通过。
服务器复查：22 和 8765 监听，面板 `/api/health` 正常、原版未验证；18526 尚无
监听，Windows 报告和引用 DLL 仍不存在，项目预检查文件存在且 artifacts 可写。
下一步让用户重跑原接入命令，逐项观察报告/DLL 上传与双向隧道；成功后保持窗口
打开，从 Windows 查看面板，再核对版本和编译 Mod。没有修改系统 SSH 配置。
脚本诊断改进已在本地提交 `779075c`，GitHub 认证阻塞尚无恢复确认。

2026-10-22 Windows 首次接入反馈：用户在 Windows 实际运行接入脚本，游戏发现成功，
输出 Steam Build ID `23811903`；密码提示后 SSH 连接关闭，远程预检查失败。
这是用户提供的终端记录，尚未收到 `report.json` 和三个引用 DLL，不能据此确认
游戏语义版本、DLL 指纹或与 v0.107.1 的兼容性；原版验收仍为 0/60。
服务器只读检查确认：目标地址属于本机，22 端口监听，两个项目预检查文件存在，
账号和密码未过期，8765 面板 `/api/health` 正常，18526 无监听。当前账号不能读取
系统 SSH 日志，`sudo -n` 要求密码；未修改 SSH/PAM/防火墙配置或读取凭据。
已请用户在 Windows 用 `ssh -vvv -E ... -T ... "echo SPIRE2LAB_SSH_OK"` 收集末尾
70 行诊断，区分认证和会话失败。根因仍未确认，不推断为密码错误或路径错误。
接入脚本现区分 SSH exit 255、项目缺失 exit 20、目录创建失败 exit 21 和其他失败，
在检查成功后才提示上传，并显示失败时保留的本地版本报告路径。
验证：`tests/test_windows_scripts.py` 通过，模拟 SSH 失败不触发上传/隧道；实际本机
POSIX shell 执行脚本生成的预检查命令，验证缺文件、目录创建失败、成功三条路径。
测试仍不是 Windows 到 Linux 的认证验证。更新包见 `artifacts/installers/`。
既有 GitHub 认证阻塞未收到恢复确认；本轮不反复调用已失败的凭据服务。

进程采样与接入工具检查点：`a2c29eb`（进程采样测量与 Windows 接入改进）。推送仍因
GitHub 凭据服务连接失败退出 128，尚未上传；不能把本地检出验证当作远程已更新。

此前实施检查点（2026-10-22，用户要求继续第一阶段，当时 Windows 文件尚未接入）：
原版验收仍为 0/60。已完成可独立推进的进程采样测量和 Windows 接入脚本改进：

- `benchmark_sampling.py`：1/2/4 个 spawn 进程，各 3 轮，每轮 300 场，合计 2,700 场、
  44,100 次决策；所有对应公开轨迹指纹一致，超时和异常退出后的进程清理测试通过。
  本机 AMD EPYC 7T83、Python 3.12.3，平均约 951/1,616/3,025 决策/秒；包括初态准备、
  策略、模拟、公开轨迹哈希和 IPC，排除启动/预热/退出，另报端到端口径。
  RSS 为各进程生命周期峰值，峰值之和不是同时物理内存。证据：
  `artifacts/sampling-development.json`，不得当作 RL 收益或原版性能。
- Windows 两个脚本新增必填 `-RemoteRoot`，支持更换服务器项目路径；上传前检查远程
  项目文件。安装时保留 LICENSE.txt 和 build.json；失败恢复已管理文件。
  PowerShell 7.6.6 在 Linux 上以合成文件、模拟 SSH/SCP/Steam 测试路径、连接失败、
  非法路径、指纹拒绝、成功安装和回滚。Windows 实机执行仍待确认。
- 接入 ZIP 已重新生成；必须使用本轮版本并给两个脚本传相同服务器、项目路径和端口。
- 完整项目测试：47 passed（1 项现有依赖弃用警告）。
- 新目录复现已通过：本机另行检出 `a2c29eb`，新建 venv、下载依赖和源码、隔离
  Python/NuGet/SDK 缓存、重新编译 NativeAOT，bootstrap 得到 46 passed / 1 skipped。
  跳过项为新目录没有安装可选 PowerShell 的模拟脚本测试；原工作区该测试已通过。
  新旧二进制哈希不同，但 60 个固定用例的公开逐步轨迹一致，测量源码哈希相同。
  证据：`artifacts/repro-check.json` 与 `artifacts/repro-bootstrap.log`。这是同一机器
  的全新检出验证，未证明另一台机器/系统兼容性；保留上游编译警告与依赖弃用警告。
- 主工作区面板已启动，当前 PID 4055089、监听 127.0.0.1:8765；健康检查
  `artifacts/dashboard-health.json` 显示原版未验证。接手时重新检查进程，不依赖旧 PID。

为本轮增加的 `sampling.py` 先定义了固定工作量、信息边界、测量口径和进程退出用例，
再使用 Python 标准库实现；规则仍经原有适配器执行，未替换上游引擎或 Mod。

当前路线：`three-stage-v1`。三个阶段依次为可信实验平台、搜索与分层决策、
高效训练与原版评测；详细任务 P1-01 至 P1-08 见 `ARCHITECTURE-PLAN.txt`。
此前五阶段划分已被这份路线替代，原版画面要求合并到阶段 2/3，原创优先继续执行。
三阶段规划变更只涉及文档和机器可读状态；未新增功能或原版证据，未重新运行历史测试。

当前文档工作：用户要求专业英文科研 README，先制作有《杀戮尖塔》辨识度的原创
SVG Logo 并更新上传首页。完整要求已记录于 `PROJECT-IDENTITY.md`，后续会话继续遵守。
本轮新增浅/深 Logo 与独立图标，重写 README 的首屏、结构、最小示例、来源及验证边界；
不涉及核心行为变更。验证和 Git 同步结果在本文件持续记录。

2026-10-22 品牌与 README 验证：三份 SVG 的 XML、内部引用、无外部资源和浅/深几何
一致性通过；README 的 30 个内部链接/锚点通过。使用本地 CommonMark + HTML/table
预览及 Mermaid 11.4.1，在 1280/390 宽度、浅/深主题下验证图片、主题选择、架构图
及无页面溢出；这是本地兼容预览，不是 GitHub 线上渲染截图。
README 的 Python 单步示例已执行；`bash scripts/start.sh` 启动检查和面板 6 项交互
检查通过，无 JavaScript 错误，临时服务已关闭。记录见 `artifacts/branding/`。
未重新运行完整 pytest 或新机器 bootstrap；此前 43 项测试报告仍属历史证据。
本轮一次文档写入因 heredoc 分隔符冲突失败，意外重跑了开发集基准（60 场、980 步，
报告已刷新）并触发无服务时的浏览器连接失败；随后采用独立分隔符重写，源码未变。
初次健康检查还受代理影响；改为直接访问本机回环后验证通过。保留失败与纠正记录，
这些检查均不新增 Windows 实机证据。

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
| Python 测试 | 47 passed | `artifacts/lab-tests.xml`；包含模拟 PowerShell 流程，非 Windows 实机 |
| 模拟器面板浏览器检查 | 6 passed | `artifacts/browser-checks.json` |
| 合成原版接口面板检查 | 5 passed | `artifacts/original-dashboard-synthetic/report.json` |
| 开发集模拟器基准 | 60 episodes / 980 decisions | `artifacts/benchmark-development.json` |
| 进程采样测量 | 9 rounds / 2,700 episodes / 44,100 decisions | `artifacts/sampling-development.json`；对应轨迹一致，含硬件与计时边界 |
| 全新检出安装 | 46 passed / 1 optional skip；60 条公开轨迹一致 | `artifacts/repro-check.json`；同一 Linux 主机，新依赖和新二进制 |
| 验收矩阵 | incomplete | Windows report 缺失，60 条原版 case 全部缺失 |
| 原版实机 | 未验证 | 尚无 Windows DLL、Mod 编译运行和真实捕获 |

运行验收状态：

```bash
cd /user/chenzk/sts2-lab
.venv/bin/python scripts/audit_acceptance.py
```

目前预期返回非零：Windows 报告已收到，但游戏语义版本尚未确认，60 条原版参考仍缺失。

## 当前阻塞与下一项动作

当前关键路径是首次启用 Mod 后重新启动游戏并读取首个原版状态。以下保留完整接入顺序；
版本报告/DLL 上传、Linux 编译和 Windows 安装已完成，用户现在应保持隧道并从 Steam 重启：

第一执行单元为 P1-01 → P1-03：核对版本、编译桥接、取得一次真实状态、执行一张牌并
确认结算。随后由我们实现 P1-04 的场景准备和重复捕获工具，再扩充参考集；无需用户
手工拼凑 60 场。Linux 侧可同时推进 P1-02 的适配器边界和 P1-06 的复现/接口证据。

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\Connect-Windows.ps1 `
  -Server 用户@服务器 -RemoteRoot /user/chenzk/sts2-lab -SshPort 22
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
Set-ExecutionPolicy -Scope Process Bypass -Force
.\Install-Windows-Mod.ps1 `
  -Server 用户@服务器 -RemoteRoot /user/chenzk/sts2-lab -SshPort 22
```

然后启动 Steam 游戏、启用 Mod、保持连接窗口运行，打开 `http://127.0.0.1:8765`，先完成一次稳定战斗状态读取和单步动作。之后再处理原版场景初始化、随机对齐和 60 条参考集。

## Git 提交规则

远程仓库：`https://github.com/Lidz-abel/Spire2Lab.git`

历史推送曾遇到 TLS 错误，后来已成功推送至 `0a5c869`。下一次提交前读取当前远程状态；推送结果需要核实，不根据缓存或旧日志推断成功。
最近一次推送为 2026-10-22 的认证失败，具体情况见本文开头的 Git 检查点。

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
- [`PROJECT-IDENTITY.md`](PROJECT-IDENTITY.md)：品牌方案、完整 README 设计要求与验收清单；
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
| 2026-10-22 | 用户重新规划 | 按三个阶段推进，准备完成第一阶段；再次提供 `.git` 仓库地址 | `three-stage-v1`；P1-01 至 P1-08 明确任务/证据/依赖；当前仍为 0/60 原版参考；远程只读检查为 `0a5c869`，不代表写入认证恢复 |
| 2026-10-22 | 用户品牌与文档要求 | 持久记录完整 README 设计标准；优先原创尖塔 Logo、当前 README 与 GitHub 上传 | `PROJECT-IDENTITY.md` 保存验收清单；新增三份 SVG，README 按真实实现重组；核心代码与实机验收状态不变 |
| 2026-10-22 | 用户继续第一阶段 | 推进环境建设与验收 | `a2c29eb`：新增 1/2/4 进程采样测量；Windows 脚本支持指定目录并保留安装来源；47 项测试通过；同机全新检出安装与 60 用例复现通过；面板已启动；原版仍为 0/60，推送仍待认证 |
| 2026-10-22 | 用户 Windows 终端反馈 | 游戏发现成功，Steam build 23811903；SSH 在密码提示后关闭 | 服务和路径已本机核对；尚缺客户端/系统诊断，不能判定根因。改进预检查错误分类，保留本地报告；版本和实机验收仍未完成 |
| 2026-10-22 | 用户 SSH 详细日志 | 简单远程命令输出 SPIRE2LAB_SSH_OK，Exit status 0 | 确认该次登录和命令执行成功；重试完整接入，文件上传、隧道和原版桥接仍待验证，先前断连根因未定 |
| 2026-10-22 | 用户上传与服务器实测 | public build 23811903 的三份 DLL 和报告收到，反向监听出现 | 大小/哈希验证及桥接编译通过；Enchantment 元数据检查通过；实际游戏版本、Mod 运行与 60 场参考仍待验证 |
| 2026-10-22 | 用户安装与启用反馈 | 四个文件安装成功，首次同意加载 Mod 后游戏退出 | 已从本机 DLL 确认同意处理包含保存设置与主动退出；请用户从 Steam 重启，运行/接口/版本尚待验证，未执行游戏动作 |
