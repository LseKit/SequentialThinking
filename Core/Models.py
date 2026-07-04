"""
Sequential Thinking MCP — 数据模型定义
路径: Core/Models.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# ── 步骤类型常量 ──
# 定义四种推理步骤类型
STEP_TYPES = {"analysis", "hypothesis", "verification", "conclusion"}

# ── 质量评估常量 ──
# 启发式引擎计算质量分时的权重和阈值
MAX_QUALITY_STEPS = 25        # 步骤数达到此值时深度维度满分（对齐典型推理深度）
QUALITY_TYPE_WEIGHT = 0.3     # 类型多样性权重 30%
QUALITY_CONN_WEIGHT = 0.3     # 连接密度权重 30%
QUALITY_DEPTH_WEIGHT = 0.4    # 步数深度权重 40%

# ── 输入校验常量 ──
MAX_STEP_CONTENT_LENGTH = 20000  # 单步推理内容最大字符数
MAX_PROBLEM_LENGTH = 5000        # 问题描述最大字符数


@dataclass
class ThinkingStep:
    """
    单步推理记录
    
    Attributes:
        number: 步骤序号（从1开始）
        type: 步骤类型，必须是 STEP_TYPES 之一
        content: 推理内容文本
        timestamp: 创建时间（UTC）
        parent_step: 父步骤序号（分支时使用）
        metadata: 附加元数据字典
        connections: 关联的步骤序号列表
    """
    number: int
    type: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    parent_step: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    connections: list[int] = field(default_factory=list)
    is_revision: bool = False
    revises_step: Optional[int] = None


@dataclass
class Branch:
    """
    替代推理分支
    
    从主推理链的某个步骤分叉出的独立推理路径
    
    Attributes:
        id: 分支唯一标识（32字符十六进制）
        from_step: 从主链的第几步分叉
        steps: 分支内的推理步骤列表
        created: 创建时间（UTC）
        alternative_desc: 分支描述（为什么走这条路）
    """
    id: str
    from_step: int
    steps: list[ThinkingStep] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    alternative_desc: str = ""


@dataclass
class ThinkingSession:
    """
    完整的思维会话
    
    包含一个问题从提出到得出结论的完整推理过程
    
    Attributes:
        id: 会话唯一标识（32字符十六进制）
        problem: 待解决的问题描述
        context: 会话上下文（如使用的模板类型）
        steps: 主推理链的步骤列表
        branches: 替代推理分支字典（branch_id -> Branch）
        created: 创建时间（UTC）
        last_modified: 最后修改时间（UTC）
        current_step: 当前步骤序号
        quality_score: 推理质量评分（0.0~1.0）
        status: 会话状态（active/completed/archived）
        tags: 用户自定义标签列表
        initial_analysis: LLM 生成的初始分析
    """
    id: str
    problem: str
    context: dict = field(default_factory=dict)
    steps: list[ThinkingStep] = field(default_factory=list)
    branches: dict[str, Branch] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    current_step: int = 0
    quality_score: float = 0.5
    status: str = "active"
    tags: list[str] = field(default_factory=list)
    initial_analysis: str = ""


@dataclass
class SessionSummary:
    """
    会话摘要（列表视图用）
    
    用于 list_sessions 返回的轻量摘要，不含完整步骤
    
    Attributes:
        id: 会话唯一标识
        problem: 问题描述
        step_count: 主链步骤数
        branch_count: 分支数
        status: 会话状态
        quality_score: 质量评分
        created: 创建时间
        last_modified: 最后修改时间
        tags: 标签列表
    """
    id: str
    problem: str
    step_count: int = 0
    branch_count: int = 0
    status: str = "active"
    quality_score: float = 0.5
    created: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)


@dataclass
class LogicalIssue:
    """
    逻辑问题
    
    validate_logic 工具检测到的推理链中的逻辑缺陷
    
    Attributes:
        step_number: 出问题的步骤序号（0 表示全局问题）
        issue_type: 问题类型名称
        description: 问题详细描述
        severity: 严重程度（低/中/高）
        suggestion: 修复建议
    """
    step_number: int
    issue_type: str
    description: str
    severity: str
    suggestion: str


@dataclass
class ThinkingPattern:
    """
    推理模式
    
    LLM 从多个会话中识别出的思维模式
    
    Attributes:
        name: 模式名称
        frequency: 出现频率
        confidence: 识别置信度（0.0~1.0）
        description: 模式描述
    """
    name: str
    frequency: int = 0
    confidence: float = 0.0
    description: str = ""


@dataclass
class Assumption:
    """
    推理过程中的假设
    
    从步骤内容中提取的隐含假设，用于追踪和验证
    
    Attributes:
        id: 假设唯一标识（格式：A1, A2, A3...）
        text: 假设内容
        step_number: 提出该假设的步骤序号
        confidence: 置信度（0.0~1.0，LLM 评估）
        critical: 是否为关键假设（影响结论的假设）
        verified: 是否已被验证
        invalidated: 是否已被推翻
        verified_by: 验证该假设的步骤序号列表
        invalidated_by: 推翻该假设的步骤序号列表
    """
    id: str
    text: str
    step_number: int
    confidence: float = 0.5
    critical: bool = False
    verified: bool = False
    invalidated: bool = False
    verified_by: list[int] = field(default_factory=list)
    invalidated_by: list[int] = field(default_factory=list)


@dataclass
class QualityReport:
    """
    五维质量评估报告
    
    evaluate_quality 工具返回的完整评估结果
    
    Attributes:
        overall: 综合评分（0.0~1.0）
        coherence: 一致性评分
        completeness: 完整性评分
        rigor: 严谨性评分
        novelty: 创新性评分
        actionable: 可操作性评分
        strengths: 优点列表
        weaknesses: 不足列表
    """
    overall: float = 0.0
    coherence: float = 0.0
    completeness: float = 0.0
    rigor: float = 0.0
    novelty: float = 0.0
    actionable: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


@dataclass
class BiasResult:
    """
    认知偏见检测结果
    
    detect_biases 工具检测到的单个偏见
    
    Attributes:
        name: 偏见名称（如"确认偏见"）
        description: 偏见描述
        severity: 严重程度（低/中/高）
        evidence: 在哪个步骤中发现的证据
        suggestion: 如何避免此偏见的建议
    """
    name: str
    description: str = ""
    severity: str = "中"
    evidence: str = ""
    suggestion: str = ""


@dataclass
class ConfidenceMeta:
    """
    步骤置信度元数据
    
    对单个推理步骤的可靠性评估
    
    Attributes:
        score: 置信度评分（0.0~1.0）
        rationale: 评分理由
        risks: 潜在风险列表
    """
    score: float = 0.0
    rationale: str = ""
    risks: list[str] = field(default_factory=list)


@dataclass
class MergeResult:
    """
    分支合并结果
    
    merge_insights 工具合并多个分支后的综合分析
    
    Attributes:
        synthesis: 综合结论
        conflicts: 分支间的冲突点
        confidence: 合并后置信度
        strengths: 合并后优势
    """
    synthesis: str = ""
    conflicts: list[str] = field(default_factory=list)
    confidence: float = 0.0
    strengths: list[str] = field(default_factory=list)


@dataclass
class SessionCompare:
    """
    会话对比结果
    
    compare_sessions 工具对比两个会话后的分析
    
    Attributes:
        shared_assumptions: 两会话共同的假设
        divergent_conclusions: 不同的结论
        similarity: 相似度（0.0~1.0）
        recommendation: 综合建议
    """
    shared_assumptions: list[str] = field(default_factory=list)
    divergent_conclusions: list[str] = field(default_factory=list)
    similarity: float = 0.0
    recommendation: str = ""


@dataclass
class ComplexityEstimate:
    """
    问题复杂度评估
    
    estimate_complexity 方法对问题难度的预估
    
    Attributes:
        level: 难度等级（easy/medium/hard）
        estimated_steps: 预估需要的推理步骤数
        suggested_template: 推荐的思维模板
    """
    level: str = "medium"
    estimated_steps: int = 10
    suggested_template: str = ""


@dataclass
class SessionMetrics:
    """
    会话统计指标
    
    get_metrics 工具返回的聚合统计
    
    Attributes:
        total_sessions: 总会话数
        active_sessions: 活跃会话数
        completed_sessions: 已完成会话数
        average_steps: 平均步骤数
        average_quality: 平均质量分
        average_branches: 平均分支数
        step_type_distribution: 步骤类型分布
        sessions_by_day: 每日创建数
        common_issues: 常见问题
        top_tags: 热门标签
    """
    total_sessions: int = 0
    active_sessions: int = 0
    completed_sessions: int = 0
    average_steps: float = 0.0
    average_quality: float = 0.0
    average_branches: float = 0.0
    step_type_distribution: dict = field(default_factory=dict)
    sessions_by_day: dict = field(default_factory=dict)
    common_issues: dict = field(default_factory=dict)
    top_tags: dict = field(default_factory=dict)
