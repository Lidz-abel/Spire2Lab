# Spire2Lab：新窗口接续入口

核对日期：2026-11-19，Asia/Shanghai。本页保持短摘要；详细现状见
[项目总结](docs/PROJECT-SUMMARY-20261119.md)，历史见[PROJECT-HANDOFF](PROJECT-HANDOFF.md)。
按需查证据，不全量加载旧日志；服务、端口、Git远端及Windows状态必须现场核验。

## 当前用户任务

用户要求总结最终目标和当前能力，并用grill-me式逐题追问，为新窗口重建上下文。
未找到grill-me技能文件，已说明采用逐题追问方式。Q1用户于11.19回答“要求完整自主通关”：
截至12月28日原版完整自主通关是课程硬指标，第一幕只作中间门，不能默认降级。
Q2已问是否接受战斗RL＋局外规则/搜索，还是全部决策由RL主导；用户先要求说明差别，
尚未选择。两种均要求无人代替决策；现有starter模型均不足以直接完整通关。
继续解释后等待Q2选择，再按总结第7节追问验收条件，不一次抛出大量问题。
本轮不启动新训练、不修改游戏或探针、不尝试实机动作。

## 不变目标与已实现程度

个人Build Track，工程实现为主，强化学习为重点，最终目标原版自主完整通关。
原四项顺序：采样可靠性→搜索改进→原版画面→完整单幕。前三项有限范围通过；
普通原版整幕尝试0，PPO原版部署战斗0。第一幕不是完整通关终点。

E0/E1限定验收完成；E2实际9984转换。E3三seed各32768、共98304转换，预算用尽。
末次模型在同60验证例均60胜；HP67.90±0.30，低于启发式76.55。seed43初始容量错误
使主要前后对照不完整，失败及修订保留。300个最终测试用例仍封存，不追加旧预算训练。
E4适配/模型审计/模拟器部署和面板已实现；三场模拟30动作，历史48观测只做离线兼容。
完整306项回归通过；模拟器浏览器9动作/10帧。均不是新增原版模型执行证据。
当前只有固定starter范围模型，单幕原策略为公开启发式；没有全游戏或分层RL训练。
部署模型固定E3 seed42/update8，SHA及选模偏差在config/rl-deployment-v1.json和E4结果中。

## 当前阻塞与下一步

1. 旧证据与模拟器冻结v0.107.1；Windows已更新v0.111.1/cc1f9462，新DLL已隔离接收。
   旧桥接对新版编译7错误；种子uint→ulong、随机数保存格式及大厅接口变化。
   不能继承旧版规则/可复现性验收，不能只放宽哈希或覆盖冻结引用。
2. 新版只读探针readonly-02编译通过，用户日志显示Mod加载，但HTTP监听因Code.exe
   占用Windows21526失败。lab_protocol=0，无游戏控制能力，不允许生产控制器绕过拒绝。
3. Windows PID49180属Code.exe；服务器日志有VS Code错误连接Linux同号端口的记录。
   用户指出助手运行似乎重建已删除转发，工具输出触发是可能原因，具体创建事件未证明。
4. 本会话根目录/user/chenzk/sts2原无防转发配置；已新建.vscode/settings.json，关闭
   autoForwardPorts、restoreForwardedPorts、forwardOnOpen，并忽略桥接端口。
   文件值已核对；实际VS Code窗口生效、端口不再重建、探针HTTP成功均尚未验证。
5. 下一步先完成访谈/范围确认；恢复操作时请用户保存并Reload Window，移除残留转发，
   端口空闲后重启游戏，从独立Windows PowerShell只读核验探针。不要反复要求重装。
   避免远程终端回显Windows接口URL，不在Linux本机访问Windows游戏端口。
6. 诊断连通后再登记版本策略、控制接口和规则再验证，分别执行starter RL实机门与正常整幕门。
   不运行会覆盖旧report/assemblies的Connect-Windows.ps1，不重装旧控制包到新版游戏。

## 工作区、服务、环境、交付

- 根/user/chenzk/sts2；项目/user/chenzk/sts2/sts2-lab-phase2；分支phase2/search-hierarchy。
- 第一阶段/user/chenzk/sts2/sts2-lab固定main f9faf0a，保持源码/环境；两worktree共享Git元数据。
- 11.19只读监听检查：面板8766仍监听，PID2628732；8765/反向入口18526无监听。
  本轮未做HTTP健康探测，不沿用旧会话finished/act idle作为最新状态。停止前核验PID/命令。
- Windows游戏端口21526；正确方向Linux18526→Windows21526。仅面板需要转发到Windows。
- 使用.venv-rl；旧bootstrap.py可能移除RL依赖，不运行。GPU0异常，仅GPU1做过E0核验；E3用CPU。
- 用户要求日志存服务器、控制Windows占用。直接上传脚本Upload-Windows-Logs.ps1，不额外复制日志。
- 私有artifacts、.tools、模型/DLL/截图/轨迹/环境不在Git；根.vscode配置也不在phase2 Git。
  迁移必须另行保存，源码推送或bundle不能冒充完整资产备份。
- 总结初稿与此前积压提交已推送，11.19已核对远端6f8eda3；后续访谈提交需另核对。
  本轮提交与推送结果看artifacts/handoff/20261119/delivery.json，并实际核对远端，禁止混称。
- 用户持续提交/推送授权有效；姓名李东泽，学号241240041，提交邮箱241240041@smail.nju.edu.cn。

## 课程日期与验收边界

Proposal已由用户确认上传，不能重新标待上传。下一截止11月30日23:59：2–3页Milestone+Demo。
12月8–14日冻结范围；12月21日23:59交Slides/代码快照/Demo；12月22–28日4分钟展示+1分钟问答；
12月28日23:59交4–6页报告、完整代码/说明、结果、视频、最终Slides。课程资料来自用户说明。

原冻结整幕门ACT001/002/003、最多1200动作、Ironclad/A0、实验槽位2、shouldSave=false。
当前槽位未知；执行前核验实例/版本/槽位/菜单。正常路线奖励和第一幕Boss连续完成且证据完整
才算整幕通过。公开输入、动作只提交一次、未知结果先核对、失败全留；不调试跳层或人工接管冒充自主。

主要证据：docs/RL-E3-RESULTS.json、RL-E4-RESULTS.json、SINGLE-ACT-VALIDATION.json；
新版诊断docs/WINDOWS-V111-PROBE.txt，私有version-probes/v0.111.1-20261118-input01和
probes/v0.111.1-readonly-02均位于artifacts/windows。完整导航见总结第8节。
