# Sequential Thinking 🤔

<div align="center">

**高级结构化多步推理 MCP 服务**

双引擎推理 · 双模型 MoA · 中文 FTS5 全文搜索 · 26 个 MCP 工具

[![PyPI](https://img.shields.io/pypi/v/LseKit-SequentialThinking?color=2563eb&label=PyPI)](https://pypi.org/project/LseKit-SequentialThinking/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-192%20passed-brightgreen)](Tests/)

</div>

---

## 📖 项目简介

Sequential Thinking 是一个纯 Python 的 MCP 服务，为 AI 助手提供结构化多步推理能力。

它的核心功能是：把一个大问题拆成多个小步骤（分析→假设→验证→结论），一步步推理，支持分支探索、质量评估、偏见检测，最终导出可视化图表或逐步回放审查。

> **适用场景：** 日常推理、思路整理、决策分析、教学演示——只要是需要「把想法理清楚」的场景。

---

## ⚡ 快速开始

### PyPI 安装（推荐）

```bash
pip install LseKit-SequentialThinking
lseqthink
```

### uvx 零安装

```bash
uvx --from LseKit-SequentialThinking lseqthink
```

### 克隆代码自行部署

```bash
git clone https://github.com/LseKit/SequentialThinking.git
cd SequentialThinking
uv venv SeqThinkVenV --python 3.12
uv pip install -r GitHubSrc/Requirements.txt
mkdir -p Config && cp GitHubSrc/.env.example Config/.env && chmod 600 Config/.env
mkdir -p Ecosystem && cp GitHubSrc/ecosystem.config.example.js Ecosystem/ecosystem.config.js
pm2 start Ecosystem/ecosystem.config.js && pm2 save
```

```bash
# 验证
pm2 status SequentialThinking
ss -tlnp | grep 20010
cd GitHubSrc && python3 -m pytest Tests/ -q
```

> 📖 完整部署见[项目部署手册](%E9%A1%B9%E7%9B%AE%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.md)

### 各客户端 MCP 配置

| 客户端 | 配置方式 |
|--------|---------|
| **Claude Desktop** | `claude_desktop_config.json` → `mcpServers` 加入下方 JSON |
| **Cherry Studio** | 设置 → MCP 服务器 → 命令 `uvx` 参数 `--from LseKit-SequentialThinking lseqthink` |
| **Cursor** | `.cursor/mcp.json` → 加入下方 JSON |
| **Claude Code** | `claude mcp add seqthink -- uvx --from LseKit-SequentialThinking lseqthink` |
| **Hermes** | MCPHub 面板 → 添加 → 命令 `uvx` 参数同上 |
| **大龙虾** | MCP 服务器 → 命令模式 → 填 `uvx` 和参数 |
| **VS Code (Cline/Continue)** | `mcp.json` → 加入下方 JSON |

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

---

## 🎯 为什么选择本项目

### 功能对比矩阵

| 功能 | [MCP官方](https://github.com/modelcontextprotocol/servers) (TS) | [bpradana](https://github.com/bpradana/sequentialthinking) (Go) | [spences10](https://github.com/spences10/mcp-sequentialthinking-tools) (TS) | [arben-adm](https://github.com/arben-adm/mcp-sequential-thinking) (Python) | [ad](https://github.com/ad/sequentialthinking) (Go) | [recallnet](https://github.com/recallnet/sequential-thinking-recall) (TS) | **本项目** |
|:------|:---:|:----:|:-----:|:-----:|:--:|:-------:|:--------:|
| **工具数** | 1 | 11 | 3 | 5 | 1 | 1 | **26** |
| **语言** | TypeScript | Go | TypeScript | Python | Go | TypeScript | **Python** |
| **持久化** | ❌ 内存 | ❌ 内存 | ✅ 按 session | ✅ JSON 文件 | ❌ 内存 | ❌ 内存 | **✅ SQLite WAL** |
| **数据库表** | — | — | — | — | — | — | **✅ 5 表 + FK** |
| **FTS5 全文搜索** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **LLM 集成** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ OpenAI 兼容** |
| **双引擎降级** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 自动** |
| **质量评估** | ❌ | ✅ 基础 | ❌ | ❌ | ❌ | ❌ | **✅ 5 维 + 交叉验证** |
| **偏见检测** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 5 种 |
| **矛盾检测** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 双重** |
| **假设追踪** | ❌ | ❌ | ❌ | ✅ axioms | ❌ | ❌ | **✅ 完整 CRUD** |
| **修订标记** | ✅ isRevision | ❌ | ✅ is_revision | ❌ | ✅ | ❌ | **✅ is_revision** |
| **分支推理** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **自动完成** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **模板** | ❌ | 7 | ❌ | ❌ | ❌ | ❌ | **✅ 9 种** |
| **Self-MoA** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 3 轮投票** |
| **Iterative-MoA** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 双模型迭代** |
| **MCP Resources** | ❌ | 3 | ❌ | ❌ | ❌ | ❌ | **✅ 2 个** |
| **MCP Prompts** | ❌ | 3 | 1 | ❌ | ❌ | ❌ | **✅ 3 个** |
| **自动标签** | ❌ | ❌ | ❌ | ✅ tags | ❌ | ❌ | ✅ |
| **导入/导出** | ❌ | 导出 | ❌ | ✅ 导入+导出 | ❌ | ❌ | 导出 (Markdown/JSON) |
| **Mermaid 可视化** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |
| **回放** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **安全扫描** | ❌ | ❌ | ✅ prompt injection | ❌ | ❌ | ✅ key redact | ❌ |
| **链上存储** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Recall | ❌ |
| **传输** | stdio | HTTP+stdio | stdio | stdio | stdio+SSE+HTTP | stdio | **Streamable HTTP+stdio** |
| **Web 面板** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Docker** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **单元测试** | ✅ | ❌ | ✅ vitest | ✅ pytest | ✅ | ❌ | **✅ 192 个** |
| **包管理** | npm | Go mod | pnpm | uv | Go mod | npm | **uv / PyPI** |

### 性能对比

| 维度 | MCP 官方 | Go 版 | Python 轻量版 | **本项目** |
|:-----|:--------:|:----:|:-----------:|:--------:|
| 启动速度 | 🟢 快 | 🟢 快 | 🟡 中 | 🟡 中 |
| 内存占用 | 🟢 极低 | 🟢 低 | 🟡 中 | 🟡 中 |
| 并发能力 | 🔴 无 | 🔴 低 | 🔴 低 | 🟢 WAL+aiosqlite |
| 数据安全 | 🔴 进程死数据丢 | 🔴 进程死数据丢 | ⚠️ 文件可能损坏 | 🟢 FK+WAL 保护 |
| 查询速度 | — | — | 🔴 文件全读 | 🟢 FTS5 <1ms |
| 可恢复性 | 🔴 无 | 🔴 无 | ⚠️ JSON 可恢复 | 🟢 SQLite 持久化 |

### 我们的不足（诚实说明）

- **无 Web 调试面板**：ad/sequentialthinking 支持 SSE+HTTP 模式，还带 Web 界面。我们暂不支持
- **无安全扫描**：spences10 和 recallnet 做了 prompt injection 和 key 脱敏扫描，我们没做
- **无链上存储**：recallnet 支持 Recall 链上存证，我们不支持
- **无导入功能**：支持导出 Markdown/JSON，但不支持反向导入
- **Python 启动速度**：比 Go/TS 版本慢（加载 jieba 等依赖约 1-2 秒）
- **缺少「反方观点」功能**：计划中但没有实现的功能——AI 自己反驳自己的推理，充当「魔鬼代言人」角色

---

## ⚡ MoA 多智能体推理

### Self-MoA（温度采样）— 默认模式

**是什么：** 同一模型用多种不同的「心态」（温度参数 0.1~0.9）去回答同一个问题，然后投票合并。

```python
# 伪代码：换 N 种心态问自己
for temp in [0.3, 0.7, 1.0, 0.5, 0.9]:
    答案 = 模型.回答(问题, 温度=temp)
    # temp=0.3 → 保守精准
    # temp=0.7 → 常规水平
    # temp=1.0 → 天马行空
    收集答案()
投票合并(所有答案)
```

**为什么需要：** 同一个模型用固定温度回答容易陷入固定思考模式。温度采样相当于让同一个人换几种心情回答，综合不同视角。论文 [arXiv 2502.00674](https://arxiv.org/abs/2502.00674) 证实 Self-MoA 在多数场景优于混合多模型。

### Iterative-MoA（迭代推理）

**是什么：** 两个不同模型互相看对方说了什么，然后各自修正，多轮迭代逼近最优解。

**为什么需要：** 每个模型有各自的训练数据和擅长领域。DeepSeek 擅长代码和技术，Qwen 擅长中文理解和产品思考。两者互补能覆盖单一模型的盲区。参考 [arXiv 2406.04692](https://arxiv.org/abs/2406.04692)。

### 模式选择速查

| SELECTOR | MODE | 效果 | Token | 场景 |
|:--------:|:----:|:-----|:----:|:-----|
| 0 | — | 离线启发式引擎（零 API） | 0 | 测试/降级/简单问题 |
| 1 | self-moa | 模型1 多温度采样投票 | ~3× | 日常推理，最省 |
| 2 | self-moa | 模型2 多温度采样投票 | ~3× | 对比模型效果 |
| 3 | self-moa | 双模型各自采样后合并 | ~6× | 需多视角 |
| 3 | iterative | 双模型互相看+迭代修正 | ~4~8× | 重要决策，最高质量 |

---

## 🔧 配置

```
Config/.env（敏感，chmod 600）
├── DEEPSEEK_API_KEY     ← 模型1 API Key
└── DASHSCOPE_API_KEY    ← 模型2 API Key（双模型模式需要）

Ecosystem/ecosystem.config.js（非敏感）
├── ST_LLM_SELECTOR      ← 0/1/2/3
├── ST_LLM_MODE          ← self-moa / iterative
├── ST_MOA_ROUNDS        ← 1~20（默认 3）
├── ST_LLM_MODEL         ← 模型1（默认 deepseek-v4-flash）
├── ST_LLM2_MODEL        ← 模型2（默认 qwen3.7-plus）
├── ST_HOST / ST_PORT    ← 监听地址和端口
└── ST_DB_PATH           ← SQLite 数据库路径
```

> 支持任何 OpenAI 兼容的 API，只需改 `ST_LLM_MODEL` 和 `ST_LLM_API_BASE`。

### 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | 模型1 的 API Key | *必填* |
| `DASHSCOPE_API_KEY` | 模型2 的 API Key | 可选 |
| `ST_LLM_MODEL` | 模型1 名称 | `deepseek-v4-flash` |
| `ST_LLM2_MODEL` | 模型2 名称 | `qwen3.7-plus` |
| `ST_LLM_API_BASE` | API 端点（兼容 OpenAI 协议即可） | `https://api.deepseek.com/v1` |
| `ST_TRANSPORT` | 传输模式 | `streamable-http` |
| `ST_HOST` | 监听地址 | `0.0.0.0` |
| `ST_PORT` | 监听端口 | 由配置文件决定 |
| `ST_DB_PATH` | SQLite 数据库路径 | `~/.seqthink/thoughts.db` |

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────┐
│              fastmcp (MCP 协议层)                     │
│         Streamable HTTP · stdio 双传输                │
├──────────────────────────────────────────────────────┤
│  HeuristicEngine          │     LLMEngine            │
│  (规则推理 · 零外部依赖)    │  (OpenAI 兼容 · 异步)    │
├──────────────────────────────────────────────────────┤
│                    Core 层                            │
│          Context · Models · Templates                 │
│                  Utils · Logger                       │
├──────────────────────────────────────────────────────┤
│              SQLite + FTS5 中文全文检索                │
│              5 表 + FK + WAL 模式                     │
└──────────────────────────────────────────────────────┘
```

---

## 🧰 26 个 MCP 工具

### 会话管理（8 个）

| 工具 | 作用 |
|:-----|:-----|
| `start_thinking` | 创建推理会话，返回复杂度评估（easy/medium/hard）和推荐模板 |
| `add_step` | 添加推理步骤（analysis/hypothesis/verification/conclusion），返回质量评分 |
| `update_step` | 修改已有步骤的内容或类型 |
| `review_thinking` | 获取完整思维链（linear/tree/summary 三种视图） |
| `branch_thinking` | 从指定步骤创建替代分支，探索不同推理路径 |
| `merge_insights` | 合并主分支和多分支的洞察为统一结论 |
| `complete_session` | 手动标记会话为 completed 状态 |
| `delete_session` | 级联删除会话及其所有关联数据 |

### 质量控制（3 个）

| 工具 | 作用 |
|:-----|:-----|
| `validate_logic` | 检测逻辑谬误（无支撑结论、未验证假设、循环论证） |
| `evaluate_quality` | 5 维质量评估（一致性/完整性/严谨性/创新性/可操作性）+ LLM↔启发式交叉验证 |
| `detect_biases` | 检测过度自信、过度简化、锚定效应等 5 种认知偏见 |

### 管理（4 个）

| 工具 | 作用 |
|:-----|:-----|
| `export_session` | 导出为 Markdown / JSON / Text |
| `list_sessions` | 按状态和标签筛选会话列表 |
| `search_sessions` | FTS5 全文检索（jieba 中文分词） |
| `get_metrics` | 按日/周/月统计推理指标 |

### 增强（11 个）

| 工具 | 作用 |
|:-----|:-----|
| `compare_sessions` | Jaccard 相似度对比两会话 |
| `suggest_next` | 上下文感知的下一步建议 |
| `rewrite_query` | LLM 优化问题表述 |
| `visualize_thinking` | Mermaid 流程图导出 |
| `replay_thinking` | 逐步回放推理过程 |
| `auto_tag` | LLM 自动生成标签 |
| `moa_analyze` | MoA 多轮投票分析 |
| `add_connection` | 步骤间添加推理链路 |
| `detect_contradictions` | 双引擎自相矛盾检测 |
| `extract_assumptions` | LLM 提取隐含假设 |
| `update_tags` | 替换会话标签 |

### Resources & Prompts

- `config://server` — 服务配置信息
- `thinking://templates/catalog` — 9 种思维模板目录
- `problem_breakdown` — 问题分解提示
- `critical_analysis` — 批判性分析提示
- `synthesis_prompt` — 综合结论提示

---

## 🧪 测试

```bash
cd GitHubSrc
python3 -m pytest Tests/ -v    # 192 全量
```

| 模块 | 数量 |
|:-----|:---:|
| Core Models/Templates/Context | 48 |
| Utils Logger | 6 |
| Handlers Helpers | 24 |
| HeuristicEngine | 26 |
| LLMEngine + MoA | 36 |
| Storage + FTS5 中文 | 52 |
| **总计** | **192** |

---

## 📄 MIT 许可证

© 2026 小逸 (LseKit)

```
MIT License

Copyright (c) 2026 小逸 (LseKit)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

> 允许：商业使用、修改、分发、私人使用。唯一要求：保留原始版权声明。

---

<div align="center">

**设计和开发：小逸 · 欢迎提交 Issue 或 PR**

</div>