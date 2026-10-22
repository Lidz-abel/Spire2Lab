# Spire2Lab 项目转接文档

更新时间：2026-10-23

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
项目目标：**完成第一阶段所有的内容**（用户于本轮重新设为 active；当前未完成）

2026-10-23 本轮交付与阻塞核对：实现已提交为 9ac68a2，本地 main 此时领先跟踪远程
30 个提交。独立安装目录保留原先下载的依赖及新构建，源码从 2c25a99 升级至
9ac68a2 后重跑全套：122 项通过、1 项可选 PowerShell 跳过；tracked source 未变化。
证据 artifacts/interface-fresh-regression.json 和同名前缀日志/XML。此检查是源码升级
后的独立构建回归，不是对 9ac68a2 再做一次冷安装。
最终只读检查 artifacts/windows/interface-final-readiness.json 仍是同一个旧 Mod
进程，lab_mod_sha256/能力字段缺失；新构建未加载。该条件已在连续多轮目标推进中
重复确认，用户尚未反馈安装结果。本轮可独立进行的分支/训练边界、回归和文档
工作已完成；后续实机初始化、RNG 对齐、面板完整战斗及 60 场/9 类覆盖均依赖此步。
目标应保持未完成并按 blocked 等待 Windows 操作；GitHub 写入认证另行阻塞远程
同步。保留现有服务和隧道，不重发游戏动作，不重复上传引用或重编译同一 Mod。

2026-10-23 接口验收补齐（本段优先于下方历史记录）：新增不可变 BranchProvenance，
记录分支 ID、父分支、父决策和 root/snapshot/sample_world/restore 操作；reset
生成新根，restore 以检查点为父生成新编号。环境协议和实验头暴露来源，Observation
和训练张量不携带这些元数据。原版后端为 None，仍显式拒绝克隆/恢复，不发 HTTP。
此前怀疑“策略版本缺失”经源码复核不成立：Decision.policy 已是 heuristic-v1 /
random-v1；本轮新增保存轨迹检查，未更改策略算法、协议 0.3 或编码 v3。
30 项针对性、123 项完整回归通过，各 1 项既有依赖弃用警告；报告在 artifacts/
interface-boundary-tests.xml 和 interface-boundary-regression-tests.xml。新增真实
模拟器检查覆盖非法动作无操作/过滤、wrapper 与 simulator 截断以及限步末端胜负
优先级。受控 Mod 源码和构建未变化，已给用户的安装指纹仍有效。
完整原版审计 interface-boundary-status.json 位于 artifacts/acceptance/：errors=[]，
60 场和全部 9 类边界缺失；最新只读原版检查仍无新 Mod 指纹，未发游戏动作。
独立检出复现记录仍明确绑定 2c25a99，不把它写成后来提交的新一次冷安装证明。
面板已正常重启加载本轮代码，PID 165874 / exec session 73014；当前是暂停的模拟器
新会话。旧完成态轨迹以 session_closed/server_shutdown 收尾，原始记录保留；新
实验头和 API 均含根分支来源，health 仍 original_game_verified=false。证据为
artifacts/interface-service-restart.json，其中保留检查脚本最初误期望归档事件的更正。
下一实机动作仍是 Windows 安装新 Mod、重启到主菜单、核验指纹和槽位 2，再检查
声明种子的第 2 层初态。GitHub 认证仍无恢复证据，所有新增实现保持本地提交。

2026-10-23 最新状态核对（本段优先于下方历史记录）：用户询问当前工作和阶段。
仍在第一阶段，正在完善 P1-02/P1-06 的平台与复现证据，实机关键路径是 P1-03/04。
阶段 2 搜索与分层决策、阶段 3 高效训练尚未开始。完整原版参考集仍为 0/60。
网络恢复后，独立检出 2c25a99 的 bootstrap 成功结束（退出 0），没有复制运行依赖；
新 venv、SDK 下载、依赖安装及原生构建完成，113 项测试通过、1 项因该检出未安装
可选 PowerShell 工具而跳过、1 项既有依赖警告。此前两次 TLS 失败记录保留。
证据为 artifacts/repro-2c25a99-bootstrap-resumed-result.json 和对应日志。
新构建的 300 次模拟器运行（60 个不同用例、4,900 次决策）与既有构建的公开轨迹、
策略、结局和最终 HP 全部一致；比较仅排除每条记录中的二进制 SHA 字段。
两份原生库 SHA 不同，故不宣称二进制逐字节复现，也不宣称原版一致。
artifacts/repro-2c25a99-comparison.json 包含源报告哈希与比较边界；tracked source
未改动，报告 working_tree_dirty=true 来自未跟踪的 .repro-cache/，如实保留。
最新只读检查 artifacts/windows/status-request-check.json 确认隧道与面板可读，
游戏仍是第 1 层战斗，缺少新 Mod 指纹与能力字段；本次未发送任何游戏动作。
下一项实机工作仍需关闭游戏、安装已编译的新 Mod，再启动至主菜单核验运行指纹，
随后检查受控第 2 层初态和完整战斗。新 Mod 仅编译和合成测试通过，未实机验证。
GitHub 认证没有恢复的新证据，本地进度提交尚未同步；本轮只更新验收记录。

2026-10-23 当前代码检查点 2c25a99：内容边界迁移已提交，main 领先跟踪远程 27 个
提交，仍无 GitHub 认证恢复证据。为 P1-06 更新协议 0.3 采样报告：1/2/4 workers、
3 repeats、每轮 300 场，共 2,700 场/44,100 决策；轨迹一致、worker 清理通过。
报告 artifacts/sampling-protocol03-development.json 记录 git_commit=2c25a99 与
working_tree_dirty=false，包含硬件/延迟/RSS 与计时定义；未覆盖旧采样报告，也不
计入原版参考集。
已创建 .tools/repro-phase1-2c25a99 独立检出，使用新 venv 和独立 UV/PIP/NuGet/
DOTNET_CLI_HOME 缓存，不复制运行依赖。bootstrap 初次及一次重试均已终止（退出 1），
停在 uv pip sync 的 PyPI TLS handshake EOF，尚未进行原生构建或测试。curl 对同一
PyPI 地址也在已建立代理连接后 TLS 超时；没有关闭证书验证或修改代理配置。失败
日志及结果保存在 artifacts/repro-2c25a99-bootstrap*；检出 tracked source 未改变。
旧 a2c29eb 的成功复现仍作为历史证据保留，不用它宣称当前版本冷安装通过。
最新 Windows 只读检查 artifacts/windows/staging-install-check-20261022T182139974246.json
仍是旧 Mod 的战斗状态，无新指纹；安装问题已向用户提出，尚未收到执行反馈。
当前没有进行中的 bootstrap/采样任务：相关 exec session 均返回终止结果；面板服务
PID 127906 / exec session 8562 保持运行，浏览器验证后为已结束的模拟器实验。
下一步：Windows 新构建加载后验证一个固定种子原版初态；联网恢复后从现有独立
检出继续 bootstrap 并保存新日志。完整原版验收仍 0/60，第一阶段未完成。

2026-10-23 内容边界迁移已实现并验证：上一生命周期提交为 5856de0。先在
docs/ENVIRONMENT-CONTRACT.md 定义迁移契约，再新增项目 token 词表与加载校验。
协议升为 0.3.0，公开 Card 移除 native_id；config/phase1.json 的牌组/遗物改为语义
名称，benchmark_version 升为 ironclad-starter-v2，仅标记配置表示变化。第 2 层、
牌组、HP、种子、三遭遇和 60 原版场次要求完全保留。native ID 仍在适配器内部转换。
Gym 编码升为 combat-entities-v3，使用 config/content-v1.json 中项目分配的 token，
0 为 padding、未知内容显式拒绝；训练入口和实验头记录词表版本/指纹，验收缓存跟踪
该 JSON 与 ENCODING.json。旧协议轨迹完整保留，当前语义重放在解析字段前要求迁移。
原版 Mod / C# 扩展没有改变，已通知用户安装的构建指纹仍然有效。
私有 artifacts/vocabulary_migration_check.py 在代码修改前后分别执行固定开发及
保留种子、3 遭遇、2 策略：120 场、2,180 决策完全一致（只排除协议版本/删除的数字
ID），证据 vocabulary-migration-before.json 与 -after.json；这不是原版对照。
针对性 58 项与完整回归 114 项通过，各 1 个既有依赖警告。浏览器原生路径 6 项、
合成原版路径 5 项通过，均无 JS 错误；旧浏览器产物已归档。当前面板新进程
PID 127906 / exec session 8562，已加载协议 0.3，浏览器 QA 后是模拟器完成态。
完整实机审计仍 errors=[]、0/60、缺全部 9 类边界。最新只读记录
artifacts/windows/staging-install-check-20261022T180129896726.json 仍是旧 Mod 的
第 1 层战斗；尚未收到 Windows 安装反馈，也未发送 lab_prepare。可继续独立做
当前提交的全新检出复现检查；实机初始化须等待运行 Mod 指纹匹配。

2026-10-23 后端接口继续推进：场景初始化里程碑已提交为 650f3a4（仍未推送）。
等待 Windows 安装期间新增 docs/ENVIRONMENT-CONTRACT.md，定义本项目 Environment
协议、统一同步/异步 step 调用及可选能力拒绝。模拟器 reset 成功创建新状态后才释放
原状态，错误种子/遭遇保持原状态；原版 reset/snapshot/restore/sample_world 明确
拒绝且不发 HTTP。针对性 33 项及完整回归 100 项通过，各 1 项既有依赖警告，证据
artifacts/environment-contract-tests.xml 和 environment-contract-regression-tests.xml。
未更改 C# 扩展或已通知用户安装的 Mod；其构建指纹继续有效。
P1-02 边界审阅还发现 Card.native_id 暴露上游编号、gym_env.py 读取 sim.names，
下一步须建立内容词表并版本化迁移观测/训练编码；本任务尚未全部完成。
面板旧进程已正常停止，原暂停模拟器会话先归档保留，未向 Windows 发送动作；
新服务 PID 109135 / exec session 94569 在 8765 正常工作，加载 650f3a4 版本。
旧轨迹最后事件为 session_archived；检查器最初误期望 session_closed，已核对源码
语义并在 dashboard-restart-20261022T175710789348.json 记录更正及实际证据。
新生命周期改动尚需在下一次实际实验前重启面板加载，不必为等待安装反复重启。
最新 staging-install-check-20261022T175804953650.json 仍读到旧 Mod/原第 1 层战斗；
无用户安装反馈，未调用 lab_prepare。先完成此接口提交，再可独立推进内容边界，
实机初始化必须等新 Mod 的运行指纹匹配。阶段 1 仍未完成，0/60 原版参考场次。

2026-10-23 场景初始化交付前检查通过：57 项针对性检查及 92 项完整回归测试通过，
各有 1 项既有 Starlette/httpx 弃用警告；证据为 artifacts/windows/ 下
scenario-component-tests.xml、scenario-regression-tests.xml。C# 测试独立编译生产
ScenarioContract.cs，对 36 组合成输入核验，不加载游戏 DLL。Python 覆盖错误 Mod、
槽位、菜单、种子、初态及来源拒绝，超时/异常回执只读恢复，以及 Ctrl+C 留存报告、
进程异常退出后从已落盘 JSONL 恢复。OriginalEnvironment 默认接入现校验本地构建
和运行 Mod 指纹；使用合成 client 的测试仍明确与实机证据区分。
prepare_scenario.py --help 验证通过；完整 audit_acceptance.py 返回预期退出码 1、
errors=[]、缺少全部 60 场与 9 类边界，不减少验收范围。
最新只读实机检查 artifacts/windows/staging-preinstall-20261022T174839985791.json
确认隧道可读、仍在第 1 层战斗、没有新 Mod 的指纹/能力字段。已通过异步问题给用户
提供关闭游戏、运行现有 Install-Windows-Mod.ps1、重启到主菜单的具体操作；新编译
DLL 指纹为 6de822b9db90892337ff0c00f08aae023f2fd4d192b12c8292315e5dd723268c。
等待用户执行 Windows 安装；未发送 lab_prepare 或任何新的游戏动作。收到安装反馈
后先只读确认运行 Mod 指纹、专用槽位 2 和主菜单，再执行一个声明种子的场景检查。
本轮依然是 P1-03/04 进展，不是完整实机闭环或第一阶段完成；GitHub 认证无新进展。

2026-10-23 最新状态核对（优先于下方历史记录）：用户询问当前工作及所处阶段。
仍在阶段 1，当前推进 P1-03 实机闭环与 P1-04 受控场景；阶段 2/3 尚未开始。
工作区已新增 bridge/ScenarioContract.cs、bridge/McpMod.Scenario.cs，扩展 lab_prepare
请求和 Mod 指纹/能力声明。scripts/build_bridge.py 已支持多扩展文件、旧构建归档、
临时目录构建及清单最后发布；新 Mod 编译成功，0 错误、1 项上游 CS8602 警告。
证据 artifacts/windows/scenario-build-3.log 与 mod/build.json；前两次失败日志保留。
旧构建已归档到 artifacts/windows/mod-history/。新构建尚未安装到 Windows，也未
执行过场景初始化；不能把编译通过写成可重复场景或原版一致性通过。
Python 的 sts2lab/scenarios.py、scripts/prepare_scenario.py 和 Mod 指纹检查已写入
工作区，针对本轮新增逻辑的测试及审阅尚未完成，代码尚未提交。下一步先完成这些
检查，再提供新 Mod 安装操作并开展原版初始化验收。此前真实防御牌探针仍是独立
诊断，正式原版参考战斗保持 0/60；实时面板与原版完整战斗的对应尚未验收。
本次只核对本地记录及构建文件，没有向游戏发送动作或要求用户再次上传引用。
Git 本地 main 领先跟踪的 origin/main 24 个提交；无认证恢复或成功推送的新证据。

2026-10-23 下一实施单元已经启动：发行门与出牌探针提交为 `3832456`；随后新增
docs/SCENARIO-STAGING.md，先定义专用档案、固定初态、声明种子、幂等设置请求、
独立失败证据和禁止事后拟合的契约。P1-04 场景准备因首战楼层差异提前成为 P1-03
范围内面板闭环的前置条件。尚未新增 staging 端点、编译新 Mod 或再次安装。
已只读提取本机 API 元数据到 artifacts/windows/scenario-api.json、scenario-api-extra.json；
工具源码在 artifacts/windows/scenario-api-inspection/，不执行游戏程序集。关键签名：
RunState.CreateForNewRun、RunManager.SetUpNewSingleplayer(runState, shouldSave, dailyTime)、
RunManager.EnterMapCoordDebug、CombatRoom(encounter, runState)、RunRngSet(string seed)、
PlayerRngSet(uint seed)。下一步继续核对 NGame 启动与 SeedHelper 转换，不凭签名猜测
执行顺序。已阅读固定上游 NativeExports.ResetArena / SeedStreams、GameRng 与
EncounterRng，确认模拟器使用分路 seed 名称且 Slimes 组成依赖楼层。后续实现如引用
这些兼容事实须记录来源，不能改 vendor 或用搜索种子/覆写未来状态拟合输出。
当前游戏仍停在槽位 2、第 1 层防御牌之后；未继续游戏。Windows 更换 Mod 需要用户
安装，必须先完成可审阅的构建与校验再提供操作命令；既有编译产物先归档。

2026-10-23 发行版本与首次真实出牌探针通过：用户上传了游戏安装目录的
release_info.json。版本 v0.107.1、日期 2026-06-18T15:43:56-07:00、提交 59260271，
与原始报告中 DLL 产品版本的完整提交一致。进一步只读检查 AssemblyHasher 的调用
目标，确认兼容校验值是 SHA-1 前 4 字节的有符号小端整数；对收到的 DLL 重算为
-1555940892，与发行文件一致。该 32 位值不是安全哈希；完整 SHA-256 仍与收到的
报告、Mod 构建引用及运行时桥接一致。证据 release-verification.json 和
assembly-hasher-inspection.json 均在 artifacts/windows/。未执行游戏程序集中的方法。

新增 sts2lab/release.py；verify_windows_bundle 现在接受与 DLL 关联的真实发行文件，
跟踪其 SHA-256，缓存会在证据变化后失效；不修改原始 report.json 或 mod/build.json。
文件存在但版本/提交/校验值不符时拒绝，不回退忽略；缺文件时保留原来的 DLL 版本
元数据路径。16 项相关测试通过（1 项既有依赖警告），包括不可改写原始报告与缓存
失效，证据 artifacts/windows/release-gate-tests.xml。首次证据记录误用系统 Python
因缺 pydantic 未执行成功，改用项目 .venv 后成功。审计已通过版本门，首次推进到
缺少 index.json；随后创建 cases=[] 的空索引，重审 errors=[]、仍缺 60/60 与全部边界。

已通过真实游戏 UI 切换到此前无数据的 Mod 存档槽位 2，并选择铁甲战士、关闭该槽位
的新手教程后开局；槽位 1 没有用于本次实验，不删除任何槽位。每次导航 POST 单独
记录，未自动重发。新存档首战是 Nibbit，但实际楼层为 1，固定基准要求 2；原版适配器
的 verify_scope 正确拒绝。未改基准、初态字段或隐含随机状态去适配这次开局。

为先验证真实桥接动作，单独记录 floor1 诊断：BridgeClient 以请求编号和状态令牌
打出一张防御。9 项检查通过：能量 3→2、格挡 0→5、HP 80 不变、手牌少一张、弃牌
多一张、回合/实例不变、结算稳定且回执对应本次请求。证据
artifacts/windows/one-step-probe-20261022T171722625580.json，明确
benchmark_eligible=false；未写入参考集或假冒面板实验轨迹。当前停留槽位 2、第 1 层、
第 1 回合、出牌后状态；没有结束回合。导航原始记录为 artifacts/windows/navigation-*.json。
这完成首次真实出牌探针，不等于 P1-03、P1-05 或第一阶段完成；还需受控第 2 层初态、
面板接入、结束回合/断线/暂停/完整战斗、随机对齐和 60 场对照。用户无需再次上传文件。
用户本轮询问当前进度，已明确答复仍在第一阶段 P1-03，阶段 2/3 未开始。
GitHub 认证没有恢复证据，继续保留本地提交。下一会话不要重装 Mod、重开测试局，
不要把先前的主菜单状态当作当前状态；先核对最新游戏状态与现有轨迹。

2026-10-23 Linux → Windows 隧道只读验收通过：用户确认隧道连接后，服务器使用
实际 BridgeClient 读取根路径及连续 5 次主菜单状态，协议 1、游戏 DLL SHA-256、
进程实例、状态令牌均匹配；最后读数 lab_settled=true，主菜单 lab_action_ready=false
符合设计。证据 artifacts/windows/tunnel-main-menu-20261022T165341.json。
本轮新增 scripts/check_bridge.py 与 sts2lab/bridge_check.py，把只读检查做成可重复
命令：校验原始报告/收到的 DLL/Mod 构建引用一致，再采集 GET；不覆盖旧证据，
合成传输与实机传输明确区分。新命令实机运行的 7 项检查全部通过，证据
artifacts/windows/bridge-check-20261022T165923467279.json。其通过仅限主菜单连接，
不能满足版本门或战斗验收。tests/test_bridge.py 与 test_bridge_check.py 共 12 项
通过，包含实例变化、令牌变化、协议/指纹不匹配、未稳定和超时；均为合成 HTTP。
测试记录 artifacts/windows/bridge-check-tests.xml，不计为原版战斗。

当前发行版本门仍未通过：收到的 DLL 元数据版本为 0.1.0.0。只读 PE 元数据和调用
目标检查确认 ReleaseInfoManager 从游戏安装根目录读取 release_info.json；ReleaseInfo
包含 Version、Commit、Date、Branch、MainAssemblyHash。证据
artifacts/windows/release-metadata-inspection.json，不执行游戏 DLL，也不推定哈希算法。
已请求用户在另一 Windows PowerShell 上传该文件到 artifacts/windows/release_info.json；
尚未收到。接手后先检查是否到账，再核实实际字段与原始 DLL 的关联，按证据完善
验收器；不得覆盖 report.json、改目标版本或伪造 release_info 来绕过门禁。
额外 GET /api/v1/profiles 显示当前槽位 1 有数据，2/3 无数据，私有响应存于
artifacts/windows/profiles-readonly.json；未切换槽位，未发送任何 POST 或游戏动作。
完整审计仍缺 60/60 原版战斗及全部边界覆盖。版本确认后推进隔离实验槽位、战斗
单步与受控场景初始化，不能把菜单连通标成 P1-03 或第一阶段完成。
GitHub 认证没有恢复证据，本轮保留本地进度提交，不重复触发失败的推送认证。
验证补充：新 Python 文件 Black 检查通过，状态 JSON 与 34 个 README 本地链接/锚点
通过；完整 audit_acceptance.py 仍以预期退出码 1 返回上述版本错误和 60 个缺失场景。

2026-10-23 首次 Windows 本机 HTTP 成功：用户完整回传配置输出 port=21526，
以及绕过代理的 GET / 和 GET /api/v1/singleplayer JSON。根路径 status=ok，
状态为 menu/main、lab_protocol=1。运行时 game_assembly_sha256 与服务器重新
计算的 sts2.dll SHA-256、原始 Windows 报告和 Mod 构建记录全部一致。这确认
本次主菜单读数来自匹配引用的桥接运行，证据来源仍明确为用户提供的终端响应。
原始回传保存在 artifacts/windows/local-main-menu-user-transcript.json，指纹核对
保存在 local-main-menu-check.json；不把手工保存的回传当作服务器直接采集。
lab_action_ready=false 符合主菜单状态；源码只在战斗玩家出牌阶段允许动作。
lab_settled=false 表示本次读数尚未满足 250ms 稳定观察窗口，不据此判网络错误。
服务器检查仍只有 8765 监听，18526 无监听，故请求用户建立独立 SSH 反向隧道
18526 -> Windows 21526 并保持游戏主菜单。未发送任何 POST 或游戏动作。
本轮同步 README 的编译/主菜单状态，保留服务器隧道、运行时语义版本独立核验、
战斗单步、可重复初态和 60 场原版验收未完成的边界；不能将指纹匹配等同于版本门
或战斗一致性通过。GitHub 认证仍无恢复证据，本地提交保留。
验证：状态/证据 JSON、README 本地文件链接和 git diff --check 通过；无核心代码
变更，不重复运行模拟器或合成 HTTP 测试。历史超时记录继续保留。

2026-10-23 端口释放进展：用户按上一轮 Windows 15526/21526 监听检查反馈
“现在没有输出了”，记录为游戏关闭期间两端口无监听的用户报告；此前 Code.exe
占用已解除到可以继续配置的程度，但尚未验证游戏启动后的 HTTP 服务。
服务器本轮只读复查：8765 监听且 /api/health 返回 ok、original_game_verified=false；
18526 无监听，旧反向隧道已不占用服务器入口。证据
artifacts/windows/ports-released-check.json 区分用户报告与服务器直接检查。
下一步保持游戏关闭，备份 STS2_MCP.conf 并设置整数 port=21526，再从 Steam
启动至主菜单，验证本机根路径和单人状态。成功后使用独立 SSH 命令重建
Linux 18526 -> Windows 21526 及面板 8765 转发；旧 Windows 接入脚本默认仍指向
15526，不能用于本次新端口连接。无需重传引用、重编译或重新安装 Mod。
本轮只同步状态/证据；JSON、git diff --check 校验通过，不重复运行代码测试。
配置写入、游戏 HTTP、隧道映射均尚待用户执行；原版参考集仍为 0/60。

2026-10-23 用户补充确认：游戏已关闭；Windows 127.0.0.1:15526 和
127.0.0.1:21526 均由同一 PID 44400 / Code.exe 监听。证据汇总在
artifacts/windows/both-ports-owned-by-vscode.json，来源为用户 PowerShell 输出和
明确的游戏关闭说明。21526 的占用者已知；具体转发条目、自动/手动/扩展来源仍待核对。
下一步保持 21526 迁移方案，在实际远程 VS Code 窗口的工作区设置关闭
remote.autoForwardPorts、remote.restoreForwardedPorts、remote.forwardOnOpen，
再在 Ports 按本地转发地址停止 15526 和 21526 对应条目，确认端口释放后继续配置。
仓库 .vscode/settings.json 已增加上述设置，范围仅为本项目工作区；若打开的是
父目录或其他工作区，需要用户在实际窗口设置。已有转发不会因设置自动删除，
扩展仍可显式建立转发；不能仅凭设置文件改动就声称 Windows 占用已经解除。
本项目使用独立 SSH 隧道，上述设置不控制该隧道；未关闭其他转发、强杀进程、
修改全局配置或重装 Mod。游戏配置当前内容仍未回传，迁移尚未执行，原版仍为 0/60。
参考 Microsoft 官方 Remote SSH 文档与 remote.contribution.ts 设置定义，链接见
README.txt。GitHub 认证仍无恢复证据，保留本地提交，不重复调用失败的凭据服务。
本轮校验：工作区设置/状态 JSON、接入包生成与逐文件哈希、git diff --check 均通过。
两个 PowerShell 脚本没有改动；不重复运行与本次配置/文档无关的测试。

2026-10-23 换端口尝试反馈：用户运行上一轮提供的 PowerShell 配置代码，触发
“21526 已被占用”保护检查并退出。按回传代码执行顺序，本次尚未读取、备份或写入
STS2_MCP.conf，也没有由该代码重建隧道；不能记为已迁移到 21526。新监听者的
PID/名称/地址尚未知，不能把 15526 的历史 Code.exe 身份套用到 21526。
证据 artifacts/windows/port-migration-blocked.json，来源为用户终端输出。
已请求一次性收集 Windows 15526/21526 当前监听地址、PID、进程名/路径、现有
配置内容，并确认游戏是否关闭。先区分编辑器转发、仍运行的游戏或其他服务，再
确定释放端口还是选择空闲端口。未终止进程、改全局 VS Code 设置或重装 Mod。
本轮只更新证据与状态；JSON 与 git diff --check 校验通过，不重复运行代码测试。
原版仍为 0/60；GitHub 认证阻塞尚无恢复证据，本地提交保留。

2026-10-23 用户选择换端口：采用 Windows 游戏端口 21526，Linux 桥接入口保持
18526、面板保持 8765。此前“先解除 VS Code 的 15526 占用”不再是本轮必要前置，
但新端口是否空闲须由 Windows 实测；不能将端口迁移规划记为已经修复。
已核对实际编译输入 .tools/bridge-src/McpMod.cs：LoadPort 读取 Mod 同目录的
STS2_MCP.conf，JSON 整数属性 port 可配置；不需要改 DLL 或重新安装。独立 SSH
隧道须同步改为 Linux 18526 -> Windows 21526，旧隧道由用户 Ctrl+C 正常关闭。
Connect-Windows.ps1 增加 -GameBridgePort，默认 15526 保持现有安装兼容；拒绝
越界端口和与本地面板冲突的 8765。该参数只改 SSH 目标，不修改游戏配置。
项目设置排除 21526 自动转发，README.txt 与接入包新增迁移和恢复步骤。为当前已
上传/已安装环境提供直接 SSH 命令，不要求重传 DLL，也不覆盖原始版本报告。
尚待用户关闭游戏、检查新端口、备份/修改配置、重启及重建隧道，再读 HTTP 状态。
仍无原版状态或战斗证据，参考集 0/60；GitHub 认证阻塞尚无恢复证据。
验证：tests/test_windows_scripts.py 通过（1 个 pytest 包装测试；PowerShell 在
Linux 模拟 SSH/SCP/Steam），覆盖默认/自定义转发、非法/冲突端口拒绝、安装与失败
回滚保留端口配置。证据 artifacts/windows/port-migration-tests.xml。接入 ZIP 已
重建并校验文件内容；JSON 和 git diff --check 通过。未重跑不相关的模拟器测试。

2026-10-22 端口拥有者已确认：用户回传 Win32_Process 显示 PID 44400 为 Code.exe，
与此前 Windows 127.0.0.1:15526 的监听 PID 一致；这是当前明确的端口冲突。
用户日志显示 [STS2 MCP] Instant Mode checkbox injected into settings，游戏已到主菜单；
只证明部分 Mod 初始化执行，不能证明 HTTP 服务已启动。日志末尾的手柄 InputMap
报错与超时尚无已证实的因果联系。证据汇总在 artifacts/windows/port-owner-conflict.json。
固定上游的 Initialize 在 HttpListener.Start 失败时打印 [STS2 MCP] Failed to start；
本轮请求用户从完整日志筛选桥接信息，以补足启动时错误。Code.exe 很可能来自端口
转发，但具体 VS Code 条目、远程/本地映射及是否导致本次绑定失败仍待确认。
下一步：保存筛选日志，正常退出游戏，在 VS Code Ports 中按本地转发地址停止
127.0.0.1:15526 对应条目；保留独立 SSH 接入窗口。确认 Windows 15526 已无监听者
后从 Steam 重启，先验证本机根路径和单人状态，再验证 Linux 18526；不发送游戏动作。
本轮增加项目级 .vscode/settings.json，排除 15526/18526 自动转发，更新 README.txt
与接入包说明。设置只在本项目作为工作区时应用，不关闭已有、手动或恢复的转发，
不修改用户全局配置；当前 Windows 冲突尚未解除验证。未改 Mod 或游戏输入配置，
未重编译、杀进程或修改防火墙。原版状态/单步/完整战斗仍未取得，参考集仍为 0/60。
验证：JSON、项目级设置范围、接入包生成脚本语法和 ZIP 文件集合/清单哈希均通过，
两个 PowerShell 脚本与源文件逐字节一致，git diff --check 通过；未重复运行完整测试。
这些检查仅验证本轮配置与说明，不能替代用户解除占用后的 Windows HTTP 验证。
GitHub 认证阻塞尚未收到恢复证据，保留本地提交，不重复触发已失败的凭据服务。

2026-10-22 本机端口诊断后续：用户回传 `127.0.0.1:15526` 处于 Listen，拥有者
PID 为 `44400`；显式设置 `HttpWebRequest.Proxy = null` 后根路径请求仍在 5 秒超时。
记录于 `artifacts/windows/local-listener-timeout.json`，来源明确为用户终端输出。
这排除了该请求使用系统 HTTP 代理作为唯一解释，但不能仅凭端口监听确认拥有者
就是游戏或 Mod。已请求 `Win32_Process` 的名称/路径及本次 `godot.log` 末尾 150 行，
先区分端口被其他程序占用、桥接启动失败或 HTTP 处理未响应；根因仍未确认。
服务器面板与 18526 仍监听，未反复探测已确定超时的接口，未改防火墙/URL ACL、
未终止进程、未重编译或替换 Mod；等待进程身份和启动日志后再做针对性修复。

2026-10-22 最新诊断：用户报告主菜单显示 `v0.107.1`、`2026.06.18`，与配置目标一致。
这比最初的“2026.6.19 默认公开版本”描述更具体，记录为主菜单人工读值；不把显示
日期擅自视为 DLL 编译时间。独立证据 `artifacts/windows/user-reported-release.json`
关联本轮 Build ID 和上传指纹，但明确标记未采集截图/运行时版本。未改写原始报告、
DLL 版本字段或已安装 Mod 的构建报告；当前验收器仅认识 DLL 文件/产品版本，仍需
建立与实机运行指纹绑定的版本证据，不能靠改目标标签绕过验收。
重启后服务器根路径与单人状态 GET 仍超时，见 `artifacts/windows/restart-probe.json`。
用户随后反馈 Windows 本机 15526 的两个 Invoke-RestMethod 请求也超时，说明不能
只归因于 SSH 转发；尚缺端口监听和明确禁用代理后的检查，未确定根因。
已请求用户在游戏主菜单、隧道保留时运行 Get-NetTCPConnection 和 Proxy=null 的
只读 WebRequest。未修改防火墙、URL ACL、权限、游戏设置或 Mod，未发送动作。
后续如需启动日志，开发者官方说明给出的 Windows 路径为
`%APPDATA%\SlayTheSpire2\logs`：
<https://steamcommunity.com/app/2868840/discussions/0/798968342700463372/>。
本机已编译来源中 HTTP 根路径不等待游戏主线程，故本机根路径结果有助于先分离
HTTP 启动/监听/代理问题；不要在取得日志前假定为主线程卡住或 URL 权限错误。

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

- 协议 `0.3.0`：`sts2lab/contracts.py`
- C# NativeAOT 模拟器和只读观测导出：`native/`
- Linux 模拟器、snapshot/restore、`sample_world` 与父分支记录：`sts2lab/simulator.py`
- 共享环境与能力拒绝契约：`sts2lab/environment.py`、`docs/ENVIRONMENT-CONTRACT.md`
- Gymnasium `combat-entities-v3` 与项目 token 词表：`sts2lab/gym_env.py`、`config/content-v1.json`
- 随机和可解释启发式策略：`sts2lab/policies.py`
- FastAPI + 无构建步骤浏览器面板：`sts2lab/server.py`、`web/`
- Windows 原版异步适配器与桥接：`sts2lab/original.py`、`sts2lab/bridge.py`
- 主菜单只读连接检查及独立证据输出：`scripts/check_bridge.py`、`sts2lab/bridge_check.py`
- 发行信息与 DLL 提交/校验值绑定：`sts2lab/release.py`
- 轨迹哈希链、语义重执行和比较器：`sts2lab/traces.py`、`sts2lab/parity.py`
- 参考重放与验收矩阵：`sts2lab/reference_replay.py`、`sts2lab/acceptance.py`
- Windows 接入和安装脚本：`scripts/Connect-Windows.ps1`、`scripts/Install-Windows-Mod.ps1`
- 原版异常动作归档、断线确认、暂停和回放
- `ARCHITECTURE-PLAN.txt`：完整架构、路线和阶段边界

### 当前可核查证据

历史基线与本轮检查分别保留；局部复查不代表重跑全套：

| 证据 | 结果 | 说明 |
| --- | --- | --- |
| Python 测试 | 123 passed | `artifacts/interface-boundary-regression-tests.xml`；含模拟 PowerShell 流程，非 Windows 实机 |
| 模拟器面板浏览器检查 | 6 passed | `artifacts/browser-checks.json` |
| 合成原版接口面板检查 | 5 passed | `artifacts/original-dashboard-synthetic/report.json` |
| 开发集模拟器基准 | 60 episodes / 980 decisions | `artifacts/benchmark-development.json` |
| 进程采样测量 | 9 rounds / 2,700 episodes / 44,100 decisions | `artifacts/sampling-protocol03-development.json`；2c25a99，含硬件与计时边界 |
| 全新检出安装 | 113 passed / 1 optional skip；300 次公开轨迹一致 | `artifacts/repro-2c25a99-comparison.json`；同一 Linux 主机，提交 2c25a99，新依赖和新二进制，非逐字节复现 |
| 桥接与只读诊断测试 | 12 passed | `artifacts/windows/bridge-check-tests.xml`；合成 HTTP，未重跑整个项目测试集 |
| 原版主菜单 | 7 项检查通过 | `artifacts/windows/bridge-check-20261022T165923467279.json`；服务器经隧道直接采集，仅 GET |
| 发行版本 | v0.107.1 关联核验通过 | `artifacts/windows/release-verification.json`；原始报告不改写 |
| 版本验收器测试 | 16 passed | `artifacts/windows/release-gate-tests.xml`；合成证据，只验证校验器 |
| 首次真实出牌探针 | 9 项检查通过 | `artifacts/windows/one-step-probe-20261022T171722625580.json`；第 1 层防御牌，不计入固定基准 |
| 验收矩阵 | incomplete | 版本门通过；60 条原版 battle case 全部缺失 |
| 面板实机与完整战斗 | 未验证 | 原版场景准备、完整闭环与逐步一致性仍待实现/验证 |

运行验收状态：

```bash
cd /user/chenzk/sts2-lab
.venv/bin/python scripts/audit_acceptance.py
```

目前预期返回非零：发行版本核验通过，60 条原版参考及要求的边界覆盖仍缺失。

## 当前阻塞与下一项动作

当前关键路径是受控第 2 层场景准备，再将原版适配器接入面板。安装、隧道、发行版本
和一次第 1 层真实出牌探针已经通过，不需要用户继续上传文件。游戏目前停在槽位 2
首战出牌后，SSH 窗口保持打开；接手先读取当前状态，勿重放导航脚本或重复动作。
新受控场景 Mod 尚待 Windows 安装并重启到主菜单；需要核对运行指纹，不能仅凭
原版桥接旧端点仍可读便提交初始化请求。

以后返回主菜单时可重做只读连接检查（当前战斗状态不会通过该菜单检查）：

```bash
cd /user/chenzk/sts2-lab
.venv/bin/python scripts/check_bridge.py
```

第一执行单元仍为 P1-01 → P1-03；版本核验已完成。新存档首战楼层与基准不同，
P1-04 的场景准备需要提前解决，不能通过修改当前战斗楼层标签绕过检查。
随后完成范围内状态读取、面板出牌与结算确认、回合结束、暂停/断线及完整战斗，
再验收重复初态和随机对齐、扩充 60 场参考集，不要求用户手工拼凑场景。
完整安装和端口排障步骤保留在 `README.txt`。Linux 可继续推进 P1-02 边界和
P1-06 接口证据，但不能因此跳过实机验收。

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
| 2026-10-23 | 用户隧道连接后继续验收 | 服务器直接读取原版主菜单并保留证据 | 7 项只读检查与 12 项相关测试通过；发行信息文件待上传；战斗 0/60，尚无游戏动作 |
| 2026-10-23 | 用户上传发行文件并询问阶段 | 确认版本并推进首次真实动作 | 版本关联与 16 项测试通过；槽位 2 的第 1 层防御牌探针 9 项通过；仍处 P1-03，基准要求第 2 层，参考集 0/60 |
