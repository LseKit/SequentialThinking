<div align="center">

# Sequential Thinking 🤔

**让 Agent 真正「推理」——不只是「生成文字」**

[![PyPI](https://img.shields.io/pypi/v/LseKit-SequentialThinking?color=2563eb&label=PyPI)](https://pypi.org/project/LseKit-SequentialThinking/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-192%20passed-brightgreen)](Tests/)

双引擎推理 · 双重模型 MoA · 中文 FTS5 全文搜索 · 26 个 MCP 工具

</div>

---

## 📊 功能对比

| 功能 | [MCP官方](https://github.com/modelcontextprotocol/servers) (TS) | [bpradana](https://github.com/bpradana/sequentialthinking) (Go) | [spences10](https://github.com/spences10/mcp-sequentialthinking-tools) (TS) | [arben-adm](https://github.com/arben-adm/mcp-sequential-thinking) (Python) | [ad](https://github.com/ad/sequentialthinking) (Go) | **本项目** |
|:------|:---:|:----:|:-----:|:-----:|:--:|:--------:|
| **工具数** | 1 | 11 | 3 | 5 | 1 | **26** |
| **持久化** | ❌ 内存 | ❌ 内存 | ✅ 按 session | ✅ JSON 文件 | ❌ 内存 | **✅ SQLite WAL** |
| **中文 FTS5** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **LLM 集成** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ OpenAI 兼容 |
| **双引擎降级** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 自动** |
| **质量评估** | ❌ | ✅ 基础 | ❌ | ❌ | ❌ | **✅ 5 维 + 交叉验证** |
| **偏见检测** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 5 种 |
| **矛盾检测** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 双重 |
| **假设追踪** | ❌ | ❌ | ❌ | ✅ axioms | ❌ | ✅ 完整 CRUD |
| **修订标记** | ✅ isRevision | ❌ | ✅ is_revision | ❌ | ✅ | ✅ is_revision |
| **分支推理** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **自动完成** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **模板** | ❌ | 7 | ❌ | ❌ | ❌ | **✅ 9 种** |
| **Self-MoA** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 3 轮投票 |
| **Iterative-MoA** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 双模型迭代 |
| **MCP Resources** | ❌ | 3 | ❌ | ❌ | ❌ | ✅ 2 个 |
| **MCP Prompts** | ❌ | 3 | 1 | ❌ | ❌ | ✅ 3 个 |
| **Mermaid 可视化** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **回放** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Web 面板** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Docker** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **单元测试** | ✅ | ❌ | ✅ vitest | ✅ pytest | ✅ | **192 个** |

> 每个实现各有侧重。官方版是参考实现，简洁可靠；Go 版编译为单二进制、启动快、有 Web 面板；本项目的重点是多引擎推理和中文场景支持。

### 我们的不足

- 无 Web 调试面板（ad 版有）
- 无安全扫描（spences10、recallnet 有）
- 不支持反向导入（arben-adm 支持）
- Python 启动比 Go/TS 慢（加载 jieba 约 1-2 秒）
- 无 Docker 支持

---

## ⚡ 三种使用方式

### 方式一：PyPI 安装（最简单）

```bash
pip install LseKit-SequentialThinking
lseqthink
```

### 方式二：uvx 零安装

```bash
uvx --from LseKit-SequentialThinking lseqthink
```

### 方式三：克隆源码自行部署

```bash
git clone https://github.com/LseKit/SequentialThinking.git
cd SequentialThinking
uv venv SeqThinkVenV --python 3.12
uv pip install -r Requirements.txt
cp .env.example Config/.env && chmod 600 Config/.env
cp ecosystem.config.example.js Ecosystem/ecosystem.config.js
pm2 start Ecosystem/ecosystem.config.js && pm2 save
```

```bash
# 验证
pm2 status SequentialThinking
cd GitHubSrc && python3 -m pytest Tests/ -q
```

> 📖 完整部署见[项目部署手册](%E9%A1%B9%E7%9B%AE%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.md)

---

## 🔌 各智能体接入方式

### Claude Desktop

```json
{
  "mcpServers": {
    "seqthink": {
      "command": "uvx",
      "args": ["--from", "LseKit-SequentialThinking", "lseqthink"]
    }
  }
}
```

### Hermes

在 `~/.hermes/config.yaml` 中配置：

```yaml
mcp_servers:
  sequential-thinking:
    command: uvx
    args: ["--from", "LseKit-SequentialThinking", "lseqthink"]
    env:
      DEEPSEEK_API_KEY: sk-xxx
```

或者通过 Streamable HTTP 连接（先在另一台机器启本服务）：

```yaml
mcp_servers:
  sequential-thinking:
    url: http://your-host:21000/mcp
```

### Cherry Studio

MCP 设置 → 添加 → 命令填 `uvx`，参数填 `--from LseKit-SequentialThinking lseqthink`

### OpenClaw

在 `~/.openclaw/mcp.json` 中配置：

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["--from", "LseKit-SequentialThinking", "lseqthink"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add seqthink -- uvx --from LseKit-SequentialThinking lseqthink
```

### Cursor / VS Code (Cline / Continue)

在 `.cursor/mcp.json` 或 `mcp.json` 中加入：

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

## 🧠 启用双重思维

本项目的核心与大多数 Sequential Thinking 实现不同：**它有两套推理引擎，自动选择、可独立运行。**

```
不配 API Key → 自动使用 HeuristicEngine（内置规则推理，零 API 消耗）
配了 API Key → 启用 LLMEngine（调用大模型，支持 MoA 多智能体推理）
```

### 模式速查

| SELECTOR | MODE | 引擎 | Token | 场景 |
|:--------:|:----:|:-----|:----:|:-----|
| 0 | — | HeuristicEngine（零 API） | 0 | 测试 / 降级 / 简单问题 |
| 1 | self-moa | 模型1 多温度采样 | ~3× | 日常推理 |
| 2 | self-moa | 模型2 多温度采样 | ~3× | 对比模型 |
| 3 | self-moa | 双模型各自采样后合并 | ~6× | 多视角 |
| 3 | iterative | 双模型相互审视 + 迭代修正 | ~4~8× | 重要决策 |

### 为什么需要双重模型

不同的模型有各自擅长领域——比如 DeepSeek 在代码和技术分析上更精确，而 Qwen 在中文理解和产品思考上更自然。**双重模式让两个模型相互审视对方的输出**，覆盖单一模型的盲区。这里只说"比如"，是因为支持任意 OpenAI 兼容的 API，你用什么模型都可以。

### 降级是自动的

如果你只配了一个 API Key，系统自动使用单引擎模式。如果什么都没配，自动退回 HeuristicEngine，**零额外成本也能完成基础推理**。不需要手动切换模式。

---

## 🔧 配置

支持任何 **OpenAI 兼容的 API**（DeepSeek、OpenAI、Qwen、本地模型等），只需改 `ST_LLM_API_BASE` 和对应的模型名。

```
Config/.env（敏感，chmod 600）
├── DEEPSEEK_API_KEY     ← 模型1 API Key
└── DASHSCOPE_API_KEY    ← 模型2 API Key（双模型模式需要）

Ecosystem/ecosystem.config.js（非敏感）
├── ST_LLM_SELECTOR      ← 0/1/2/3
├── ST_LLM_MODE          ← self-moa / iterative
├── ST_MOA_ROUNDS        ← 1~20
├── ST_LLM_MODEL         ← 模型1 名称
├── ST_LLM2_MODEL        ← 模型2 名称
├── ST_LLM_API_BASE      ← API 端点
├── ST_HOST / ST_PORT    ← 监听地址和端口
└── ST_DB_PATH           ← SQLite 数据库路径
```

### 环境变量参考

| 变量 | 用途 | 参考值 |
|------|------|:------:|
| `DEEPSEEK_API_KEY` | 模型1 的 API Key | 必填 |
| `DASHSCOPE_API_KEY` | 模型2 的 API Key | 可选 |
| `ST_LLM_MODEL` | 模型1 名称 | `deepseek-v4-flash` |
| `ST_LLM2_MODEL` | 模型2 名称 | `qwen3.7-plus` |
| `ST_LLM_API_BASE` | API 端点（兼容 OpenAI 协议即可） | `https://api.deepseek.com/v1` |
| `ST_LLM_SELECTOR` | 引擎选择（0=启发式 / 1-3=LLM） | `3` |
| `ST_LLM_MODE` | MoA 模式 | `self-moa` |
| `ST_MOA_ROUNDS` | 采样/迭代轮数 | `3` |
| `ST_TRANSPORT` | 传输模式 | `streamable-http` |
| `ST_PORT` | 监听端口 | 由配置决定 |
| `ST_DB_PATH` | SQLite 数据库路径 | `~/.seqthink/thoughts.db` |

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────┐
│            fastmcp (MCP 协议层)                       │
│       Streamable HTTP · stdio 双传输                  │
├──────────────────────────────────────────────────────┤
│  HeuristicEngine          │     LLMEngine            │
│  (规则推理 · 零外部依赖)    │  (OpenAI 兼容 · 异步)    │
│  关键词提取 · Jaccard对比  │  Self-MoA · Iterative-MoA│
├──────────────────────────────────────────────────────┤
│                    Core 层                            │
│       Context · Models · Templates                   │
│           Utils · Logger · Helpers                   │
├──────────────────────────────────────────────────────┤
│         SQLite + FTS5 中文全文检索                    │
│        5 表 + FK 约束 + WAL 并发模式                  │
└──────────────────────────────────────────────────────┘
```

### 双引擎降级路径

```
启动 → 检测 DEEPSEEK_API_KEY
              │
     有 Key ──┼── 无 Key
              │        │
       LLMEngine    HeuristicEngine
       (MoA 推理)   (内置规则 · 零成本)
              │
      SELECTOR=3?
         │
    有 Key2? ── 无 Key2?
        │           │
   双模型 MoA    单模型 MoA
```

---

## 🎯 这些功能解决了什么

### 推理像是「黑箱」

LLM 能生成流畅的推理，但内部逻辑不一定可靠。工具内置了矛盾检测（`detect_contradictions`）、假设提取（`extract_assumptions`）、和逻辑验证（`validate_logic`），让推理过程更透明——不是为了让输出「更好看」，而是让结果更可信。

### 中文的推理质量

大多数 Sequential Thinking 工具是基于英文构建的。本项目在分词（jieba）和全文检索（FTS5）两端都对中文做了针对性优化，对中文问题和中文思考的检索命中率明显更高。

### 思考不留痕迹

推理完就丢了，下次同样问题又要从头来。SQLite WAL 持久化让每个会话可搜索、可回放、可对比——比如对比两次不同的推理路径，看看哪次更合理。

### 单一模型的盲区

单一模型容易陷入固定模式。Self-MoA 用不同温度采样多条推理路径后投票，Iterative-MoA 让两个模型反复审视对方输出——两种策略覆盖了「多角度验证」和「逐步逼近最优」两种需求。

---

## 🧰 26 个 MCP 工具

### 会话管理（8 个）

| 工具 | 作用 |
|------|------|
| `start_thinking` | 创建推理会话，返回复杂度评估和推荐模板 |
| `add_step` | 添加推理步骤 |
| `update_step` | 修改已有步骤 |
| `review_thinking` | 获取完整思维链（linear / tree / summary） |
| `branch_thinking` | 从指定步骤创建替代推理分支 |
| `merge_insights` | 合并多个分支的洞察 |
| `complete_session` | 标记会话完成 |
| `delete_session` | 级联删除会话 |

### 质量控制（3 个）

| 工具 | 作用 |
|------|------|
| `validate_logic` | 检测逻辑谬误 |
| `evaluate_quality` | 5 维质量评估 + 交叉验证 |
| `detect_biases` | 检测 5 种认知偏见 |

### 管理（4 个）

| 工具 | 作用 |
|------|------|
| `export_session` | 导出 Markdown / JSON / Text |
| `list_sessions` | 按状态和标签筛选 |
| `search_sessions` | FTS5 中文全文检索 |
| `get_metrics` | 日/周/月使用统计 |

### 增强（11 个）

| 工具 | 作用 |
|------|------|
| `compare_sessions` | 对比两个会话 |
| `suggest_next` | 推荐下一步方向 |
| `rewrite_query` | LLM 优化问题表述 |
| `visualize_thinking` | Mermaid 流程图 |
| `replay_thinking` | 逐步回放 |
| `auto_tag` | 自动生成标签 |
| `moa_analyze` | MoA 多轮投票分析 |
| `add_connection` | 建立步骤间因果关系 |
| `detect_contradictions` | 检测推理矛盾 |
| `extract_assumptions` | 提取隐含假设 |
| `update_tags` | 替换会话标签 |

### Resources & Prompts

- `config://server` — 服务配置
- `thinking://templates/catalog` — 9 种思维模板目录
- `problem_breakdown` — 问题分解
- `critical_analysis` — 批判性分析
- `synthesis_prompt` — 综合结论

---

## 🧪 测试

```bash
cd GitHubSrc
python3 -m pytest Tests/ -v    # 192 全量
```

| 模块 | 数量 |
|:-----|:---:|
| Core Models / Templates / Context | 48 |
| Utils Logger | 6 |
| Handlers Helpers | 24 |
| HeuristicEngine | 26 |
| LLMEngine + MoA | 36 |
| Storage + FTS5 中文 | 52 |
| **总计** | **192** |

---

<div align="center">

MIT · [小逸 (LseKit)](https://github.com/LseKit)

</div>