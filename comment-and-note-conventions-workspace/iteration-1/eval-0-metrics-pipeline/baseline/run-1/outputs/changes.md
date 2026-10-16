# 注释整理记录

- 整理对象：原 `scenarios/metrics_pipeline.py`（共 13 处注释/说明位置）。
- 整理原则：留下的每条注释都必须可信——要么解释了代码读不出的关键信息，要么有可核验的引用；复述代码的、会漂移的、误导的一律删除或改写。
- 除注释与 docstring 文本外，未改动任何代码，行为语义保持原样。
- 下文行号均指**原文件**行号。

## 逐条处置

1. **L1 模块 docstring** — `"""Order ingestion pipeline for the analytics service."""`
   - 处置：保留
   - 理由：一句话说清模块职责，不含任何会随版本漂移的细节，是文档字符串的标准写法。

2. **L10 `# currently supports: CSV, JSON, Parquet.`**
   - 处置：删除
   - 理由：下一行 `SUPPORTED_FORMATS = {"csv", "json", "parquet"}` 已逐字表达同一事实，注释纯属复述；"currently" 还暗示需要人工同步，只会变成会撒谎的冗余。

3. **L15 `# serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").`**
   - 处置：保留
   - 理由：解释了 `_lock` 存在的真正原因，代码本身完全看不出，且给出可核验来源（vendor 文档章节）。

4. **L20 `"""Token bucket shared by every caller in this process."""`**
   - 处置：改写
   - 原文：`"""Token bucket shared by every caller in this process."""`
   - 现文：`"""Sleeps one token interval, then returns the limiter parameters ({'burst', 'rate'}). It installs no shared state itself, despite the name."""`
   - 理由：原文声称"进程内所有调用者共享的 token bucket"，与代码矛盾——函数只是 sleep 一个间隔并返回参数字典，不创建、不注册任何共享状态，属误导性注释；改写为如实描述行为，并点破名实不符（函数名与行为的落差是代码问题，不在本次注释整理范围内，仅通过注释如实呈现）。

5. **L25 `# callers: ingest.py, backfill.py, admin_cli.py`**
   - 处置：删除
   - 理由：调用方列表随代码演进必然过期，且在被调方无法维护（新增调用方的人不会回来改这里）；需要时用一次搜索即可得到，留在原地只会制造"改这里很安全"的虚假确信。

6. **L27 `"""Send one batch to the vendor, blocking until it is acknowledged."""`**
   - 处置：保留（文字本身未动，仅在条目 7 的改写中与返回值说明合并）。

7. **L28 `# returns the number of processed records`**
   - 处置：改写（并入 L27 的 docstring）
   - 现文：`"""Send one batch to the vendor, blocking until it is acknowledged; returns the number of processed records."""`
   - 理由：该事实（`sdk.send` 返回已处理记录数）代码读不出来、调用方却需要，值得留；但函数契约应写在 docstring，而不是作为一句 `# returns ...` 漂在函数体里——内容保留、位置纠正。

8. **L34 `# counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.`**
   - 处置：保留
   - 理由：点明 `limit + 1` 看似 off-by-one、实为上游分页 API 双端闭区间的契约，防止后人把它当 bug"修掉"。

9. **L39 `# format changed in v2.1: dates moved from local to UTC`**
   - 处置：改写
   - 原文：`# format changed in v2.1: dates moved from local to UTC`
   - 现文：`# parsed dates are UTC (changed from local in v2.1).`
   - 理由：时区语义（输出为 UTC）是下游消费方必须知道、代码读不出的硬事实，值得保留；但原句以"format changed"叙事、主语含糊（说的其实是取值而非格式），改写为现在时契约并保留 v2.1 这一可核验的版本锚点。

10. **L43 `# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).`**
    - 处置：保留
    - 理由：解释了 `RETRY_WINDOW = 60` 指代的外部机制（网关按租户计重试、20/min 触发熔断），并附运行手册编号可核验，是典型的"为什么"注释。

11. **L48 `# see line 57 for the rate-limiter setup`**
    - 处置：删除
    - 理由：行号引用已失效——第 57 行不是限流器设置（限流器定义在第 19–22 行）；且紧接的下一行就按名字调用了 `_install_rate_limiter`，该注释既错又冗余。行号引用本身也是必然腐化的形式。

12. **L53 `# TODO: clean this up`**
    - 处置：删除
    - 理由：无对象、无条件、无工单，读者无法据此行动，只是噪音；与之对比 L58 的 TODO 即为正确形态。

13. **L58 `# TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.`**
    - 处置：保留
    - 理由：有明确动作（删除 `ts`）、明确触发条件（billing 团队迁移落地）和可追踪工单号，是 TODO 应有的完整形态。

## 汇总

- 保留 6（L1、L15、L27、L34、L43、L58）
- 改写 3（L20、L28、L39）
- 删除 4（L10、L25、L48、L53）
- 合计 13 处，与原文注释位置一一对应。
