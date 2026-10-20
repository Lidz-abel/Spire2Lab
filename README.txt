SpireLab — 第一阶段实验环境

项目目录：/user/chenzk/sts2-lab（建议 GitHub 仓库名：spirelab）
当前状态：Linux 战斗环境与面板可运行；原版适配已接入运行控制并通过合成接口测试，Windows 实机兼容与逐步一致性尚未通过。
完整验收清单见 PHASE1-STATUS.json。不得将模拟器自测视为本机原版一致性证明。
整体架构、第一阶段建设顺序与后续路线见 ARCHITECTURE-PLAN.txt。

启动（Linux）
  cd /user/chenzk/sts2-lab
  bash scripts/start.sh
  本机访问 http://127.0.0.1:8765
  API 文档 http://127.0.0.1:8765/docs
  浏览器页面为无构建步骤的 HTML/CSS/JavaScript；服务由 Python/FastAPI 提供。

首次复现（Linux x86_64；需要 Python 3.12、curl、gcc 和 NativeAOT 所需系统库）
  python3 scripts/bootstrap.py
  所有 Python/.NET 安装均在项目 .venv 和 .tools 中。
  模拟器和桥接源码按 vendor/*.json 的提交与归档校验值下载。
  初次安装不会安装或启动 Windows 游戏 Mod。

Windows 接入
  1. 将 scripts/Connect-Windows.ps1 复制到 Windows。
     powershell -ExecutionPolicy Bypass -File .\Connect-Windows.ps1 -Server 用户@服务器 -SshPort 22
     自动查找 Steam 游戏，记录构建 ID 和 DLL 哈希，将三个编译引用 DLL 发送到你的服务器。
     DLL 仅保存在被 Git 忽略的 artifacts/windows/assemblies，不发布、不进入项目源码。
     隧道：Windows 127.0.0.1:8765 -> Linux 127.0.0.1:8765。
     反向隧道：Linux 127.0.0.1:18526 -> Windows 127.0.0.1:15526。
     保持脚本窗口打开，即可在 Windows 浏览器访问面板。
  2. Linux 核对实际版本后构建：
     .venv/bin/python scripts/build_bridge.py
     当前桥接代码尚未用你的 DLL 编译；编译成功也不等于实机行为验证通过。
  3. 将 scripts/Install-Windows-Mod.ps1 复制到 Windows，关闭游戏后执行：
     powershell -ExecutionPolicy Bypass -File .\Install-Windows-Mod.ps1 -Server 用户@服务器
     安装器会校验本机游戏指纹，备份已有同名 Mod，再通过 Steam 启动游戏。
     游戏首次加载 Mod 可能要求你在界面中启用。
  4. 在面板选择“Windows 原版游戏”，连接符合范围的首回合战斗。
     此操作读取当前对局，不会替你创建或重置游戏。环境种子不会伪装成原版实际种子。
     原版必须是铁甲战士 A0、初始牌组/遗物、未附魔、无药水、80/80 HP、99 金币、
     第 2 层、首回合 5 张手牌、3 点能量；选择与实际敌人一致的遭遇。
     原版初始化与随机状态对齐工具仍需补齐，不能只凭相同种子宣称一致。
  5. 动作响应丢失会显示“结果待确认”。点击“确认游戏结果”只读取状态，不重发动作。
     等待结算期间可暂停后续决策；已提交的动作不能撤销。
     未决动作禁止直接切换实验。无法继续确认时，可点“归档异常实验”，保留未知结果；
     归档不操作游戏，也不生成胜负或奖励。之后可以创建新实验。

桥接构建采用固定上游的 mods/STS2_MCP/STS2_MCP.dll 与 mod_manifest.json 布局。
安装器会备份已有文件并在复制失败时尝试恢复。该脚本尚未在你的 Windows 上执行。

实验范围
  config/phase1.json 定义 A0 铁甲战士、10 张初始牌、燃烧之血、初始 80/80 HP。
  三种普通遭遇、开发与保留评测种子分别固定。原版对齐前场景标为未验证。
  奖励 terminal-win-v1：胜利 +1，失败 -1，其他步骤 0；原始 HP 等事实另存。
  环境一步表示一次玩家决策。动画等待不构成训练步骤。
  决策内 card/ref 和 enemy/ref 唯一；引用仅在该 decision_id 下有效。
  当前上游 CardInstance 没有持久实例 UUID，因此不伪称已支持跨洗牌追踪同名实例。
  native Turn 从 0 开始，面板从 1 开始显示回合。

主要接口（语义协议 0.2.0；训练编码 combat-entities-v2）
  sts2lab.simulator.Simulator：observe / step / snapshot / restore / sample_world / close。
  snapshot 是精确的进程内检查点，须 close 释放；仅用于校验和恢复。
  sample_world(search_seed) 强制重采样未知牌序及随机流，供后续搜索使用。
  持久复现通过带版本的初始配置、动作和逐步轨迹完成，不把内存句柄当跨进程存档。
  sts2lab.policies.Policy：只接收 Observation，无法访问真实隐藏状态。
  sts2lab.gym_env.CombatEnv：标准 reset/step 和 action_masks，详见 ENCODING.json。
  固定动作宽度 64，每步对应当前语义动作表；超出编码容量会报错，禁止静默截断。
  Gym 随机采样到被 mask 排除的动作时返回显式无操作，info.training_transition=False；
  这类样本应从训练数据中过滤。控制接口仍严格拒绝非法动作。

测试与复现
  .venv/bin/python -m pytest -q
  .venv/bin/python scripts/build_bridge.py --prepare-only
  .venv/bin/python scripts/benchmark.py --split development
  .venv/bin/python scripts/benchmark.py --split heldout
  .venv/bin/python -c "from sts2lab.verification import replay_trace; print(replay_trace('artifacts/runs/你的运行ID.jsonl'))"
  浏览器验证（先启动服务）：
    PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" .venv/bin/playwright install chromium
    PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" .venv/bin/python scripts/check_dashboard.py
  Playwright 验证包含真实页面单步、人工干预标记、自动运行、暂停、回放与手机布局。

记录与限制
  artifacts/runs/*.jsonl：带哈希链的实验记录；包含配置、策略依据和真实执行变化。
  artifacts/browser-checks.json、dashboard-*.png：实际浏览器验证结果。
  artifacts/benchmark-*.json：本机模拟器结果，不是原版胜率或学习性能结论。
  上游 C# 测试：4801 通过、1 跳过。
  上游 Python 测试：527 项中 519 通过、7 跳过、1 失败。
  已知失败为 TENDER_POWER 显示值比较规则，位于上游比较工具，不在本阶段内容范围。
  我们的逐步比较器独立实现；仍需真实原版参考轨迹才能验收。
  原版桥接 transport 测试用合成响应验证通信契约，不能证明实机兼容。

后续扩展
  新策略复用 Observation/Action/Decision；搜索接 sample_world；层级目标写入
  Decision.goal / parent_decision_id。并行采样使用进程隔离，因为上游句柄池非线程安全。
  UI 不实现卡牌规则。规则由固定 C# 引擎执行，原版后端的真值由游戏提供。
  增加新角色、牌组或效果前，先扩大协议与参考用例，再更新支持清单。
  加入原版画面时按 run_id / decision_id 对齐实机对局，不能把模拟分支伪装为原版截图。

原版适配与比较证据
  sts2lab/original.py 将 Mod 读数转换为统一观测，隐藏牌序不会进入策略或面板。
  缺失的终局能量/手牌等字段标记为不可读取，不能把缺失当作零。
  非攻击意图通常只保留类型；StatusCard 的玩家可见数量会保留。
  原版牌面的基础伤害/格挡目前来自固定规则表，不属于独立原版测量证据。
  原始读数保存在 artifacts/original-raw/<capture_id>，普通轨迹只记录文件名与校验值。
  .venv/bin/python scripts/compare_traces.py 原版轨迹.jsonl 模拟器轨迹.jsonl --output artifacts/parity/report.json
  比较器核对原始捕获、动作关联、协议版本、场景配置，并重新执行模拟器候选轨迹。
  报告声明比较字段与排除项；拒绝合成接口数据、未决动作、缺失证据及不匹配初态。
  通过表示这一条完整战斗轨迹的已测字段一致，不证明整个游戏或隐藏随机流一致。
  当前没有你本机原版的通过报告。

当前本地证据
  43 项 Python 测试通过；原生模拟器页面 6 条浏览器流程通过。
  原版协议页面 5 条流程使用合成 HTTP 接口验证，明确不是实机兼容或规则证据：
    PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" .venv/bin/python scripts/check_original_dashboard.py
  开发集 60 场、980 次决策完成。报告包含实际构建指纹、配置与计时范围。
  重建原生库使用临时输出和文件原子替换；已加载旧库的进程需要重新启动才能创建新实验。
  重建脚本会保留被替换版本到 .tools/native-history；已经核验备份与当前同指纹的旧库。
  更早的历史版本不保证已归档。
  旧协议轨迹不能直接作为新协议验收证据，需要明确迁移。

固定种子的原版参考重放
  .venv/bin/python scripts/replay_reference.py 原版轨迹.jsonl --seed 事先指定的模拟器种子 --candidate artifacts/parity/candidate.jsonl --report artifacts/parity/attempt.json
  输入必须有真实原版捕获，合成接口记录不能用于验收。
  工具先核对配置、原版原始记录、公开初态及私有抽牌顺序，然后重放原版的动作。
  它不会搜索种子，也不会改写模拟器状态来匹配后续结果；第一处差异会保留到报告。
  原始隐藏顺序只用于校验，不进入策略或公开轨迹。随机流完全对齐仍未得到证明。
  候选轨迹和报告都必须使用新路径，避免覆盖失败尝试。
  当前没有本机原版初态成功对齐的证据；工具完成不代表原版验收完成。

来源核验与接入包
  bootstrap、两个构建脚本和模拟器首次加载会核对固定源码归档及已安装文件。
  已核验模拟器 1383 个文件、桥接 34 个文件；改动的固定文件及额外构建源码会报错。
  构建产物目录例外仅用于生成文件，不改变对归档内每个文件的核验。
  当前服务器上已完整执行 bootstrap；这不是另一台全新机器或 Windows 的安装证明。
  .venv/bin/python scripts/package_windows.py
  接入包位于 artifacts/installers/sts2-lab-windows.zip，含两个 PowerShell 脚本、步骤和校验值。
  接入时使用 Windows 平时访问此 Linux 的 SSH 目标与端口，不需要提供密码或私钥给助手。

第一阶段原版参考集验收
  config/acceptance.json 固定 3 个遭遇 × 10 个开发种子 × 2 个基线策略，共 60 条完整参考。
  必须另行补充基线未覆盖的边界探针，例如失败结局；不能用同一次捕获重复计数。
  artifacts/acceptance/index.json 格式：
    {"suite_version":"phase1-live-reference-v1","cases":[
      {"id":"nibbits-weak:1:heuristic","reference":"artifacts/runs/REAL.jsonl","candidate":"artifacts/parity/CANDIDATE.jsonl"}
    ]}
  额外边界探针使用 probe: 开头的唯一 id；上例中的路径必须替换成实际原始证据。
  .venv/bin/python scripts/audit_acceptance.py
  缺失或失败时返回非零状态，报告写入 artifacts/acceptance/status.json。
  核验实际 DLL 版本/哈希、Mod 构建、固定策略动作、原始捕获和模拟器重执行。
  通过只表示有限参考集已验证；修改代码、版本或证据后已有结论需重新核验。
  /api/acceptance 和面板显示该状态。目前 60 条实机参考全部缺失，第一阶段尚未完成。
