# Spire2Lab 项目转接文档

更新时间：2026-11-17

2026-11-17 E4离线交付：ff80df0干净源码运行三类seed3模拟部署，9/12/9动作，HP73/
75/72，全部胜；编码逐字段相同、模型审计和模拟器重执行通过。历史三份原版参考共
48个公开观测经原始捕获佐证并完成离线预测，不算新原版模型动作。公开RL-E4-RESULTS.json。
真实浏览器在模拟后端演示PPO9动作，10帧只读回放零修改请求/JS错误，桌面/手机通过。
attempt1测试脚本设置不存在的速度选项导致422、0动作；修正脚本后attempt2通过，均保留。
8766服务PID2628732（操作前重核），server-run.json/log在E4证据目录；原版单幕idle。
初始urllib启动探测受继承代理影响超时，服务实际启动正常，trust_env=False直连健康正常。
服务保留供Windows连接；18526仍无监听，原版只读探测失败已保存。当前无新原版动作、
starter模型实机和普通整幕门均未执行，未声称E4完成。用户Windows操作问题仍待回复。
E3预算哈希不变，模型/训练核心/native/Mod/阶段一不变，无新依赖或正式训练。

2026-11-17 E4启动：用户授权推进。事前docs/course/E4-EXECUTION-PLAN.txt区分starter
模型实机部署与普通连续整幕两个门；不改变原单幕配方、策略或上限。选择E3 seed42/
update8，因已有验证HP最高用于演示，选模偏差披露；无新训练或最终测试。
新增learned_policy/replay、固定配置、审计与部署检查脚本，面板/API增加ppo选项。
只读Observation对象复用原编码，无环境私有数据；checkpoint固定SHA先验核对，历史
源码和当前核心指纹严格匹配。拒绝未知/越界输入，无规则回退；模型/观测/动作记录可审计。
51项针对性及306项完整回归通过（重叠）；部署/浏览器证据待保存，不能预称实机通过。
现有DLL与单幕包本地哈希吻合，但18526连接失败；Windows实装未知。已向用户询问
是否能操作Windows，恢复说明复制到20261117并修正RemoteRoot。本轮不改Mod、不装依赖。

2026-11-17 用户确认Proposal已经上传，课程提交状态改为“用户确认已提交”；具体上传
时间和平台回执未独立核验，不按确认日期判断是否逾期。下一正式截止为11.30 23:59。
本轮仅核对并介绍现状，未新增训练或游戏动作。E3结果/本地分析存在；8765/8766/18526
仍无监听，Windows实装未知。E0–E2完成；E3训练与审计完成但初始对照缺口保留，
E4原版部署和普通整幕验证、E5报告/Demo仍待推进。历史“Proposal待上传”记录仅代表当时状态。

2026-11-15 E3收尾：三次训练分别在干净cfaf367、5d17889、49348a6源码完成，每seed
32768转换/64更新，总98304且预算预留=确认、各seed一致。约300.92/300.30/298.63秒。
末次均60/60验证胜，HP68.05/67.55/68.10，均值67.90、样本SD0.30；启发式76.55。
验证所选update48/8/8，HP69.0167/71.25/69.2167，均值69.8278、样本SD1.2357。
seed43初始错误按修订保留，主要三seed前后HP比较缺失，不给总体平均提升、不称完全通过。
分析源码f3edbed；全98304转换边界、27次checkpoint重载、3×512动作和首更新精确
离线复现通过。9个低HP验证例回放108步，哈希匹配；另容量诊断186有效步/187动作，
公开抽牌堆65张。均不算新训练或保留集评估。20个记录中的父/worker PID均已退出。
公开docs/RL-E3-RESULTS.json、RL-E3-ANALYSIS.txt；本地analysis/summary.json、3份CSV、
27份checkpoint与原始证据保留。SESSION从300行压缩至约125行，历史保留在本页/Git。
端口8765/8766/18526仍无监听，Windows实装未知、原版普通单幕0。无新依赖或GPU，
E1/E2核心/native/Mod不变，main f9faf0a干净。下一项E4适配与实机恢复，E5报告仍待完成。
11.16 Proposal上传回执仍未知，11.30 Milestone截止不变；本轮不启动百万步/保留集。
最终交付以E3证据根delivery.json与远端SHA核验为准，不能用前次推送推断新HEAD。

2026-11-15 E3修订1：seed41/42各完成32768步及离线边界/首更新复现审计。seed43
attempt1初始验证40胜19负1错误；slimes-weak/20015第186步后超过固定牌区容量，
训练0步。原始失败保留，amendment1绑定两份原文件与初始模型哈希；只允许attempt2
复用不完整对照，原预算内训练，不扩大编码/删除用例/补值。三seed主要HP对照不完整。
训练后验证依旧严格遇错停止；历史checkpoint用各自Git源码绑定，核心兼容性不放宽。
92项针对性检查通过（与先前94项有重叠，不相加）；当前准备提交后执行seed43attempt2。

2026-11-15 E3启动准备：用户要求推进E3。实查资源128逻辑CPU、357GiB可用内存、
558GiB空闲磁盘、load约2；三个服务端口仍无监听。按E2吞吐冻结rl-e3-v1：CPU4环境
单学习器线程，run41/42/43各32768转换，总98304，逐seed顺序执行，每次900秒软限。
新增同初始化未训练对照；主要看固定预算末次相对初始，验证选模结果另列。E1的网络、
PPO、奖励、seed划分不变，最终300例封存，不运行百万步或占GPU。独立预算有按seed
限额及全程锁，失败占用额度，E2台账不动。新入口scripts/train_rl_e3.py --seed 41/42/43；
证据根artifacts/rl-mvp/experiments/e3-20261115-v1，run.json记录PID/argv，SIGINT/TERM
在完整update边界保存退出。预检查94 passed/9.37s；源码提交后再开始训练。
可选资源限制已向用户询问；未收到额外限制，按上述保守CPU方案执行，不请求重复授权。

2026-11-15 E2完成：main-01在干净bc277f4上执行8192有效转换/64次PPO更新，耗时
129.62秒，采样+更新85.77转换/秒；独立resume-01从64更新/8192步恢复后再训256步。
workers2-01/4-01各512/1024步、各2次更新，在干净1811ccf（新增审计脚本）上完成。
总9984有效转换与预算台账预留/确认吻合，总624次minibatch step，无失败学习运行。
14份checkpoint重载证明全部通过，模型/优化器/RNG/probe一致；环境按契约新episode
重启，保留aborted_by_resume。审计全部转换掩码/奖励/episode连续性、正常进程清理，
首128动作及首update参数哈希离线重放精确一致，无新增环境步。所有训练进程已退出。
138项相关测试及后续14项E2复查有重叠，不相加；合成优化器测试不代替上述真实交互。
公开摘要docs/RL-E2-RESULTS.json；本地证据artifacts/rl-mvp/smoke/e2-20261115/含
acceptance.json、budget.jsonl、四个run、完整公开rollout、checkpoint/校验和和曲线CSV。
主运行8次验证按既定规则选update0040（5120步）：60例全胜、平均finalHP69.4667；
同60例启发式60胜/76.55HP，随机52胜8负/31.2667HP，各无截断/错误。RL未超过
启发式HP；仅run41、选模使用验证集、没有未训练策略对照，不称独立泛化或训练净收益。
最终300例仍封存，原版普通第一幕仍0尝试；没有新增Windows/Mod或整幕证据。
README与状态同步训练实现、有限结果和局限；第一阶段工作区/依赖未变，无新包或GPU任务。
下一步是E3事前冻结资源与对照配方，E2预算仅余16，不能另建campaign规避上限；
11.16 Proposal上传回执仍待用户，11.30 Milestone日期保持。私有模型未作为Git文件发布。

2026-11-15 E2实施启动：用户授权推进E2。按已冻结计划实现636898参数ActorCritic、
显式reset采样、GAE/PPO、持久预算台账、含优化器/RNG的checkpoint和验证集评估。
首轮相关测试138 passed/21.16s；加强优化器续训测试和恢复选模后，14项E2复查
passed/8.82s。证据artifacts/rl-mvp/smoke/e2-20261115/tests-attempt1/2.*，不相加。
准备开始main-01的8192有效转换；run.json记录实际PID，SIGINT/TERM在update后退出。
预算台账在同一campaign根，共10000上限，所有恢复/进程短测/失败共用；E3与最终集禁用。
启动前尚无真实游戏学习结果；本实现提交用于固定源码。说明docs/RL-TRAINING.txt。

2026-11-15 下一步规划：用户要求规划E1后的工作；基于已推送9dda564，新增
docs/course/E2-EXECUTION-PLAN.txt，将E2拆为网络、采样、GAE/PPO首更新、保存恢复、
验证/吞吐五步。成功路径8192主运行+256恢复+512二进程+1024四进程共9984转换；
失败重试也计同一10000上限，不能重置预算。算法/种子仍用E1冻结配置，E3禁用。
内部目标11.18前首次128转换更新、11.23前完成E2；课程11.16 Proposal和11.30
Milestone截止不变。用户配合上传回执和Windows时段，服务器E2无需等待Windows。
本轮只规划和更新交接，没有实现训练器、执行训练或新增实机验收；不重复运行代码测试。

2026-11-15 远程推送恢复：用户表示可以推送后实查，HTTPS仍退出128；直接SSH因
DNS失败、agent socket失效且自定义密钥未被默认选择而无法使用。使用现存
id_ed25519_github密钥，经既有HTTP代理CONNECT到ssh.github.com:443，主机Ed25519
公钥按GitHub官方文档及SHA256指纹固定在忽略目录.tools/git/github_known_hosts，
严格主机校验保持启用。SSH认证返回Lidz-abel，推送phase2/search-hierarchy退出0；
独立ls-remote核对95c87e3c4110844ac5d226098ac2928c3221a1be与本地一致，包含E0/E1。
证据artifacts/rl-mvp/contracts/e1-20261115/push-verified-initial.json；此交接提交后
再推送/核对的最终SHA保存于同目录push-verified-final.json。只修改共享仓库本地
remote.origin.pushurl和core.sshCommand，原值保存在git-ssh-config-before.json；
没有修改全局Git/SSH配置、第一阶段源码、课程材料或训练结果。运行配置有本机
路径/代理依赖，迁移后重核。历史失败保留；此结果解除远程交付阻塞，不解除实机单幕阻塞。

2026-11-15 E1推送复查：用户询问为何未推送，实际重试将本地05f12d8推至origin的
phase2/search-hierarchy；退出128：could not read Username for 'https://github.com':
terminal prompts disabled。当前HTTPS身份获取仍失败，未成功推送；证据保存于
artifacts/rl-mvp/contracts/e1-20261115/push-retry-*.json。不能仅凭历史阻塞替代当次
推送实查；后续认证配置恢复后继续推送并核对远端SHA，凭据不经聊天传递。

2026-11-15 E1训练契约完成：用户要求执行E1；以f7eef1a干净工作树开始，核对E0、
课程计划、来源、环境与现有边界。新增docs/RL-MVP.md及config/rl-mvp-v1.json：
公开特征固定缩放与分类embedding、共享候选评分/value规格、原奖励、截断bootstrap、
显式reset、PPO参数、独立种子划分与验证选模、checkpoint恢复边界。训练seed10000–
10999，验证20000–20019，最终30000–30099，每seed三类遭遇；排除所有已用历史范围。
E2目标8192/上限10000有效转换，CPU单worker起步，E3预算disabled；最终集未执行。
新增sts2lab/rl_contract.py检查公开数组、padding/动作引用/掩码与奖励、终局和截断，
拒绝无效no-op/autoreset结果，复制末状态；scripts/check_rl_contract.py静态展开清单。
tests/test_rl_contract.py新增59项，最终含既有65项的回归124 passed/11.89s；首轮
120项通过后补充配置/掩码防护，两个报告不相加。六场starter胜/负边界测试只用旧
开发seed3，另有截断测试；均是模拟器/合成验证，没有策略训练或原版证据。
证据artifacts/rl-mvp/contracts/e1-20261115/，含regression-attempt1/2.xml/.log和
contract-manifest.json；固定配置、源码/文档/依赖指纹及完整3360用例定义。
无新依赖，无native/Mod/第一阶段变更，无长期训练进程；服务/隧道三端口无监听。
E2还需实现网络、collector、GAE/PPO和保存器，用真实模拟器证明非零参数更新与恢复；
不能以E1边界测试替代E2验收。Windows实装和普通整幕仍未知/0次，不改变原四项目标。
GitHub HTTPS认证没有恢复证据；当前工作本地提交，未宣称推送。11.16 Proposal上传
回执仍待用户，11.30 Milestone期限不变。下次先读SESSION-HANDOFF再按E2所需取证。

2026-11-15 E0本地交付：3a4c70b保存环境锁、检查器与接续记录，提交后工作树干净。
一次限时非交互推送origin phase2/search-hierarchy退出128，错误为could not read
Username for https://github.com: terminal prompts disabled；缺少当前可用HTTPS认证。
日志artifacts/rl-mvp/environment/e0-20261115/github-push.log。未推送，远程HEAD未认证；
用户提供的Git作者邮箱只用于提交元数据，不能替代GitHub登录。E0服务器就绪结论不变。

2026-11-15 E0服务器恢复通过：用户提供硬件输出后，当前环境直接确认128逻辑CPU、
377GiB内存、四张RTX4090标签/49140MiB设备；GPU0有异常，本轮只以UUID选择GPU1。
worktree repair修复phase2双向Git路径，四个.tools链接改相对路径；新建独立.venv-rl，
.venv指向它。main仍f9faf0a、源码无diff、安装包清单前后一致，未改系统Python/驱动。
下载代理TLS失败、直连DNS失败；使用同机pip wheels/uv缓存以copy模式恢复65个包，
其中setuptools78.1.0经514个RECORD哈希校验后从另一同机环境复制。记录全部来源，
不称独立冷安装。依赖锁requirements-rl.lock；PyTorch2.14.0/CUDA13.0与pip check通过。
新增scripts/check_rl_environment.py：CPU/GPU1合成前向/反向/Adam测试、numpy桥接，
两份上游源码1383+34文件及native指纹检查；三类starter seed1各跑两次公开轨迹一致，
Nibbit11步74HP、Slimes19步80HP、SludgeSpinner9步77HP。65项相关回归10.40秒通过。
这是依赖数值测试和模拟器证据，未训练游戏Agent、未验证Windows或正常单幕。
证据artifacts/rl-mvp/environment/e0-20261115/，含原链接/Git备份、网络与离线失败、
恢复脚本、包清单、轨迹和测试报告。说明docs/RL-ENVIRONMENT.md；E1–E5待执行。
未启动面板或长期训练，GPU任务已退出；ss未发现8765/8766/18526监听。
当前工作目录/user/chenzk/sts2/sts2-lab-phase2；避免运行旧bootstrap.py把RL依赖同步掉。
历史repro工作树仍旧路径且未清理，不影响当前主工作区。课程Proposal未有上传回执。

2026-11-15 Milestone规划：用户要求规划现在先完成的部分。以8a9cf4f干净工作树为
基线，只读复核Gym、采样、词表、训练边界和依赖；torch未装、phase2旧链接仍失效。
新增docs/course/MILESTONE-PLAN.txt，定义E0环境恢复、E1训练契约、E2最多10000
有效转换的真实模拟器PPO冒烟，作为首批工作；后接E3训练评估、E4原版单幕/模型部署、
E5十一月三十日报告和Demo。给出各项输入、验收、证据位置、外部依赖和时间窗口。
当前只规划，未安装依赖、修改运行环境、训练或执行游戏动作。保留原四项验收顺序和
完整通关目标；基础训练准备不表示第二阶段完成。Windows阻塞时可推进独立Linux
工作，明确缺失实机证据。新训练划分/超参数尚待E1冻结，历史保留集不得重新冒称未见。

2026-11-15 Proposal 个人版：用户提供姓名、学号和Git提交邮箱。已使用提供的信息生成
artifacts/course/proposal-20261116-personalized/下的两页PDF和按学号命名的ZIP，
identity_complete=true、submitted=false；身份信息仅应用到私有生成文件，跟踪模板保留
占位。两页A4、页脚边界、文字提取、个人信息和ZIP完整性已检查；旧草稿目录保留。
已在项目共享Git目录中配置用户指定的作者身份，未改全局配置，解除此前提交阻塞。
本轮保存Proposal源码/导出脚本与累积交接更新，实际本地HEAD需git log核对；远程同步
未验证，不称已推送。课程提交仍需用户审阅并于11月16日23:59前上传，尚无回执。

2026-11-15 Proposal 实际交付准备：用户要求先完成11月16日前任务。本轮已写两页中文
Build Track Proposal，题目“Spire2Lab：面向《杀戮尖塔2》自主通关的强化学习系统”。
内容覆盖场景、课程前基础与新增RL工程、拟采用PPO/动作掩码、环境覆盖扩展、训练与部署、
MVP/最终完整通关验收、独立评估、个人时间表、资源、风险、离线演示及来源/AI辅助披露。
方案中的算法与数值为计划，不作为已运行实验或已证明可行性的结果；未运行训练或游戏。
源文件docs/course/proposal.html；生成说明docs/course/PROPOSAL-BUILD.txt；脚本
scripts/render_course_proposal.py与course_pdf_layout.py。PDF/ZIP/预览/检查结果位于
artifacts/course/proposal-20261116/，保持私有忽略。姓名、学号待用户提供，ZIP暂名
待填学号_proposal.zip；尚未提交课程平台，用户未提供提交链接。GPU/配额尚未确认，
nvidia-smi驱动不可访问，仅按预算写资源，不把宿主CPU/内存总量当独占资源。
浏览器导出受沙箱限制、gi缺Cairo外部类型；改用现有Pango/Cairo原生库，无依赖安装。
两页A4、中文内嵌字体、文字提取、页脚边界、ZIP完整性与逐页预览检查；属于文档验证。
首次页2过长后缩写资源段并规范空白，失败说明保留于PROPOSAL-BUILD.txt。
本轮未修改游戏、训练代码、已有虚拟环境或Git路径，未启动服务；先前暂存交接更改保留。
Git作者身份缺失，暂不能形成新commit；未推送。接续时先收身份信息并生成个人版，
由用户审阅后在11月16日23:59前上传，并保存回执；只有回执才能确认正式提交。

2026-11-15 课程方向与接续纪律更新：用户确认既有个人项目可继续拓展，选择以
Build Track 的工程交付为方向，要求强化学习成为项目新增重点，最终实现原版自主
完整通关。第一幕为中间验收，原四项任务保留；当前训练未开始，整幕仍是公开启发式，
普通原版单幕尝试0。此前讨论的PPO、分层RL、课程训练及RL+搜索仍是候选设计，
须先审计可训练环境范围、实际资源及原版覆盖，再冻结架构和评测配置；不将规划列为成果。
课程截止：11月16日23:59 Proposal（1–2页）；11月30日23:59 Milestone（2–3页及Demo）；
12月8–14日范围冻结；12月21日23:59路演材料；12月22–28日4+1分钟路演；
12月28日23:59最终4–6页PDF、代码、结果、视频和Slides。个人提交、来源及AI辅助披露，
需保留课程前已有工作与新增工作的区分。Proposal尚未制作/提交。
用户明确要求持续交接以控制上下文窗口和环境污染：SESSION-HANDOFF维护短摘要与
证据入口，本文件保留详细历史；按任务查阅，不重复堆入全部日志。环境/配置/输出隔离，
记录长任务、进程、端口、日志和恢复步骤，保存失败，保留既有环境。
本会话实际路径为/user/chenzk/sts2/sts2-lab-phase2；共享Git目录位于其同级sts2-lab。
.git双向指针与.venv仍引用迁移前路径，尚未修复。显式指定Git路径读回本地
phase2/search-hierarchy、410c1a3及干净工作树（本轮文档编辑前）。HTTP三个端口均连接
失败，沙箱ss权限不足，不能宣称完整宿主机监听检查；Windows实装版本仍未知。
本地ff144ee8... Mod和a1f9e653...游戏引用哈希匹配；本轮只维护交接，无新测试、训练、
实机动作或推送。本段与SESSION-HANDOFF新增段优先于下方旧路径及运行状态。

2026-11-15 新窗口转接：用户要求总结并保存接续信息，本轮仅整理文档和备份，未开始
新实验。请先读 [SESSION-HANDOFF.md](SESSION-HANDOFF.md)，再按其中入口查看细节。
本轮实查 phase2 在 phase2/search-hierarchy，整理前 HEAD 67302ae，工作区干净；
第一阶段仍在 main/f9faf0a。两个目录共享第一阶段的 .git，不能只移动 phase2 的 .git 文件。
8765、8766、18526 均无监听且 HTTP 连接失败，无相应 uvicorn 进程；下方历史 PID 和
“服务器保持运行”的描述现已过期。本轮未重启服务或改动游戏。artifacts/act-runs 无轨迹，
普通原版单幕尝试仍为0，完整目标保持blocked/未完成。已有188/4/26项测试报告核对存在且
无失败，属于不同历史运行并有重叠，本轮未重跑或合并计数。当前ff144ee8... Mod包再次
通过清单校验；Windows安装和当前游戏版本仍未知，恢复后需验证。GitHub成功推送未确认。
新摘要保存目标、需求、来源边界、里程碑、证据、版本哈希、恢复与单幕完成门；私有恢复命令、
实际检查快照、代码bundle和证据清单放在 artifacts/handoff/20261115/，保持Git忽略。
该代码备份不包含所有DLL/截图/原始轨迹；换服务器必须另行保留两工作区artifacts等私有数据。
以下均为历史记录，不覆盖2026-11-15实查。

2026-10-25 阻塞审计第3轮：上一goal轮有实际服务器修复（f4ce166），本轮只读核对
仍为18526 Connection refused，ss无该监听，8766 combat closed / act idle / running false，
无pending；artifacts/act-runs为空，正常单幕尝试0。已准备的ff144ee8... Windows包
清单再次校验通过，26项相关测试报告无失败。没有活动的单幕任务可等待，也没有新的
Windows安装/隧道回复；服务器可独立完成的必要准备已完成。不能用重复测试或合成
路线代替真实整幕。因此同一阻塞达到3个连续goal轮，完整目标标记blocked而非complete。
证据 artifacts/single-act/continuation-2-check.json；状态 PHASE2-STATUS.json。
Windows步骤仍是安装已有phase2单幕包、重启至实验槽位2主菜单、恢复18526反向隧道
和8766面板转发。包没有新增变更，已安装该版本则只需恢复连接。收到恢复消息后先验证
真实Mod/实例/版本/槽位，再开始冻结配方的普通完整第一幕，保留所有失败和截图。
服务器PID1538323 / exec58440保持运行且空闲；第一阶段8765仍closed未改。
GitHub远程同步仍未验证，先前网络/写认证问题单独保留。不要把本地提交报告为已推送。

2026-10-25 自动续轮核对：前一goal轮为实质进展；本轮18526仍拒绝连接，Windows
安装/连接请求未有新回复，同一阻塞连续第2个goal轮。此轮修复了已确认到达且
execution_idle的不支持屏幕被一直当作未知结果等待的问题，忙碌/过渡状态仍拒绝确认；
传输异常时保存最近有效私有读取但不生成公开转换。新增3项测试，26项相关测试通过，
包括已有审计和图像门检查。Windows包仍为 ff144ee8...，策略/配方不变，无需新一轮换包。
主实现a8a861c和审计3351c61保持历史检查点；本轮仅服务器控制/证据处理跟进。
服务已按无活动会话条件重载，exec58440，实际PID见 artifacts/single-act/continuation-1.json；
combat closed、act idle，8765仍closed且未改。正常原版单幕尝试仍为0。
无GitHub专用连接工具可用；前次推送的网络/认证问题未有新证据，不重复盲推。
下一步需要Windows新Mod安装并恢复SSH隧道后，验证完整普通第一幕。完整目标仍active；
若下一goal轮同一阻塞仍存在且已没有可独立完成的必要工作，达到第3轮阈值后应标blocked。

2026-10-25 单幕主实现/配方已冻结提交 a8a861c；Windows安装请求已通过异步输入
发送，需关闭游戏、从 phase2 路径安装新 ff144ee8... 包、重启至实验槽位2主菜单，
恢复18526反向及8766面板正向隧道。尚未收到新的安装回复，最近18526仍拒绝连接。
单幕离线审计器 act_replay.py / scripts/audit_act.py 已补齐，4项合成拒绝测试通过，
覆盖未完成/合成证据不能通过、公开观测替换、私有捕获改动、策略目标和请求确认。
它只重读记录，不能称原版重执行或整幕模拟器验证。核心188项测试另有完整报告。
新 a8a861c 推送超过90秒无输出，终止退出143；远程HEAD未确认，私有日志
artifacts/single-act/github-push.json/log。先前写认证失败也没有恢复证据。
当前服务器8766 PID1525929/exec6538，combat closed、act idle；没有游戏动作循环。
完整四项目标保持active，前三项有限门通过，第4项等待安装/连接与真实完整单幕验收。
本轮发生实现、测试和冻结的实质进展；安装等待不能因此标记完整目标完成。

2026-10-25 第4项实现检查点：普通单幕控制、公开协议 single-act-v1、全动作保护与
去重、独立选牌边界、地图/奖励/休息/商店/事件/宝箱/战斗适配、固定公开启发式和
持续目标、轨迹/原版图片/面板回放已实现。规格 docs/SINGLE-ACT.md；配方
config/single-act-v1.json 预登记 ACT001/002/003，冻结后再实机。188 项完整测试通过；
桌面/手机两帧合成图片回放通过，零变更请求/JS错误。公共摘要
 docs/SINGLE-ACT-VALIDATION.json。当前正常原版单幕尝试数为0，不能称完成。
新 Mod SHA ff144ee812218f9a3ffbb7dbdb2f5b1c4d6b750a189180d836b6092f85db41bd
已编译并通过清单验证；需安装 phase2/artifacts/windows/mod 后重启，保留21526配置。
去掉生成副本 GET 自动开商店/宝箱副作用，改为显式动作；未改 vendor 或原版规则。
Windows刚安装的 b6c1a3ab... 属于已验收截图版本，不含本次新单幕接口。
8766已重新加载：PID1525929 / exec6538；启动模拟会话已归档，act idle，无动作。
8765 第一阶段仍为 closed，未改。临时8767合成服务已停止。
最新只读检查18526连接被拒绝，服务器无该监听，需恢复SSH反向隧道；记录
artifacts/single-act/service-check.json。未向游戏提交任何第4项动作。
下一步先提交冻结，发送Windows安装/隧道指令；用户完成后核验哈希、main/profile2、
正常不保存开局，再执行连续单幕并记录失败。整幕策略目前是可解释启发式，0模型步，
不把starter搜索结论推广到整幕。GitHub写认证仍无恢复证据，不能称已推送。

项目地址：<https://github.com/Lidz-abel/Spire2Lab>

当前开发目录：`/user/chenzk/sts2-lab-phase2`（`phase2/search-hierarchy`）。
第一阶段保留目录：`/user/chenzk/sts2-lab`（`main`，`f9faf0a`）。

2026-10-25 第3项实机验收通过：用户已安装并重启，实际 Mod b6c1a3ab...、实例
070a3a1965674ae1816b044992a1a55b、游戏SHA/实验槽位2正确。主菜单3072×1728
PNG可读取。Nibbit/seed1/新分层配置完整11步、12张决策边界画面，最终74HP获胜；
每张图与原始捕获token、实例、版本、run/decision、公开观测摘要和文件SHA一致。
状态逐步对照及策略重放通过；实时桌面/手机和全部12帧回放通过，零变更请求/JS错误。
旧状态token及错误实例请求均409，原版状态和最后动作未变化。
公共摘要 docs/DECISION-IMAGES-VALIDATION.json，私有证据
artifacts/phase2-v2/image-live-battle/20261025T065715193624/。已目视检查主菜单与开局
真实画面；开局可能包含回合横幅，不能称动画完全静止。该战斗已归档，8766仍运行
PID1484278、无未决动作，Windows在实验奖励页。第1、2、3项完成有限门，继续第4项
完整单幕；不把这场调试战斗代替普通单幕验证。前一goal轮属于实质进展，本轮Windows
安装阻塞已解除。GitHub写认证仍无恢复证据。

2026-10-25 截图实现检查点 54eec85 已提交本地。已向用户发送 Windows 安装指令，
RemoteRoot 必须使用 /user/chenzk/sts2-lab-phase2，等待安装并重启；读回仍为旧
Mod 60d7f563...，没有真实截图验收。8766 已加载新代码，PID 1484278 / exec95091，
启动的模拟会话已归档，无未决请求；8767 合成测试服务已停止。私有状态记录
artifacts/phase2-v2/image-service-check.json。第一阶段8765保持原样。
GitHub 登录恢复请求也仍待用户回复，不能称本地提交已推送。

2026-10-25 第3项实现已编译，等待 Windows 安装验收：新 Mod b6c1a3ab...，
完整 SHA 在 PHASE2-STATUS.json。新增只读 post-draw 截图、进程/版本/token 绑定、
PNG 限额/CRC/解压校验、run/decision/公开观测摘要关联，以及实时/回放显示。
175 项全套测试通过；合成图片浏览器检查通过，不能称已采集原版画面。
包在 phase2/artifacts/windows/mod，旧 Mod 在 mod-history/60d7f563...；安装必须
从 phase2 路径取包，现有21526配置无需修改。Windows当前仍是旧 Mod。
新桥接使当前 phase2 验收缓存失效；此前60+1审计原件另存
artifacts/phase2-v2/search-ui-historical-audit.json。第一阶段目录/证据保持不变，
不得把旧 Mod 的参考集当成新 Mod 实机证明。第4项仍未开始实现。

2026-10-25 第 2 项有限战斗验证完成：选择冻结 f2bc4c7 后，新保留集 2001–2030，
5 条件 × 90 场 = 450 场全部获胜，450 次环境重放和 27 次策略重放通过；加开发集
共 660 次环境、42 次策略重放。预选 HP32/1024 平坦与分层均 77.94 HP，heuristic
77.03，提升 0.91；低预算旧效用32/256 为 78.08。后者略高，不因此改选配置或继续
在该保留集调参。分层无额外收益；见 docs/PLANNING-V2-RESULTS.md 与
SEARCH-V2-HELDOUT.json。不得把该有限 HP 改善说成胜率/全游戏/训练改进。
新原版验证 4 场通过：平坦新配置在三遭遇 seed1、分层在 Nibbit seed1，共49步逐步
对齐且策略重放通过，未截图。全部归档，8766 PID1462967 / exec45729 保留运行，
无未决动作；8765 未改。原版最新处于已完成的非保存实验奖励页。私有报告
artifacts/phase2-v2/live-summary.json；168 项全套测试、随后4项评测分片测试及新的
交互/原版语义回放浏览器检查均通过。临时8767测试服务已关闭，历史60+1再次重审通过。
面板显式采用公开条件采样、HP效用、深度32/预算1024/2秒软限；Python旧默认保留，
新旧确定性评测与交互软限结果分开。下一项真实画面规格 docs/DECISION-IMAGES.md
已写；尚未实现或安装。第1、2项有限验收已通过，第3、4项及完整目标继续。

2026-10-25 搜索开发对照已完成：7 条件 × 30 场 = 210 场，全部获胜，210 次环境
重放、15 次完整策略重放通过。固定实现 075f47b。HP：heuristic 76.53，depth8/256
71.27，depth32/256 77.97，depth32/1024 78.33，HP 效用平坦/分层均 78.57。
选择 HP 效用、depth32、1024 calls 的平坦搜索为主要配置；分层保留为独立消融，
目前没有额外收益证据。低预算 depth32/256 作为成本对照。新配方
config/phase2-search-selected.json；公共开发摘要 docs/SEARCH-V2-VALIDATION.json。
168 项全套测试通过。新保留集 2001–2030 尚未运行；先提交冻结再运行。
评测脚本新增预登记种子的确定性分片，减少等待；不改策略/规则，合并时必须覆盖每例
且不重复。阶段 2/四项目标仍未完成。第一阶段 8765 服务归档、Windows 为实验奖励
页面且已结算；阶段 2 的 8766 仍停止，下一次启动将使用新 native。

2026-10-25 第 2 项开发实验已登记：config/phase2-search-ablation.json 共 7 条件，固定
public_opening，对比 depth 8/32、预算 256/1024、旧效用/HP 连续尺度效用、平坦/分层。
新效用针对旧评分“已获胜”与“未到终局”之间过大的跳变，不据此先宣称有效。开发
仍用 1–10；新保留集预登记为 2001–2030，当前未运行。选择优先胜负/无截断，再看平均
终局 HP，最后同效时比较模型工作量。新实验脚本支持条件筛选且不会合并同预算的不同
深度/效用条件；23 项相关测试通过。先导正在 artifacts/phase2-v2/search-pilot/。
第 1 项提交 f94a5c0；推送已越过此前 TLS 故障，但现为 GitHub 写认证失败：
No anonymous write access / Authentication failed；SSH 只读探测另为 DNS 失败。
证据 artifacts/phase2-v2/github-step1.json/log 和 github-ssh-check.log。不能称已上传。

2026-10-25 第 1 项已达到预登记开发回归门：新增独立公开条件开局工厂，仅条件化已知
敌人初始 HP 与手牌，未知牌序另采样，未改动 actor 或转换后结果。60 条固定公开历史、
975 决策的成对回放：旧方法开局 44/60、耗尽 309/975；新方法开局 60/60、耗尽 29/975
（2.97%，低于事前 5% 门）。仍非精确后验、不是所有局面零回退。摘要
 docs/BELIEF-V2-VALIDATION.json，原始对照 artifacts/phase2-v2/belief-development.json。
164 项全套测试通过，另新增条件采样策略的隐藏状态非干扰检查；旧 60 场原版参考与
1 探针已为新库重新生成候选并重审通过，原始捕获未变。新 native SHA
6321ca69c3ac6024d069f00b683d698523d8b22819609ee0044f078492856131；旧库在 .tools/native-history。
第二阶段服务在归档状态下已停止，以免旧进程混用新库；第一阶段 8765 保留。
接下来进行第 2 项深度/效用/战术目标消融。旧评测配方仍默认 seed_rejection；新方案
须显式 belief_proposal=public_opening，完成选择与新保留集验证后再更新面板默认。

2026-10-25 当前目标：用户明确要求按顺序完成四项：1 采样可靠性；2 搜索决策改进；
3 原版决策画面；4 地图/奖励/休息/商店与单幕控制。完整目标持续有效，不因单项完成
而结束。执行规格与逐项证据要求见 docs/PHASE2-EXECUTION.md。当前开始第 1 项，
保留 64f34eb 基线，先量化公开开局拒绝原因，再实现独立条件提议；不得向规划器提供
实际执行 seed、快照、隐藏牌序或 RNG，也不得改写真实结果来通过比较。

2026-10-24 最新交接（优先于下方历史）：第二阶段首个 starter 搜索/分层基线已实现并评测，
整个第二阶段尚未完成。实现与评测配方冻结提交 2f36503；计划提交 3ca7dc4。
新增 belief/planning/hierarchy/planning_replay、运行器与面板，源码/模型指纹随轨迹记录。
152 项全套测试通过；桌面/手机、完整战斗、覆盖动作终止目标、暂停及零变更回放通过。
完整 development 180 + heldout 180 场全部完成；360 轨迹重执行、24 搜索策略重执行通过。
所有配置每个 split 都赢 30/30，但没有优于 heuristic：heldout heuristic HP 76.50；
分层 64/256 预算 HP 71.53/71.67。Slimes 粒子常耗尽，回退计入统计；不能宣传搜索提升。
公开完整摘要 docs/PHASE2-VALIDATION.json，讨论 docs/PLANNING-RESULTS.md。
已看过的 heldout 1001–1010 不再作为下一次调参的未触碰保留集；新迭代预登记新 split。

新增原版分层搜索冒烟通过：Nibbit / seed 1 / policy_seed 773 / 256 calls / depth 8 /
无墙钟截止，9 步全对齐，68 HP 获胜，零回退，9 次决策重执行一致。使用原有已验证 Mod，
只在实验槽位 2 的不保存场景执行，未改写游戏/规则/随机数来拟合结果；未采集原版截图。
证据 artifacts/phase2-live/20261023T170930347979/report.json；不会并入第一阶段 60 场索引。
同一工作树还重审通过旧 60 场+1 探针，artifacts/acceptance/status.json；有限旧证据与新
冒烟分开，不等于全部搜索动作已原版验证。第一阶段目录/源码/服务未改动。

原版 9 步语义/搜索回放另已通过浏览器检查：零变更请求、零 JS 错误；首次检查脚本
误用 #runs 选择器，失败记录保留，改为实际 #run-list 后通过；未修改产品代码。

当前第二阶段面板 PID 981147，端口 8766，exec session 67980，日志
artifacts/phase2-dashboard-frozen.log。最新原版会话已归档，无未决动作/自动执行；可以在
面板回放 9 步原版搜索轨迹。Windows 无需再次安装 Mod。第一阶段仍为 8765 / PID 633440。
完整评测已退出；没有后台采集循环。以上 PID 仅为交接快照，重启后须核对。
GitHub 分支推送 2f36503 退出 128：gnutls_handshake / TLS connection non-properly
terminated，未进入有效上传/远程 HEAD 确认；日志 artifacts/phase2-github-push.log。
当前各里程碑是本地提交，不能报告已上传；没有索取或记录令牌。

下一步优先解决公开条件采样的命中率/粒子存活，再用 development 单独消融 rollout
效用与目标控制；同时按 P2-06 准备决策边界原版画面绑定，随后增量单幕契约与参考例。
P2-07 单幕、P2-08 独立复现/远程交付仍待完成，训练属于第三阶段。不要重新做第一阶段
60 场采集或把本轮工程可运行称为整个第二阶段验收通过。详细入口 docs/PLANNING.md。

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
当前工作：用户于 2026-10-24 要求进入第二阶段。第一阶段本地验收通过，历史远程交付仍待同步。

2026-10-24 第二阶段首个实现单元：公开历史粒子、根动作 rollout 搜索和持续战术目标
已接入实验控制与实时/回放面板；不读取实际环境种子、快照或隐藏 RNG。新增来源与
预算协议见 docs/PLANNING.md。152 项测试通过（PowerShell 正确路径为
.tools/powershell/bin/pwsh），桌面/手机 UI 通过。第一次全套因测试工具路径写错失败，
日志保留；不是代码跳过测试。18 场种子 1 先导及策略/环境重执行通过，但搜索并非
总优于 heuristic；不据此宣传提升。固定评测使用深度 8、预算 64/256、无墙钟截止，
与交互默认深度 12/2 秒分开。下一个提交冻结实现与配方，再跑完整 development/heldout。
第一阶段 1179 个私有证据文件按哈希复制到新目录，60 场+1 探针重放通过；首次审计
因 vendor 符号链接越过项目边界而拒绝，已改用固定源码的实体副本，未弱化路径检查。
当前 native 和 Windows Mod 无变更；旧原版证据不代表新搜索策略已实机验证。
新实现和测试应从 phase2 工作树运行；8766 为新面板，8765 仍保留旧工作树。

2026-10-24 第二阶段已开始：工作树 /user/chenzk/sts2-lab-phase2，分支
phase2/search-hierarchy。原 /user/chenzk/sts2-lab 保留第一阶段已验收源码与运行环境。
先按 docs/PHASE2-PLAN.md 实现只使用可见历史的粒子采样、预算 rollout 搜索、战术
目标与面板记录，再冻结配置做基线/消融。原版截图和单幕扩展仍是第二阶段独立验收项。
实时状态见 PHASE2-STATUS.json；不得把第一执行单元称为整个第二阶段完成。
依赖复用原安装，native 二进制/清单及生成副本复制到新工作树，不称新环境冷安装。

2026-10-23 远程交付结果：本地验收提交 ac59b44 已生成。默认推送及单次 HTTP/1.1
重试均因 gnutls_handshake / TLS connection non-properly terminated 退出 128，尚未
上传，不能称阶段完整交付。此前 HTTPS 只读核对远程 main 仍为 0a5c869；SSH 探测
另因 DNS 失败。当前推送未到认证，因此历史写认证故障也没有恢复证据。无需重复
安装游戏 Mod 或重新采集 60 场；修复 GitHub 连接后从本目录 git push origin main，
再用 git ls-remote origin refs/heads/main 核对与本地 HEAD 一致。日志和结构化结果
见 artifacts/github-final-delivery.json。工作区保留标准面板 PID 633440，无采集进程。

2026-10-23 最终本地验收摘要（本段优先）：60/60 固定原版战斗与单独的
probe:live-loss-recovery 均通过，9/9 类边界覆盖，最终审计无错误。Nibbit、Slimes、
Sludge Spinner 各 20 场；公开状态比较、原始捕获哈希和独立模拟器重执行全部通过。
报告 artifacts/acceptance/final-phase1-audit.json；公开有限摘要 docs/PHASE1-VALIDATION.json。
原始捕获/DLL/存档不入 Git，摘要本身不能让新克隆获得“已验证”状态。范围不外推到
全游戏、隐藏 RNG 或未独立测量的卡牌数值；原版画面、搜索、层级策略与训练仍属后续阶段。
固定采集批次已结束，最后一场实验已归档，没有未决动作或仍运行的采集循环。
标准面板服务保留运行，用户可以查看已记录决策和回放；无需再次安装 Windows Mod。
最终服务/浏览器检查：验收 API 为 verified_scope，health 原版验证 true、全局一致性
false，页面显示“限定参考集已通过”，无 JS 错误或变更请求；报告 final-service-check.json
位于 artifacts/acceptance/。固定矩阵共 975 决策，额外探针 12 决策，分开统计。
73 个文档相对路径/锚点、公开摘要中的 61 个 case 及源码/审计哈希均检查通过。
本地技术验收完成，P1-08 的远程交付仍需核实 GitHub 连通/写认证和实际远程 HEAD。
此前最新行为测试检查点为 4f8447b（133 通过）；之后为文档与接入包说明更新。
独立重建、共享主机采样、控制探针与下载的具体证据见 docs/LIVE-VALIDATION.md。

2026-10-23 分项检查点：Nibbit 与 Slimes 各 20/20 完整参考通过，Sludge Spinner
剩余用例继续按固定队列采集。矩阵总进度以状态文件为准。仍为同一 Mod 与 native
行为版本；后续提交仅更新文档/接入包说明。GitHub SSH 只读探测因 DNS 解析失败
退出 255，尚未进入认证；不据此推断 SSH 凭据是否可用。证据 artifacts/github-ssh-connectivity.json。

2026-10-23 当前交接摘要（优先于下方历史）：结算 Mod 已实机验证，游戏无需重装。
当前 native 为 1ef77a847010c7c0590f2c610da26c711dc5d636649df5afea6f61e9c64a005d，
源码检查点 4f8447b。固定 60 场矩阵正在继续；实时已通过数量见 PHASE1-STATUS.json
的 live_reference_progress 和 artifacts/acceptance/status.json，不用下方历史计数。
新增 12 步原版控制探针通过，所有 9 类覆盖已齐：受控丢弃一次真实动作回执后 GET-only
恢复，重复请求缓存/旧决策拒绝无额外 game POST，执行中暂停阻止下一动作，人工覆盖
有记录，真实 HP 0 战败不回血，桌面/手机回放无动作或 JS 错误。此探针不是自然断网，
单独登记 probe:live-loss-recovery，不能替代 60 场中的任何一场。报告
artifacts/live-boundaries/20261023T085145678089/report.json，说明 docs/LIVE-VALIDATION.md。
第一次探针因开局无 Defend，在发动作前停止，失败报告保留；第二次选择实际存在的
Strike 后完成。标准服务现 PID 633440 / session 56479，加载当前 native。固定批次
PID 621267 / session 68770 在两个用例间暂停以进行此探针，完成后恢复；实际调度
报告仍为 artifacts/live-batches/20261023T083526929967/report.json，首差异自动停止。
当前版本独立复现已补齐：原独立安装目录升级 4f8447b 并重新构建，132 通过、1 可选
PowerShell 跳过，300 场/4875 决策公开轨迹一致，二进制不同；不是另一次冷安装。
主目录 133 测试通过。1/2/4 workers 九轮 2700 场/43875 决策一致，测量与实机采集
及部分构建重叠，不作独占吞吐宣称。证据 artifacts/live-compat-reproduction.json。
实机轨迹下载补验通过：浏览器下载与归档字节相同、哈希链有效、12 条转换，零变更
请求。证据位于该探针目录的 download-check.json。使用说明和接入包文案同步当前
状态，修正“安装脚本自动启动 Steam”的错误描述；包内容与 SHA 检查通过。
GitHub 写认证尚无恢复证据；本地 commit 不等于已上传。第一阶段暂不标完成。

2026-10-23 六个先导用例均通过（历史检查点）：三种遭遇 × 两种策略、seed 1，全部完成原版
捕获与独立重放。Sludge Spinner random 第 15 步曾暴露胜利后 Weak 1 未清除，失败
报告 artifacts/live-cases/20261023T083121680034/report.json 保留；仅补 starter 胜利
时清除战斗能力，没有改写捕获。最新 native 为
1ef77a847010c7c0590f2c610da26c711dc5d636649df5afea6f61e9c64a005d，133 项全套测试通过。
所有 6 条 candidate 已针对新库重新生成并审计，目录
artifacts/acceptance/revalidated-20261023T083501459263；当前 6/60、覆盖 8/9（仅缺 lost）。
先前批次已在首个差异停止，新的固定剩余 54 例在
artifacts/live-batches/20261023T083526929967/report.json 逐场记录。服务在原版完成会话
归档后重启为 PID 621175 / session 81683，已加载最新 native；游戏无需重装。
独立检出目录已升级 e48eedb 并重建旧 cc60 修正对应版本，尚未升级本次 powers 修复，
不得把那次独立构建当成最新版本复现通过。GitHub 写认证仍未恢复。

2026-10-23 种子 1 先导对照完成：Nibbit heuristic/random、Slimes heuristic、Sludge Spinner
heuristic 共 4/60 完整原版轨迹通过，覆盖 8/9，仅缺 lost。最新 native 为 cc60ed03...，
132 项全套测试通过；补充原生源码清单/生成文件指纹验收失效检查，相关 19 项测试通过。
剩余 56 例已按既定矩阵排队，逐步比对、单次提交、首个差异停止；当前私有运行器为
artifacts/windows/run_remaining_cases.py，进度记录 artifacts/live-batches/。不可自动
把批次启动或模拟器测试视为完成。

2026-10-23 结算修复实机生效与首场完整对照（最新进度）：用户报告重新加载后，
已核实实际 Mod 为 60d7f563...、新实例 e1b21206ada744d48766562b005c9043、实验槽位 2，
execution_idle_v1 正常。证据 artifacts/windows/settlement-reloaded-20261023T080740976086.json。
新开局 scenario-20261023T080752516781.json 匹配，浏览器前 6 步通过，之前 Defend
过早结算已不再发生。第 7 步原版 Nibbit 格挡 5、上游模拟器 6；后续 GET 仍稳定为 5。
已按 docs/NATIVE-COMPATIBILITY.md 规格修正生成副本，原始 vendor 未改；本机 DLL
只读 getter/枚举确认该招 A0 为 5，ToughEnemies（8）起为 6。修正是上游派生兼容工作，
不能称为独立规则引擎。原始输入、生成输出、转换/构建脚本指纹均随 native 清单记录。

同一原版轨迹继续到第 11 步胜利，发现 arena API 没有运行层 Burning Blood 回血：
原版 68→74，模拟器保持 68。新增 native/LabCombat.cs 胜利生命周期适配，参考原版捕获
及固定 RunRewardGenerator，只在胜利 transition 补一次封顶回血，不触发奖励选择/RNG，
不改写原版捕获或按原版 HP 赋值。11 步重新独立重放通过；不可变参考文件
artifacts/acceptance/references/nibbits-weak-1-heuristic.jsonl 已登记，证明报告
artifacts/live-dashboard/20261023T081506924270/victory-comparison.json。首次 audit 为
1/60、覆盖 5/9、errors=[]；第 1 场的原版 run_id 为 50c9dc0a33c745f59fef3f0fcc5e84d1。
首次胜利边界版本 native d0fe8859...，131 项回归测试通过；失败报告仍保留，七步旧
报告对应的原始 trace 前缀已按 SHA 精确保存，没有替换中间态。

随后固定 random / seed 1 / policy_seed 773 的原版战斗完成 17 步；前 16 步匹配，
终局原版剩余格挡清零，arena 仍为 5。证据 artifacts/live-cases/20261023T082235837426/report.json，
run_id a79d9f1762c44e469b996c6d35bc137f。胜利清格挡修复已完成，新 native 为
cc60ed03d210843f76f35c565b20066a0cc8029e6b4fde74dce034bfbce16a66。两场 candidate
均重新生成、完整对照通过，验收 index 原子更新为 2/60、覆盖 5/9；证据
artifacts/acceptance/victory-cleanup/*-comparison.json。132 项回归通过、1 项既有警告。
Windows 无需重装。服务 PID 614003 / session 53679 在第一场之后重启，仍加载 d0fe...；
原版会话可继续，下一次切换模拟器前需归档并重启加载 cc60...。两场已归档，继续核对
Slimes 固定开局。GitHub 写认证无恢复证据。

2026-10-23 可重复开局与逐步实机验收（最新状态，优先于下方历史）：用户再次重启后，
已确认 Mod 93e1cc5c... 正在运行、游戏指纹匹配、主菜单/实验槽位 2 正确。可变模型
修复已实机生效。nibbits-weak / seed 1 两次独立初始化均达到固定第 2 层开局，公开
观测、私有牌序及命名 RNG 前后快照重复一致；证据 repeated-opening-seed1.json 和
scenario-20261023T073425321785.json、scenario-20261023T073740714856.json 在
artifacts/windows/。这只证明该种子/遭遇的开局，不能扩展为全套 RNG 或战斗一致性。

随后通过真实浏览器面板执行 Bash、Strike、end_turn、Defend，共 4 步；原版 run_id
为 33c7740c8a904cd394a58e3f7e1e3faf。前两步匹配，第三步发现 Nibbit Slice 在原版
显示 Attack + Defend，而固定模拟器仅导出 Attack；上游已执行对应格挡，故仅在
native/LabExports.cs 补公开副意图，不改规则、RNG 或隐藏数值。新 native SHA 为
1a24569fc418c34e3cd5427dc94eb8afe8ea1289ae79ace7a7c58729a88c7140，旧库已归档；
独立重放前三步匹配，但因不完整仍拒绝通过。证据 artifacts/windows/nibbit-intent-analysis.json
和 artifacts/live-dashboard/20261023T074035521068/corrected-partial-comparison.json。

第四步 Defend 暴露桥接过早确认：捕获弃牌堆 5 张，稍后同一请求的 GET 已为 6 张。
立即停止并保留中间态，没有改写原始捕获；整条四步轨迹已 archive，不能计入参考集。
证据 artifacts/live-dashboard/20261023T074617146880/report.json、artifacts/windows/
after-defend-settling-20261023T074708346882.json 与 early-settlement-archive.json。

新增结算门：游戏队列为空、执行器空闲且无当前动作、出牌区为空、手牌动画结束，
之后状态 token 继续稳定至少 250 ms 才确认。忙碌期间的静止时间不计入；执行事实
仅为私有桥接元数据。SettlementGate.cs 是本项目实现，实际生产类通过合成时间线
测试；API 及 IsRunning getter 用本机 DLL 只读元数据核实，未在 Linux 执行游戏代码。
新 Mod SHA 60d7f563611013b31d46438c5b03cfb99765b6ef00fecd28f0732bb62a38257a，
编译 0 错误、1 项既有上游警告，构建/来源/发行绑定验证通过；125 项全套测试通过、
1 项既有依赖警告。证据 artifacts/windows/settlement-build-verification.json 与
artifacts/settlement-regression-tests.xml。新 Mod 尚未实机验证，已请用户关闭游戏、
运行原安装脚本并 Steam 重启到主菜单/槽位 2。下一步核对上述 SHA 和 execution_idle_v1，
重新初始化并采集新完整战斗，不能恢复已归档的失败轨迹。上一次安装操作本身成功。

服务在归档后已安全重启，PID 603656 / exec session 44151，加载新 native，默认暂停
模拟器；证据 artifacts/settlement-service-restart.json。验收仍 0/60、9 类覆盖全缺，
errors=[]，见 artifacts/acceptance/settlement-status.json。旧性能/复现报告保留原构建
绑定，不自动继承到新库。GitHub 写入认证仍无恢复证据，未声称远程更新成功。

2026-10-23 新 Mod 实机接入与首次初始化失败（优先于下方历史）：用户报告安装并
重启后，直接读取确认运行 DLL 为 6de822b9db90892337ff0c00f08aae023f2fd4d192b12c8292315e5dd723268c，
游戏指纹匹配，进程已更换，主菜单/槽位 2/场景能力正确；7 项只读菜单检查通过。
证据 artifacts/windows/restarted-mod-20261023T071130936391.json 与
bridge-check-20261023T071154498270.json。此前“新 Mod 未安装”的阻塞已解除。
随后仅提交一次 nibbits-weak / seed 1 初始化请求。游戏报告非保存运行、初始牌组
和 12 个命名 RNG 流初始化成功，但创建战斗时抛 CanonicalModelException：
本项目把共享 canonical 遭遇模板直接传给 CombatRoom，而接口要求可变副本。
明确失败，不是结果未知；未发出牌/结束回合动作，也未将失败初态或楼层算作通过。
完整报告和日志 artifacts/windows/scenario-20261023T071207228987.json/.jsonl
保留，包含一次请求、一次回执及 13 次状态读取。游戏最后报告第 2 层地图状态，
这是部分初始化残留，必须重启后重新开始，不能从该状态继续填补通过记录。
已将 EncounterModel.ToMutable() 与 AssertMutable() 移到启动实验之前，记录
encounter_model_type/mutable；API 由本机 DLL 元数据确认，用法参考固定上游
McpMod.Debug.cs，来源说明已更新。旧产物按 SHA 归档，新包编译 0 错误、1 项既有
上游警告；57 项相关测试通过、1 项既有依赖警告。构建/来源/发行关联验证通过。
修复包 SHA 为 93e1cc5c0d903d9b2bd23731e8ed7e9baccf47edb5e7daba7290bef601ee15bd，
证据 scenario-mutability-build.log、scenario-mutability-build-verification.json、
scenario-mutability-regression-tests.xml 均在 artifacts/windows/。这不是修复实机
成功的证明；已请用户关闭游戏、再次运行原安装命令、Steam 重启到主菜单后继续。
验收门重算仍 errors=[]、0/60，缺全部 9 类覆盖；第一阶段未完成。勿重新提交旧
失败请求、勿沿用旧包指纹；收到安装反馈后先核对新 SHA、进程和槽位，再做固定种子。

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
