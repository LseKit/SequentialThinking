# Changelog

## v1.2.1 (2026-07-03)

### 🚀 新功能
- **双模型 MoA**：支持 Self-MoA（温度采样）和 Iterative-MoA（迭代推理）两种模式
- **jieba 中文 FTS5**：索引端和查询端双对齐，中文搜索命中率从 0 到正常工作
- **SQLite PRAGMA 优化**：synchronous=NORMAL + 8MB cache + 32MB mmap

### ⚡ 性能优化
- `_self_moa_dual`：双模型采样从顺序改为并行，延迟减半
- `_iterative_moa`：每轮两个模型同时调用 via `asyncio.gather`
- 全量 192 测试，13.55s 完成

### 🐛 Bug 修复
- 修复 pytest.ini `cache_dir` 路径嵌套问题
- 修复 FTS5 索引端和查询端分词不一致问题

---

## v1.2.0 (2026-07-02)

### 📦 单元测试
- 新增 182 个单元测试，覆盖全部 8 个模块
- FTS5 全文搜索虚拟表（替代 LIKE）
- 自动完成：step_type=conclusion + quality>0.7 触发 complete_session
- MCP Resources 2 个 + Prompts 3 个
- 6 个新 Hermes 技能（MCP构建器、现实检验者等）

---

## v1.1.x (2026-07-02)

### 🔧 配置体系重构
- 删除 Config.yaml，改用 PM2 ecosystem.config.js
- Linux 凭据分离：DEEPSEEK_API_KEY → Config/.env
- __package__ 方案：让 __main__.py 可以直接运行
- 项目部署手册.md 完整重写

---

## v1.0.x (2026-07-01)

### 🎉 初始重构版
- 用 Python + FastMCP 完全重写 Go 原版
- 20 个 MCP 工具（原版 11 个）
- LLM 引擎 + 启发式引擎双引擎
- SQLite WAL 持久化
- Streamable HTTP + stdio 双协议