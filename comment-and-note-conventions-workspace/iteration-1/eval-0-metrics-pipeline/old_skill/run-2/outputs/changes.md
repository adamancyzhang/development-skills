# 注释整理记录：metrics_pipeline.py

**范围**：仅整理注释与 docstring，未改动任何代码；条目中的行号均指整理前的原文件。

**处置口径**：只留下"有 keeper、且承载代码本身无法表达的信息（口径 / 使用约束 / 失效模式 / 外部契约 / 反直觉）"的注释；对代码的复述、状态快照、无人看守的意图、已经失真的话，删除或改写。

**统计**：保留 7 / 改写 1 / 删除 5（共 13 处）。

## 逐条处置

1. **L1 模块 docstring** — `"""Order ingestion pipeline for the analytics service."""`
   - 处置：**保留**。
   - 理由：交代模块的领域定位（订单摄入管线、服务对象是 analytics），是代码推导不出的信息，且不随代码演进腐坏。

2. **L10** — `# currently supports: CSV, JSON, Parquet.`
   - 处置：**删除**。
   - 理由：与下一行 `SUPPORTED_FORMATS` 集合逐字重复（同一事实的第二份拷贝），且 `currently` 使它成为会被代码抢先更新的状态快照；集合本身即权威，改格式时只有一行需要动。

3. **L15** — `# serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").`
   - 处置：**保留**。
   - 理由：解释 `_lock` 为何存在——外部契约（厂商 SDK 线程不安全），失去它读者会认为锁是多余的随手可删；括号中的 `"Concurrency"` 是章节名（可检索的坐标），不是位置指针。

4. **L20** — `"""Token bucket shared by every caller in this process."""`（`_install_rate_limiter` 的 docstring）
   - 处置：**删除**。
   - 理由：声称存在"进程内共享的令牌桶"，但实现里既没有桶、也没有任何共享状态（只是一次 sleep 加一个被调用方丢弃的字典），是一句无法兑现、会诱使后续维护者按"已有限流保障"去推理的假话，且改写除了复述代码别无真话可写。

5. **L25** — `# callers: ingest.py, backfill.py, admin_cli.py`
   - 处置：**删除**。
   - 理由：调用者清单是第二份事实，会在第一个新调用者出现时无声失真；调用关系由各调用点自行声明，无需人工维护的副本。

6. **L27** — `"""Send one batch to the vendor, blocking until it is acknowledged."""`
   - 处置：**保留**。
   - 理由："blocking until it is acknowledged" 是调用方依赖的行为契约（同步阻塞语义），类型标注与函数体都表达不了。

7. **L28** — `# returns the number of processed records`
   - 处置：**保留**。
   - 理由：说明返回值的口径（厂商 `sdk.send` 的返回值代表"已处理记录数"），属于本仓库代码无法推导的语义。

8. **L34** — `# counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.`
   - 处置：**保留**。
   - 理由：典型的反直觉注释——提前拦住下一位把 `limit + 1` 当 bug"修掉"的读者，正是注释的正当用途。

9. **L39** — `# format changed in v2.1: dates moved from local to UTC`
   - 处置：**改写**为：`# dates are UTC, not local (vendor format since v2.1)`
   - 理由：删除"何时改、从什么改成什么"的变更叙事（那属于变更/发布记录），只保留仍在生效的口径事实——日期是 UTC——并留版本坐标便于溯源。

10. **L43** — `# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).`
    - 处置：**保留**。
    - 理由：外部契约加失效模式（网关按租户计重试、超阈触发熔断），并命名了它的 keeper（ops runbook RB-7），是理解 `RETRY_WINDOW` 的唯一线索。

11. **L48** — `# see line 57 for the rate-limiter setup`
    - 处置：**删除**。
    - 理由：位置指针不但违反"不指路"，而且已经烂掉——原文件第 57 行是空行；即使指对，它指向的也只是下一行代码本身，信息量为零。

12. **L53** — `# TODO: clean this up`（`legacy_shim` 上方）
    - 处置：**删除**。
    - 理由：无 owner、无触发条件、无具体动作的空话；函数名 `legacy_shim` 已自带"这是遗留垫片"的标记，真有意向应进 tracker。

13. **L58** — `# TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.`
    - 处置：**保留**。
    - 理由：三个 keeper 齐备——工单（BILL-1421）、负责人（billing 团队）、触发条件（迁移落地）；它同时阻止读者把 `LEGACY_FIELDS` 当成死代码误删。

---

**核对**：保留 = 1、3、6、7、8、10、13（7 条）；改写 = 9（1 条）；删除 = 2、4、5、11、12（5 条）。代码逻辑未动，仅删除或改写了注释/docstring 行。
