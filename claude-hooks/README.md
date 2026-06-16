# Claude Code Hooks — 变更收集与自动 Review

基于 Claude Code 官方 hook 系统实现的一组脚本，将 **UserPromptSubmit → Stop** 周期内的文件变更自动收集，并在 Claude 即将停止时注入 review 提示，触发 Claude 自动审查代码。

## 生命周期

```
UserPromptSubmit  →  clear-change-cache.sh  清空变更缓存 + 守护文件
     │
     ▼
PostToolUse × N   →  record-change.sh       将 Write/Edit 操作写入变更记录
     │
     ▼
Stop              →  review-session.sh      汇总变更 → 注入 additionalContext
                                             无变更 → 跳过
```

## 配置

**`settings.local.json`** 注册三个 hook：

| Hook 事件 | Matcher | 脚本 | 超时 |
|---|---|---|---|
| `UserPromptSubmit` | (无，始终触发) | `clear-change-cache.sh` | 5s |
| `PostToolUse` | `Write\|Edit` | `record-change.sh` | 5s |
| `Stop` | (无，始终触发) | `review-session.sh` | 15s |

**`config.json`** 定义文件匹配规则和 review 提示：

- `include`: 只记录匹配这些 glob 的文件变更
- `exclude`: 排除匹配的文件（优先于 include）
- `promptFile`: 指向自定义 review 提示的 markdown 文件

---

## Hook 契约

### 1. UserPromptSubmit — `clear-change-cache.sh`

每次用户提交 prompt 时触发，在 Claude 处理之前运行。

#### stdin 输入（Claude Code 传入）

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "用户提交的文本"
}
```

> 官方文档：[UserPromptSubmit](https://code.claude.com/docs/zh-CN/hooks#userpromptsubmit)

#### 脚本行为

| 操作 | 说明 |
|---|---|
| 从 stdin 解析 `session_id`、`cwd` | 使用 `jq` 提取 |
| 删除 `{cwd}/.claude/cache/{session_id}/changes/` | 清空上一周期的变更缓存 |
| 删除 `{cwd}/.claude/cache/{session_id}/.reviewed` | 重置守护文件，允许新周期触发 review |
| stdout | 无输出 |
| exit code | 始终 0 |

---

### 2. PostToolUse — `record-change.sh`

每次 Write 或 Edit 工具调用成功后触发。

#### stdin 输入（Claude Code 传入）

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "src/index.ts",
    "content": "export const x = 1;\n"
  },
  "tool_response": {
    "filePath": "src/index.ts",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123...",
  "duration_ms": 12
}
```

Edit 操作的 `tool_input` 包含 `old_string`、`new_string` 和可选的 `replace_all`。

> 官方文档：[PostToolUse](https://code.claude.com/docs/zh-CN/hooks#posttooluse)

#### 脚本行为

| 操作 | 说明 |
|---|---|
| 跳过 `agent_id` 存在的调用 | 子 agent 的变更不记录 |
| 跳过非 Write/Edit 工具 | 仅记录文件写入和编辑 |
| 文件路径 Glob 匹配 | 通过 `config.json` 的 include/exclude 过滤 |
| 写入变更记录到磁盘 | `{cwd}/.claude/cache/{session_id}/changes/{timestamp}_{random}.json` |

#### 输出（变更记录文件）

**Write 操作**：
```json
{
  "tool": "Write",
  "file_path": "src/index.ts",
  "timestamp": "2026-06-16T10:00:00Z",
  "action": "write",
  "lines": 5,
  "content": "export const x = 1;\nexport const y = 2;\n"
}
```

**Edit 操作**：
```json
{
  "tool": "Edit",
  "file_path": "src/utils.ts",
  "timestamp": "2026-06-16T10:01:00Z",
  "action": "edit",
  "old_lines": 3,
  "new_lines": 2,
  "old": "原始文本",
  "new": "替换文本"
}
```

---

### 3. Stop — `review-session.sh`

Claude 完成响应、即将停止时触发。

#### stdin 输入（Claude Code 传入）

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": false,
  "last_assistant_message": "Claude 最后一条回复的文本...",
  "background_tasks": [],
  "session_crons": []
}
```

> 官方文档：[Stop](https://code.claude.com/docs/zh-CN/hooks#stop)

#### 脚本行为

| 操作 | 说明 |
|---|---|
| 检查 `.reviewed` 守护文件 | 存在则跳过（防重复触发） |
| 检查 `changes/` 目录 | 无变更记录则跳过 |
| 汇总所有变更记录 | total_edits, total_lines, file_paths 去重 |
| 构建 review 提示 | 使用 `config.json` → `promptFile` 或默认内置提示 |
| 写入 `summary.md` | 保存汇总报告 |
| 创建 `.reviewed` 守护文件 | 防止同一周期内重复注入 |

#### 输出（stdout JSON，有变更时）

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "## 会话变更摘要\n\n- **变更次数**: 3 次\n- **涉及文件**: 2 个\n- **新增行数**: ~42\n- **删除行数**: ~8\n\n### 变更文件列表\n  - `src/login.ts`\n  - `src/auth.ts`\n\n### 详细变更记录\n`.claude/cache/abc123/changes/`\n\n---\n请 review 本次会话的所有代码变更..."
  }
}
```

`additionalContext` 被 Claude Code 注入为 `<system-reminder>`，Claude 看到后会继续执行 review。无变更时 stdout 为空，Claude 正常停止。

> 根据官方文档，Stop hook 使用 `hookSpecificOutput.additionalContext` 是**推荐的非错误反馈方式**。`decision: "block"` 用于阻止停止的错误路径。

#### 输出（无变更时）

```
(空 — review 流程跳过，Claude 正常停止)
```

---

## 缓存文件布局

```
{project}/.claude/cache/{session_id}/
├── changes/              # PostToolUse 写入的变更记录
│   ├── 20260616T100000_12345.json
│   └── 20260616T100001_67890.json
├── summary.md            # Stop 钩子写入的汇总报告
└── .reviewed             # 守护文件（存在则 Stop 跳过）
```

每次 `UserPromptSubmit` 触发时，`changes/` 目录和 `.reviewed` 文件被清空。

---

## 测试

```bash
# 22 个单元测试（边界条件、回归）
bash claude-hooks/tests/test-hooks.sh

# 11 个 I/O 契约测试（展示每个 case 的输入 JSON 和输出结果）
bash claude-hooks/tests/test-io.sh
```

要求：`bash`（非 POSIX sh）、`jq`。

---

## 文件清单

| 文件 | 用途 |
|---|---|
| `settings.local.json` | Hook 注册配置 |
| `hooks/config.json` | 文件匹配规则 + promptFile 路径 |
| `hooks/review-prompt.md` | 自定义 review 提示（被 config.json 引用） |
| `hooks/clear-change-cache.sh` | UserPromptSubmit hook — 清空变更缓存 |
| `hooks/record-change.sh` | PostToolUse hook — 记录文件变更 |
| `hooks/review-session.sh` | Stop hook — 汇总变更并注入 review |
| `tests/test-hooks.sh` | 单元测试 (22 cases) |
| `tests/test-io.sh` | I/O 契约测试 (11 assertions) |
| `docs/hooks.md` | Claude Code 官方 hooks 参考文档 |
