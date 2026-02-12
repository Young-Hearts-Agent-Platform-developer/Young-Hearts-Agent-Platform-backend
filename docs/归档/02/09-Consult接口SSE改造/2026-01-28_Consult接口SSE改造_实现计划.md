# Consult 接口 SSE 改造实现计划

## 版本记录

| 日期 | 版本 | 修改内容 | 修改原因 |
|---|---|---|---|
| 2026-01-28 | v1.0 | 初始计划 | 基于研究报告及用户针对 JSON 格式、结束信号的补充要求制定 |

## 关联研究
[2026-01-28_Consult接口SSE改造_研究报告.md](docs/tasks/罗问然/09-Consult接口SSE改造/2026-01-28_Consult接口SSE改造_研究报告.md)

## 功能概述
将 `POST /api/v1/consult/chat` 接口当前的自定义流式响应改造为标准的 Server-Sent Events (SSE) 协议。
前端将不再需要解析特殊的 `[TOPIC]` 或 `[ERROR]` 前缀，而是通过 `event` 字段区分消息类型。
同时，规范化消息体格式：所有 payload 均为 JSON 格式（除结束信号外），且 AI 内容片段封装在 `{"content": "..."}` 结构中。

## Phase 1: SSE 工具函数实现

### 目标
在接口文件中实现私有的 SSE 格式化辅助函数，统一处理 JSON 序列化和协议格式。

### 修改文件清单
| 文件路径 | 修改类型 | 说明 |
|---|---|---|
| [app/api/v1/routes/consult.py](app/api/v1/routes/consult.py) | Edit | 添加 `_format_sse` 辅助函数 |

### 具体变更
在 `app/api/v1/routes/consult.py` 中定义辅助函数：

```python
# 伪代码 - 将放置在 event_stream 函数定义之前
def _format_sse(event: str, data: Any) -> str:
    """
    格式化为 SSE 消息字符串。
    
    Args:
        event: 事件类型 (message, topic, error, done)
        data: 数据载荷。
              - 如果是 dict，将被 json.dumps
              - 如果是 str 且 event != 'done'，将被封装为 {"content": str} 后 dumps (针对 message)
              - 如果是 'done' 事件，data 保持原样 (通常为 [DONE])
    """
    payload = ""
    if event == "done":
        payload = str(data)
    elif event == "message" and isinstance(data, str):
        # 用户要求: message 事件的内容需封装为 { "content": "..." }
        payload = json.dumps({"content": data}, ensure_ascii=False)
    else:
        # topic, error 或其他 dict 数据
        payload = json.dumps(data, ensure_ascii=False)
        
    return f"event: {event}\ndata: {payload}\n\n"
```

## Phase 2: 业务逻辑 SSE 迁移

### 目标
重构 `event_stream` 生成器，使用新的 SSE 格式替代旧的文本拼接方式。

### 修改文件清单
| 文件路径 | 修改类型 | 说明 |
|---|---|---|
| [app/api/v1/routes/consult.py](app/api/v1/routes/consult.py) | Edit | 重写 `event_stream` 内部 yield 逻辑 |

### 具体变更
修改 `event_stream` 函数内部逻辑：

1.  **AI 内容片段 (Yield Chunk)**:
    *   **旧**: `yield chunk`
    *   **新**: `yield _format_sse(event="message", data=chunk)` (实际输出 data: `{"content": "..."}`)

2.  **错误处理 (Error)**:
    *   **旧**: `yield f"[ERROR]{error_msg}"`
    *   **新**: `yield _format_sse(event="error", data={"detail": error_msg})`

3.  **Topic 生成 (Topic)**:
    *   **旧**: `yield f"[TOPIC]{json.dumps({'topic': topic})}"`
    *   **新**: `yield _format_sse(event="topic", data={"topic": topic})`

4.  **结束信号 (Done)**:
    *   **新增**: 在流结束前 (正常结束或异常结束最后) 发送 `yield _format_sse(event="done", data="[DONE]")`

### 验证标准
*   使用 `curl` 或 Python 脚本请求接口：
    ```bash
    curl -X POST http://localhost:8000/api/v1/consult/chat ...
    ```
*   **Checkpoint 1**: 响应头包含 `Content-Type: text/event-stream` (维持现状)。
*   **Checkpoint 2**: 每一块数据应形如：
    ```
    event: message
    data: {"content": "你好"}

    ```
*   **Checkpoint 3**: 结束时收到：
    ```
    event: done
    data: [DONE]

    ```

## Phase 3: 验证脚本

### 目标
创建一个临时的手动测试脚本，用于验证 SSE 格式是否符合设计。

### 修改文件清单
| 文件路径 | 修改类型 | 说明 |
|---|---|---|
| [tests/manual_test_sse.py](tests/manual_test_sse.py) | Create | 新建测试脚本 |

### 具体变更
创建脚本，模拟 POST 请求并打印 raw bytes 以人工核对 SSE 格式。

```python
import requests
import json

def test_sse():
    url = "http://localhost:8000/api/v1/consult/chat"
    # 需替换为有效的 token 和 session_id
    headers = {"Authorization": "Bearer ..."} 
    data = {
        "session_id": "...",
        "query": "测试SSE"
    }
    
    with requests.post(url, json=data, headers=headers, stream=True) as r:
        for line in r.iter_lines():
            if line:
                print(line.decode('utf-8'))

if __name__ == "__main__":
    print("请先手动填入有效的 Token 和 Session ID 运行此测试")
    # test_sse()
```

## 下一步建议
实施完成后，需通知前端（罗问然对接组）按照新文档进行解析逻辑的更新。
PR 描述中应明确指出这是一个 **Breaking Change**（尽管旧的解析逻辑可能只是乱码，但实质协议已变）。
