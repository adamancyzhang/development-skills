# changes.md —— metrics_pipeline.py 注释处置清单

处置统计：保留 7 / 改写 1 / 删除 5（共 13 处注释与 docstring）。
除下列处置外，代码行逐字未动；未改变任何运行行为。

判定依据（skill 的审查框架）：这句由谁看护、事实归谁、失真时什么会坏、谁会及时察觉 —— 进而决定 保留 / 就地改写 / 删除。

| # | 原行号 | 原文（摘） | 处置 |
|---|--------|-----------|------|
| 1 | L1 | `"""Order ingestion pipeline for the analytics service."""` | 保留 |
| 2 | L10 | `# currently supports: CSV, JSON, Parquet.` | 删除 |
| 3 | L15 | `# serialized: the vendor SDK is not thread-safe ...` | 保留 |
| 4 | L20 | `"""Token bucket shared by every caller in this process."""` | 删除 |
| 5 | L25 | `# callers: ingest.py, backfill.py, admin_cli.py` | 删除 |
| 6 | L27 | `"""Send one batch to the vendor, blocking until it is acknowledged."""` | 保留 |
| 7 | L28 | `# returns the number of processed records` | 保留 |
| 8 | L34 | `# counterintuitive: looks like an off-by-one; the upstream page API is inclusive ...` | 保留 |
| 9 | L39 | `# format changed in v2.1: dates moved from local to UTC` | 改写 |
| 10 | L43 | `# the gateway counts retries per tenant; crossing 20/min trips a circuit breaker ...` | 保留 |
| 11 | L48 | `# see line 57 for the rate-limiter setup` | 删除 |
| 12 | L53 | `# TODO: clean this up` | 删除 |
| 13 | L58 | `# TODO: drop the legacy \`ts\` field ... — ticket BILL-1421.` | 保留 |

## 逐条理由

1. **L1 模块 docstring — 保留**：陈述了模块在系统里的角色（订单摄入、面向分析服务），这是代码本身表达不出的事实，且模块存在一天就有邻域看护它。
2. **L10 `# currently supports: ...` — 删除**：下一行的集合字面量已逐字声明同样内容，属纯复述，且 "currently" 是无人看守的时态快照，只会先于代码腐烂。
3. **L15 锁的说明 — 保留**：解释了 `_lock` 存在的理由（外部契约：厂商 SDK 非线程安全），是代码说不出的 why；引用的文档小节名可检索，不会随位置移动而失联。
4. **L20 `_install_rate_limiter` 的 docstring — 删除**：邻近代码只做一次 `sleep` 并返参数字典，不存在任何"进程级共享"的令牌桶，该句与代码直接矛盾，是一句会被读者当真、却从来没人维护的假话；删掉后其自述内容均可从函数名与实现读出，没有事实损失。
5. **L25 `# callers: ...` — 删除**：调用方清单会被下一次新增调用悄悄作废（"calls declare themselves"），是典型的第一份过时就出错的第二副本，无机制能保持它属实。
6. **L27 `send_batch` docstring — 保留**：承载的是厂商调用的外部契约语义（阻塞直至被确认），代码与函数名都表达不出，失真时调用方的时序假设会崩。
7. **L28 `# returns the number of processed records` — 保留**：返回值的口径（数字 = 已处理记录数）是调用方必须知道、而 `sdk.send` 的返回值本身说不出的信息，且紧贴其主体。
8. **L34 `# counterintuitive: ...` — 保留**：防止后来者把有意的 `limit + 1` 当错误"修掉"；"上游 API 双端包含"是代码无法表达的外部事实，正是该留下的一句。
9. **L39 `# format changed in v2.1: ...` — 改写为 `# raw dates are UTC`**：历史叙述（v2.1 迁移）应归变更记录，此处耐久的事实是日期口径（UTC）；改写为现在时事实，去掉会无声腐烂的日记部分。
10. **L43 重试/断路器说明 — 保留**：外部约束与失效后果（每租户计数、20/min 触发断路器）说了出问题时会怎么坏，并署名权威出处（ops runbook RB-7）；约束仍由网关执行，失真时损失真实且可察觉。
11. **L48 `# see line 57 ...` — 删除**：指路型注释，位置会移动（且此指针已经指错——第 57 行并非限流设置），而它所指的东西就在下一行、抬头可见；没有携带任何独有事实，只剩误导。
12. **L53 `# TODO: clean this up` — 删除**：无主、无触发条件、无票号的模糊意图，"清理什么"本身都不可判定——没有 keeper、失真也无后果可言。
13. **L58 BILL-1421 TODO — 保留**：有明确的负责人（计费团队）、触发事件（迁移落地）与追踪票号（BILL-1421），且紧贴届时将被删除的常量本身，是能诚实死亡的有主意图，与第 12 条形成对照。

## 备注

- 唯一改写处为 L39；改写只去掉历史叙述、保留同一条耐久事实。
- 全部保留项原样未动（不因措辞风格做无谓翻新）。
- 删去 L20 后 `_install_rate_limiter` 不再有 docstring：这是诚实的缺失——读者会转向代码本身，而代码是唯一的真相所在；若日后确需表达限流设计意图，应由机制（测试/生成）或持有人看护后重新落笔。
