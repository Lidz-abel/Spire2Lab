# Spire2Lab：新会话接续入口

核对日期：2026-11-15。用于在同一服务器的新窗口继续工作。
本文件是当前摘要；[PROJECT-HANDOFF.md](PROJECT-HANDOFF.md) 保留历史过程。
若两者描述的进程状态冲突，以最新实际检查为准。

## 先读这段

项目要构建具有搜索规划、分层决策和高效训练能力的自主强化学习系统，使用
《杀戮尖塔 2》验证，并让用户实时看到智能体的决策和对应的原版画面。
目前在第二阶段，第一阶段有限范围验收已完成，第三阶段训练尚未开始。

用户要求按顺序完成的四项仍完整保留：采样可靠性 → 搜索决策改进 → 原版画面 →
完整单幕。前三项已通过各自限定范围的验收；第四项已实现但尚无真实整幕验收。
旧会话目标状态是 `blocked`，不是完成。本轮用户仅要求整理转接资料，未开始游戏实验。

**2026-11-15 实际状态：`8765`、`8766`、`18526` 均连接失败，没有相应监听或
`uvicorn sts2lab.server:app` 进程。旧 PID、exec 会话号已失效。**
代码与本机私有证据仍在，Windows 安装包清单校验通过；原版普通单幕轨迹数仍为 0。
没有证据说明 Windows 已安装最新单幕包，也无法在隧道缺失时确认当前游戏版本。

## 工作区与提交

| 项目 | 正确位置 / 状态 |
| --- | --- |
| 当前开发目录 | `/user/chenzk/sts2-lab-phase2` |
| 当前分支 | `phase2/search-hierarchy` |
| 本次文档整理前 HEAD | `67302ae`；新窗口用 `git log -1` 获取文档提交后的实际 HEAD |
| 最近实现提交 | `f4ce166`：明确不支持的单幕界面与异常私有记录 |
| 第一阶段保留目录 | `/user/chenzk/sts2-lab`，`main`，`f9faf0a`，保持不变 |
| Git 关系 | 两目录是共享 `/user/chenzk/sts2-lab/.git` 的 worktree；迁移时不要只复制 phase2 的 `.git` 文件 |
| GitHub | <https://github.com/Lidz-abel/Spire2Lab> |
| 远程交付 | 未验证成功；历史写认证失败，最后一次推送无输出超过 90 秒后终止，退出 143 |

当前代码与文档以本机为准。新窗口不要仅从 GitHub 克隆后假定已有最新成果。
持续小步提交已经获得用户授权；只有核对远程提交后才能报告“已推送”。

关键检查点：`f94a5c0` 采样，`f2bc4c7` 搜索配置冻结，`601b580` 搜索验证，
`4d33aea` 原版截图验收，`a8a861c` 单幕主实现/配方冻结，`3351c61` 离线审计，
`f4ce166` 服务器传输修复。后续修复没有修改 Windows 单幕包或固定策略。

## 已确认的需求与边界

- 三阶段路线：可信实验平台 → 搜索与分层决策 → 高效训练与原版评测。
- Linux 服务器承担控制、搜索和后续训练；另一台配置较低的 Windows PC 运行 Steam 游戏。
- 实验面板与原版必须在状态、动作、决策和图片上可对应；实时可观察，并支持只读回放。
- 平台尽可能原创，可参考开源实现。当前模拟器/Mod 仍依赖固定上游，不是全栈原创；
  来源和派生改动记录在 [CODE-PROVENANCE.md](CODE-PROVENANCE.md)。
- 需求、规划、证据、失败、状态和待办持续写入文档，按可审阅进度提交 commit。
- README 主语言英文，专业科研风格；原创 SVG 要有尖塔、卡组和登塔路径辨识度。
  设计要求与资产入口已在 [PROJECT-IDENTITY.md](PROJECT-IDENTITY.md) 保存。
- 不虚构实验结果；模拟器、合成测试、实机证据分开；不将已实现描述为已实机验收。
- 策略输入仅为公开观测与公开历史，不给实际 seed、RNG、隐藏牌序或原版快照。
- 单幕实验限槽位 2、Ironclad/A0、正常种子开局、`shouldSave=false`；
  保留真实奖励与路线，不跳调试房间、不修改资源或规则来通过验收。
- 动作只提交一次；不确定结果通过读取核对，不盲目重发。出现不支持界面停止自动动作。
- 私有 DLL、存档、游戏图片、原始采集和凭据不入 Git；所有失败证据保留。

## 进度与证据范围

| 工作 | 已有证据 | 仍须保留的限制 |
| --- | --- | --- |
| 第一阶段 | 可信控制/协议/面板、60 条原版参考和额外探针等；详见第一阶段状态 | 有限 starter 范围，不是全游戏一致性；旧 Mod 验收不能自动认证新 Mod |
| 1. 采样 | 同 60 条公开历史、975 决策；新开局 60/60，耗尽 29/975（2.97%），达到事前 ≤5% 开发门 | 近似粒子方法，可耗尽，不是精确后验或普遍保证 |
| 2. 搜索 | V2 开发 210 场 + 新保留集 450 场；660 次环境重放、42 次策略重放；另 4 场原版共 49 步 | 预选 HP32/1024 平坦/分层均 77.94 HP，heuristic 77.03，低预算旧效用 78.08；分层无额外收益，未证明胜率/全游戏/训练收益 |
| 3. 原版画面 | 真实 Nibbit/seed1 战斗 11 步、12 张 3072×1728 图，74 HP 获胜；逐步状态/策略、图像绑定、桌面/手机回放通过 | 一场调试战斗，不是整幕；决策画面可能含动画横幅，不承诺完全静止 |
| 4. 完整单幕 | 正常开局、地图/奖励/休息/商店/战斗控制、目标、记录、图片、面板、离线审计已实现 | 原版普通单幕尝试 **0**；当前整幕策略是公开启发式、0 模型调用，不是已训练或已验证的整幕搜索 |

搜索选择只使用开发种子 1–10。V1 已用 1001–1010，V2 已用 2001–2030；
这些都不能重新称为未触碰保留集。V2 面板显式采用 public_opening、HP 效用、深度 32、
预算 1024、2 秒软限；固定预算评测没有墙钟截止，Python 旧默认仍保留。

测试报告：单幕实现完整套件 188 项通过，随后离线审计 4 项通过，再随后相关回归
26 项通过。**三组存在重叠，不相加宣称为一个新全套结果。** 这些报告是在 10 月 25 日
运行，11 月 15 日仅核对文件与结果，未重新运行。合成 UI 通过不等于原版单幕通过。

| 证据入口 | 用途 |
| --- | --- |
| [PHASE1-STATUS.json](PHASE1-STATUS.json) / [PHASE2-STATUS.json](PHASE2-STATUS.json) | 状态与证据索引 |
| [docs/PHASE2-EXECUTION.md](docs/PHASE2-EXECUTION.md) | 用户四项任务与完整完成门 |
| [docs/BELIEF-V2-VALIDATION.json](docs/BELIEF-V2-VALIDATION.json) | 采样配对回归 |
| [docs/PLANNING-V2-RESULTS.md](docs/PLANNING-V2-RESULTS.md) / [docs/SEARCH-V2-HELDOUT.json](docs/SEARCH-V2-HELDOUT.json) | 搜索有限结果及负面结论 |
| [docs/DECISION-IMAGES-VALIDATION.json](docs/DECISION-IMAGES-VALIDATION.json) | 实机图片验收摘要 |
| [docs/SINGLE-ACT.md](docs/SINGLE-ACT.md) / [docs/SINGLE-ACT-VALIDATION.json](docs/SINGLE-ACT-VALIDATION.json) | 单幕契约、当前实现及尚缺证据 |
| [config/single-act-v1.json](config/single-act-v1.json) | 预登记单幕配方 |

## 当前实现的入口

- starter 环境与控制：`sts2lab/contracts.py`、`simulator.py`、`original.py`、`bridge.py`、
  `runtime.py`、`server.py`；公开粒子/搜索/目标在 `belief.py`、`planning.py`、`hierarchy.py`。
- 单幕：`sts2lab/act_contracts.py`、`act_bridge.py`、`act_policy.py`、`act_runtime.py`、
  `act_server.py`、`act_replay.py`；UI 为 `web/act.html`、`act.js`、`act.css`。
- Mod 扩展：`bridge/ActContract.cs`、`McpMod.Act.cs`、`McpMod.Lab.cs`、`McpMod.Images.cs`。
  `scripts/build_bridge.py` 修改构建副本，vendor 原件不改。
- 原版截图由 Godot 视口读取，绑定 instance/build/token、run/decision、公开观测摘要和 PNG 哈希。
- 单幕读取去掉上游 GET 自动打开商店/宝箱的副作用，改为显式动作；选牌有独立稳定门。
- 未支持的假商店、bundle/relic 选择、Crystal Sphere、未知选牌模式等会停止。
  明确已到达且 execution_idle 的未支持界面可以记录；忙碌/过渡状态仍不能确认。
- 离线审计检查记录、公开投影、请求确认、策略/目标、路线和图片；它不重新执行原版或整幕模拟规则。

## 版本与端口：恢复前必须核对

目标是历史固定版本 **v0.107.1，2026-06-18，Steam build 23811903**，不是 11 月的
“默认最新版”。如果 Steam 更新了游戏，要重新确认版本及引用，不能绕过哈希检查。

| 内容 | SHA-256 |
| --- | --- |
| 游戏 `sts2.dll` | `a1f9e653f1e28e4076558fee1e60d218619cb7e057b887c6417f62c62c6d7a52` |
| 待验收单幕 Mod | `ff144ee812218f9a3ffbb7dbdb2f5b1c4d6b750a189180d836b6092f85db41bd` |
| 已验收截图版 Mod（旧） | `b6c1a3ab3ca649be06a3ec0aeb2a995d4aa82daedf5d95b51ce87a8773e5c61b` |
| 搜索 V2 native | `6321ca69c3ac6024d069f00b683d698523d8b22819609ee0044f078492856131` |

Windows Mod 的本地端口为 **21526**；Linux 通过 SSH 反向端口 **18526** 访问。
第二阶段面板用 **8766**，路径 `/` 为战斗实验、`/act` 为单幕。
第一阶段面板历史使用 8765；不要在 phase2 直接运行默认端口为 8765 的 `scripts/start.sh`。
Windows 历史上 Code.exe 占用过 15526/21526，遇到超时先核对端口所有者，不盲目换端口或杀进程。

## 新窗口接手顺序

1. 进入 phase2，依次读本文件、`AGENTS.md`、`PHASE2-STATUS.json`、`docs/PHASE2-EXECUTION.md`、
   `docs/SINGLE-ACT.md`、`CODE-PROVENANCE.md`；历史细节查 `PROJECT-HANDOFF.md`。
2. 核对 `git status`、当前提交、端口与现有进程。当前保存的快照无运行服务；以后仍以实查为准。
3. 用户要求继续验收后，在服务器启动第二阶段面板：

   ```bash
   cd /user/chenzk/sts2-lab-phase2
   .venv/bin/python -m uvicorn sts2lab.server:app --host 127.0.0.1 --port 8766
   ```

4. Windows 安装 phase2 已备好的单幕包，重启至实验槽位 2 主菜单，恢复 SSH 隧道。
   本机专用路径和可复制命令放在被 Git 忽略的
   `artifacts/handoff/20261115/LOCAL-RESUME.txt`；凭据不在文档中。
   先验证 live game/Mod SHA、实例、槽位、主菜单与结算状态；不要把过去的“已重启”当作当前证明。
5. 实机执行前核对实际提交及源文件指纹；保留 `a8a861c` 配方冻结与后续服务器修复的区别。
   按配方 ACT001/ACT002/ACT003 顺序测试；最多 1200 动作。保留每次失败，发生修复就注明版本。
6. 验收必须在一条普通连续路线中到达并击败第一幕 Boss，并覆盖地图、奖励、真实购买、
   实际休息/升级与战斗。检查所有图片绑定、无未决动作、自动策略与只读回放；
   不用调试战斗、合成路线或分散探针代替整幕，也不能把人工接管算作自主验收。
7. 归档后运行：

   ```bash
   .venv/bin/python scripts/audit_act.py artifacts/act-runs/RUN_ID.jsonl \
     --output artifacts/single-act/RUN_ID-audit.json
   ```

8. 更新状态、交接与来源文档，提交可审查结果；恢复 GitHub 登录/网络后再推送并核对远程。
   单幕实机及剩余交付没有通过前，不能标记四项目标或第二阶段整体完成。

## 必须保留的本机数据

`.git`/Git bundle 只保存被跟踪的代码文档，**不包含**被忽略的实验记录和依赖。
仅换会话时继续使用原目录即可；迁移机器必须单独复制以下目录并保持私有：

- 两个工作区的 `artifacts/`：第一阶段参考、原始采集、报告和失败记录。
- phase2 的 `artifacts/windows/`：引用 DLL、报告、当前包、旧包历史。
- phase2 的 `artifacts/phase2-v2/`、`artifacts/images/`：搜索证据及已验收原版图片。
- `artifacts/act-runs/`、`act-raw/`、`act-images/`：未来单幕轨迹与绑定资料（目前无正式单幕轨迹）。
- `.tools/`、`.venv/`、被忽略的 `vendor/` 安装目录：可按锁定来源重建；同机工作区可能依赖
  第一阶段目录中的共享资源，移动前检查符号链接。

本次接续包目录：`artifacts/handoff/20261115/`。其中的 `Spire2Lab-code.bundle`
保存 main 与 phase2 的代码历史；快照、私有恢复指令、关键证据清单和 SHA-256 校验文件
用于查验。**它不是全部私有实验数据的备份，文件清单也不能替代文件本体。**
`HANDOFF.txt` 是旧实现笔记，不作为当前完成状态依据。

## 可直接粘贴到新窗口

> 继续 Spire2Lab，工作目录 `/user/chenzk/sts2-lab-phase2`，分支 `phase2/search-hierarchy`。
> 首先阅读 `SESSION-HANDOFF.md`，按其中顺序核对文件与实际运行状态。
> 保留用户“按顺序完成采样、搜索、原版画面、完整单幕”的完整目标。
> 前三项仅在声明范围内验收通过；第四项代码已实现，但普通原版单幕尝试为 0。
> 2026-11-15 核对时 8765/8766 面板与 18526 隧道都未运行，旧 PID 不可用；
> Windows 最新单幕 Mod 是否安装仍须实查。请先报告接续核对结果及最少必要恢复步骤，
> 然后继续真实单幕验收。不要重写已验收部分、把合成测试当实机、或宣称提交已推送。
