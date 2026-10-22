# Spire2Lab

Spire2Lab 是面向《杀戮尖塔 2》的可复现自主强化学习实验环境。

- 对外项目名：`Spire2Lab`
- GitHub 仓库名：`Spire2Lab`
- 中文描述：杀戮尖塔 2 自主强化学习实验室
- 英文描述：A reproducible research lab for search, hierarchical decision-making, and efficient reinforcement learning in Slay the Spire 2.
- 当前内部 Python 包：`sts2lab`
- 当前本地目录：`sts2-lab`

保留内部包名和本地目录是有意的兼容措施。以后如果需要重命名 Python 导入路径，单独安排迁移提交，不与实验环境或原版桥接变更混在一起。

GitHub 提交原则：每个 commit 表示一个可说明、可复核的进度；测试结果和真实原版证据分开记录。模拟器测试通过不等于原版一致性通过。

开发原则（2026-10-22 用户要求）：平台尽可能原创，允许参考开源实现。核心平台与研究
逻辑优先自行实现；已有上游运行依赖按 CODE-PROVENANCE.md 逐项替换、验证并保留来源。

## README 与视觉设计要求（2026-10-22，持续有效）

用户要求 README 达到成熟 AI Research / LLM Infrastructure / Agent Framework 项目的
首页质量，主语言为英文。当前优先完成原创 Logo、更新首页并上传；完整文档工作按以下
清单持续验收，不能把一次首屏改版当作所有研究能力均已交付。

1. **仓库事实审查**：核对目录、文档、配置、核心代码和依赖，以及安装、运行、训练、
   推理、评测、示例、测试与基准入口。回答项目是什么、解决什么问题、为何有用、如何
   工作、怎样快速开始、有哪些证据。缺失信息明确标记，不自行补造。
2. **原创品牌**：必须有 `assets/logo.svg`，必要时增加横幅；以矢量为主，图形应有
   《杀戮尖塔》的独特辨识度。允许参考 AdaFlash 的简洁与对比、verl-agent 的留白和
   科研排版，不复制商标或素材。浅/深背景均可读，控制首屏高度与留白。
3. **信息结构**：Hero（Logo、名称、准确 tagline、技术定位、真实 badges 和入口）、
   Overview、真实 Key Features、Architecture、Quick Start、Usage、可信验证结果、
   Project Structure、Reproducibility，以及有实际依据的 Roadmap / Contributing /
   Citation / License。复杂流程移入补充文档，遵守现有文档导航。
4. **快速开始**：列清前提、安装、配置和最小例子，命令必须对应实际代码；只有实测
   后才写预期输出。五分钟上手是体验目标，未经测量不能承诺冷启动安装五分钟完成。
5. **科研可信度**：禁止虚构实验、性能、论文、作者、机构、CI 或许可证。计划功能
   不写成已实现；模拟器测试、合成传输和原版证据分开。性能表需有硬件、配置、指标、
   基线与复现路径；证据不足时不展示宣传性数值。
6. **写作和审美**：技术准确、简洁、易扫描；clean / minimal / engineering-oriented。
   避免无意义 emoji、GIF、巨幅截图、模板化营销、空泛形容词和不齐的 badges。
7. **交付与审查**：修改集中在文档及视觉资源；验证 GitHub Markdown、SVG、相对链接、
   锚点、实际命令和目录。不得暴露密钥或内部服务器地址。实际检查浅/深主题与窄屏，
   审查首眼品牌辨识度、30 秒理解、启动可用性、技术边界，并记录仍待人工补充的信息。
8. **持续记录与提交**：同步需求、实施、验证和后续工作；每个可审阅进度 commit。
   用户已明确要求上传 GitHub；只有远程提交核对成功后才报告已上传。

## 当前视觉方案：The ascent, inspected

- 图形：扇形卡组、突破牌框的非对称尖塔、塔底的分叉登塔路线；路线节点同时表达
  搜索与决策。塔身采用切面和断开的石阶，不使用通用芯片或无关装饰。
- 字标：路径绘制的 `Spire²Lab`；`i` 的菱形点与路线顶端节点呼应，金色上标强调 2。
- 配色：墨色 `#172B38`、古金 `#B08438`、石金渐变与少量青色路线；深色主题改用
  浅色字标。主图没有外部字体、脚本、嵌入位图或远程资源。
- 文件：`assets/logo.svg`（浅色）、`assets/logo-dark.svg`（深色）、`assets/mark.svg`
  （独立图标）。README 使用 `<picture>` 随系统颜色偏好选择，浅色版作为回退。
- 构图参考：[AdaFlash](https://github.com/ZinYY/AdaFlash)、
  [verl-agent](https://github.com/langfengQ/verl-agent)；游戏背景参考
  [Mega Crit 官方网站](https://www.megacrit.com/)。所有交付矢量路径由本项目绘制，
  未下载、描摹或移植参考项目 Logo 或游戏素材。
- 同时维护两个横版的几何内容；主题差异只涉及字标颜色。预览截图属于本地验证产物，
  保存在被忽略的 `artifacts/branding/`，不是原版游戏或运行效果截图。

## 本次范围与剩余验收

本次落地 SVG 标志、README 结构与入口、真实最小 Python 示例、来源与三阶段边界。
新机器完整安装、Windows 实机兼容、可重复原版初态与 60 条参考集仍待实际环境验证；
缺少标准化硬件条件下的性能报告，不宣称速度提升、训练收益或完整原版一致性。
以后新增功能、公开证据或更换后端时，必须重新核对 README 的状态和命令。
