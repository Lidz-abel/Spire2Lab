# Spire2Lab：新会话接续入口

核对日期：2026-11-18，Asia/Shanghai。本页只保留当前摘要；历史与失败见
[PROJECT-HANDOFF.md](PROJECT-HANDOFF.md)。旧摘要可从Git历史读取，不必全量加载日志。
进程、端口、Windows安装及远端SHA必须实查，不能沿用旧PID或“已推送”描述。

## 当前任务与结果

用户已要求推进E4。模型适配/面板入口/只读审计已实现，见docs/RL-DEPLOYMENT.txt及
docs/course/E4-EXECUTION-PLAN.txt。固定部署E3 seed42/update8，config/rl-deployment-v1.json。
首批51项针对性、完整306项回归通过（有重叠，不相加）；公开结果docs/RL-E4-RESULTS.json。
三类seed3模拟演示30动作，编码/模型审计/重执行一致；另历史原版48公开观测兼容，
不是新实机执行。浏览器模拟演示9动作、10帧回放，零修改请求/JS错误、手机无横向溢出。
浏览器attempt1因测试脚本速度选项错误返回422（0动作），修正后attempt2通过，失败保留。
证据根artifacts/rl-mvp/deployment/e4-20261117/。桥接只读探测失败ConnectError，实机仍待
Windows配合；恢复命令artifacts/handoff/20261117/LOCAL-RESUME.txt已改为迁移后路径。
8766服务已启动，PID2628732，源码ff80df0；server-run.json/server.log在上述证据根。
当前模拟会话finished，单幕idle；服务保留等待Windows，核对PID/命令后用SIGTERM停止。
初始urllib健康探测受代理影响失败；httpx(trust_env=False)直连状态和健康正常。
11.18完整启动日志已收到：artifacts/windows/logs/startup-20261118-003437.log，
同目录diagnosis.json记录SHA/大小；16929字节，服务器SHA已计算，尚未与Windows源比对。
日志明确运行v0.111.1，旧Mod目标v0.107.1；ReflectionTypeLoadException缺少
MegaCrit.Sts2.Core.Entities.Multiplayer.LobbyPlayer，0个Mod加载成功。
用户补充只读核对：release_info为v0.111.1/cc1f9462，递归仅列出原路径的sts2.dll，
9757184字节、SHA 3fb1fa1bf0249087b706a5d0f062a60579e2f5b08df4ee477ddd6f2607f654d5。
与此前同路径a1f9e6…不同，更新发生时间未知；不再假设另有旧目录/新布局。
新版三份DLL及release_info已收到并隔离在artifacts/windows/version-probes/v0.111.1-20261118-input01/。
receipt.json核对sts2哈希/大小及发行JSON，另外两份DLL仅有服务器SHA。较早missing检查保留。
完整旧桥接副本编译7错误1警告；元数据确认RunRngSet.Seed由uint变ulong，Rng公开Seed/Counter
移除、随机数保存格式变化，以及大厅接口变化。旧实验契约不可直接移植，不只是重编译。
详见docs/WINDOWS-V111-PROBE.txt，私有compatibility-summary.json保存诊断和旧文件不变核验。
已独立实现只读诊断Mod，包artifacts/windows/probes/v0.111.1-readonly-02/，0警告0错误。
其SHA80cf809bcebc9d272711c30a9450bf714e629044ff7a1ede9e7d474ae58b0428。
01因Environment同名编译失败保留。3项相关测试通过（合成游戏真实HTTP+Windows mock），非实机。
探针只GET，lab_protocol=0、无控制能力，不能用于PPO/整幕；旧控制器应拒绝，禁止放宽校验。
用户已安装探针并称Mod正常；但GET /probe超时。随后确认21526再次由Code.exe/PID49180占用，
绕代理curl仍5秒零字节，启动日志明确RuntimeProbe.Initialize的HttpListener.Start异常32。
“Loaded 1 mods”不是HTTP启动成功；初始化捕获异常后仍会被游戏列为已加载，未自动重试监听。
证据readonly-02/windows-feedback-port-conflict.json；先前timeout记录保留。
下一步退出游戏、保存工作后退出所有VS Code窗口，在独立Windows PowerShell确认端口空闲，
再从Steam重启游戏并GET /probe；无需重装。Windows端口当前是否释放仍待用户核验。
进一步调查发现服务器VS Code remoteagent.log在01:31/01:33/02:16/02:19多次记录
Failed to connect tunnel to localhost:21526 / ECONNREFUSED。结合Windows Code.exe占用，
强烈支持错误正向转发Windows21526→Linux21526；正确是Linux18526→Windows21526。
本项目.vscode/settings.json已关闭自动/恢复，但父目录/user/chenzk/sts2无该配置；
实际打开的工作区与转发创建来源仍未知。不要把自动恢复候选原因写成已证实根因。
证据readonly-02/vscode-forwarding-analysis.json。下一步在持有转发的实际VS Code窗口
查21526对应行/来源及有效设置，删除该转发；关闭所有窗口仅作定位，不要求永久不用VS Code。
不要运行Connect-Windows.ps1覆盖冻结assemblies/report；不要重装旧v107控制包。
模型/native/旧Mod包与冻结引用未改；v111规则及控制适配需后续独立验证。当前槽位未知。
最新用户输出确认21526再次由Code.exe占用（Windows PID49180）；
如再次占用只停止对应转发，不杀整个编辑器。本轮实查8766 PID2628732监听，18526/8765无监听。
E4两个实机门仍未执行；不重跑E3、不改single-act-v1。兼容恢复后再核验版本/实例/profile2/菜单。
用户要求后续日志备份到服务器、控制Windows存储。scripts/Upload-Windows-Logs.ps1
直接上传、不额外本地复制，唯一目录及双端SHA校验；见docs/WINDOWS-LOGS.txt。
该脚本仍只有mock证据；本次日志由用户手工scp上传。不自动删本地源或批量清理。

E3三次CPU训练和全量分析已结束，seed41/42/43各32768转换，总98304；训练进程均退出。
公开结果[docs/RL-E3-RESULTS.json](docs/RL-E3-RESULTS.json)，入口[docs/RL-E3-TRAINING.txt](docs/RL-E3-TRAINING.txt)，
配方[config/rl-e3-v1.json](config/rl-e3-v1.json)，解释[docs/RL-E3-ANALYSIS.txt](docs/RL-E3-ANALYSIS.txt)。
证据根 `artifacts/rl-mvp/experiments/e3-20261115-v1/`，各run.json记录源码/命令/PID；
所有尝试共用budget.jsonl，不得新建目录绕预算。每seed额度已用尽，不再追加训练。
末次模型均60/60验证胜，HP依次68.05、67.55、68.10；启发式76.55，RL未超越。
末次HP跨seed均值67.90、样本标准差0.30；验证选模HP69.83±1.24，不能当独立测试。
全部转换边界、27份checkpoint重载、3×512动作/首更新精确离线重放通过；9个低HP
案例回放哈希一致，额外108验证转换；容量诊断另186有效转换/187动作，不计训练。

seed43-attempt1训练0步，初始对照40胜19负1错误。slimes-weak/20015经过186有效
转换，第187次动作后抽牌堆65张，超过64张编码容量；独立诊断复现，证据保留。
[amendment1](config/rl-e3-v1-amendment1.json)是在观察失败后登记的修订，仅允许
seed43-attempt2复用同原始文件/同权重的初始对照并继续原预算训练。未改编码/奖励/用例。
该seed初始HP及前后差为null，三seed主要HP比较不完整；不能称E3无条件验收通过。
训练中和训练后验证仍遇错即停，失败不记作战败、不删除或以成功重跑覆盖。
seed41初始HP61.43→68.05；seed42初始0胜/HP0→60胜/67.55，保留逐seed结果。

E3事前94项、修订92项及后续6项检查有重叠，不相加。合成检查不代替实际模拟器学习。
无新依赖，E1/E2核心、native/Mod未修改，未使用GPU。最终测试300例仍封存，原版新增证据0。

## 目标与课程期限

个人Build Track，以工程实现为主，强化学习是新增重点，最终目标为原版自主完整通关。
四项顺序保留：采样可靠性 → 搜索改进 → 原版画面 → 完整单幕。前三项仅限范围通过；
第四项实现已在，但普通原版整幕尝试仍0。第一幕是中间门，不是完整通关终点。
当前只有starter训练模型，没有全游戏训练环境、已验收原版模型部署或分层RL训练。
姓名李东泽，学号241240041，Git邮箱241240041@smail.nju.edu.cn。

| 截止 / 时间段 | 交付 |
| --- | --- |
| 11月16日23:59 | 1–2页Proposal |
| 11月30日23:59 | 2–3页Milestone Report + 初步结果/Demo |
| 12月8–14日 | 结果完善、进度检查、范围冻结 |
| 12月21日23:59 | Slides、代码快照、Demo/结果材料 |
| 12月22–28日 | 4分钟展示 + 1分钟问答，场次待公布 |
| 12月28日23:59 | 4–6页PDF报告、完整代码/说明、结果、视频、最终Slides |

Proposal个人版 `artifacts/course/proposal-20261116-personalized/241240041_proposal.zip`
已生成并核验两页/打包；源docs/course/proposal.html，说明docs/course/PROPOSAL-BUILD.txt。
用户于11.17确认Proposal已经上传；按用户确认记为已提交，不再作为待上传事项。
具体上传时间与平台回执未独立核验，不据确认日期推断是否逾期。
披露既有工作、外部依赖和AI辅助，准备离线回放与备用录屏。Milestone工作包见
[docs/course/MILESTONE-PLAN.txt](docs/course/MILESTONE-PLAN.txt)，E4原版部署/整幕门及E5报告待完成。

## 工作区、环境与交付

- phase2：`/user/chenzk/sts2/sts2-lab-phase2`，分支`phase2/search-hierarchy`。
- 第一阶段：`/user/chenzk/sts2/sts2-lab`，main `f9faf0a`，源码/包版本保持不变。
  两目录共享后者.git；已修复worktree指针，迁移不能只复制phase2的.git文件。
- 独立`.venv-rl`，`.venv`指向它；Torch2.14.0/CUDA13.0，完整锁requirements-rl.lock。
  禁止旧bootstrap.py按base-only锁删RL依赖。E0为同机缓存恢复，不称独立冷安装。
- 主机128逻辑CPU、377GiB内存，不等于独占。GPU0有错误，仅GPU1通过E0数值核验，
  GPU2/3未核验；E2/E3用CPU单Torch线程，E3同时最多一个学习器、4环境worker。
- 用户持续提交/推送授权有效；Git身份为上述姓名/邮箱，全局配置未改。
  origin fetch HTTPS，push `ssh://git@ssh.github.com:443/Lidz-abel/Spire2Lab.git`。
  repo-local SSH使用现有密钥、代理和.tools/git/github_known_hosts固定指纹；迁移需核对路径。
  私钥不入Git、不经聊天传递。E3修订源码49348a6、分析源码f3edbed；最终交付查收据及远端。
- E2收据在其证据目录delivery.json；E3交付收据同名。实际HEAD用git log与ls-remote核对，
  不把本地提交称为推送，不把旧收据当后续HEAD证明。第一阶段main未做新的推送或合并。

## 已完成证据索引

| 项目 | 入口与边界 |
| --- | --- |
| E0 | docs/RL-ENVIRONMENT.md；环境/CPU/GPU1数值、65项工程检查，不是训练或实机验收 |
| E1 | docs/RL-MVP.md、config/rl-mvp-v1.json；公开编码/PPO/奖励/划分冻结，124项相关检查 |
| E2 | docs/RL-E2-RESULTS.json、docs/RL-TRAINING.txt；9984转换、14次checkpoint重载、独立恢复及1/2/4worker，额度仅余16 |
| E2效果 | 同60验证例所选RL60胜/HP69.47，启发式60胜/76.55，随机52胜/31.27；不证明泛化/原版收益 |
| 原版/搜索 | PHASE1-STATUS.json、PHASE2-STATUS.json、docs/PHASE2-EXECUTION.md |
| 采样/搜索细节 | docs/BELIEF-V2-VALIDATION.json、docs/SEARCH-V2-HELDOUT.json、docs/PLANNING-V2-RESULTS.md |
| 原版图片 | docs/DECISION-IMAGES-VALIDATION.json；真实starter一场11步/12图，不是整幕 |
| 单幕门 | docs/SINGLE-ACT.md、docs/SINGLE-ACT-VALIDATION.json、config/single-act-v1.json |

训练环境seed10000–10999，验证20000–20019，最终测试30000–30099，各乘三种遭遇。
旧搜索seed1–10/1001–1010/2001–2030已使用，不能重新称未触碰保留集。
E2主源码bc277f4，恢复/短测1811ccf；E3各run.json保留干净源码与兼容指纹。
原单幕策略为公开启发式、0模型调用；搜索分层未证明额外收益，不能混称已训练策略。

## 版本与端口：恢复前必须核对

2026-11-18实查8766监听，8765/18526无监听。上传日志显示Windows运行v0.111.1，
与冻结v0.107.1不兼容；用户同路径新版DLL哈希与服务器接收一致；只读探针待安装及读回。

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

## 下一步与必须保留的约束

1. 核对本页、AGENTS、PHASE2-STATUS、E3结果和delivery.json；E3训练不重跑。
2. E4先核对原版连接及模型适配范围，保留原冻结单幕门。Windows需要安装/重启/SSH配合；
   本机命令在artifacts/handoff/20261115/LOCAL-RESUME.txt，RemoteRoot旧路径必须先修正。
3. 执行前验证live game/Mod哈希、实例、profile2、菜单及结算，不能凭过去“已重启”判断。
   单幕沿用ACT001/002/003顺序、最多1200动作、Ironclad/A0、正常种子、槽位2、shouldSave=false。
   保留真实路线、奖励、购买、休息/升级、战斗，连续击败第一幕Boss且绑定证据完整才能验收。
4. 策略只用公开观测/历史，不给实际seed、RNG、隐藏牌序/原版快照。未知输入拒绝；动作只
   提交一次，结果不确定先读取核对。禁止调试跳层、改资源通过验收或将人工接管算自主。
5. 保存全部失败，使用scripts/audit_act.py审计；合成UI、离线/模拟器测试都不是实机证据。
6. 会话结束更新当前状态、下一步、阻塞、进程、依赖与远端交付；只处理本轮已确认进程，
   不清理用户既有环境。按任务读必要入口，避免每次重载全部历史/日志。

Git不保存被忽略的模型、轨迹、台账、DLL、截图和环境；迁移需单独私有备份两个工作区
的artifacts、.tools、环境及上游资源，并核对共享链接。旧handoff代码bundle不是全部数据备份。
来源见CODE-PROVENANCE.md；README英文，修改前读PROJECT-IDENTITY.md。不得提交私有游戏
文件或凭据。E3训练不解除原版整幕门，未完成完整通关前不得标记总体目标完成。
