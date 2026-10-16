# 注释整理处置清单 — metrics_pipeline.py

范围：输入文件中全部 13 条注释（含模块与函数 docstring）。处置：保留 7 条 / 改写 2 条 / 删除 4 条。代码语义零改动，仅调整注释。

---

**1. 第 1 行（模块 docstring）— 保留**
原文：`"""Order ingestion pipeline for the analytics service."""`
理由：文件内没有任何内容与之冲突，在没有反证的情况下保持原样是唯一不臆测的选择（文件名与 docstring 的表述差异不构成过时证据）。

**2. 第 10 行 — 删除**
原文：`# currently supports: CSV, JSON, Parquet.`
理由：逐字复述下一行的集合字面量，代码本身就是该事实最强的保管者，写两份只会同步漂移。

**3. 第 15 行 — 保留**
原文：`# serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").`
理由：回答了"这把锁为什么存在"这一非显然问题，并给出可核对的出处，正是注释应当承担的信息。

**4. 第 20 行（docstring）— 改写**
原文：`"""Token bucket shared by every caller in this process."""`
改为：`"""Sleeps one rate interval, then returns the {"burst", "rate"} config."""`
理由：原文与代码直接矛盾——代码既不实现 token bucket，也不存在任何跨调用者共享的状态（每次调用新造并返回一个字典）；改为如实描述可观察行为（sleep 的用意无法在文件内验证，故只陈述行为、不编造意图）。

**5. 第 25 行 — 删除**
原文：`# callers: ingest.py, backfill.py, admin_cli.py`
理由：调用方清单只在调用点才能被维护，写在这里必然滞后却仍会被信任，而"谁在调用"的检索永远是最新的。

**6. 第 27 行（docstring）— 保留**
原文：`"""Send one batch to the vendor, blocking until it is acknowledged."""`
理由：准确陈述函数契约（阻塞语义），与代码一致，无漂移风险。

**7. 第 28 行 — 改写（并入上方 docstring）**
原文：`# returns the number of processed records`
改为：docstring 末句 `Returns the number of processed records.`
理由：返回值是调用者需要知道的契约事实，埋在函数体内部调用者永远看不到，应放到契约面（docstring）上。

**8. 第 34 行 — 保留**
原文：`# counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.`
理由：解释了 `+1` 这一最容易被"顺手修正"的反直觉写法的上游依据，是防止把有意行为改成真 bug 的关键注释。

**9. 第 39 行 — 保留**
原文：`# format changed in v2.1: dates moved from local to UTC`
理由：已发生的版本化变更不会再度漂移，且"时间戳为 UTC"这一信息能直接防止时区假设错误。

**10. 第 43 行 — 保留**
原文：`# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).`
理由：给出常量取值背后的外部约束与可追查的 runbook 编号，属于典型的"为什么"注释。

**11. 第 48 行 — 删除**
原文：`# see line 57 for the rate-limiter setup`
理由：行号引用已失效（第 57 行是空行，该区域属于 LEGACY_FIELDS 相关内容），且它要指的内容就在下一行，删除后零信息损失。

**12. 第 53 行 — 删除**
原文：`# TODO: clean this up`
理由：无行动内容、无完成条件，永远不会被勾销，只会作为被信任的噪音永久留存。

**13. 第 58 行 — 保留**
原文：`` `# TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.` ``
理由：合格的待办——动作、触发条件（迁移落地）、外部追踪凭据（工单号）齐备，任何接管者都可核实其状态。

---

总判据：留下的注释只做三件事——回答"为什么"、陈述代码无法表达且不会漂移的事实、指向可核实的外部凭据（文档/工单/runbook）；凡是复述代码、依赖行号、或无法被勾销的清单与待办，一律删除或改写。
