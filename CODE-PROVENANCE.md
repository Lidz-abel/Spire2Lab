# Spire2Lab 代码来源说明

更新时间：2026-10-21

这份文件定义“原创代码”在本项目中的含义：代码由 Spire2Lab 项目成员为本项目新编写，或由本项目成员编写的适配、验证和实验工具。它不表示项目拥有《杀戮尖塔 2》的游戏规则、素材、专有 DLL 或上游模拟器代码的版权。

## 来源分类

| 路径或内容 | 来源 | 可以怎样描述 |
| --- | --- | --- |
| `sts2lab/contracts.py` | 本项目 | 我们定义的版本化语义协议、观测/动作模型和比较投影 |
| `sts2lab/simulator.py` | 本项目封装 + 上游引擎 | 我们编写生命周期、快照、分支和 Python 适配；战斗规则由固定上游 C# 引擎执行 |
| `sts2lab/gym_env.py` | 本项目 | Gymnasium 封装、动作掩码和 `combat-entities-v2` 编码 |
| `sts2lab/policies.py` | 本项目 | 随机策略和可解释启发式策略 |
| `sts2lab/runtime.py`、`server.py` | 本项目 | 实验控制、异步执行、确认状态和 FastAPI 面板服务 |
| `sts2lab/bridge.py`、`original.py` | 本项目 | 原版状态映射、动作提交、去重、重协调和未知结果处理 |
| `sts2lab/traces.py`、`parity.py`、`reference_replay.py`、`acceptance.py` | 本项目 | 轨迹哈希链、重执行、原版对照和有限验收门 |
| `sts2lab/catalog.py` | 本项目代码 + 上游数据表 | 加载和转换上游名称/定义；名称和卡牌定义的事实来源是上游 |
| `native/LabExports.cs` | 本项目 | 只读观测导出扩展；不新增卡牌效果或敌人规则 |
| `native/Sts2Lab.csproj` | 本项目构建文件 | 将我们的观测扩展与上游 C# 引擎一起编译 |
| `bridge/McpMod.Lab.cs` | 本项目适配扩展 | 对 STS2MCP 的状态、请求去重和实验桥接扩展；依赖上游 Mod API |
| `scripts/*.py`、`scripts/*.ps1` | 本项目 | 构建、来源校验、Windows 接入、安装、回放、审计和浏览器检查 |
| `tests/*.py`、`config/*.json`、`web/*` | 本项目 | 测试、实验范围、验收规则和可视化界面 |
| `ARCHITECTURE-PLAN.txt`、`README.md`、`PROJECT-HANDOFF.md` | 本项目 | 研究规划、使用说明和转接记录 |
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

## 我们可以主张的原创工作

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

验证上游归档和工作区是否发生漂移：

```bash
.venv/bin/python -m pytest -q tests/test_source_integrity.py
```

完整构建前会再次执行来源校验。真实原版 DLL、游戏存档和原始捕获保存在被 Git 忽略的 `artifacts/` 中，不应提交到公共仓库。
