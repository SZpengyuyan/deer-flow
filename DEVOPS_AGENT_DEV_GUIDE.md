# DevOps 智能运维 Agent — 完整开发指南

> 基于 DeerFlow Agent 框架，构建一个端到端的 DevOps/SRE 智能运维诊断平台。
> 本文档是开发参考手册，包含架构设计、模块拆解、代码示例、配置变更、开发步骤等全部内容。

---

## 一、项目概述

### 1.1 目标

构建一个 **DevOps 智能运维诊断 Agent**，能够：
- 接收告警信息（手动输入 / IM Bot 推送）
- 通过 MCP 协议对接 Prometheus、Grafana 等监控系统，自动采集指标数据
- 通过自定义 Community Tool 分析日志文件
- 通过 Skill 编排多步诊断流程（告警解析 → 数据采集 → 根因分析 → 修复建议 → 诊断报告）
- 通过自定义 Middleware 记录完整的审计日志
- 最终生成结构化的故障诊断报告

### 1.2 技术含量体现

| 层级 | 模块 | 技术含量 | 面试价值 |
|------|------|---------|---------|
| **MCP 协议层** | prometheus-mcp-server | 实现 MCP Server 端（不是调用方） | ⭐⭐⭐⭐⭐ |
| **工具层** | log_analyzer Community Tool | 在框架 community/ 目录下扩展 | ⭐⭐⭐⭐ |
| **中间件层** | AuditLogMiddleware | 深入框架内核，理解洋葱模型 | ⭐⭐⭐⭐ |
| **编排层** | ops-diagnosis Skill | 多步骤诊断流程编排 | ⭐⭐⭐ |

### 1.3 与已有 ai-test-platform 的关系

```
代码提交 → [ai-test-platform 自动化测试] → 部署上线 → [ops-diagnosis 智能运维] → 故障修复
```

两个项目形成 **DevOps 全链路闭环**。

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        入口层                                    │
│  ┌─────────────────┐    ┌─────────────────────────────────┐     │
│  │  DeerFlow Web UI │    │  飞书/Slack Bot（IM Channel）    │     │
│  │  手动诊断入口    │    │  告警自动推送入口               │     │
│  └────────┬────────┘    └──────────────┬──────────────────┘     │
└───────────┼─────────────────────────────┼───────────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DeerFlow 框架层                               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Lead Agent (make_lead_agent)                │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        │                                         │
│  ┌─────────────────────▼───────────────────────────────────┐    │
│  │               Middleware Chain (洋葱模型)                 │    │
│  │  1. ThreadDataMiddleware                                 │    │
│  │  2. UploadsMiddleware                                    │    │
│  │  3. SandboxMiddleware                                    │    │
│  │  4. DanglingToolCallMiddleware                           │    │
│  │  5. ToolErrorHandlingMiddleware                          │    │
│  │  6. SummarizationMiddleware (可选)                       │    │
│  │  7. TodoListMiddleware (可选)                            │    │
│  │  8. TitleMiddleware                                      │    │
│  │  9. MemoryMiddleware                                     │    │
│  │  10.📌 AuditLogMiddleware  ← 你开发的                    │    │
│  │  11. ViewImageMiddleware (条件)                          │    │
│  │  12. SubagentLimitMiddleware (条件)                      │    │
│  │  13. LoopDetectionMiddleware                             │    │
│  │  14. ClarificationMiddleware (必须最后)                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Tool Layer                            │    │
│  │  ┌────────────────┐ ┌────────────────┐ ┌──────────────┐│    │
│  │  │ MCP Tools      │ │ Community Tools│ │ Built-in     ││    │
│  │  │ (Prometheus)   │ │ (log_analyzer) │ │ (bash, file) ││    │
│  │  │ 📌 你开发的    │ │ 📌 你开发的    │ │ (web_search) ││    │
│  │  └────────────────┘ └────────────────┘ └──────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Skill Layer                              │    │
│  │  📌 ops-diagnosis Skill  ← 你开发的                      │    │
│  │  Step 1: 告警解析                                        │    │
│  │  Step 2: 多维数据采集 (Prometheus + 日志)                │    │
│  │  Step 3: 根因分析                                        │    │
│  │  Step 4: 修复建议生成                                    │    │
│  │  Step 5: 诊断报告生成                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       外部系统                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Prometheus   │  │ Grafana      │  │ 日志文件 / ELK / Loki│  │
│  │ HTTP API     │  │ Dashboard API│  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、模块 1：自定义 MCP Server — `prometheus-mcp-server`

> ⭐⭐⭐⭐⭐ **核心亮点** — 你实现了 MCP 协议的 Server 端，不是"写脚本调工具"。

### 3.1 项目结构

```
d:\deer-flow\ops-mcp-server\
├── server.py                    # MCP Server 主入口（~200行）
├── tools/
│   ├── __init__.py
│   ├── query_metrics.py         # Prometheus PromQL 即时查询 & 范围查询
│   ├── query_alerts.py          # 获取 Prometheus 活跃告警列表
│   ├── query_targets.py         # 获取 Prometheus 监控目标状态
│   └── query_logs.py            # 日志查询（对接 Loki / 本地文件）
├── config.py                    # 配置管理（Prometheus URL 等）
├── requirements.txt
└── README.md
```

### 3.2 核心代码示例

#### `server.py` — MCP Server 主入口

```python
#!/usr/bin/env python3
"""
Prometheus MCP Server — 对接 Prometheus/Grafana 监控系统
通过 MCP 协议为 DeerFlow Agent 提供监控数据查询能力
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 MCP Server 实例
server = Server("prometheus-mcp-server")

config = get_config()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="query_metrics",
            description="通过 PromQL 查询 Prometheus 监控指标。支持即时查询和范围查询。"
                       "常用场景：查询 CPU 使用率、内存使用率、请求延迟、错误率等。"
                       "示例 PromQL: rate(http_requests_total[5m]), node_cpu_seconds_total",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "PromQL 查询表达式，如 rate(http_requests_total[5m])"
                    },
                    "range_minutes": {
                        "type": "integer",
                        "description": "查询时间范围（分钟），默认30分钟。设为0表示即时查询",
                        "default": 30
                    },
                    "step": {
                        "type": "string",
                        "description": "范围查询的步长，默认 '60s'",
                        "default": "60s"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="query_alerts",
            description="获取 Prometheus 当前活跃的告警列表。"
                       "返回告警名称、严重等级、触发时间、标签等信息。"
                       "用于了解当前系统存在哪些异常。",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "告警状态过滤: firing, pending, 或留空获取所有",
                        "enum": ["firing", "pending", ""]
                    },
                    "severity": {
                        "type": "string",
                        "description": "严重等级过滤: critical, warning, info",
                        "enum": ["critical", "warning", "info", ""]
                    }
                }
            }
        ),
        Tool(
            name="query_targets",
            description="获取 Prometheus 监控目标（targets）的健康状态。"
                       "用于检查各服务实例是否正常上报指标数据。",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "目标状态过滤: active, dropped, any",
                        "enum": ["active", "dropped", "any"],
                        "default": "active"
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "query_metrics":
            result = await _query_metrics(arguments)
        elif name == "query_alerts":
            result = await _query_alerts(arguments)
        elif name == "query_targets":
            result = await _query_targets(arguments)
        else:
            result = {"error": f"未知工具: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        logger.exception(f"工具 {name} 执行失败")
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "tool": name,
            "hint": "请检查 Prometheus 服务是否正常运行"
        }, ensure_ascii=False))]


async def _query_metrics(args: dict) -> dict:
    """执行 PromQL 查询"""
    query = args["query"]
    range_minutes = args.get("range_minutes", 30)
    step = args.get("step", "60s")

    async with httpx.AsyncClient(timeout=30) as client:
        if range_minutes == 0:
            # 即时查询
            resp = await client.get(
                f"{config.prometheus_url}/api/v1/query",
                params={"query": query}
            )
        else:
            # 范围查询
            end = datetime.now()
            start = end - timedelta(minutes=range_minutes)
            resp = await client.get(
                f"{config.prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start.timestamp(),
                    "end": end.timestamp(),
                    "step": step
                }
            )

        resp.raise_for_status()
        data = resp.json()

        if data["status"] != "success":
            return {"error": data.get("error", "查询失败"), "query": query}

        result_type = data["data"]["resultType"]
        results = data["data"]["result"]

        return {
            "query": query,
            "result_type": result_type,
            "result_count": len(results),
            "results": results[:20],  # 限制返回数量，避免上下文过长
            "time_range": f"最近 {range_minutes} 分钟" if range_minutes > 0 else "即时查询"
        }


async def _query_alerts(args: dict) -> dict:
    """查询活跃告警"""
    state_filter = args.get("state", "")
    severity_filter = args.get("severity", "")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{config.prometheus_url}/api/v1/alerts")
        resp.raise_for_status()
        data = resp.json()

        alerts = data["data"]["alerts"]

        # 过滤
        if state_filter:
            alerts = [a for a in alerts if a.get("state") == state_filter]
        if severity_filter:
            alerts = [a for a in alerts if a.get("labels", {}).get("severity") == severity_filter]

        return {
            "total_alerts": len(alerts),
            "alerts": [
                {
                    "name": a["labels"].get("alertname", "unknown"),
                    "state": a.get("state"),
                    "severity": a["labels"].get("severity", "unknown"),
                    "summary": a.get("annotations", {}).get("summary", ""),
                    "description": a.get("annotations", {}).get("description", ""),
                    "active_since": a.get("activeAt", ""),
                    "labels": {k: v for k, v in a.get("labels", {}).items()
                              if k not in ("alertname", "severity")}
                }
                for a in alerts[:20]
            ]
        }


async def _query_targets(args: dict) -> dict:
    """查询监控目标状态"""
    state = args.get("state", "active")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{config.prometheus_url}/api/v1/targets",
            params={"state": state} if state != "any" else {}
        )
        resp.raise_for_status()
        data = resp.json()

        active_targets = data["data"].get("activeTargets", [])

        return {
            "total_targets": len(active_targets),
            "targets": [
                {
                    "job": t.get("labels", {}).get("job", "unknown"),
                    "instance": t.get("labels", {}).get("instance", "unknown"),
                    "health": t.get("health"),
                    "last_scrape": t.get("lastScrape", ""),
                    "scrape_duration": t.get("lastScrapeDuration", 0),
                    "last_error": t.get("lastError", "")
                }
                for t in active_targets[:30]
            ],
            "summary": {
                "healthy": sum(1 for t in active_targets if t.get("health") == "up"),
                "unhealthy": sum(1 for t in active_targets if t.get("health") != "up"),
            }
        }


async def main():
    """启动 MCP Server"""
    logger.info("启动 Prometheus MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
```

#### `config.py` — 配置管理

```python
"""Prometheus MCP Server 配置"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3001"
    grafana_api_key: str = ""
    request_timeout: int = 30


def get_config() -> Config:
    return Config(
        prometheus_url=os.environ.get("PROMETHEUS_URL", "http://localhost:9090"),
        grafana_url=os.environ.get("GRAFANA_URL", "http://localhost:3001"),
        grafana_api_key=os.environ.get("GRAFANA_API_KEY", ""),
        request_timeout=int(os.environ.get("REQUEST_TIMEOUT", "30")),
    )
```

#### `requirements.txt`

```
mcp>=1.0.0
httpx>=0.27.0
```

### 3.3 注册到 DeerFlow

在 `d:\deer-flow\extensions_config.json` 中添加（如果文件不存在，从 `extensions_config.example.json` 复制）：

```json
{
  "mcpServers": {
    "prometheus": {
      "enabled": true,
      "type": "stdio",
      "command": "python",
      "args": ["ops-mcp-server/server.py"],
      "env": {
        "PROMETHEUS_URL": "http://localhost:9090",
        "GRAFANA_URL": "http://localhost:3001"
      },
      "description": "Prometheus/Grafana 监控数据查询，支持 PromQL 指标查询、活跃告警获取、监控目标健康检查"
    }
  },
  "skills": {}
}
```

### 3.4 验证方式

```bash
# 1. 先启动一个本地 Prometheus（可用 Docker）
docker run -d -p 9090:9090 prom/prometheus

# 2. 测试 MCP Server 能否独立运行
cd d:\deer-flow\ops-mcp-server
python server.py
# 应该能正常启动，等待 stdio 输入

# 3. 启动 DeerFlow 后，在 Web UI 中测试
# 输入："帮我查一下当前有哪些活跃告警"
# Agent 应该会自动调用 prometheus MCP 的 query_alerts 工具
```

---

## 四、模块 2：自定义 Community Tool — `log_analyzer`

> ⭐⭐⭐⭐ **框架层贡献** — 在 DeerFlow 的 `community/` 目录下新增工具，与 tavily、jina_ai 同级。

### 4.1 文件结构

```
d:\deer-flow\backend\packages\harness\deerflow\community\log_analyzer\
├── __init__.py
└── tools.py                    # 定义 log_analyze_tool, log_search_tool
```

### 4.2 核心代码

#### `__init__.py`

```python
"""日志分析工具 — 用于运维故障诊断场景"""
```

#### `tools.py`

> **参考 `tavily/tools.py` 的模式**：使用 `@tool` 装饰器 + `get_app_config().get_tool_config()` 读取配置。

```python
"""日志分析工具集 — 提供日志文件分析和搜索能力"""

import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from langchain.tools import tool

from deerflow.config import get_app_config


def _get_log_config() -> dict:
    """获取日志分析工具的配置"""
    config = get_app_config().get_tool_config("log_analyze")
    if config is not None and config.model_extra:
        return config.model_extra
    return {}


# ============================================================================
# 常见日志模式
# ============================================================================
ERROR_PATTERNS = [
    r"(?i)(error|exception|fatal|critical|panic|fail(?:ed|ure)?)\b",
    r"(?i)traceback\s*\(most recent call last\)",
    r"(?i)caused by:",
    r"(?i)at\s+[\w.$]+\([\w.]+:\d+\)",  # Java stack trace
    r"(?i)File\s+\"[^\"]+\",\s+line\s+\d+",  # Python stack trace
]

TIMEOUT_PATTERNS = [
    r"(?i)(timeout|timed?\s*out|deadline\s*exceeded)",
    r"(?i)(connection\s*refused|connect(?:ion)?\s*reset)",
    r"(?i)(ETIMEDOUT|ECONNREFUSED|ECONNRESET)",
]

OOM_PATTERNS = [
    r"(?i)(out\s*of\s*memory|oom|memory\s*limit|killed\s*process)",
    r"(?i)(heap\s*space|java\.lang\.OutOfMemoryError)",
    r"(?i)(cannot\s*allocate\s*memory)",
]


@tool("log_analyze", parse_docstring=True)
def log_analyze_tool(log_path: str, lines_limit: int = 1000) -> str:
    """分析日志文件，提取错误模式、异常堆栈、频率统计等关键信息。

    用于故障诊断场景，自动识别日志中的错误类型、频率、时间分布。
    支持常见的 Java/Python/Node.js 日志格式。

    Args:
        log_path: 日志文件的路径（绝对路径或相对于工作目录的路径）
        lines_limit: 最多分析的行数，默认1000行（从文件末尾开始）
    """
    try:
        path = Path(log_path)
        if not path.exists():
            return json.dumps({"error": f"日志文件不存在: {log_path}"}, ensure_ascii=False)

        # 读取文件最后 N 行
        lines = _tail_lines(path, lines_limit)
        total_lines = len(lines)

        if total_lines == 0:
            return json.dumps({"error": "日志文件为空"}, ensure_ascii=False)

        # 分析错误模式
        errors = _find_patterns(lines, ERROR_PATTERNS, "error")
        timeouts = _find_patterns(lines, TIMEOUT_PATTERNS, "timeout")
        ooms = _find_patterns(lines, OOM_PATTERNS, "oom")

        # 提取异常堆栈
        stack_traces = _extract_stack_traces(lines)

        # 错误频率统计
        error_counter = Counter()
        for line in lines:
            for pattern in ERROR_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    error_counter[match.group(0).lower()] += 1
                    break

        result = {
            "file": str(path),
            "analyzed_lines": total_lines,
            "summary": {
                "total_errors": len(errors),
                "total_timeouts": len(timeouts),
                "total_ooms": len(ooms),
                "unique_stack_traces": len(stack_traces),
            },
            "error_frequency": dict(error_counter.most_common(10)),
            "recent_errors": errors[-10:],  # 最近10条错误
            "timeout_events": timeouts[-5:],
            "oom_events": ooms[-3:],
            "stack_traces": stack_traces[:5],  # 前5个唯一堆栈
            "diagnosis_hints": _generate_hints(errors, timeouts, ooms, stack_traces),
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"分析失败: {str(e)}"}, ensure_ascii=False)


@tool("log_search", parse_docstring=True)
def log_search_tool(log_path: str, keyword: str, context_lines: int = 3, max_results: int = 20) -> str:
    """在日志文件中搜索关键字或正则表达式，返回匹配行及其上下文。

    用于在大量日志中快速定位特定事件、错误信息或关键字。
    支持正则表达式搜索。

    Args:
        log_path: 日志文件的路径
        keyword: 搜索关键字或正则表达式
        context_lines: 每个匹配结果显示的上下文行数（前后各N行），默认3
        max_results: 最大返回结果数，默认20
    """
    try:
        path = Path(log_path)
        if not path.exists():
            return json.dumps({"error": f"日志文件不存在: {log_path}"}, ensure_ascii=False)

        try:
            pattern = re.compile(keyword, re.IGNORECASE)
        except re.error:
            # 如果不是有效正则，当作纯文本搜索
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        matches = []

        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = lines[start:end]

                matches.append({
                    "line_number": i + 1,
                    "matched_line": line.strip(),
                    "context": "\n".join(context),
                })

                if len(matches) >= max_results:
                    break

        result = {
            "file": str(path),
            "keyword": keyword,
            "total_matches": len(matches),
            "matches": matches,
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)


# ============================================================================
# 内部辅助函数
# ============================================================================

def _tail_lines(path: Path, n: int) -> list[str]:
    """读取文件最后 N 行"""
    content = path.read_text(encoding="utf-8", errors="replace")
    all_lines = content.splitlines()
    return all_lines[-n:] if len(all_lines) > n else all_lines


def _find_patterns(lines: list[str], patterns: list[str], category: str) -> list[dict]:
    """在日志行中查找匹配模式"""
    results = []
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.search(pattern, line):
                results.append({
                    "line_number": i + 1,
                    "category": category,
                    "content": line.strip()[:500],
                })
                break
    return results


def _extract_stack_traces(lines: list[str]) -> list[str]:
    """提取异常堆栈信息"""
    traces = []
    current_trace = []
    in_trace = False

    for line in lines:
        # 检测堆栈开始
        if re.search(r"(?i)(traceback|exception|error:)", line) and not in_trace:
            in_trace = True
            current_trace = [line.strip()]
        elif in_trace:
            # 检测堆栈行（缩进行或 at xxx 行）
            if re.match(r"^\s+", line) or re.match(r"^\s*at\s+", line):
                current_trace.append(line.strip())
            else:
                if len(current_trace) > 1:
                    trace_text = "\n".join(current_trace[:20])  # 限制堆栈长度
                    if trace_text not in traces:
                        traces.append(trace_text)
                in_trace = False
                current_trace = []

    # 处理最后一个堆栈
    if current_trace and len(current_trace) > 1:
        trace_text = "\n".join(current_trace[:20])
        if trace_text not in traces:
            traces.append(trace_text)

    return traces


def _generate_hints(errors, timeouts, ooms, stack_traces) -> list[str]:
    """根据分析结果生成诊断提示"""
    hints = []

    if len(ooms) > 0:
        hints.append("🔴 检测到 OOM（内存溢出）事件，建议检查：1) 容器/JVM 内存限制 2) 是否存在内存泄漏 3) 近期是否有流量突增")

    if len(timeouts) > 0:
        hints.append("🟡 检测到超时事件，建议检查：1) 下游服务/数据库响应时间 2) 网络连通性 3) 连接池配置")

    if len(errors) > 20:
        hints.append(f"🔴 错误密度较高（{len(errors)} 条），可能存在系统性问题而非偶发异常")
    elif len(errors) > 5:
        hints.append(f"🟡 存在 {len(errors)} 条错误记录，建议关注频率最高的错误类型")

    if len(stack_traces) > 3:
        hints.append(f"⚠️ 发现 {len(stack_traces)} 种不同的异常堆栈，可能涉及多个故障点")

    if not hints:
        hints.append("✅ 日志中未发现明显异常模式")

    return hints
```

### 4.3 注册到 DeerFlow

在 `d:\deer-flow\config.yaml` 的 `tools:` 部分添加：

```yaml
tools:
  # ... 已有的工具配置保持不动 ...

  # 日志分析工具（运维诊断用）
  - name: log_analyze
    group: file:read
    use: deerflow.community.log_analyzer.tools:log_analyze_tool

  - name: log_search
    group: file:read
    use: deerflow.community.log_analyzer.tools:log_search_tool
```

### 4.4 验证方式

```bash
# 启动 DeerFlow 后，在 Web UI 中测试：
# 输入："帮我分析 /var/log/app/error.log 这个日志文件"
# Agent 应该自动调用 log_analyze 工具
```

---

## 五、模块 3：自定义 Middleware — `AuditLogMiddleware`

> ⭐⭐⭐⭐ **框架理解深度** — 在 DeerFlow 的 Middleware 链中插入审计日志中间件。

### 5.1 文件位置

```
d:\deer-flow\backend\packages\harness\deerflow\agents\middlewares\audit_log_middleware.py
```

### 5.2 DeerFlow Middleware 开发规范

**必须了解的基类接口** — 继承 `AgentMiddleware`，可覆写以下方法：

| 方法 | 触发时机 | 用途 |
|------|---------|------|
| `before_agent(state, runtime)` | Agent 执行前 | 初始化、注入数据到 state |
| `after_agent(state, runtime)` | Agent 执行后 | 清理、记录结果 |
| `wrap_tool_call(request, handler)` | 同步工具调用时 | 拦截工具调用 |
| `awrap_tool_call(request, handler)` | 异步工具调用时 | 拦截异步工具调用 |
| `wrap_model_call(request, handler)` | LLM 调用时 | 拦截模型调用 |
| `awrap_model_call(request, handler)` | 异步 LLM 调用时 | 拦截异步模型调用 |

**关键导入**：
```python
from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command
```

### 5.3 核心代码

```python
"""审计日志中间件 — 记录所有工具调用和 Agent 决策，用于运维诊断的可追溯性。"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphBubbleUp
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command

logger = logging.getLogger(__name__)


class AuditLogMiddleware(AgentMiddleware[AgentState]):
    """记录所有工具调用和 Agent 决策的审计日志。

    功能：
    1. 在 awrap_tool_call 中拦截每次工具调用，记录：工具名、参数、耗时、结果状态
    2. 在 after_agent 中记录 Agent 的最终决策摘要
    3. 审计日志写入线程目录下的 audit_log.jsonl 文件

    审计日志格式（JSONL，每行一个 JSON）：
    {
        "timestamp": "2026-03-25T16:00:00",
        "event": "tool_call",
        "tool_name": "query_alerts",
        "tool_args": {"state": "firing"},
        "duration_ms": 234,
        "status": "success",
        "thread_id": "abc-123"
    }
    """

    def __init__(self, log_dir: str | None = None):
        """初始化审计日志中间件。

        Args:
            log_dir: 审计日志目录。如果为 None，则使用线程目录。
        """
        super().__init__()
        self._log_dir = log_dir
        self._session_start: float | None = None

    def _get_thread_id(self, runtime: Runtime) -> str:
        """从 runtime 中提取 thread_id"""
        return runtime.context.get("thread_id", "unknown")

    def _get_log_path(self, thread_id: str) -> Path:
        """获取审计日志文件路径"""
        if self._log_dir:
            base = Path(self._log_dir)
        else:
            # 使用 DeerFlow 的线程目录
            base = Path(".deer-flow") / "threads" / thread_id
        base.mkdir(parents=True, exist_ok=True)
        return base / "audit_log.jsonl"

    def _write_log(self, thread_id: str, record: dict):
        """写入一条审计日志"""
        try:
            log_path = self._get_log_path(thread_id)
            record["timestamp"] = datetime.now().isoformat()
            record["thread_id"] = thread_id

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"写入审计日志失败: {e}")

    @override
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict | None:
        """Agent 执行前：记录会话开始"""
        self._session_start = time.time()
        thread_id = self._get_thread_id(runtime)
        self._write_log(thread_id, {
            "event": "agent_start",
            "message_count": len(state.get("messages", [])),
        })
        return super().before_agent(state, runtime)

    @override
    def after_agent(self, state: AgentState, runtime: Runtime) -> dict | None:
        """Agent 执行后：记录会话结束和总耗时"""
        thread_id = self._get_thread_id(runtime)
        duration = (time.time() - self._session_start) * 1000 if self._session_start else 0

        self._write_log(thread_id, {
            "event": "agent_end",
            "duration_ms": round(duration),
            "final_message_count": len(state.get("messages", [])),
        })
        return super().after_agent(state, runtime)

    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """同步工具调用拦截：记录工具名、参数、耗时、结果状态"""
        tool_name = request.tool_call.get("name", "unknown")
        tool_args = request.tool_call.get("args", {})
        thread_id = request.config.get("configurable", {}).get("thread_id", "unknown")

        start_time = time.time()
        try:
            result = handler(request)
            duration = (time.time() - start_time) * 1000

            status = "success"
            if isinstance(result, ToolMessage) and result.status == "error":
                status = "error"

            self._write_log(thread_id, {
                "event": "tool_call",
                "tool_name": tool_name,
                "tool_args": _sanitize_args(tool_args),
                "duration_ms": round(duration),
                "status": status,
            })
            return result

        except GraphBubbleUp:
            raise
        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            self._write_log(thread_id, {
                "event": "tool_call",
                "tool_name": tool_name,
                "tool_args": _sanitize_args(tool_args),
                "duration_ms": round(duration),
                "status": "exception",
                "error": str(exc)[:200],
            })
            raise

    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """异步工具调用拦截"""
        tool_name = request.tool_call.get("name", "unknown")
        tool_args = request.tool_call.get("args", {})
        thread_id = request.config.get("configurable", {}).get("thread_id", "unknown")

        start_time = time.time()
        try:
            result = await handler(request)
            duration = (time.time() - start_time) * 1000

            status = "success"
            if isinstance(result, ToolMessage) and result.status == "error":
                status = "error"

            self._write_log(thread_id, {
                "event": "tool_call",
                "tool_name": tool_name,
                "tool_args": _sanitize_args(tool_args),
                "duration_ms": round(duration),
                "status": status,
            })
            return result

        except GraphBubbleUp:
            raise
        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            self._write_log(thread_id, {
                "event": "tool_call",
                "tool_name": tool_name,
                "tool_args": _sanitize_args(tool_args),
                "duration_ms": round(duration),
                "status": "exception",
                "error": str(exc)[:200],
            })
            raise


def _sanitize_args(args: dict) -> dict:
    """脱敏处理工具参数（移除过长的内容，避免日志膨胀）"""
    sanitized = {}
    for k, v in args.items():
        if isinstance(v, str) and len(v) > 500:
            sanitized[k] = v[:500] + "...(truncated)"
        else:
            sanitized[k] = v
    return sanitized
```

### 5.4 注册到 Middleware 链

需要修改 `d:\deer-flow\backend\packages\harness\deerflow\agents\lead_agent\agent.py` 中的 `_build_middlewares` 函数：

```python
# 在文件顶部添加导入
from deerflow.agents.middlewares.audit_log_middleware import AuditLogMiddleware

# 在 _build_middlewares 函数中，MemoryMiddleware 之后添加：
def _build_middlewares(config: RunnableConfig, model_name: str | None, agent_name: str | None = None):
    middlewares = build_lead_runtime_middlewares(lazy_init=True)

    # ... 已有的 SummarizationMiddleware、TodoListMiddleware、TitleMiddleware ...

    # Add MemoryMiddleware (after TitleMiddleware)
    middlewares.append(MemoryMiddleware(agent_name=agent_name))

    # 📌 Add AuditLogMiddleware (after MemoryMiddleware)
    middlewares.append(AuditLogMiddleware())

    # ... 后续的 ViewImageMiddleware、LoopDetectionMiddleware、ClarificationMiddleware ...
```

**具体修改位置**：在 `middlewares.append(MemoryMiddleware(agent_name=agent_name))` 之后，`ViewImageMiddleware` 之前插入。

### 5.5 验证方式

```bash
# 启动 DeerFlow 后随便进行一次对话
# 然后检查审计日志文件：
# d:\deer-flow\backend\.deer-flow\threads\{thread_id}\audit_log.jsonl

# 日志内容示例：
# {"timestamp": "2026-03-25T16:10:00", "event": "agent_start", "message_count": 1, "thread_id": "abc-123"}
# {"timestamp": "2026-03-25T16:10:02", "event": "tool_call", "tool_name": "web_search", "tool_args": {"query": "test"}, "duration_ms": 1234, "status": "success", "thread_id": "abc-123"}
# {"timestamp": "2026-03-25T16:10:05", "event": "agent_end", "duration_ms": 5000, "final_message_count": 4, "thread_id": "abc-123"}
```

---

## 六、模块 4：运维诊断 Skill — `ops-diagnosis`

> ⭐⭐⭐ **编排层** — 设计 5 步诊断流程，编排 Agent 行为。

### 6.1 文件结构

```
d:\deer-flow\skills\custom\ops-diagnosis\
├── SKILL.md                              # 技能定义（YAML frontmatter + 诊断流程指令）
├── scripts/
│   ├── parse_alert.py                    # 解析告警信息，提取关键字段
│   ├── collect_metrics.py                # 生成 PromQL 查询建议
│   ├── analyze_logs.py                   # 日志分析策略
│   ├── correlate_events.py               # 时间线关联分析
│   └── generate_diagnosis_report.py      # 生成诊断报告
├── templates/
│   ├── diagnosis_rules.yaml              # 诊断规则配置
│   └── report_template.md                # 报告模板
└── references/
    └── common_incidents.md               # 常见故障模式知识库
```

### 6.2 SKILL.md

> **YAML frontmatter 允许的字段**：`name`、`description`、`license`、`allowed-tools`、`metadata`、`compatibility`

```markdown
---
name: ops-diagnosis
description: >
  DevOps 智能运维诊断技能。当用户提到告警、故障、异常、监控、运维、诊断、排查、
  CPU 高、内存溢出、超时、5xx 错误、服务不可用等问题时，自动触发此技能。
  该技能通过 Prometheus 查询监控指标、分析日志文件、关联时间线事件，
  最终生成结构化的根因分析报告和修复建议。
  即使用户只是简单描述"线上有问题"或"服务挂了"，也应该使用此技能。
allowed-tools:
  - web_search
  - web_fetch
  - bash
  - read_file
  - write_file
  - log_analyze
  - log_search
---

# DevOps 智能运维诊断

## 概述

本技能用于接收告警或故障描述，自动执行多维度诊断分析，生成根因分析报告。

## 诊断流程

### Step 1: 告警解析

1. 解析用户输入的告警信息或故障描述
2. 提取关键字段：
   - 告警名称/类型
   - 受影响的服务/实例
   - 触发时间
   - 严重等级
3. 如果信息不足，主动向用户确认以下信息：
   - 哪个服务出问题了？
   - 大约什么时候开始的？
   - 有没有告警截图或日志路径？

可以参考脚本 `scripts/parse_alert.py` 的解析逻辑。

### Step 2: 多维数据采集

根据告警类型，使用以下工具采集数据：

**监控指标采集**（通过 Prometheus MCP 工具）：
- CPU 使用率: `rate(process_cpu_seconds_total[5m])`
- 内存使用: `process_resident_memory_bytes`
- HTTP 错误率: `rate(http_requests_total{status=~"5.."}[5m])`
- 请求延迟: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`

注意：如果 Prometheus MCP 工具不可用，改用 `bash` 工具执行 `curl` 命令查询。
参考 `scripts/collect_metrics.py` 中的 PromQL 查询建议。

**日志分析**（通过 log_analyze 和 log_search 工具）：
- 使用 `log_analyze` 工具自动分析错误模式
- 使用 `log_search` 工具搜索特定关键字
- 常见日志路径：
  - 应用日志: `/var/log/app/` 或 `/mnt/user-data/workspace/logs/`
  - 系统日志: `/var/log/syslog`、`/var/log/messages`
  - 容器日志: 通过 `bash` 执行 `docker logs <container_name>`

### Step 3: 根因分析

1. 综合监控指标和日志信息，进行关联分析
2. 参考 `references/common_incidents.md` 中的常见故障模式
3. 分析步骤：
   - 时间线对齐：将告警时间、指标异常时间、日志错误时间进行对齐
   - 因果推理：判断是资源瓶颈、代码 Bug、外部依赖故障、还是配置问题
   - 排除法：逐一排查可能的原因
4. 参考 `scripts/correlate_events.py` 的关联分析逻辑

### Step 4: 修复建议

根据根因分析结果，生成针对性的修复建议：

**资源瓶颈类**：
- 扩容建议（CPU/内存/磁盘）
- JVM/容器参数调优
- 限流降级策略

**代码 Bug 类**：
- 定位到具体的异常堆栈和代码位置
- 建议修复方向

**外部依赖类**：
- 下游服务状态检查
- 超时/重试策略优化
- 熔断器配置建议

**配置问题类**：
- 指出可能的配置项问题
- 给出配置修正建议

### Step 5: 生成诊断报告

使用 `write_file` 工具，按照 `templates/report_template.md` 的格式生成诊断报告。

报告应包含以下章节：
1. **故障摘要** — 一句话总结
2. **影响范围** — 受影响的服务、用户、时长
3. **时间线** — 关键事件的时序排列
4. **根因分析** — 详细的因果推理过程
5. **监控数据** — 关键指标的数据表格
6. **日志证据** — 关键的错误日志和堆栈
7. **修复建议** — 立即行动项 + 长期改进项
8. **预防措施** — 如何避免类似故障再次发生

将报告保存到 `/mnt/user-data/outputs/diagnosis_report_{timestamp}.md`。
```

### 6.3 关键脚本示例

#### `scripts/parse_alert.py`

```python
#!/usr/bin/env python3
"""
告警信息解析脚本
从各种格式的告警信息中提取关键字段
"""

import json
import re
import sys
from datetime import datetime


def parse_alert(alert_text: str) -> dict:
    """解析告警文本，提取结构化信息"""
    result = {
        "alert_name": "",
        "severity": "unknown",
        "service": "",
        "instance": "",
        "trigger_time": "",
        "description": "",
        "raw_text": alert_text,
    }

    # 尝试解析 JSON 格式告警（Prometheus AlertManager webhook）
    try:
        data = json.loads(alert_text)
        if "alerts" in data:
            alert = data["alerts"][0]
            result["alert_name"] = alert.get("labels", {}).get("alertname", "")
            result["severity"] = alert.get("labels", {}).get("severity", "unknown")
            result["service"] = alert.get("labels", {}).get("service", "")
            result["instance"] = alert.get("labels", {}).get("instance", "")
            result["trigger_time"] = alert.get("startsAt", "")
            result["description"] = alert.get("annotations", {}).get("description", "")
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试从纯文本中提取信息
    severity_match = re.search(r"(?i)(critical|warning|info|error|fatal)", alert_text)
    if severity_match:
        result["severity"] = severity_match.group(1).lower()

    service_match = re.search(r"(?i)(?:service|服务)[:\s]*(\S+)", alert_text)
    if service_match:
        result["service"] = service_match.group(1)

    time_match = re.search(r"(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})", alert_text)
    if time_match:
        result["trigger_time"] = time_match.group(1)

    # 提取告警名称（第一行通常是标题）
    first_line = alert_text.strip().split("\n")[0]
    result["alert_name"] = first_line[:100]
    result["description"] = alert_text[:500]

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        alert_text = " ".join(sys.argv[1:])
    else:
        alert_text = sys.stdin.read()

    result = parse_alert(alert_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

#### `scripts/generate_diagnosis_report.py`

```python
#!/usr/bin/env python3
"""
诊断报告生成脚本
将诊断结果格式化为 Markdown 报告
"""

import json
import sys
from datetime import datetime


def generate_report(diagnosis_data: dict) -> str:
    """生成诊断报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# 故障诊断报告

> 生成时间: {now}
> 诊断引擎: DeerFlow DevOps Agent

---

## 1. 故障摘要

{diagnosis_data.get("summary", "待填写")}

## 2. 影响范围

| 维度 | 详情 |
|------|------|
| 受影响服务 | {diagnosis_data.get("affected_service", "待确认")} |
| 受影响实例 | {diagnosis_data.get("affected_instances", "待确认")} |
| 故障持续时间 | {diagnosis_data.get("duration", "待确认")} |
| 影响用户数 | {diagnosis_data.get("affected_users", "待评估")} |

## 3. 时间线

{_format_timeline(diagnosis_data.get("timeline", []))}

## 4. 根因分析

{diagnosis_data.get("root_cause", "待分析")}

## 5. 监控数据

{diagnosis_data.get("metrics_summary", "无数据")}

## 6. 日志证据

```
{diagnosis_data.get("log_evidence", "无日志")}
```

## 7. 修复建议

### 立即行动
{_format_list(diagnosis_data.get("immediate_actions", []))}

### 长期改进
{_format_list(diagnosis_data.get("long_term_improvements", []))}

## 8. 预防措施

{_format_list(diagnosis_data.get("prevention", []))}

---
*此报告由 DeerFlow DevOps Agent 自动生成，建议人工审核后执行修复操作。*
"""
    return report


def _format_timeline(events: list) -> str:
    if not events:
        return "| 时间 | 事件 |\n|------|------|\n| - | 暂无时间线数据 |"
    lines = ["| 时间 | 事件 |", "|------|------|"]
    for event in events:
        lines.append(f"| {event.get('time', '')} | {event.get('event', '')} |")
    return "\n".join(lines)


def _format_list(items: list) -> str:
    if not items:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in items)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    print(generate_report(data))
```

#### `templates/report_template.md`

```markdown
# 故障诊断报告模板

> 此模板供 Agent 参考，生成结构化的诊断报告。

## 必须包含的章节

1. **故障摘要** — 一句话描述故障现象和根因
2. **影响范围** — 表格形式列出受影响的服务、实例、用户、持续时间
3. **时间线** — 按时间顺序列出关键事件（告警触发、指标异常、恢复等）
4. **根因分析** — 详细描述推理过程，列出排查步骤和证据
5. **监控数据** — 关键指标的数值（CPU、内存、请求延迟、错误率等）
6. **日志证据** — 关键的错误日志片段和异常堆栈
7. **修复建议** — 分为"立即行动"和"长期改进"两部分
8. **预防措施** — 如何防止同类故障再次发生

## 格式要求

- 使用 Markdown 格式
- 表格对齐
- 代码块使用正确的语言标记
- 时间使用 ISO 8601 格式
```

#### `references/common_incidents.md`

```markdown
# 常见故障模式知识库

## 1. CPU 使用率过高

### 症状
- Prometheus: `rate(process_cpu_seconds_total[5m]) > 0.8`
- 系统日志: load average 持续 > CPU 核心数

### 常见原因
- 死循环或算法复杂度问题
- GC 频繁（Java/Go）
- 正则表达式回溯
- 流量突增

### 诊断步骤
1. 查看 CPU 使用率的时间维度变化
2. 检查是否与流量变化相关
3. 查看应用日志中的 GC 日志
4. 检查是否有慢查询

---

## 2. 内存溢出（OOM）

### 症状
- Prometheus: `process_resident_memory_bytes` 持续增长
- 系统日志: "Out of memory: Killed process"
- 应用日志: "java.lang.OutOfMemoryError"

### 常见原因
- 内存泄漏（未释放的缓存、连接池）
- JVM 堆配置不足
- 大对象/大查询结果集
- 容器内存限制过小

### 诊断步骤
1. 查看内存使用的趋势图
2. 检查是否有持续增长（泄漏）或突然飙升（大对象）
3. 查看 OOM 前后的日志
4. 检查容器/JVM 内存配置

---

## 3. 请求超时

### 症状
- Prometheus: `histogram_quantile(0.99, ...) > threshold`
- 应用日志: "TimeoutException", "deadline exceeded"
- 上游告警: 5xx 错误率上升

### 常见原因
- 下游服务响应慢
- 数据库慢查询
- 网络抖动
- 连接池耗尽
- 线程池饱和

### 诊断步骤
1. 查看请求延迟的 P99/P95 趋势
2. 检查下游服务的健康状态
3. 查看数据库慢查询日志
4. 检查连接池/线程池指标

---

## 4. 服务不可用（5xx）

### 症状
- Prometheus: `rate(http_requests_total{status=~"5.."}[5m])` 上升
- 负载均衡健康检查失败
- 用户反馈页面报错

### 常见原因
- 应用进程崩溃（OOM/异常未捕获）
- 配置错误（发布后）
- 依赖服务不可用
- 证书过期
- 磁盘满

### 诊断步骤
1. 检查服务进程是否存活
2. 查看最近的部署记录
3. 检查依赖服务状态
4. 查看应用启动日志
```

---

## 七、配置变更清单

### 7.1 需要修改的文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `extensions_config.json` | 新增/修改 | 添加 prometheus MCP Server 配置 |
| `config.yaml` | 修改 | 在 tools 部分添加 log_analyze、log_search |
| `lead_agent/agent.py` | 修改 | 在 `_build_middlewares` 中添加 AuditLogMiddleware |

### 7.2 需要新增的文件

| 文件路径 | 说明 |
|---------|------|
| `ops-mcp-server/server.py` | MCP Server 主入口 |
| `ops-mcp-server/config.py` | MCP Server 配置 |
| `ops-mcp-server/requirements.txt` | MCP Server 依赖 |
| `deerflow/community/log_analyzer/__init__.py` | 日志分析工具包 |
| `deerflow/community/log_analyzer/tools.py` | 日志分析工具实现 |
| `deerflow/agents/middlewares/audit_log_middleware.py` | 审计日志中间件 |
| `skills/custom/ops-diagnosis/SKILL.md` | 运维诊断技能定义 |
| `skills/custom/ops-diagnosis/scripts/*.py` | 诊断脚本 |
| `skills/custom/ops-diagnosis/templates/*` | 报告模板 |
| `skills/custom/ops-diagnosis/references/*` | 知识库 |

---

## 八、开发顺序和验证步骤

### Phase 1：MCP Server 开发（第1天）

```
□ 1.1 创建 ops-mcp-server/ 目录结构
□ 1.2 实现 server.py（MCP Server 主入口）
□ 1.3 实现 config.py（配置管理）
□ 1.4 安装依赖: pip install mcp httpx
□ 1.5 本地测试: python server.py（确认能启动）
□ 1.6 创建 extensions_config.json，注册 prometheus server
□ 1.7 启动 DeerFlow，验证 MCP 工具被正确加载
□ 1.8 在 Web UI 中测试: "查一下当前有哪些告警"
```

### Phase 2：Community Tool 开发（第2天）

```
□ 2.1 创建 deerflow/community/log_analyzer/ 目录
□ 2.2 实现 tools.py（log_analyze_tool + log_search_tool）
□ 2.3 在 config.yaml 的 tools 部分注册两个工具
□ 2.4 准备测试日志文件（可从网上下载示例日志）
□ 2.5 启动 DeerFlow，验证工具被正确加载
□ 2.6 在 Web UI 中测试: "帮我分析一下这个日志文件"
```

### Phase 3：Middleware 开发（第3天上午）

```
□ 3.1 创建 audit_log_middleware.py
□ 3.2 修改 lead_agent/agent.py 注册 Middleware
□ 3.3 启动 DeerFlow，进行一次对话
□ 3.4 检查 .deer-flow/threads/{id}/audit_log.jsonl 文件
□ 3.5 验证日志格式正确，包含工具调用信息
```

### Phase 4：Skill 开发（第3天下午 - 第4天）

```
□ 4.1 创建 skills/custom/ops-diagnosis/ 目录结构
□ 4.2 编写 SKILL.md
□ 4.3 编写脚本: parse_alert.py, collect_metrics.py 等
□ 4.4 编写模板: report_template.md
□ 4.5 编写知识库: common_incidents.md
□ 4.6 启动 DeerFlow，验证 Skill 被正确加载
□ 4.7 端到端测试: 输入一个模拟告警，看完整诊断流程
```

### Phase 5：端到端集成测试 + Demo（第5天）

```
□ 5.1 准备完整的测试场景（模拟 CPU 告警 + 日志文件）
□ 5.2 跑通完整流程: 告警 → 数据采集 → 分析 → 报告
□ 5.3 录制演示视频（3~5 分钟）
□ 5.4 整理代码，提交到 fork 仓库
□ 5.5 整理简历项目描述
```

---

## 九、Demo 测试场景

### 场景：模拟 CPU 使用率过高告警

**准备工作：**
1. 启动本地 Prometheus（Docker）
2. 准备一个模拟的应用日志文件 `test_app.log`，内容包含一些错误和堆栈信息

**用户输入：**
```
线上告警：订单服务 order-service 的 CPU 使用率超过 90%，持续 10 分钟。
实例: order-service-pod-abc-123
告警时间: 2026-03-25 15:30:00
严重等级: critical
日志路径: /mnt/user-data/workspace/logs/test_app.log

请帮我诊断根因并给出修复建议。
```

**预期流程：**
1. Agent 识别并触发 `ops-diagnosis` Skill
2. Step 1: 解析告警信息 → 提取服务名、实例、时间、等级
3. Step 2: 调用 Prometheus MCP 查询 CPU、内存、请求延迟等指标
4. Step 2: 调用 log_analyze 分析日志文件
5. Step 3: 综合指标和日志，进行根因分析
6. Step 4: 生成修复建议
7. Step 5: 生成诊断报告 → 保存到 outputs 目录

**审计日志验证：**
检查 `audit_log.jsonl`，应包含所有工具调用记录。

---

## 十、面试话术

> "我基于字节跳动开源的 DeerFlow Agent 框架，构建了一个 **DevOps 智能运维诊断平台**。整个项目深入了框架的每一层：
>
> 1. **MCP 协议层**：我用 Python 的 `mcp` SDK 实现了一个 Prometheus MCP Server，它通过 PromQL 查询监控指标和活跃告警。DeerFlow 通过 stdio 传输协议自动发现并注册为 Agent 可用工具。这证明我理解了 Agent-Tool 交互的底层协议，不只是调用工具。
>
> 2. **工具层**：在 DeerFlow 的 `community/` 目录下新增了日志分析工具（`log_analyzer`），支持错误模式识别、异常堆栈提取和频率统计。遵循与 Tavily 搜索工具相同的 `@tool` 装饰器模式和配置机制。
>
> 3. **中间件层**：开发了审计日志 Middleware（`AuditLogMiddleware`），拦截所有工具调用记录耗时和状态，写入 JSONL 格式的审计日志。这需要深入理解 DeerFlow 的洋葱模型 Middleware 链，以及 `before_agent`、`after_agent`、`awrap_tool_call` 的生命周期。
>
> 4. **编排层**：设计了 5 步诊断流程的 Skill（告警解析 → 多维采集 → 根因分析 → 修复建议 → 诊断报告），包含知识库和报告模板。
>
> 端到端场景：接收一条 CPU 告警 → Agent 自动通过 MCP 查询 Prometheus 近 30 分钟的指标 → 并行分析日志中的错误堆栈 → 关联时间线 → 生成根因分析报告，全程 < 3 分钟。"

---

## 十一、技术栈总结

| 技术 | 用途 |
|------|------|
| **LangGraph / LangChain** | Agent 框架基础，create_agent + Middleware 机制 |
| **MCP 协议** | 自定义 MCP Server 对接外部系统 |
| **Python mcp SDK** | 实现 MCP Server 端 |
| **httpx** | 异步 HTTP 客户端，调用 Prometheus API |
| **Prometheus / PromQL** | 监控指标查询 |
| **正则表达式** | 日志分析中的模式匹配 |
| **JSONL** | 审计日志存储格式 |
| **DeerFlow Harness** | AgentMiddleware、Community Tool、Skill 扩展 |
