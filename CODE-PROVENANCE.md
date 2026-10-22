# Spire2Lab 代码来源说明

更新时间：2026-10-23

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
| O-05 搜索、分层与学习 | 当前有接口和基线策略，尚无完整搜索/分层/RL 训练 | 后续按路线图独立实现，报告所参考方法、实验预算、基线和消融结果 |

替换验收必须覆盖合法动作、结算顺序、信息边界、快照/分支隔离、复现性、性能测量
及原版参考轨迹。上游模拟器保留为对照后端；最终行为依据来自原版采集。
源码独立性与行为正确性分开验收，新的实现不能继承旧引擎的验证结论。

第一阶段继续按原有有限战斗范围与真实游戏要求推进。完整游戏规则重写不是本轮
追加的第一阶段交付条件；独立后端替换进度另行记录。当前 O-02 至 O-04 尚未实现。
三个阶段路线见 `ARCHITECTURE-PLAN.txt`（three-stage-v1）：阶段 1 落实核心边界与来源，
O-02 至 O-04 随实机证据逐步替换；阶段 2 实现搜索/层级核心，阶段 3 实现训练调度
及搜索学习衔接。任何阶段都不把当前上游引擎改称独立实现。

## 来源分类

| 路径或内容 | 来源 | 可以怎样描述 |
| --- | --- | --- |
| `sts2lab/contracts.py` | 本项目 | 我们定义的版本化语义协议、观测/动作模型和比较投影 |
| `sts2lab/simulator.py` | 本项目封装 + 上游引擎 | 我们编写生命周期、快照、分支和 Python 适配；战斗规则由固定上游 C# 引擎执行 |
| `sts2lab/gym_env.py` | 本项目 | Gymnasium 封装、动作掩码和 `combat-entities-v2` 编码 |
| `sts2lab/sampling.py`、`scripts/benchmark_sampling.py` | 本项目 | 固定任务的进程隔离采样测量、轨迹一致性校验、资源回收与硬件/延迟/RSS 报告；规则仍由当前上游引擎执行 |
| `sts2lab/policies.py` | 本项目 | 随机策略和可解释启发式策略 |
| `sts2lab/runtime.py`、`server.py` | 本项目 | 实验控制、异步执行、确认状态和 FastAPI 面板服务 |
| `sts2lab/bridge.py`、`original.py` | 本项目 | 原版状态映射、动作提交、去重、重协调和未知结果处理 |
| `sts2lab/bridge_check.py`、`scripts/check_bridge.py`、`tests/test_bridge_check.py` | 本项目 | 基于现有 BridgeClient 的只读主菜单验收；输入引用指纹，输出逐次 GET 证据与检查结果；合成测试覆盖版本/实例/状态变化与超时，不能替代原版战斗证据 |
| `sts2lab/release.py` | 本项目校验实现；兼容格式来自本机程序集元数据 | 将发行 JSON 的精确版本、提交号和兼容校验值关联到收到的 DLL；只读检查确认 AssemblyHasher 使用 SHA-1 的前 4 字节按有符号小端整数读取，使用标准库重算；另保留完整 SHA-256 绑定，不复制或执行游戏方法 |
| `sts2lab/traces.py`、`parity.py`、`reference_replay.py`、`acceptance.py` | 本项目 | 轨迹哈希链、重执行、原版对照和有限验收门 |
| `sts2lab/catalog.py` | 本项目代码 + 上游数据表 | 加载和转换上游名称/定义；名称和卡牌定义的事实来源是上游 |
| `native/LabExports.cs` | 本项目 | 只读观测导出扩展；不新增卡牌效果或敌人规则 |
| `native/Sts2Lab.csproj` | 本项目构建文件 | 将我们的观测扩展与上游 C# 引擎一起编译 |
| `bridge/McpMod.Lab.cs` | 本项目适配扩展 | 对 STS2MCP 的状态、请求去重和实验桥接扩展；依赖上游 Mod API |
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

`native/Sts2Lab.csproj` 会把 `vendor/sts2/src/Sts2Emulator/**/*.cs` 和我们的 `native/LabExports.cs` 一起编译。生成的 `.so` 因此是上游规则引擎与本项目观测扩展的组合产物。`scripts/build_native.py` 会在构建前校验上游归档和扩展源文件；`sts2lab/source_integrity.py` 会拒绝被修改的上游文件和额外的构建源文件。

同样，`scripts/build_bridge.py` 会准备上游 STS2MCP 文件，并应用 `bridge/McpMod.Lab.cs` 中的本项目扩展。生成的 Windows Mod 仍然包含上游依赖，必须保留上游许可证和实际构建报告。

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
