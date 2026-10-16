# 注释整理处置记录 — metrics_pipeline.py

整理原则：交出去的每条注释都必须可信（事实有出处、约束可依、有 keeper 维系）；代码运行逻辑零改动（仅注释与 docstring 文本变化）。行号均指整理前的原文件。

**处置计数：保留 6 / 改写 2 / 删除 5（共 13 条）**

## 逐条处置

### 1. 第 1 行 模块 docstring — `"""Order ingestion pipeline for the analytics service."""`
**保留** — 一句话点明模块在系统中的角色（面向 analytics 服务的订单摄取），是通读代码也推不出的定位信息，且就靠在文件顶端、由邻域看守。

### 2. 第 10 行 `# currently supports: CSV, JSON, Parquet.`（SUPPORTED_FORMATS 上方）
**删除** — 下方的集合字面量已精确声明了支持的格式，此句是代码的散文复述（复述），且 "currently" 是随时过期的状态快照，没有存在的必要。

### 3. 第 15 行 `# serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").`（_lock 上方）
**改写** → `# sdk.send must be serialized by this lock: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").`
理由：事实本身是必须留的外部契约与失败模式（SDK 非线程安全、故须经此锁串行化、出处可查），但 "serialized:" 是个无主语的残句，有被误读为"数据序列化"的风险，改写为完整的约束句。

### 4. 第 20 行 `"""Token bucket shared by every caller in this process."""`（_install_rate_limiter docstring）
**删除** — 声明与实现不符：函数体只是 sleep 一次并返回一个新建的参数字典，既无 token bucket 语义（无令牌、无桶状态、burst 未被使用），也不存在任何进程内共享状态；这是误导性的久置声明，能救回的真事实为零（函数体两行自明）。删除后请维护者留意：该函数名承诺的限流语义与实现存在落差（见文末附注）。

### 5. 第 25 行 `# callers: ingest.py, backfill.py, admin_cli.py`（send_batch 上方）
**删除** — 调用方名单的"本家"在各调用点，工具链（import / 引用检索）能随时保持最新，手写名单只会在第一个新调用方出现时变旧；这正是 "无人刷新的 callers 清单" 失效模式的标本。

### 6. 第 27 行 `"""Send one batch to the vendor, blocking until it is acknowledged."""`
**保留** — "blocking until it is acknowledged" 是代码推不出的调用语义（同步、以对方确认为准），属外部契约，且句子自足。

### 7. 第 28 行 `# returns the number of processed records`
**保留** — 说明 vendor 返回值口径（数的是"已处理"条数，不是发送数），类型与代码都无法表达。

### 8. 第 34 行 `# counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.`（page 内）
**保留** — 典型"看似 bug 实为正确"的护栏：上游分页 API 双端闭区间（外部契约）解释了 `limit + 1` 的来历，防止后来者"顺手修正"。是本文件里范例级的注释。

### 9. 第 39 行 `# format changed in v2.1: dates moved from local to UTC`（parse_dates 内）
**改写** → `# sdk.parse_time returns UTC timestamps, not local time.`
理由：保留可长期成立的口径事实（"whose clock"：UTC，不要当本地时间用），删除 "v2.1 变更史"——那是属于变更记录的往事叙述，过去时叙事留在代码旁只会占用读者而不服务于读者。

### 10. 第 43 行 `# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).`（RETRY_WINDOW 上方）
**保留** — 外部契约 + 失败模式 + 可查出处（运维手册 RB-7）三合一，解释了常量含义与越界后果，代码推不出，keeper 在运维侧且有名可循。

### 11. 第 48 行 `# see line 57 for the rate-limiter setup`（bootstrap 内）
**删除** — 行号指针是最不持久、无法被检索的指路方式，且此指针已经烂掉：本文件第 57 行是 BILL-1421 的 TODO，与限流器毫无关系；何况 `_install_rate_limiter` 就在下一行按名字调用，根本无需指路。

### 12. 第 53 行 `# TODO: clean this up`（legacy_shim 上方）
**删除** — 裸意图：无名无票无触发，不知道要清理什么、由谁在何时清理；就地也装不了 keeper（手里没有真实工单，编造即失实）；按纪律收编或清除，此处清除。

### 13. 第 58 行 ``# TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.``（LEGACY_FIELDS 上方）
**保留** — 意图已具名 keeper：明确的触发条件（billing 迁移落地）与工单号（BILL-1421），字段名 `ts` 可检索；这是 TODO 长期留在代码旁的正当形式。

## 附注（交接备忘）

- 第 4 条删除的 docstring 揭示：`_install_rate_limiter` 的名字/曾宣称语义与实现不一致，建议后续核查其限流是否真的生效（本次不改行为）。
- 第 3 条的约束只覆盖 `sdk.send`；`parse_dates` 直接调用 `sdk.parse_time` 未经此锁——若该调用同样不是线程安全的，需要单独排查（本次不改行为）。
