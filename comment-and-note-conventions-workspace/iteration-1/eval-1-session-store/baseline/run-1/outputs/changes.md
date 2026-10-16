# 注释整理记录 — session_store.js

只改动注释文本，未触碰任何代码 token，文件语义与行为不变。原文件共 10 处注释，逐条处置如下（行号为原文件行号）。

| # | 位置 | 原注释 | 处置 | 理由 |
|---|------|--------|------|------|
| 1 | 行 1（文件头） | `Session store for the web app. Sessions are read on every request.` | 改写 | 前半句复述文件名、属废话；后半句"每次请求都读取"是代码外的关键使用事实——删头留尾，改为 `// Sessions are read on every request.` |
| 2 | 行 5–6 | `MIRROR of auth-service SessionPolicy …` | 保留 | 跨服务耦合 + 守卫测试名 + 漂移后果，三项均无法从代码推出，是可信注释的标杆。 |
| 3 | 行 10 | `iterate sessions and find expired ones` | 删除 | 纯复述紧下面三行循环的字面行为，零信息量。 |
| 4 | 行 17 | `keep in sync with the mobile SDK copy of this policy` | 保留 | 解释了 `POLICY_VERSION` 常量为何存在及其跨端同步义务，代码中无迹可寻。 |
| 5 | 行 20 | `Chrome evicts storage under memory pressure — client-side session persistence is best-effort.` | 保留 | 交代了 `persistLocally` 为何允许不可靠的领域前提（浏览器可能回收存储），非代码可推导；无法证伪，不做改写。 |
| 6 | 行 25 | `ported from the callback version during the perf pass` | 删除 | 变更史考古，描述的是已不存在的"回调版本"；历史交给 git blame，留在代码旁只会继续腐烂。 |
| 7 | 行 27 | `eslint-disable-next-line no-await-in-loop -- refresh must stay ordered …` | 保留 | 解释了故意保留 await-in-loop 的原因（保持 TTL 顺序），防止后人"顺手优化"成 `Promise.all`；eslint 抑制注释必须携带理由。 |
| 8 | 行 33 | `sessions now live in Redis; DB-backed storage planned for Q3.` | 删除 | "now"与"planned for Q3"（哪个 Q3？）是典型会腐烂的时间性承诺，属"绝不能写进被信任之处的注"；仅剩的"会话存 Redis"已被 `TRANSPORT = "redis"` 和 redis 调用自证。路线图应留在 issue 里。 |
| 9 | 行 36 | `see redis_session_ttl in infra/tuning.tf` | 保留 | 指向调优值的权威出处，是指针型注释：正当、精炼、可自行核验。 |
| 10 | 行 39 | `TTL was 15m until v3.2; support wanted 30m (see #441).` | 改写 | "was 15m until v3.2"是版本考古（git 已保存）；保留决策出处，改为 `// 30m TTL per support request #441.` |

**汇总：保留 5 / 改写 2 / 删除 3（共 10 处）。**

补充原则说明：

- 删除的都不是"事实错误"，而是**结构性不可信**的注：复述代码（#3）、历史考古（#6）、未来承诺（#8）——它们没有守卫者，注定在后续演进中失真。它们承载的原始信息各有归宿：git 历史、issue 台账。
- 保留/改写后的每条注都满足一条：所在位置发生变化时，它有理由被同时更新（镜像契约有测试守护、指针可核验、理由是常量存在的唯一解释）。
