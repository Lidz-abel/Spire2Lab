# Spire2Lab：新会话接续入口

核对日期：2026-11-15。用于在同一服务器的新窗口继续工作。
本文件是当前摘要；[PROJECT-HANDOFF.md](PROJECT-HANDOFF.md) 保留历史过程。
若两者描述的进程状态冲突，以最新实际检查为准。

## 2026-11-15 用户最新要求与课程期限

课程 Final Project 采用 Build Track 定位，用户确认既有个人项目可以继续拓展。
用户要求以工程实现为主，强化学习必须成为新增工作的重点，最终目标为原版自主完整
通关。第一幕验收是中间里程碑，不能替代完整通关目标。已有四项任务及其证据边界保留。
训练环境、采样/更新、模型保存与恢复、评估和原版部署应形成可运行闭环；当前没有
正式 RL 训练或训练模型证据。E1 已冻结 starter 单场 PPO v1 规格，见 docs/RL-MVP.md；
课程训练、分层学习与 RL+搜索仍未冻结；多策略头不能证明已经实现分层强化学习。
现有模拟器的原版验证仅覆盖有限 starter 战斗，不能假设已有可训练的全游戏环境。

课程时间以用户提供的 2026 年安排为准，按当前 Asia/Shanghai 时区管理：

| 截止 / 时间段 | 交付 |
| --- | --- |
| 11 月 16 日 23:59 | Proposal，1–2 页 |
| 11 月 30 日 23:59 | Milestone Report，2–3 页，附初步结果或 Demo |
| 12 月 8–14 日 | 结果完善、非正式检查和范围冻结 |
| 12 月 21 日 23:59 | 路演 Slides、代码快照、Demo/结果材料 |
| 12 月 22–28 日 | 4 分钟展示 + 1 分钟问答；具体场次待公布 |
| 12 月 28 日 23:59 | 4–6 页 PDF 报告、源代码及说明、结果、视频、最终 Slides |

项目为个人提交，需披露既有工作、课程新增工作、外部依赖及 AI 辅助；准备离线回放和
备用录屏。打包名为“学号_proposal/milestone/presentation/final.zip”，分别取对应阶段。
11 月 16 日 Proposal 已制作：可编辑源 `docs/course/proposal.html`，两页 PDF 与 ZIP 在
`artifacts/course/proposal-20261116-personalized/`；生成与提交步骤见 `docs/course/PROPOSAL-BUILD.txt`。
正文以 Build Track 的 RL 训练与原版部署为核心，保留完整自主通关目标，第一幕为中间门。
用户已提供姓名/学号，个人版 PDF 已填齐，ZIP 按实际学号命名；两页与打包检查通过。
旧 `artifacts/course/proposal-20261116/` 仅为占位草稿，提交应使用上述个人版目录。
GPU 硬件现已实查，长期配额未确认；Proposal 保留预算表述。尚未取得课程提交回执。
下一步：用户审阅个人版 ZIP，于 11 月 16 日 23:59 前提交课程平台并保存回执。
用户指定的 Git 姓名/邮箱已写入本项目共享 Git 目录的本地配置，全局配置未改。
远程交付已恢复：2026-11-15使用现有GitHub SSH密钥，经代理连接ssh.github.com:443，
认证身份Lidz-abel；已推送phase2/search-hierarchy，并用ls-remote确认95c87e3与本地一致，
包含E0及E1实现05f12d8。证据为E1目录push-verified-initial.json；本次交接提交后的
最新核对另存push-verified-final.json，实际HEAD仍用git log/ls-remote核对。
仓库本地Git配置保存remote.origin.pushurl与core.sshCommand，全局配置未改；两个
worktree共享此本地配置。SSH主机密钥按GitHub官方指纹固定在.tools/git/github_known_hosts。
配置引用本服务器私钥路径和代理；它们不入Git，迁移工作区后必须重新核对路径。
历史HTTPS退出128及超时记录保留，不代表当前SSH仍阻塞；凭据不经聊天传递。

11 月 30 日 Milestone 规划已记录于 `docs/course/MILESTONE-PLAN.txt`（planning-v1）。
首批执行顺序：E0 环境/路径恢复与隔离依赖 → E1 训练契约与评估划分 → E2 最多
10,000 有效转换的 PPO 冒烟及 checkpoint 恢复。后续为 E3 初步训练评估、E4 实机
单幕与模型部署、E5 2–3 页报告及 Demo。E0 服务器环境门、E1 训练契约门已通过；
详见 `docs/RL-ENVIRONMENT.md`。普通第一幕与最终完整自主通关目标保留，Windows
连接与实装版本仍待核验。下一个独立工作包为 E2，不自动启动长期训练。
E2细化计划已保存docs/course/E2-EXECUTION-PLAN.txt，仍是规划。下一次从网络、
单环境采样和首个128转换更新开始；8192主运行+256恢复+512/1024并行短测，
总计9984且失败重试共享10000硬上限。目标11.18前首次更新、11.23前完成E2；
11.16 Proposal上传优先，E2不依赖Windows。尚未创建训练进程或修改冻结配方。

E1 已交付 docs/RL-MVP.md、config/rl-mvp-v1.json、sts2lab/rl_contract.py 和检查脚本。
固定公开特征缩放/embedding/候选评分规格、terminal-win-v1、GAE终局/截断边界、
选模和恢复规则；网络/collector/PPO/checkpoint保存器尚待E2实现。环境seed为训练
10000–10999、验证20000–20019、最终测试30000–30099，分别乘三类遭遇；未运行
新验证/测试清单。旧种子排除。E2 CPU单worker目标8192、硬上限10000有效转换；
E3长期预算仍disabled。恢复仅保证学习器状态，环境重启新局，不承诺逐步精确续接。
证据artifacts/rl-mvp/contracts/e1-20261115/：最终124项通过（E1新增59项+既有65项），
regression-attempt2.xml/.log；attempt1保留不相加；contract-manifest.json展开清单及指纹。
合成边界和旧开发seed3模拟器测试，不是游戏RL训练或实机验收。未安装新依赖，
没有长期进程/游戏动作；8765/8766/18526仍无监听。E1及此前提交现已通过SSH推送核对。

E0 证据在 `artifacts/rl-mvp/environment/e0-20261115/`：独立 `.venv-rl`，PyTorch
2.14.0/CUDA 13.0，CPU与GPU1数值检查通过；三类starter种子1战斗各重复两次一致，
65项相关回归通过。合成数值检查不是游戏RL；模拟战斗不是原版证据。安装来自同机
缓存及经RECORD核验的setuptools恢复，不称独立冷安装。依赖锁 `requirements-rl.lock`。
GPU0有错误，禁止默认使用；本轮按UUID仅验证物理GPU1，GPU2–3未做计算验证。
现有host报告128逻辑CPU、377GiB内存和四张约48GiB显存设备，不等于独占配额。
第一阶段源码无差异，包版本清单前后一致；未启动服务/训练，未发送游戏动作。

用户特别要求控制上下文窗口与环境污染：会话切换前更新本摘要，详细历史和证据留在
索引目标；记录当前任务、已完成工作、下一步、阻塞、进程/端口、依赖和提交状态。
按当前任务读取必要文档与证据，避免反复载入全部历史和原始日志。实验使用独立配置、
输出目录和明确的依赖环境；新增长任务记录启动位置、日志及停止方法；退出时只清理
本轮创建且已确认无用的临时进程，保留失败证据与用户已有环境。

## 当前会话环境与恢复结果

本会话实际目录为 `/user/chenzk/sts2/sts2-lab-phase2`，共享 Git 元数据在
`/user/chenzk/sts2/sts2-lab/.git`；下方旧绝对路径属于迁移前布局。
E0已用git worktree repair修复phase2双向Git指针，普通Git命令可用；`.venv`改为
指向本工作区新建的`.venv-rl`，原共享环境未安装新依赖。四个`.tools`工具链接已改为
迁移后相对路径。旧链接/Git文件备份在E0证据目录backups；历史repro工作树未修复或清理。
E0实现前HEAD为`ea8f892`，实际文档提交后HEAD用git log核对。网络代理TLS失败、
直连DNS失败，本轮依赖使用离线缓存。禁止用旧bootstrap.py同步这个RL环境，它会按
base-only锁移除训练依赖。当前完整环境以requirements-rl.lock为准。
权限恢复后可直接读取GPU和ss；本轮ss未发现8765/8766/18526监听。Windows状态仍未知。
已复核本地 Mod 与游戏引用 DLL 哈希，均匹配下文目标值；普通单幕轨迹仍为 0。
本轮已运行E0模拟/数值检查与65项回归，没有原版实验；远程提交状态未重新验证。
Proposal 导出使用系统 Pango/Cairo 原生库和临时排版工具；没有安装依赖或修复现有 venv。
页数、文字提取、内嵌字体、排版与 ZIP 校验属于文档检查；失败原因见 PROPOSAL-BUILD.txt。

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
| 当前开发目录 | `/user/chenzk/sts2/sts2-lab-phase2` |
| 当前分支 | `phase2/search-hierarchy` |
| E0 前 HEAD | `ea8f892`；新窗口用 `git log -1` 获取后续提交后的实际 HEAD |
| 最近实现提交 | `05f12d8`：E1训练契约、适配与种子划分；后续文档HEAD用git log核对 |
| 第一阶段保留目录 | `/user/chenzk/sts2/sts2-lab`，`main`，`f9faf0a`，源码与依赖保持不变 |
| Git 关系 | 两目录共享 `/user/chenzk/sts2/sts2-lab/.git`；迁移时不要只复制 phase2 的 `.git` 文件 |
| GitHub | <https://github.com/Lidz-abel/Spire2Lab> |
| 远程交付 | phase2/search-hierarchy已推送且SHA一致；见E1目录push-verified-*.json |

代码与文档已同步上述分支；GitHub不包含被忽略的私有证据、依赖环境和游戏文件。
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
   cd /user/chenzk/sts2/sts2-lab-phase2
   .venv/bin/python -m uvicorn sts2lab.server:app --host 127.0.0.1 --port 8766
   ```

4. Windows 安装 phase2 已备好的单幕包，重启至实验槽位 2 主菜单，恢复 SSH 隧道。
   本机专用路径和可复制命令放在被 Git 忽略的
   `artifacts/handoff/20261115/LOCAL-RESUME.txt`；该历史文件的RemoteRoot需先改为迁移后路径，
   不能直接照抄旧路径。凭据不在文档中。
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

8. 更新状态、交接与来源文档，提交可审查结果；使用已验证SSH推送并核对远程SHA。
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

> 继续 Spire2Lab，工作目录 `/user/chenzk/sts2/sts2-lab-phase2`，分支 `phase2/search-hierarchy`。
> 首先阅读 `SESSION-HANDOFF.md`，按其中顺序核对文件与实际运行状态。
> 保留用户“按顺序完成采样、搜索、原版画面、完整单幕”的完整目标。
> 前三项仅在声明范围内验收通过；第四项代码已实现，但普通原版单幕尝试为 0。
> 2026-11-15 核对时 8765/8766 面板与 18526 隧道都未运行，旧 PID 不可用；
> Windows 最新单幕 Mod 是否安装仍须实查。请先报告接续核对结果及最少必要恢复步骤，
> E0服务器准备和E1训练契约已通过，按docs/RL-MVP.md接续E2，Windows恢复后继续实机。
> 不要重写已验收部分、把合成测试当实机、或宣称本地提交已推送。
