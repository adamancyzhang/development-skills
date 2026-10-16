# 注释整理记录 — metrics_pipeline.py

范围：只动注释与 docstring 文本，代码零改动（导入、常量、函数签名、函数体、行为完全不变）。
原文件共 13 条注释/docstring：**保留 7 / 改写 2 / 删除 4**。
判定基准（comment-and-note-conventions）：谁在维护这句话为真（keeper）；这是谁的事实、家在哪；失真时谁受损、谁的搜索被省下。行号均指原输入文件。

## 逐条处置

### 1. 模块 docstring（原 L1）— 保留
> "Order ingestion pipeline for the analytics service."
理由：模块职责（订单摄取、服务分析）无法从模块名与代码推出，是模块门口唯一的口径声明；事实与模块同生共死，邻域即 keeper。

### 2. 格式常量注释（原 L10）— 删除
> # currently supports: CSV, JSON, Parquet.
理由：与其下方字面集合 `{"csv","json","parquet"}` 逐字重复，读者零成本即可从代码获得；"currently" 又是快照语态，删除后没有任何搜索被牺牲。

### 3. 锁注释（原 L15）— 保留
> # serialized: the vendor SDK is not thread-safe (see vendor docs, "Concurrency").
理由：解释 `_lock` 存在的理由（外部契约：vendor SDK 非线程安全，且指向可查的文档小节）；删除会诱使后人误删锁或改细粒度。

### 4. _install_rate_limiter docstring（原 L20）— 改写
> 原："Token bucket shared by every caller in this process." → 新："Applies a single 1/per_second pacing delay and returns the limiter parameters; no shared state — it throttles no other caller."
理由：原句与实现直接矛盾（函数不安装任何共享状态，返回值在唯一调用处被丢弃），会让人误以为存在进程级限流——而网关 20/min 熔断（见 RB-7）的安全边界正依赖对此的正确认知；改写为如实的契约陈述，并显式否定"限流他人"。
备注：原句像是在替一个已被替换或未完成的旧实现背书；若限流本应存在，建议开单跟进（这属于 tracker，不属于注释）。

### 5. 调用方清单（原 L24）— 删除
> # callers: ingest.py, backfill.py, admin_cli.py
理由：调用关系的家在调用点与工具检索里；这张清单无人续约，第一个未列出的调用者出现即失真（第二份事实副本），保留只会制造假信心。

### 6. send_batch docstring（原 L27）— 保留
> "Send one batch to the vendor, blocking until it is acknowledged."
理由：外部契约（阻塞语义、被确认后才返回）无法从代码推出（sdk 是外部依赖）；keeper 在本仓库之外、无法就地核验，按纪律保留。

### 7. 返回值注释（原 L28）— 保留
> # returns the number of processed records
理由：返回计数的口径（数的是"已处理记录数"而非已发送数等）是签名与代码都无法携带的语义，且紧贴 return——离事实最近的位置。

### 8. page 注释（原 L34）— 保留
> # counterintuitive: looks like an off-by-one; the upstream page API is inclusive on both ends.
理由：教科书式的反直觉提示（上游分页 API 双端包含），防止下一位细心读者"修好"一个并不存在的 off-by-one。

### 9. parse_dates 注释（原 L39）— 改写
> 原："# format changed in v2.1: dates moved from local to UTC" → 新："# dates are UTC — vendor format v2.1 onward (earlier formats were local time)."
理由：事实（时间戳为 UTC、v2.1 是分界）值得活，但"format changed in v2.1"是过去的旅程叙述，其家应属 vendor 变更记录；改写为现在时的事实本身，并保留可查的版本锚点。

### 10. RETRY_WINDOW 注释（原 L43）— 保留
> # the gateway counts retries per tenant; crossing 20/min trips a circuit breaker (ops runbook RB-7).
理由：外部契约加失效模式（按租户计重试、20/分钟触发熔断、后果是什么），并把这条事实的家指给 ops runbook——一个可查的名字而非会漂移的行号。

### 11. "# see line 57"（原 L48）— 删除
> # see line 57 for the rate-limiter setup
理由：行号指针，且已经与地面不符——原文件第 57 行是 BILL-1421 的 TODO，并非限流设置；任何编辑还会让它继续漂移，而它想指的内容就在下一行、按名字即可找到，搜索价值为零。

### 12. "# TODO: clean this up"（原 L53）— 删除
> # TODO: clean this up
理由：裸意图——无 owner、无工单、无触发条件，不指名任何 keeper；按纪律应移入 tracker，此处无 tracker 可达，故丢弃（不为它编造 keeper）。

### 13. 遗留字段 TODO（原 L58）— 保留
> # TODO: drop the legacy `ts` field once the billing team's migration lands — ticket BILL-1421.
理由：意图指名了 keeper（工单 BILL-1421）与触发条件（billing 迁移落地），可站立于其后果落点；keeper 在本仓库之外、无法就地核验，按纪律保留。

## 汇总

| 处置 | 条目 | 数量 |
| --- | --- | --- |
| 保留 | 1, 3, 6, 7, 8, 10, 13 | 7 |
| 改写 | 4, 9 | 2 |
| 删除 | 2, 5, 11, 12 | 4 |
