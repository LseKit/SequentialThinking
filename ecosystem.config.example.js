/**
 * ═══════════════════════════════════════════════════════════
 * Sequential Thinking MCP — PM2 Ecosystem 配置模板
 * ═══════════════════════════════════════════════════════════
 * 文件路径: GitHubSrc/ecosystem.config.example.js（模板，可进 Git）
 * 原作者: 小逸
 * 官方仓库: https://github.com/LseKit/SequentialThinking
 *
 * 用途:
 *     PM2 进程管理器的配置文件。定义了如何启动、守护和监控
 *     Sequential Thinking MCP 服务。
 *
 *     部署时将此文件复制到项目根目录下：
 *     cp GitHubSrc/ecosystem.config.example.js ../Ecosystem/ecosystem.config.js
 *
 *     然后用 PM2 启动：
 *     pm2 start Ecosystem/ecosystem.config.js
 *     pm2 save
 *
 * ────── 配置分离原则（重要）──────
 *     API Key 等敏感凭据 →  Config/.env（chmod 600，不进 Git）
 *     端口/路径/模型名   →  本文件 env 字段（非敏感，模板可进 Git）
 *
 *     本文件里面没有任何 API Key，只有配置参数。
 *     敏感信息（DEEPSEEK_API_KEY、DASHSCOPE_API_KEY）在 Config/.env 中。
 *
 * ────── 作者当前使用的值（仅供参考，不是硬性规定）──────
 *     你可以自由替换为任何 OpenAI 兼容的 API 和模型。
 *
 *     模型1  : deepseek-v4-flash（DeepSeek）
 *     模型2  : qwen3.7-plus（通义千问，通过 DashScope 调用）
 *     模式   : self-moa（温度采样）
 *     轮次   : 3
 *
 *     你只需要知道:
 *     - ST_LLM_MODEL / ST_LLM2_MODEL 支持任何 OpenAI 兼容的模型名
 *     - ST_LLM_API_BASE / ST_LLM2_API_BASE 写对应的 API 端点即可
 *     - API Key 放在 Config/.env 中，变量名跟 API 服务商一样即可
 *
 * ═══════════════════════════════════════════════════════════
 */
module.exports = {
  apps: [
    {
      // ── PM2 进程名 ──
      // 在 pm2 status、pm2 logs、pm2 restart 等命令中使用的名称
      name: "SequentialThinking",

      // ── 工作目录 ──
      // 所有相对路径相对于此目录
      // __dirname = Ecosystem/ 目录，resolve(..) = 项目根
      cwd: require("path").resolve(__dirname, ".."),

      // ── Python 解释器路径 ──
      // 指向 UV 虚拟环境中的专属 Python，不污染系统 Python
      // 如果用 Micromamba，则指向 micromamba/envs/xxx/bin/python
      interpreter: "SequentialThinkingVenV/bin/python",

      // ── 启动脚本（Python 入口文件）──
      script: "GitHubSrc/__main__.py",

      // ── CLI 参数 ──
      // --env-file: 告诉 Python 进程去哪里找 .env 文件
      // 路径是相对于 cwd 的
      args: ["--env-file", "Config/.env"],

      // ── 非敏感环境变量 ──
      // PM2 会自动将这些变量注入到进程的 os.environ 中
      // Python 代码里直接用 os.getenv("ST_PORT") 就能读到
      // 🔴 API Key 不在本文件，在 Config/.env 中
      env: {
        // ── Python 运行时 ──
        PYTHONUNBUFFERED: "1",

        // ── FastMCP 传输协议 ──
        // "http" = Streamable HTTP（推荐，对内网 MCPHub 开放）
        // "stdio" = 标准输入输出（用于本地 MCP 客户端直连）
        ST_TRANSPORT: "http",

        // ── HTTP 监听地址 ──
        // "0.0.0.0" = 监听所有网卡，内网其他机器可访问
        // "127.0.0.1" = 仅本机可访问（更安全但 MCPHub 连不上）
        ST_HOST: "0.0.0.0",

        // ── HTTP 监听端口 ──
        // MCP 服务段从 20000 开始，每次 +10
        // 当前已用: 20000（MCPHub）, 20010（本服务）
        ST_PORT: "20010",

        // ── SQLite 数据库路径 ──
        // 相对路径：相对于项目根目录 /mcp/SequentialThinking/
        // 绝对路径：直接写完整路径
        // 删除后重启会自动重建
        ST_DB_PATH: "Data/sequential-thinking.db",

        // ── 模型选择开关（0/1/2/3）──
        // 0 = 启发式引擎（不使用任何外部 LLM，完全离线）
        //     所有 MCP 工具仍可用，但 moa_analyze 等依赖 LLM 的不可用
        // 1 = 仅模型1（由 ST_LLM_MODEL 指定）
        // 2 = 仅模型2（由 ST_LLM2_MODEL 指定，需在 .env 中配 DASHSCOPE_API_KEY）
        // 3 = 双模型推荐（模型1 + 模型2，质量和灵活性的最佳平衡）
        ST_LLM_SELECTOR: "3",

        // ── 模型1 配置 ──
        // 任何 OpenAI 兼容的 API 和模型均可
        // 示例：DeepSeek。你也可以用 GPT-4o / Claude / Gemini 等
        ST_LLM_API_BASE: "https://api.deepseek.com/v1",
        ST_LLM_MODEL: "deepseek-v4-flash",

        // ── 模型2 配置（ST_LLM_SELECTOR=2 或 3 时需要）──
        // 任何 OpenAI 兼容的 API 和模型均可
        // 示例：通义千问（通过阿里云 DashScope 调用）
        // API Key 变量名标准: DASHSCOPE_API_KEY（在 Config/.env 中）
        ST_LLM2_API_BASE: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ST_LLM2_MODEL: "qwen3.7-plus",

        // ── 推理模式 ──
        // "self-moa"  = 温度采样（默认，推荐日常使用）
        //                同一模型用 N 种不同温度（0.1~0.9）各调一次
        //                投票合并结果，消除单次随机偏差
        //                论文已证实 Self-MoA 在多数场景优于混合多模型
        //
        // "iterative" = 迭代推理（适合重要决策）
        //                双模型互相看对方上一轮的输出后修正补充
        //                消除认知盲区，越辩越明
        //                Token 消耗：2 模型 × 2 次/轮 × rounds
        //
        // 默认 self-moa 就够了，只有特别重要的推理才切 iterative
        ST_LLM_MODE: "self-moa",

        // ── 推理深度（取值范围 1~20）──
        // self-moa 模式  → 温度采样数量（1=只用默认温度, 3=3种温度采样）
        // iterative 模式 → 迭代轮次（1=单轮并行, 3=三轮迭代修正）
        //
        // ⚠️ 推荐使用 1~3：
        //   1 = 最简（每个模型只调 1 次）
        //   2 = 轻度（2种温度 / 1轮迭代）
        //   3 = 推荐（质量和成本的平衡点，论文验证的最佳值）
        //   4~5 = 深度（Token 翻倍，质量提升有限）
        //   6~20 = 边际收益极低，不推荐（温度间隔 < 0.05，输出几乎无差异）
        //
        // 🔴 Token 消耗估算公式：
        //   self-moa:   模型数 × ROUNDS（如 双模型+3轮 = 2×3 = 6次）
        //   iterative:  模型数 × ROUNDS × 2（如 双模型+3轮 = 2×3×2 = 12次）
        ST_MOA_ROUNDS: "3",

        // ── API 单次调用超时（秒）──
        // 调用 LLM API 时的最长等待时间
        // 如果网络慢或模型响应慢，调大此值
        ST_LLM_TIMEOUT: "120",
      },

      // ── 自动重启策略 ──
      autorestart: true,             // 进程崩溃后自动重启
      max_restarts: 10,              // 连续 10 次重启失败则停止（防无限崩溃）
      restart_delay: 5000,           // 两次重启之间等 5 秒（防快速反复崩溃）
      min_uptime: "10s",             // 至少运行 10 秒才算"成功启动"
      max_memory_restart: "1G",      // 物理内存超 1GB 自动重启（防内存泄漏）
      // 当前服务正常时约 80MB，1G 留了 12 倍余量

      // ── 日志路径（相对于 cwd）──
      error_file: "Logs/SequentialThinking-err.log",
      out_file: "Logs/SequentialThinking-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
  ],
};
