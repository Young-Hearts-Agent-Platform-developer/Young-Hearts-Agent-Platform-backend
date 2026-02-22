#!/usr/bin/env python3
import os
import json
import requests
import sys


def load_dotenv(path=".env"):
    """简单读取 .env 文件并把键值对写入 os.environ（不覆盖已存在值）。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # 去除两侧引号
                if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
                    val = val[1:-1]
                # 仅在环境变量不存在时设置
                if os.getenv(key) is None:
                    os.environ[key] = val
    except FileNotFoundError:
        return


load_dotenv()

API_KEY = os.getenv("DOUBAO_EMBEDDING_API_KEY") or os.getenv("ark_api_key")
BASE_URL = os.getenv("DOUBAO_EMBEDDING_BASE_URL") or os.getenv("ark_base_url")
MODEL = os.getenv("DOUBAO_EMBEDDING_MODEL") or os.getenv("ark_model")

if not BASE_URL:
    print("ERROR: 没有设置 DOUBAO_EMBEDDING_BASE_URL 或 ark_base_url 环境变量/在 .env 中未配置。", file=sys.stderr)
    sys.exit(2)

if not API_KEY:
    print("WARNING: 没有设置 API Key (DOUBAO_EMBEDDING_API_KEY / ark_api_key)。将发送无认证请求。", file=sys.stderr)

texts = [
    "这是一个测试文档，用于验证Doubao Embedding模型和复现错误。",
    "第二条测试文本：测试多条输入时的响应。"
]

url = BASE_URL
if not url.endswith("/embeddings"):
    url = url.rstrip('/') + "/embeddings"

headers = {"Content-Type": "application/json"}
if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

payload = {"model": MODEL, "input": texts}

print("REQUEST URL:", url)
print("REQUEST HEADERS:", json.dumps(headers, ensure_ascii=False))
print("REQUEST PAYLOAD:", json.dumps(payload, ensure_ascii=False))
print('\n--- CURL 示例 ---')
print('curl -i -X POST', url, "\\")
for k, v in headers.items():
    print(f"  -H '{k}: {v}' \\")
print("  -d '" + json.dumps(payload, ensure_ascii=False) + "'\n")

try:
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print("RESPONSE STATUS:", resp.status_code)
    print("RESPONSE HEADERS:")
    for k, v in resp.headers.items():
        print(f"  {k}: {v}")
    print('\nRESPONSE TEXT:')
    # 尝试格式化 JSON 输出，否则直接打印文本
    try:
        j = resp.json()
        print(json.dumps(j, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)
    # 如果是错误，打印原始响应内容及 raise
    if resp.status_code >= 400:
        print('\n(请求返回错误状态)', file=sys.stderr)
        sys.exit(3)
except requests.exceptions.RequestException as e:
    print('REQUEST EXCEPTION:', repr(e), file=sys.stderr)
    if hasattr(e, 'response') and e.response is not None:
        try:
            print('EXCEPTION RESPONSE STATUS:', e.response.status_code, file=sys.stderr)
            print(e.response.text, file=sys.stderr)
        except Exception:
            pass
    sys.exit(4)
