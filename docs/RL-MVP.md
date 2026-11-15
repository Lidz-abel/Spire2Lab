# RL MVP v1：E1 训练契约

冻结日期：2026-11-15；课程工作包 E1。配置为
[rl-mvp-v1.json](../config/rl-mvp-v1.json)，可执行边界为
[rl_contract.py](../sts2lab/rl_contract.py)。E1 交付规格、数据适配与边界检查；
策略网络、rollout collector、GAE/PPO 更新、checkpoint 保存器属于 E2，尚未实现。
不因契约冻结而宣称已经训练、原版验收或完成第二阶段。

## 范围与输入

目标是原版自主完整通关。当前最小学习单元仅为固定版本 Ironclad/A0 starter
的 Nibbit、Slimes、Sludge Spinner 单场战斗，初始状态沿用 phase1.json。
无地图/奖励学习、课程调度、搜索联训、奖励 shaping 或模仿学习。
E0 的有限原版一致性证据不能外推到所有种子、牌组和全游戏。

输入仅为 CombatEnv 的 `combat-entities-v3` 公开数组。模型不得获得 Simulator、
真实环境 seed、RNG、快照、native_id、decision_id、debug 状态、info/facts 或评估标签。
环境 seed 仅由实验调度器使用；训练 run seed 是学习器独立随机状态。
`prepare_observation` 拒绝多余键、未知 token、错误形状、非整数和不合法动作引用。
容量溢出由现有编码器报错，不裁剪，不把未知内容变成 padding。

draw/discard/exhaust 是现有公开语义投影的排序多重集；不能替换为隐藏实际牌序。
known_top/bottom 仅为已经公开的牌序。v1 不引入历史记忆，属于公开观测上的
无记忆基线，不声称输入具有完整 Markov 性。v3 对部分缺失意图数字使用 0、
不编码完整卡牌扩展属性；当前只支持已声明 starter 范围，不能据此直接部署新牌组。

## 特征、候选动作与网络规格

所有数值转换为 float32，只除以固定常数，不截断、不根据训练/测试数据拟合统计量。
分类使用 `content-v1.json` 的项目 token，int64；各类别独立 8 维 embedding，
padding_idx=0 且其向量固定为零。ID 不作为连续大小输入。完整列顺序见
[ENCODING.json](../ENCODING.json)，实现中的 FEATURES 固定归一化与字段顺序。

| 字段 | 数值除数（按原列次序去掉分类列） |
| --- | --- |
| player | HP80、maxHP80、block80、energy3、maxEnergy3、gold100、turn30、handCount10 |
| hand/piles/known_order | upgraded1、cost3、damage20、block20、bonusDamage20、enchantAmount10 |
| enemies | HP80、maxHP80、block80；每个 intent 的 magnitude20、hits5、dealsDamage1；presence1 |
| powers | amount10 |
| relics | counter10 |

每行表示按“数值、按列序连接的分类 embedding、presence”连接；player 只有数值。
presence 来自主类别 token 非零，padding 行全零。enemies 的两个 intent 分别
使用同一 intents embedding 表。共享 cards embedding 覆盖全部牌区。
按 player、hand、piles、known_order、enemies、powers、relics 顺序逐行展开，
得到全局公开向量；不把 actions 或 action_mask 放入 value/context 输入，确保截断时
清空动作表不会改变同一公开局面的价值表示。MLP 为 128/Tanh → 128/Tanh。

每个动作按当前局部索引取得 hand 行和 enemy 行；-1 表示缺省引用，使用零向量，
同时附加两个 has_reference 位。拼接 context、hand 行、enemy 行、action-kind
embedding、has_reference，使用共享 64/Tanh → 1 网络评分。没有固定语义的
“第 i 个动作头”；64 是候选容量，同一槽位下一步可以表示另一张牌或另一个目标。
value head 是 context → 1 线性层，可在无合法动作的最后观测上独立求值。

合法 mask 以外的 logit 置为负无穷。训练用 masked Categorical；旧/新 log_prob
与 entropy 均使用**保存的同一公开状态和同一 mask**。只对合法概率计算熵，避免
0×负无穷。全零 mask 不允许构造/采样动作分布；终局只走 value 路径。
评估 greedy，最高分并列时选最小候选索引。网络设计尚待 E2 实现和测试。

## 奖励、转换与 GAE

沿用 terminal-win-v1：胜利 +1、战败 -1、其他 0；不另加 HP/速度/存活奖励。
300 步是外部采集上限，达到上限时为 truncated，不记作战败。自然胜负优先。
中断、未知内容、native 异常和非法动作是实验错误，单独记日志，不能伪造 -1。

E2 首先使用无 autoreset 的 CombatEnv。对每次 step，先保存并验证本次返回的
最后观测，再由 collector 显式 reset。禁止把新一局初态作为上一局 next_observation。
`validate_transition` 拒绝常见 autoreset 信息、非法动作/no-op、不匹配的 reward
版本及掩码/终局组合；返回独立数组副本，不返回 info。未来 vector wrapper 必须
显式适配其 final_observation 语义。没有元数据的替换初态不能靠本函数自动识别，
因此 E2 仍须测试 collector 的 reset 顺序及 episode_id/step_index。

记录每个有效转换的公开 obs、action index、旧 log_prob、旧 value、reward、
step 返回的 next_obs、terminated/truncated、episode_id、step_index、policy_update。
episode/step/update 标签仅作采样审计，不能送入网络。被拒绝转换不计 valid_steps；
出现此类错误即停止该运行并保留失败，不能跳过坏数据后将两段轨迹拼接。

对每个 worker 按时间计算，令 b=1-terminated，c=1-(terminated or truncated)：

```text
delta[t] = reward[t] + gamma * b[t] * V_old(actual_next_obs[t]) - V_old(obs[t])
adv[t]   = delta[t] + gamma * lambda * c[t] * adv[t+1]
return[t] = adv[t] + V_old(obs[t])
```

自然终局不 bootstrap；截断要 bootstrap 但不跨 reset 递推优势。rollout 切片尾部
adv[t+1]=0，最后一个正常转换仍使用其真实 next_obs 的 value；不能把切片尾部
标作环境 truncated。所有 value/target 在更新前固定、detach，不跨 worker 递推。
PPO 仅消费当前策略采集的完整 rollout；不混入启发式动作或其他更新版本。

冻结 gamma=.99、lambda=.95、clip=.2、Adam lr=3e-4/eps=1e-5、4 epochs、
每 worker 128 步、minibatch64、梯度范数上限 .5。优势用整个 rollout 的均值及
总体标准差+1e-8 标准化。loss 为负 clipped surrogate 均值 + .5×MSE(value,return)
−.01×合法分布 entropy 均值；不裁剪 value、不调度学习率。NaN/Inf 时停止并记录，
不继续写成功 checkpoint。E2 对以上公式用手算用例验证，再运行真实模拟器学习闭环。

## 种子、预算和选模

以下范围均包含端点；每个 seed 与三类遭遇取笛卡尔积。配置中的紧凑范围就是完整
清单定义，`evaluation_cases` 可展开；检查脚本保存展开清单和哈希，不执行其中用例。

| 用途 | 环境 seed | 用例数 |
| --- | --- | --- |
| 训练 | 10000–10999 | 3000 |
| 验证 | 20000–20019 | 60 |
| 最终测试 | 30000–30099 | 300 |

历史 1–10、1001–1010、2001–2030 全部排除。E1 集成测试只用旧开发 seed3。
上述新范围未在本轮运行；若后续发现历史使用记录，先记录污染并重新登记测试清单，
不能继续称未触碰。未见 seed 泛化不等于未见内容/游戏版本泛化。

训练按固定遭遇顺序循环，使用调度器独立 RNG 从训练 seed 中有放回均匀采样。
run seeds 41/42/43；E2 首次仅 run41、CPU、1 worker/1 Torch thread，目标8192、
硬上限10000有效转换（包括恢复验收继续训练，不能为恢复另开无限预算）。2/4 worker
扩展须独立记录和计数，仍属该次 E2 总预算。验证/基线步数另计，不计入训练预算。
E3 长训练 disabled，预算和 workers 为 null；E2 测吞吐后在训练前另行版本化冻结，
Proposal 的 3×约百万步只是规划，不能据此现在启动。

每 8 updates 验证一次，也评估最终 update；同一清单对比 random、heuristic、
RL greedy。random 每个用例重置 policy RNG seed71，保证顺序/并行度不改变随机基线。
每个 run 独立按验证胜率优先、全用例平均 finalHP 次优、有效训练步数较少再次优选。
HP 包含真实胜利回血；战败/截断也计入平均，不能只统计胜局。若存在错误，该轮验证
不具备完整选模资格，错误用例保留，禁止丢弃后缩小分母。基线不参与选择 RL 权重。

最终测试前记录所选模型哈希、配置/代码版本及清单哈希；每个 run 的所选模型和
基线在同一最终清单上评测一次。E2 不执行最终测试；不得根据测试结果改超参后继续
把同一清单称为最终保留集。报告逐例 outcome、HP、return、步数、延迟及总体胜负/
截断/错误数、分遭遇结果、训练吞吐/时间/内存。没有提升也照实报告。

## Checkpoint 与恢复契约（E2 待实现）

只在完整 optimizer update 之后保存；写临时文件后原子替换目标，新 run 不覆盖旧文件。
保存 model/optimizer state、已完成 update/valid_steps、Python/NumPy/Torch CPU及
实际使用的 CUDA RNG、训练用例调度 RNG/游标、配置和哈希、词表/编码/特征/奖励版本、
native/上游清单/依赖锁指纹、源码 commit及脏树状态、验证历史及所选模型指标。
加载时校验以上兼容项及 device 映射，拒绝不兼容模型；不把私有 snapshot 送入模型。

恢复学习器、优化器、RNG 和调度状态后，**所有环境从新 episode 开始**；丢弃未完成
episode 的在线状态并记 aborted_by_resume，不计作战败/截断结果。记录重置数量和
新的 episode_id。此前已完成更新中的转换仍计入预算。只保证相同输入的模型输出和
学习器状态可恢复，不承诺与未中断运行有相同后续轨迹。E2 必须测试含优化器及计数的
恢复，不能只加载权重后宣称续训成功。

## 验证与来源

E1 的 tests/test_rl_contract.py 检查分割、防泄漏、padding/引用、数值缩放、reward、
终局/截断 bootstrap 标志和数组独立性，并在三类 seed3 模拟战斗中验证转换。
相关旧测试继续覆盖编码容量、未知内容与终局。结果与命令见本地
`artifacts/rl-mvp/contracts/e1-20261115/`。这些是合成/模拟器证据，不是原版或RL训练。

本模块先按上述需求定义输入输出与用例，使用通用 NumPy 独立编写并由 AI 辅助。
未复制训练框架实现，模拟器仍是既有固定上游依赖。方法依据：

- [Schulman et al., PPO, 2017](https://arxiv.org/abs/1707.06347v2)。
- [Schulman et al., GAE](https://arxiv.org/abs/1506.02438v6)。
- [Huang & Ontañón, invalid action masking](https://arxiv.org/abs/2006.14171v3)。
- [Gymnasium 1.4 time-limit semantics](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)。

E1 没有引入新依赖；沿用隔离 `.venv-rl` 和 requirements-rl.lock。
Windows 连接/Mod 和普通单幕验收仍单独阻塞，不因本规格或模拟器测试而解除。

2026-11-15 验证：最终相关回归 **124 passed / 11.89s**，其中 E1 新增59项、
既有相关65项。`regression-attempt2.xml/.log` 为最终结果；attempt1 的120项通过
记录保留，不能相加。三类战斗集成测试分别覆盖胜/负，只使用开发 seed3。
`contract-manifest.json` 保存配置/代码指纹和全部展开清单；没有执行验证或最终测试集。

```bash
.venv-rl/bin/python scripts/check_rl_contract.py --output artifacts/rl-mvp/contracts/NEW-RUN/contract-manifest.json
.venv-rl/bin/python -m pytest -q tests/test_rl_contract.py tests/test_environment.py tests/test_environment_contract.py tests/test_training_boundary.py tests/test_sampling.py tests/test_vocabulary.py tests/test_source_integrity.py tests/test_planning.py
```
