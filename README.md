<div align="center">

# 🧠 Sequential Thinking MCP

**当 151,535 人/周在使用的 MCP 工具只有 1 个函数——这里提供了 26 个**

[![PyPI](https://img.shields.io/pypi/v/LseKit-SequentialThinking?color=2563eb&label=PyPI)](https://pypi.org/project/LseKit-SequentialThinking/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Ready-orange)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-192%20passed-brightgreen)]()
[![Stars](https://img.shields.io/github/stars/LseKit/SequentialThinking?style=social)](https://github.com/LseKit/SequentialThinking)

</div>

---

## 📊 功能对比矩阵

| 能力 | [官方版](https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking)<br><sub>TypeScript · 151K周下载</sub> | [arben-adm](https://pypi.org/project/mcp-sequential-thinking/)<br><sub>Python · 5阶段</sub> | [ad/sequentialthinking](https://github.com/ad/sequentialthinking)<br><sub>Go · 3传输模式</sub> | [**LseKit**](https://github.com/LseKit/SequentialThinking) 👑<br><sub>Python · 5,400行</sub> |
|------|:---:|:---:|:---:|:---:|
| **MCP 工具数** | 1 | 5 阶段 | 1 | **26** |
| **代码规模** | ~200 行 | ~800 行 | ~1,000 行 | **~5,400 行** |
| **AI 自动推理** | ❌ 手动录入每步 | ❌ 手动录入 | ❌ 手动录入 | ✅ **LLM 引擎自动推进** |
| **Self-MoA 并行推理** | ❌ | ❌ | ❌ | ✅ **温度采样多路并行** |
| **Iterative-MoA 迭代推理** | ❌ | ❌ | ❌ | ✅ **每轮逼近更优解** |
| **中文原生支持** | ❌ 仅英文 | ❌ 仅英文 | ❌ 仅英文 | ✅ **jieba 分词 + FTS5** |
| **思考持久化存储** | ❌ 无状态 | ❌ 无状态 | ❌ 无状态 | ✅ **SQLite 全文检索** |
| **质量评分与验证** | ❌ | ❌ | ❌ | ✅ **5 维自动评估** |
| **逻辑谬误检测** | ❌ | ❌ | ❌ | ✅ **8 种逻辑谬误 + 8 种偏见** |
| **可视化思维链** | ❌ | ❌ | ❌ | ✅ **Mermaid 流程图** |
| **思维推演回放** | ❌ | ❌ | ❌ | ✅ **逐步审计回放** |
| **多分支推理** | ❌ | ❌ | ❌ | ✅ **分支创建 + 合并** |
| **会话对比分析** | ❌ | ❌ | ❌ | ✅ **Diff 两场推理** |
| **MCP Resources** | 0 | 0 | 0 | **2（配置 + 模板）** |
| **MCP Prompts** | 0 | 0 | 0 | **3（分解/批判/综合）** |
| **单元测试** | 0 | 少量 | 未知 | **192 个** |
| **PyPI 发布** | ❌（npm only） | ✅ | ❌ | ✅ |
| **安装方式** | `npx` | `uvx` / `pip` | 手动编译 | `uvx` / `pip` |

> 「不是在改进官方版。是从零重构，实现了完全不同的架构和理念。官方版是草稿纸，这个是 AI 分析团队。」

---

## 🎯 解决的真问题

### ① AI 不会「质疑自己」

LLM 生成推理看起来很合理——但它不会主动检查：
- 这个结论有逻辑漏洞吗？
- 隐含假设是什么？
- 有没有被确认偏见影响？

→ `validate_logic` · `detect_contradictions` · `detect_biases` · `extract_assumptions` 正是为此设计

### ② 思考完就丢了

官方版用完即忘。这个版 SQLite FTS5 全文检索引擎——索引所有历史思考，相似问题自动召回，省去重复推演。支持 `search_sessions` 按关键词搜索、`compare_sessions` 多会话对比。

### ③ 中文场景被遗忘

官方版纯英文，中文分词完全失效。这个版 jieba 分词 + FTS5 索引端和查询端双对齐——「产品定价策略应该考虑用户画像」准确分词、精准检索。不是"支持中文"，是"原生为中文设计"。

### ④ 只有一条推理路径

官方版单线程思考，无法探索替代方案。这个版：
- **Self-MoA**：温度采样 → 多路径并行推理 → 交叉验证合并
- **Iterative-MoA**：多轮迭代 → 每轮逼近更优解 → 逐步收敛
- `branch_thinking` 创建并行分支 + `merge_insights` 合并最优结果

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
# 或者 pip
pip install LseKit-SequentialThinking && lseqthink
```

重启 MCP 客户端，AI 拥有 **26 工具 + 3 Prompt + 2 Resource**。

### 各客户端配置

| 客户端 | 怎么配 |
|--------|--------|
| **Claude Desktop** | `claude_desktop_config.json` → `mcpServers` 加入上方 JSON |
| **Cherry Studio** | 设置 → MCP 服务器 → 命令填 `uvx` 参数填 `--from LseKit-SequentialThinking lseqthink` |
| **Cursor** | `.cursor/mcp.json` → 同上 JSON |
| **Claude Code CLI** | `claude mcp add seqthink -- uvx --from LseKit-SequentialThinking lseqthink` |
| **VS Code (Cline)** | `mcp.json` → 同上 |

---

## 🧩 26 个 MCP 工具

### 会话管理（8 个）

| 工具 | 做什么 |
|------|--------|
| `start_thinking` | 创建思维会话，支持 9 种模板，返回复杂度评估 |
| `add_step` | 添加一个思考步骤 |
| `update_step` | 修改已有步骤 |
| `review_thinking` | 获取完整思维链（linear / tree / summary） |
| `branch_thinking` | 从指定步骤创建替代推理分支 |
| `merge_insights` | 合并多个推理分支的洞察 |
| `complete_session` | 标记会话完成，触发结论生成 |
| `delete_session` | 删除会话及所有关联数据 |

### 增强分析（11 个）

| 工具 | 做什么 |
|------|--------|
| `compare_sessions` | 对比两个会话的推理路径异同 |
| `suggest_next` | 基于当前状态推荐 3 个下一步方向 |
| `rewrite_query` | LLM 自动优化问题表述 |
| `visualize_thinking` | 导出 Mermaid 流程图，可视化推理路径和分支 |
| `replay_thinking` | 逐步回放推理过程，用于教学和审计 |
| `auto_tag` | 根据会话内容自动生成标签 |
| `moa_analyze` | Self-MoA 多智能体分析：3 轮独立采样后投票综合 |
| `add_connection` | 建立步骤之间的因果关系 |
| `detect_contradictions` | 检测推理链中的逻辑矛盾 |
| `extract_assumptions` | 提取推理过程中的隐含假设 |
| `update_tags` | 手动更新会话标签 |

### 质量控制（3 个）

| 工具 | 做什么 |
|------|--------|
| `validate_logic` | 检测 8 种逻辑谬误（无支撑结论、未验证假设等） |
| `evaluate_quality` | 5 维质量评估（一致性 / 完整性 / 严谨性 / 创新性 / 可操作性） |
| `detect_biases` | 检测 8 种认知偏见（确认偏见、锚定效应、可得性启发等） |

### 管理与数据（4 个）

| 工具 | 做什么 |
|------|--------|
| `export_session` | 导出会话为 Markdown / JSON / Text |
| `list_sessions` | 列出所有会话，按状态/标签过滤 |
| `search_sessions` | 按关键词全文搜索历史会话 |
| `get_metrics` | 获取使用统计指标（day / week / month / all） |

---

## 🚀 双 MoA 多智能体推理

有别于所有竞品的单线思考——这是唯一的**双引擎并行推理架构**。

### 模式选择速查

| 模式 | 原理 | 适合 | 典型场景 |
|------|------|------|---------|
| **Self‑MoA** | 单模型多温度采样 → 并行推理 → 投票汇聚 | 开放创意 · 多角度 | 方案评估、创意发散 |
| **Iterative‑MoA** | 多轮迭代双模型 → 每轮优化 → 逐步逼近 | 精确推理 · 收敛 | 代码审查、策略分析 |

调用 `moa_analyze` 即可启动 MoA 多智能体分析，3 轮独立 LLM 采样后投票综合。

---

## 📝 MCP Prompt & 📦 MCP Resource

接入本服务器后，这些内容会自动出现在客户端的 Prompt/Resource 菜单中。

| 类型 | 名称 | 做什么 |
|------|------|--------|
| Prompt | `problem_breakdown` | 引导 AI 将复杂问题拆分为 3-5 个子问题 |
| Prompt | `critical_analysis` | 引导 AI 从逻辑漏洞、隐含假设等角度批判推理结论 |
| Prompt | `synthesis_prompt` | 引导 AI 将多个洞察综合为统一结论，标注置信度 |
| Resource | `config://server` | 服务器元数据（名称、版本、工具数） |
| Resource | `thinking://templates/catalog` | 全部 9 种思维模板的目录 |

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
| `DEEPSEEK_API_KEY` | DeepSeek API Key（LLM 引擎必填） | *必填* |
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