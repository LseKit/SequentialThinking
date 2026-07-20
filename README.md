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

或者通过 Streamable HTTP 连接：

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

## 🧠 启用双重思维 — 让 Agent 真正「推理」，不只是「生成文字」

### 为什么需要两种推理模式

单次 LLM 调用天然是「下一个词预测」——它无法自我纠偏，也无法从多个角度审视同一个答案。

本项目的双 MoA（Mixture-of-Agents）推理引擎提供了两种互补的增强方式：一种快速发散找思路，一种深入打磨求精确。参考文献：[arXiv 2502.00674](https://arxiv.org/abs/2502.00674) 和 [arXiv 2406.04692](https://arxiv.org/abs/2406.04692)。

### 两种模式怎么工作

#### Self‑MoA — 并行发散，投票挑选

同一个模型、换几种「心态」（不同温度参数），**同时**回答同一个问题，然后用语义相似度给每条回答打分，投票选出最优的那条。

| 维度 | 说明 |
|------|------|
| 原理 | 同一 LLM，3 个不同温度各自独立完成完整推理链，对输出做语义相似度投票，选最优 |
| 论文支撑 | [arXiv 2502.00674](https://arxiv.org/abs/2502.00674)：Self-MoA 在 AlpacaEval 2.0 上比 MoA 高 6.6%，多数场景优于混合多模型 |
| 调用方式 | **并行**（`asyncio.gather`），温服样本同时跑 |
| 收敛标准 | 语义相似度投票最高者胜出 |
| Token 消耗 | 约 3 倍，但耗时 ≈ 单次调用（并行执行） |
| 主要优势 | 保证输出质量下限稳定（同一模型水平一致），并行速度快，温度多样性带来广度覆盖 |
| 潜在短板 | 温度高时可能引入随机噪声，无法利用不同模型的互补能力 |

适合：**发散找思路**——写文案、头脑风暴、多角度评估。

#### Iterative‑MoA — 串行打磨，逐步逼近

两个模型**轮流**当「作者」和「审稿人」：A 写初版 → B 审查挑刺 → A 再优化 → B 再审查…直到收敛或达到最大轮数。

| 维度 | 说明 |
|------|------|
| 原理 | A 生成初版 → B 以批判者角色审查给出修改版 → A 综合再优化 → 循环直到收敛 |
| 论文支撑 | [arXiv 2406.04692](https://arxiv.org/abs/2406.04692)：分层 MoA 架构能用纯开源模型超越 GPT-4 Omni（AlpacaEval 65.1% vs 57.5%） |
| 调用方式 | **串行**，每轮依赖上一轮输出 |
| 收敛标准 | 连续两轮输出的语义相似度超过阈墀时提前终止 |
| Token 消耗 | 轮数 × 每次约 2 倍，质量随轮数递增 |
| 主要优势 | 逐步精炼适合深度推理，混合不同模型可发挥各自特长（如一个擅长分析，一个擅长总结） |
| 潜在短板 | 串行耗时随迭代次数线性增长，混合模型时弱模型可能拖累整体质量（论文证实混合模型在多数场景不如 Self-MoA） |

适合：**深入打磨细节**——数学推理、代码审查、合规分析。

### 一张表分清

| 对比项 | Self‑MoA | Iterative‑MoA |
|--------|----------|---------------|
| 调用模型数 | 1 个模型，多个温度副本 | 2 个模型（或同一模型不同配置） |
| 调用方式 | **并行** | **串行** |
| 收敛方式 | 投票选最高分 | 连续两轮不再显著变化即停止 |
| Token 代价 | ~3 倍（一次性） | 轮数 × 每次约 2 倍 |
| 思路风格 | 发散 → 收敛 | 迭代 → 逼近 |
| 什么时候选 | 想快速看到多个角度，让模型自选最优 | 想反复打磨一个结论，直到挑不出问题 |

### 不配 API 也能用 — 自动降级

没有配任何 LLM API Key、或者 LLM 调用连续失败时，系统自动降级为**内置规则推理引擎**：

- 基于模板 + 关键词匹配做问题分解、步骤生成、总结反思
- 命中已缓存的相似思考模式时直接复现
- 降级过程不出错，只写日志

不配 Key 也能得到一个有结构、有逻辑的思考框架，**不会空白也不报错**。

---

## 🔧 配置

支持任何 **OpenAI 兼容的 API**（DeepSeek、OpenAI、Qwen、本地模型等）。

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
| `ST_LLM_API_BASE` | OpenAI 兼容 API 端点 | `https://api.deepseek.com/v1` |
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

LLM 能生成流畅的推理，但内部逻辑不一定可靠。内置的矛盾检测（`detect_contradictions`）、假设提取（`extract_assumptions`）、逻辑验证（`validate_logic`）让推理过程更透明。

### 中文的推理质量

大多数 Sequential Thinking 工具基于英文构建。本项目在分词（jieba）和全文检索（FTS5）两端对中文做了针对性优化。

### 思考不留痕迹

推理完就丢了，下次同样问题又要从头来。SQLite WAL 持久化让每个会话可搜索、可回放、可对比。

### 单一模型的盲区

单一模型容易陷入固定模式。Self-MoA 用不同温度采样多条推理路径后投票，Iterative-MoA 让两个模型反复审视对方输出——两种策略覆盖了「多角度验证」和「逐步逼近最优」两种互补需求。

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