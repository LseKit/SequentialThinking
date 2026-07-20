<div align="center">

# 🧠 Sequential Thinking MCP

**让 AI 在推理时拥有结构化思维——26 个工具，覆盖从拆解到验证的完整思维链**

[![PyPI](https://img.shields.io/pypi/v/LseKit-SequentialThinking?color=2563eb&label=PyPI)](https://pypi.org/project/LseKit-SequentialThinking/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Ready-orange)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-192%20passed-brightgreen)]()
[![Stars](https://img.shields.io/github/stars/LseKit/SequentialThinking?style=social)](https://github.com/LseKit/SequentialThinking)

</div>

---

## 📊 功能对比

以下是 Sequential Thinking 的几个主要实现。官方版是简洁的参考实现，各自在此基础上做了不同方向的扩展。

| 功能 | [MCP 官方版](https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking)<br><sub>TypeScript · npm 151K/周</sub> | [arben-adm](https://pypi.org/project/mcp-sequential-thinking/)<br><sub>Python · PyPI</sub> | [ad/sequentialthinking](https://github.com/ad/sequentialthinking)<br><sub>Go · 3传输模式</sub> | [LseKit](https://github.com/LseKit/SequentialThinking)<br><sub>Python · PyPI</sub> |
|------|:---:|:---:|:---:|:---:|
| **MCP 工具数** | 1 | 5 | 1 | **26** |
| **代码规模** | ~200 行 | ~800 行 | ~1,000 行 | ~5,400 行 |
| **AI 自动推进推理** | — | — | — | ✅ LLM 引擎驱动 |
| **并行多路推理** | — | — | — | ✅ Self-MoA |
| **迭代深度推理** | — | — | — | ✅ Iterative-MoA |
| **中文原生支持** | — | — | — | ✅ jieba + FTS5 |
| **思考持久化** | — | — | — | ✅ SQLite FTS5 |
| **质量评分** | — | — | — | ✅ 5 维评估 |
| **逻辑检查** | — | — | — | ✅ 谬误 + 偏见检测 |
| **可视化思维** | — | — | — | ✅ Mermaid 流程图 |
| **推理回放** | — | — | — | ✅ 逐步审计 |
| **多分支推理** | — | — | — | ✅ 分支 + 合并 |
| **会话对比** | — | — | — | ✅ 跨会话 Diff |
| **MCP Resources** | — | — | — | ✅ 2 个 |
| **MCP Prompts** | — | — | — | ✅ 3 个 |
| **单元测试** | — | 少量 | — | 192 个 |
| **Python 包发布** | — | ✅ PyPI | — | ✅ PyPI |

> 官方版是一个简洁的参考实现，1 个工具刚好展示 MCP 协议的基础用法。这个项目在此基础上扩展了推理引擎、持久化存储、中文支持和质量控制，适合有更复杂推理需求的场景。如果你的需求比较简单，官方版完全够用。

---

## 🎯 这些功能解决了什么问题

### ① 推理缺少自我审查

LLM 的推理看起来很流畅，但每一步的结论不一定经得起推敲。26 个工具中内置了逻辑检测、矛盾识别、偏见筛查和假设提取——不是为了让 AI 推理更"厉害"，而是让推理结果更可靠。

### ② 思考过程没有留存

有时候一个问题推演了很久，下次遇到类似的还得从头来。SQLite FTS5 全文索引记录了所有思考过程，可以随时搜索、回放、对比不同会话的推理路径。

### ③ 中文场景支持不足

英文分词在中文上效果不佳。这个项目集成了 jieba 分词和 FTS5 中文全文检索，对中文问题的理解和检索更准确。

### ④ 单一推理路径的局限

一个问题往往有多种思考角度。Self-MoA 用温度采样并行生成多条路径后投票汇聚，Iterative-MoA 通过多轮迭代逐步优化——它们是不同场景下的两种互补策略。

---

## ⚡ 安装 & 使用

### 一行配置（推荐）

```json
{
  "mcpServers": {
    "seqthink": {
      "command": "uvx",
      "args": ["--from", "LseKit-SequentialThinking", "lseqthink"],
      "env": { "DEEPSEEK_API_KEY": "sk-xxx" }
    }
  }
}
```

```bash
# 或 pip 安装
pip install LseKit-SequentialThinking && lseqthink
```

重启 MCP 客户端即可使用。

### 各客户端配置

| 客户端 | 配置方式 |
|--------|--------|
| Claude Desktop | `claude_desktop_config.json` → `mcpServers` 加入上方 JSON |
| Cherry Studio | 设置 → MCP 服务器 → 命令填 `uvx` 参数填 `--from LseKit-SequentialThinking lseqthink` |
| Cursor | `.cursor/mcp.json` → 同上 JSON |
| Claude Code CLI | `claude mcp add seqthink -- uvx --from LseKit-SequentialThinking lseqthink` |
| VS Code (Cline) | `mcp.json` → 同上 |

---

## 🧩 26 个 MCP 工具

### 会话管理（8 个）

| 工具 | 说明 |
|------|------|
| `start_thinking` | 创建思维会话，支持 9 种模板，返回复杂度评估 |
| `add_step` | 添加一个思考步骤 |
| `update_step` | 修改已有步骤 |
| `review_thinking` | 获取完整思维链（linear / tree / summary） |
| `branch_thinking` | 从指定步骤创建替代推理分支 |
| `merge_insights` | 合并多个推理分支的洞察 |
| `complete_session` | 标记会话完成，触发结论生成 |
| `delete_session` | 删除会话及关联数据 |

### 增强分析（11 个）

| 工具 | 说明 |
|------|------|
| `compare_sessions` | 对比两个会话的推理路径异同 |
| `suggest_next` | 基于当前状态推荐下一步方向 |
| `rewrite_query` | LLM 优化问题表述 |
| `visualize_thinking` | 导出 Mermaid 流程图 |
| `replay_thinking` | 逐步回放推理过程 |
| `auto_tag` | 根据内容自动生成标签 |
| `moa_analyze` | Self-MoA 多智能体分析 |
| `add_connection` | 建立步骤间因果关系 |
| `detect_contradictions` | 检测推理链中的矛盾 |
| `extract_assumptions` | 提取推理中的隐含假设 |
| `update_tags` | 手动更新会话标签 |

### 质量控制（3 个）

| 工具 | 说明 |
|------|------|
| `validate_logic` | 检测逻辑谬误 |
| `evaluate_quality` | 5 维质量评估 |
| `detect_biases` | 检测认知偏见 |

### 管理与数据（4 个）

| 工具 | 说明 |
|------|------|
| `export_session` | 导出 Markdown / JSON / Text |
| `list_sessions` | 按状态/标签过滤会话列表 |
| `search_sessions` | 全文搜索历史会话 |
| `get_metrics` | 使用统计指标 |

---

## 🚀 双 MoA 推理引擎

| 模式 | 原理 | 适合场景 |
|------|------|---------|
| **Self‑MoA** | 同模型多温度采样 → 并行生成多条路径 → 投票汇聚最优结果 | 开放性创意、多角度分析 |
| **Iterative‑MoA** | 多轮迭代双模型调用 → 每轮优化上一轮结果 → 逐步逼近更优解 | 精确推理、方案优化 |

通过 `moa_analyze` 工具调用，3 轮独立 LLM 采样后投票综合。

---

## 📝 MCP Prompt & 📦 MCP Resource

| 类型 | 名称 | 说明 |
|------|------|------|
| Prompt | `problem_breakdown` | 引导 AI 将复杂问题拆分为子问题 |
| Prompt | `critical_analysis` | 引导 AI 批判性审视推理结论 |
| Prompt | `synthesis_prompt` | 引导 AI 将多个洞察综合为统一结论 |
| Resource | `config://server` | 服务器元数据 |
| Resource | `thinking://templates/catalog` | 9 种思维模板目录 |

---

## 🏗️ 技术架构

```
────────────── fastmcp (stdio / HTTP 双传输) ──────────────
 HeuristicEngine          │          LLMEngine
 (规则推理 · 零外部依赖)     │    (DeepSeek 驱动 · 异步推理)
────────────── Core 层 ───────────────────────────────────
 Context · Models · Templates · Store · Utils
────────────── SQLite + FTS5 中文全文检索 ────────────────
```

---

## 🔧 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key（LLM 引擎需要） | *必填* |
| `ST_TRANSPORT` | 传输模式：`http` 或 `stdio` | `http` |
| `ST_PORT` | HTTP 监听端口 | `20010` |
| `ST_DB_PATH` | SQLite 数据库路径 | `~/.seqthink/thoughts.db` |

---

<div align="center">

**[⭐ Star](https://github.com/LseKit/SequentialThinking)** ·
**[📦 PyPI](https://pypi.org/project/LseKit-SequentialThinking/)** ·
**[🐛 Issue](https://github.com/LseKit/SequentialThinking/issues)**

Made by [小逸 (LseKit)](https://github.com/LseKit) · MIT

</div>