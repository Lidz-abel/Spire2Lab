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
