# metrics_pipeline.py — 注释逐条处置清单

口径：留下的每条注释都须有 keeper（机制 / 就近的改动者 / 具名的人或流程），只讲代码说不出、且与当下事实相符的内容。只动注释与 docstring，代码逐字未改、语义不变。共 13 条：**保留 7，改写 2，删除 4**。

按原文件行号逐条：

1. **L1 模块 docstring** `"""Order ingestion pipeline for the analytics service."""` — 【保留】模块用途与所属系统（analytics 服务的订单摄取管道）从代码推不出来，模块首页就是它的家。
2. **L10** `# currently supports: CSV, JSON, Parquet.` — 【删除】纯复述下一行集合字面量已完整声明的事实，"currently" 还是无主的现状快照；集合自身才是这条事实唯一、不会漂移的家。
3. **L15** `# serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").` — 【保留】给出代码说不出的理由（外部 SDK 非线程安全，必须串行化），防止后人把锁当冗余删掉；vendor 文档是具名出处。
4. **L20** `"""Token bucket shared by every caller in this process."""` — 【改写】原文描述了一个不存在的机制（代码只是一次阻塞式 sleep，无任何共享状态），留着必误导；改为真实语义，保住 docstring 位置。→ `"""Blocks the calling thread for 1/per_second seconds per call; no shared state."""`
5. **L25** `# callers: ingest.py, backfill.py, admin_cli.py` — 【删除】grep/IDE 随时能算出的调用者清单，手写副本等不来新增的调用者（典型静默腐烂），无 keeper。
6. **L27** `"""Send one batch to the vendor, blocking until it is acknowledged."""` — 【保留】"blocking until acknowledged" 是 vendor 侧的调用契约，代码与函数名都表达不出。
7. **L28** `# returns the number of processed records` — 【保留】返回值口径（处理记录数）藏在不透明的 sdk.send 里，这条注释是它在本仓唯一的家，且紧贴 return。
8. **L34** `# counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.` — 【保留】正是"看起来像错、其实不是"的反直觉行，不写就会被后人"修复"。
9. **L39** `# format changed in v2.1: dates moved from local to UTC` — 【改写】原文是过去时变更日记（变更史属于变更自己的记录），但内含现役事实：v2.1 起日期为 UTC；改为现时口径，保住时区边界。→ `# v2.1+ dates are UTC (pre-v2.1 data is local time).`
10. **L43** `# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).` — 【保留】60 秒窗口的理由在仓库之外（网关按租户计重试、20/min 触发熔断），仓外 keeper 的事实按纪律保留；跑单编号给了可查的名字。
11. **L48** `# see line 57 for the rate-limiter setup` — 【删除】行号是最不耐久的引用，且第 57 行今天已是空行——地图比地面先烂；下方调用 `_install_rate_limiter` 自带可检索的名字。
12. **L53** `# TODO: clean this up` — 【删除】无 owner、无触发条件、无内容的裸意图（"this" 指什么、"clean" 到什么程度都无从执行），没人能兑现。
13. **L58** ``# TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.`` — 【保留】意图具名了 keeper（票号 BILL-1421）与触发条件（billing 迁移落地），且站在其后果 LEGACY_FIELDS 旁边。

汇总：保留 7 条（L1、L15、L27、L28、L34、L43、L58）｜改写 2 条（L20、L39）｜删除 4 条（L10、L25、L48、L53）。代码行零改动（AST 剥除 docstring 后与原文件一致，已实测）。
