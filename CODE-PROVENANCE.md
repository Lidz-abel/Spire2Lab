# Spire2Lab 代码来源说明

更新时间：2026-10-25

本文件记录工程来源与依赖边界。“本项目新增实现”指在本项目中编写的代码，包括 AI 辅助编写的适配、验证和实验工具；这项分类本身不构成逐行原创性审计或科研创新结论。游戏内容、上游代码与参考资料各自记录来源。

## 开发原则：原创优先

用户于 2026-10-22 明确要求：“我们的平台尽可能是原创的，可以参考开源的实现。”

平台核心优先由本项目设计和实现，覆盖环境抽象、实验控制、搜索规划、分层决策、
训练调度、评测和面板。通用计算库、Web 框架和环境接口可以继续使用。

每个新模块先写需求、输入输出、信息边界和行为用例，再参考开源设计并记录来源。
如果直接复制、移植、翻译或改写上游实现，归类为派生实现；新文件、提交记录、
变量改名、不同语言或 AI 辅助编写均不能单独证明独立实现。

此前已阅读过上游实现，应保留这段来源历史。当前没有完成逐行原创性审计，
也不宣称洁净室实现。自写工程实现与算法新颖性分别评价；后者需要基线、消融和结果。

## 依赖迁移计划

下面是实施顺序；当前生产路径仍使用表中列出的上游依赖。

| 工作项 | 当前证据 | 后续实施与完成标准 |
| --- | --- | --- |
| O-01 平台核心 | `sts2lab/`、`web/` 中已有本项目新增实现 | 维护本项目协议与控制逻辑；新增搜索、层级决策和训练核心自行实现并记录参考 |
| O-02 Python 绑定与内容数据 | `simulator.py` 导入上游 `sts2_gym.native/names`；`catalog.py` 加载其名称与生成数据 | 先定义可替换的后端和内容目录边界，再独立实现调用层；卡牌事实、名称与测试素材继续标明来源 |
| O-03 最小原版桥接 | `build_bridge.py` 复制并修改 STS2MCP，加载 `McpMod.Lab.cs` 扩展 | 取得本机 DLL 后，按公开状态、主线程执行、请求确认需求设计独立桥接；实机单步与完整战斗通过后切换 |
| O-04 有限战斗引擎 | `native/Sts2Lab.csproj` 编译上游规则与本项目导出扩展 | 从第一阶段初始牌组和三个遭遇逐项建立规则规格，再实现独立状态转换；先验收模块，满足完整范围后才作为默认后端 |
| O-05 搜索、分层与学习 | 已新增公开历史粒子、预算 rollout 搜索、持续战术目标及评测；尚无 RL 训练 | 继续报告固定预算、消融及原版证据；不把工程实现称为算法创新 |

替换验收必须覆盖合法动作、结算顺序、信息边界、快照/分支隔离、复现性、性能测量
及原版参考轨迹。上游模拟器保留为对照后端；最终行为依据来自原版采集。
源码独立性与行为正确性分开验收，新的实现不能继承旧引擎的验证结论。

第一阶段继续按原有有限战斗范围与真实游戏要求推进。完整游戏规则重写不是本轮
追加的第一阶段交付条件；独立后端替换进度另行记录。当前 O-02 至 O-04 尚未实现。
三个阶段路线见 `ARCHITECTURE-PLAN.txt`（three-stage-v1）：阶段 1 落实核心边界与来源，
O-02 至 O-04 随实机证据逐步替换；阶段 2 实现搜索/层级核心，阶段 3 实现训练调度
及搜索学习衔接。任何阶段都不把当前上游引擎改称独立实现。

## 来源分类

### 第二阶段方法与阅读记录（2026-10-24）

2026-10-25 决策截图：先写 docs/DECISION-IMAGES.md，参考 Godot 官方 Viewport /
RenderingServer 文档及 Godot 4.5 RenderingServerDefault 的 post-draw 分发方式，并检查
固定 STS2MCP 的 HTTP 分发与主线程队列。新增 bridge/McpMod.Images.cs、
DecisionImageBoundary.cs、sts2lab/images.py 与面板/控制集成均为本项目编写；没有
复制 Godot 实现。桥接仍编译固定 STS2MCP，保留上游许可证。图片来自运行时视口，
不由平台绘制或冒充原版；目前仅编译和合成测试通过，实机安装/截图证据待补。
PNG 格式检查使用 Python 标准库，校验 CRC、尺寸、解压边界和哈希。源码与测试按
合成/实机证据分开，图片和游戏 DLL 不入 Git。

2026-10-25 条件开局提议：先写 `docs/PHASE2-EXECUTION.md`，再检查固定模拟器的
`NativeExports.NativeCombat`、`CombatState`、`CardInstance`、`EnemyDef.HpBand` 与
`CombatFactory.CreateEnemy`。新增 `native/LabBelief.cs` 与
`Simulator.from_public_opening` 是本项目编写的适配/提议实现；使用上游状态类型、
初始模型和 HP 范围，并按上游无放回初始 HP 规则验证公开约束，不能称为独立游戏引擎。
只在新建的独立 starter 世界中约束已公开 HP 与手牌，剩余牌序使用独立提议随机数。
不改变实际执行环境，不在已执行转换后复制原版结果；潜在 AI/未来 RNG 仍来自独立
世界，近似分布的限制保留。没有改写 vendor 源码。新库已归档旧版本并重放旧参考集。

先在 `docs/PHASE2-PLAN.md` 记录输入、输出、预算、失败与隐藏信息边界，再实现本项目
`belief.py`、`planning.py` 和 `hierarchy.py`；没有移植外部搜索框架源码。
算法背景参考 Silver 与 Veness (2010) 的
[Monte-Carlo Planning in Large POMDPs](https://proceedings.neurips.cc/paper/2010/hash/edfbe1afcf9246bb0d40eb4d8027d90f-Abstract.html)
及 Sutton、Precup、Singh (1999) 的
[Between MDPs and semi-MDPs](https://www.sciencedirect.com/science/article/pii/S0004370299000521)。
前者用于理解粒子与部分可观测规划，后者用于理解持续目标与终止条件；当前实现为
根动作 UCB 与固定启发式 rollout、规则战术控制器，不是论文算法的完整复现。

实现前检查固定模拟器提交 `37e4264` 的 `Core/StateCloning.cs` 与
`Interop/NativeExports.cs`：已有 `sample_world` 保留已知位置、重排未知抽牌区，
并在原计数基础上重新播种若干 RNG 流，保留粒子已有敌人状态。该服务是上游派生
后端能力，不属于本项目原创采样引擎。新策略只对独立生成并筛选的粒子调用它，
禁止从实际执行环境复制隐藏状态。此审查和测试限于 starter 范围；例如上游
EnergyCostRng 的克隆行为不能据此推广为所有卡牌的信息边界已验证。

粒子保留相容的历史，但重新播种未来随机数只是近似，不称精确后验；有限粒子
耗尽后显式回退。规划效用和战术阈值是本项目固定工程基线，非学习所得，也不构成
科研创新证明。通用统计方法、规则引擎、卡牌事实与本项目控制代码分别归属。

| 路径或内容 | 来源 | 可以怎样描述 |
| --- | --- | --- |
| `sts2lab/contracts.py` | 本项目 | 我们定义的版本化语义协议、观测/动作模型和比较投影 |
| `sts2lab/environment.py`、`docs/ENVIRONMENT-CONTRACT.md`、`tests/test_environment_contract.py` | 本项目 | 后端调用协议、可选能力显式拒绝及生命周期契约；分支/父决策来源作为不可变元数据，模拟器真实 reset，控制器统一同步/异步 step 调用。原版不支持能力的测试确认零 HTTP 请求 |
| `tests/test_training_boundary.py` | 本项目测试 | 按预先记录的 Gym 转换契约验证非法动作过滤、截断与真实胜负优先级；运行现有模拟器，不改写游戏状态或规则，不作为原版证据 |
| `sts2lab/simulator.py` | 本项目封装 + 上游引擎 | 我们编写生命周期、快照、分支和 Python 适配；战斗规则由固定上游 C# 引擎及下述显式兼容修正执行 |
| `sts2lab/native_compat.py`、构建生成的 `native/generated/EnemyAI.cs` | 本项目构建转换；输出为上游派生实现 | 保留固定 EnemyAI 的执行流程，仅按 v0.107.1 实机证据修正 Nibbit Slice 格挡：A0 为 5，ToughEnemies 阈值 8 起为 6。阈值与参数由本机 DLL 只读属性/枚举元数据确认，数值来自游戏事实，不宣称独立规则引擎。生成副本和转换脚本指纹进入清单，原始 vendor 文件不修改；规范见 docs/NATIVE-COMPATIBILITY.md |
| `sts2lab/gym_env.py` | 本项目 | Gymnasium 封装、动作掩码和 `combat-entities-v3` 编码；只从公开观测与项目词表编码，不读取后端名称表 |
| `sts2lab/vocabulary.py`、`config/content-v1.json`、`tests/test_vocabulary.py` | 本项目词表实现和数字 token 分配；语义名称为游戏内容事实 | 按预先定义的公开边界、padding 与未知内容拒绝契约实现；名称来自现有适配器、固定上游内容表及既定种子的模拟器观测，不宣称名称或游戏规则由本项目原创。token 不采用上游 enum 数字，版本和 SHA-256 随实验记录 |
| `sts2lab/sampling.py`、`scripts/benchmark_sampling.py` | 本项目 | 固定任务的进程隔离采样测量、轨迹一致性校验、资源回收与硬件/延迟/RSS 报告；规则仍由当前上游引擎执行 |
| `sts2lab/policies.py` | 本项目 | 随机策略和可解释启发式策略 |
| `sts2lab/belief.py`、`planning.py`、`hierarchy.py`、`planning_replay.py`、`scripts/benchmark_planning.py` | 本项目新增实现（AI 辅助编写），方法与后端依赖见下文 | 公开历史约束粒子、根动作 UCB rollout、持续战术目标、源码/模型绑定的策略重执行与固定预算评测；不宣称新算法或精确后验 |
| `sts2lab/runtime.py`、`server.py` | 本项目 | 实验控制、异步执行、确认状态和 FastAPI 面板服务 |
| `sts2lab/bridge.py`、`original.py` | 本项目 | 原版状态映射、动作提交、去重、重协调和未知结果处理 |
| `sts2lab/bridge_check.py`、`scripts/check_bridge.py`、`tests/test_bridge_check.py` | 本项目 | 基于现有 BridgeClient 的只读主菜单验收；输入引用指纹，输出逐次 GET 证据与检查结果；合成测试覆盖版本/实例/状态变化与超时，不能替代原版战斗证据 |
| `sts2lab/release.py` | 本项目校验实现；兼容格式来自本机程序集元数据 | 将发行 JSON 的精确版本、提交号和兼容校验值关联到收到的 DLL；只读检查确认 AssemblyHasher 使用 SHA-1 的前 4 字节按有符号小端整数读取，使用标准库重算；另保留完整 SHA-256 绑定，不复制或执行游戏方法 |
| `sts2lab/traces.py`、`parity.py`、`reference_replay.py`、`acceptance.py` | 本项目 | 轨迹哈希链、重执行、原版对照和有限验收门 |
| `sts2lab/catalog.py` | 本项目代码 + 上游数据表 | 加载和转换上游名称/定义；名称和卡牌定义的事实来源是上游 |
| `native/LabExports.cs` | 本项目观测导出，包含注明的上游行为映射 | 只读导出，不修改卡牌/敌人效果。Nibbit Slice 的 Defend 显示补全依据本机 v0.107.1 捕获和固定 EnemyAI 当前招式/格挡分支；上游已执行格挡但遗漏副意图，本项目仅补公开观测，未知数值保持不可用 |
| `native/Sts2Lab.csproj` | 本项目构建文件 | 将我们的观测扩展与上游 C# 引擎一起编译 |
| `native/LabCombat.cs`、生成的 `NativeExports.cs` 终局钩子 | 本项目生命周期适配，参考上游运行层行为；生成文件仍为派生代码 | 根据实机胜利捕获和固定 RunRewardGenerator 的 Burning Blood 行为，在单场 arena 胜利后补一次封顶 6 点回血，并按随机策略实机终局清除剩余格挡及 starter 范围的战斗能力。复用原生胜利标志防止重复，失败/截断不支付；不调用完整奖励生成，不复制原版状态到模拟器，不宣称遗物规则为原创 |
| `bridge/McpMod.Lab.cs`、`bridge/SettlementGate.cs` | 本项目适配与结算确认实现 | 对 STS2MCP 的状态、请求去重和实验桥接扩展；依赖上游 Mod API。按实机过早捕获失败定义空闲与稳定窗口契约，读取本机 DLL 的 ActionQueueSet、ActionExecutor、PlayPile 公开属性；只读元数据/调用检查确认接口，不移植游戏动作执行器 |
| `bridge/ScenarioContract.cs`、`bridge/McpMod.Scenario.cs`、`sts2lab/scenarios.py`、`scripts/prepare_scenario.py` | 本项目受控初始化与验证实现，包含注明的上游 API 使用参考 | 需求先记录于 `docs/SCENARIO-STAGING.md`；接口签名来自收到的本机 DLL 元数据，兼容性参考固定上游 `NativeExports.ResetArena/SeedStreams`、`GameRng`、`EncounterRng`。首次实机失败后的 `EncounterModel.ToMutable()` 用法参考固定 `STS2MCP/McpMod.Debug.cs`，并由本机 DLL 元数据确认；使用游戏自身可变模型和 RNG 工厂，不独立实现游戏规则。修复后重复初态及三种遭遇完整战斗已通过，固定矩阵计数见 PHASE1-STATUS.json |
| `tests/test_settlement_gate.py`、`tests/settlement_gate.cs` | 本项目测试 | 独立编译生产结算门，使用合成时钟验证持续忙碌、转为空闲、状态变化和忙碌中断；不加载游戏 DLL，不能代替新 Mod 的实机验收 |
| `tests/test_scenarios.py`、`tests/test_scenario_contract.py`、`tests/scenario_contract.cs` | 本项目测试 | 合成 HTTP 与临时文件覆盖未知结果、指纹/初态拒绝及中断恢复；独立编译生产 C# 请求解析器并检查 36 组合成输入，不载入游戏程序集，不作为原版运行证据 |
| `scripts/*.py`、`scripts/*.ps1` | 本项目 | 构建、来源校验、Windows 接入、安装、回放、审计和浏览器检查 |
| `tests/*.py`、`config/*.json`、`web/*` | 本项目新增实现；部分测试依赖上游素材 | 测试、实验范围、验收规则和面板；`test_original.py` 读取上游 A8 捕获，不属于本机实机证据 |
| `ARCHITECTURE-PLAN.txt`、`README.md`、`PROJECT-HANDOFF.md` | 本项目 | 研究规划、使用说明和转接记录 |
| `assets/logo.svg`、`assets/logo-dark.svg`、`assets/mark.svg` | 本项目原创矢量设计 | 独立绘制的尖塔/卡组/路线和路径字标；无复制的商标或提取的游戏素材；设计参考记录在 `PROJECT-IDENTITY.md` |
| `vendor/sts2` | 上游 `evangambit/sts2`，MIT | 固定提交的模拟器/游戏规则来源，不属于我们的原创代码 |
| `vendor/sts2mcp-v107` | 上游 `evangambit/STS2MCP`，MIT | 固定提交的原版 Mod/API 来源，不属于我们的原创代码 |
| `requirements.lock` 中的包 | 外部开源依赖 | 依各自许可证使用，不属于我们的原创实现 |
| Windows `sts2.dll`、`GodotSharp.dll`、`0Harmony.dll` | 用户本机游戏/第三方运行时 | 不进入 Git，不随项目发布 |

## 固定的上游来源

模拟器来源由 `vendor/manifest.json` 固定：

- 仓库：<https://github.com/evangambit/sts2>
- 提交：`37e4264115546b6ac640d54aab3d7e2ac6983d2d`
- 归档 SHA-256：`409f62e2654c6c4e7fbb748b1ef3c3e6cc147118c313bff6db992d1054dbdd27`
- 许可证：MIT

原版 Mod/API 来源由 `vendor/bridge-manifest.json` 固定：

- 仓库：<https://github.com/evangambit/STS2MCP>
- 提交：`18bc23be210bbe804ae4471dfd2cb33bd481e247`
- 归档 SHA-256：`5b8053e5eca28f0a6293f58588effdcb107fcc42f910186c31b2bf049710c56f`
- 许可证：MIT

这些目录在 `.gitignore` 中被忽略，bootstrap 会按 manifest 下载并校验。它们不应被误解为本项目原创文件，也不应在没有保留上游许可证和版权声明的情况下重新发布。

## 本项目的新增实现

在论文、项目介绍和提交记录中，可以把以下内容描述为 Spire2Lab 的实现工作：

1. 面向自主强化学习的语义观测/动作协议和信息边界；
2. Linux 模拟器与 Windows 原版之间的统一实验控制层；
3. 结构化观测、Gymnasium 编码、动作掩码和进程隔离采样接口；
4. 决策记录、候选动作解释、暂停/重协调/未知结果处理；
5. 原版状态规范化、轨迹哈希链、重放和有限范围 parity 验收工具；
6. 实时实验面板、Windows SSH 接入流程和项目验收/转接文档；
7. 当前项目范围内的测试、实验配置和研究路线。

“Spire2Lab 实现了某项功能”表示上面这些项目代码和流程；“Spire2Lab 实现了《杀戮尖塔 2》的全部规则”不属于当前项目可以支持的表述。

## 构建时的来源边界

`native/Sts2Lab.csproj` 编译上游规则、本项目观测扩展，以及明确列出的生成副本。
`NativeExports.cs` 的副本增加 partial 声明和两个单场 step 的终局钩子，调用本项目
`LabCombat.cs` 补齐初始遗物的胜利回血；`EnemyAI.cs` 的副本应用有实机依据的
Nibbit 格挡兼容修正。原始文件从编译列表排除，防止重复定义；生成代码仍属于上游
派生实现。`scripts/build_native.py` 校验固定归档、拒绝未知转换上下文，并记录输入、
生成输出及构建脚本指纹。`source_integrity.py` 继续拒绝 vendor 修改和额外源码。
`.so` 是上游规则、兼容修正与本项目观测扩展的组合，不能描述为完全独立引擎。

同样，`scripts/build_bridge.py` 会准备上游 STS2MCP 文件，并应用 `bridge/*.cs` 中的本项目扩展。当前工作区构建清单记录全部扩展源文件指纹。生成的 Windows Mod 仍然包含上游依赖，必须保留上游许可证和实际构建报告。

2026-10-22 已使用本机收到的 Steam public build `23811903` 引用在 Linux 编译该
组合 Mod，保留上游 MIT 许可证并记录构建来源。编译成功不改变来源分类，也不证明
游戏语义版本匹配或原版行为一致；实际 DLL 与构建报告保存在被忽略的 `artifacts/`。

## 许可证与发布注意事项

仓库根目录的 `LICENSE` 是当前项目的 MIT 许可证文本。它不能替换上游 `sts2` 和 `STS2MCP` 各自的 MIT 版权声明，也不能授权发布游戏本身或用户本机的专有文件。发布包含上游代码的归档、Mod 或二进制时，应同时保留对应的上游许可证和来源信息。

## 审计命令

查看项目自己提交的文件：

```bash
git ls-files
```

查看固定上游来源：

```bash
cat vendor/manifest.json
cat vendor/bridge-manifest.json
```

检查来源校验器的测试行为（此命令只测试校验器）：

```bash
.venv/bin/python -m pytest -q tests/test_source_integrity.py
```

核对当前安装的两份上游源码与固定归档：

```bash
.venv/bin/python -c 'from sts2lab.source_integrity import verify_installed_source; print(verify_installed_source("sts2")); print(verify_installed_source("sts2mcp-v107"))'
```

归档一致性证明对应文件来自固定版本，不证明本项目其他代码的原创性。

完整构建前会再次执行来源校验。真实原版 DLL、游戏存档和原始捕获保存在被 Git 忽略的 `artifacts/` 中，不应提交到公共仓库。
