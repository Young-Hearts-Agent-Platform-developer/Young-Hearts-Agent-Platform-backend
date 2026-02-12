# Consult 接口 SSE 改造研究报告

## 版本记录

| 日期 | 版本 | 修改内容 | 修改原因 |
|---|---|---|---|
| 2026-01-28 | v1.0 | 初始设计 | 规划 Consult 接口从自定义流式格式向标准 SSE 格式的迁移方案 |

## 研究问题

如何将 `POST /api/v1/consult/chat` 接口的返回格式从当前自定义的文本块流改为标准的 Server-Sent Events (SSE) 协议，以提高规范性并便于前端解析？

## 发现摘要

当前接口虽然声明了 `text/event-stream`，但实际上并未遵循 SSE 格式规范，导致标准客户端无法正确解析。
本研究提出了具体的 SSE 改造方案：
1.  **协议标准化**：定义明确的 `event` 类型（`message`, `topic`, `error`）。
2.  **数据封装**：所有下行数据必须遵循 `data: content\n\n` 格式，JSON 数据需序列化。
3.  **无新依赖**：利用现有的 FastAPI `StreamingResponse`，通过简单的字符串格式化即可实现，无需引入 `sse-starlette`。

## 相关文件清单

| 文件路径 | 作用说明 | 关键行号 |
|---|---|---|
| [app/api/v1/routes/consult.py](app/api/v1/routes/consult.py) | 需改造的流式响应接口 | L100-L140 |

## 当前实现回顾

目前的实现直接返回原始文本块，特殊指令（如错误、Topic）混杂在文本流中，依靠特殊前缀区分：
*   AI 内容：直接 yield 文本
*   错误：`[ERROR]...`
*   Topic：`[TOPIC]{...}`

**痛点**：
*   解析逻辑与业务逻辑耦合。
*   容易发生特殊字符碰撞（虽然概率低）。
*   不符合 Web 标准。

## SSE 对接方案设计

### 1. 协议规范

我们将使用标准的 SSE 字段：`event` 和 `data`。

| 场景 | Event Type | Data 格式 | 示例 |
|---|---|---|---|
| **AI 内容片段** | `message` (默认) | 纯文本 (Raw String) | `data: 你好` |
| **会话主题** | `topic` | JSON String | `data: {"topic": "打招呼"}` |
| **错误信息** | `error` | JSON String | `data: {"detail": "超时"}` |
| **结束信号** (可选) | `done` | String | `data: [DONE]` |

**注**：`data` 字段中的换行符需被转义（换成 `\n` 字面量）或者使用多行 `data`，但在传输简短文本片段时，直接发送即可。对于 JSON 数据，`json.dumps` 默认不包含换行符，是安全的。

### 2. 代码改造逻辑

#### 辅助函数

建议在 `app/api/v1/routes/consult.py` 或 `app/utils_openapi.py` (如果合适，或者新建 utils) 中添加 SSE 格式化函数：

```python
def format_sse(data: str, event: str = "message") -> str:
    """
    格式化为 SSE 字符串。
    注意：data 中如果包含换行符，标准 SSE 建议每行都加 'data: ' 前缀，
    或者仅转义换行。对于我们的场景，AI chunk 通常不含复杂换行，
    JSON dumps 也是单行。
    """
    return f"event: {event}\ndata: {data}\n\n"
```

#### Generator 逻辑重构

需要修改 `app/api/v1/routes/consult.py` 中的 `event_stream` 函数：

```python
# 伪代码逻辑
async def event_stream():
    ai_reply = ""
    error_flag = False
    
    try:
        async for chunk in service.chat_with_rag(...):
            ai_reply += chunk
            # 1. 发送内容片段
            yield format_sse(chunk, event="message")
            
    except Exception as e:
        error_flag = True
        # 2. 发送错误
        error_payload = json.dumps({"detail": str(e)}, ensure_ascii=False)
        yield format_sse(error_payload, event="error")
    
    # ... (持久化逻辑不变) ...

    # 3. 发送 Topic
    if topic:
        topic_payload = json.dumps({"topic": topic}, ensure_ascii=False)
        yield format_sse(topic_payload, event="topic")
        
    # 4. 可选：发送结束信号 (如果是为了兼容某些 OpenAI 风格的客户端)
    # yield format_sse("[DONE]", event="done")
```

## 前端对接说明

由于接口是 `POST` 方法，**浏览器原生的 `EventSource` API 不支持**。
前端必须使用支持 POST 的 SSE 客户端库，或者使用 `fetch` + `ReadableStream` 手动解析。

**解析逻辑建议**：
1.  读取数据流，按 `\n\n` 分割消息。
2.  解析每一条消息，提取 `event:` 和 `data:` 字段。
    *   若 `event` 为 `message` -> 追加 AI 回复显示。
    *   若 `event` 为 `topic` -> `JSON.parse` 后更新会话标题。
    *   若 `event` 为 `error` -> 显示错误提示。

**示例数据流**：
```text
event: message
data: 你好

event: message
data: ，

event: message
data: 请问

event: topic
data: {"topic": "咨询开场"}
```

## 风险与注意事项

1.  **换行符处理**：如果 AI 生成的内容片段本身包含换行符（例如代码块），直接放在 `data: ` 后面可能会破坏 SSE 格式。
    *   **解决方案**：简单的做法是将内容中的 `\n` 替换为 `\\n` (转义)，或者在此处使用 JSON 序列化 data 内容（即 `data: "line1\nline2"`）。**推荐对于 `message` 类型也进行 JSON 序列化**，这样最稳健，但前端需多一步 parse。
    *   **妥协方案**：如果前端希望直接拼接字符串，需确保后端发送时处理了换行。标准做法是多行 `data`：
        ```
        data: first line
        data: second line
        ```
2.  **兼容性**：前端必须同步修改，否则看到的数据将包含 `event: ... data: ...` 这样的原始内容。

## 结论

建议按照上述方案实施改造。由于涉及前后端协议变更，需与前端开发人员（罗问然对接的前端）协调上线时间。
