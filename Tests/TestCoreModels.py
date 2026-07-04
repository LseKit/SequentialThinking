# ============================================================================
# Core/Models.py 单元测试 — 数据模型与常量
# 路径: Tests/TestCoreModels.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from datetime import datetime

from GitHubSrc.Core.Models import (
    STEP_TYPES,
    MAX_QUALITY_STEPS,
    QUALITY_TYPE_WEIGHT,
    QUALITY_CONN_WEIGHT,
    QUALITY_DEPTH_WEIGHT,
    MAX_STEP_CONTENT_LENGTH,
    MAX_PROBLEM_LENGTH,
    ThinkingStep,
    Branch,
    ThinkingSession,
    SessionSummary,
    LogicalIssue,
    ThinkingPattern,
    Assumption,
    QualityReport,
    BiasResult,
    ConfidenceMeta,
    MergeResult,
    SessionCompare,
    ComplexityEstimate,
    SessionMetrics,
)


class TestConstants:
    """测试模块级常量"""

    def test_step_types(self):
        """STEP_TYPES 应包含四种推理步骤类型"""
        assert STEP_TYPES == {"analysis", "hypothesis", "verification", "conclusion"}

    def test_max_quality_steps(self):
        """MAX_QUALITY_STEPS 应为正整数"""
        assert MAX_QUALITY_STEPS == 25
        assert MAX_QUALITY_STEPS > 0

    def test_quality_weights_sum_to_one(self):
        """质量权重之和应接近 1.0"""
        total = QUALITY_TYPE_WEIGHT + QUALITY_CONN_WEIGHT + QUALITY_DEPTH_WEIGHT
        assert abs(total - 1.0) < 0.01

    def test_max_content_lengths(self):
        """输入校验常量应为合理值"""
        assert MAX_STEP_CONTENT_LENGTH == 20000
        assert MAX_PROBLEM_LENGTH == 5000


class TestThinkingStep:
    """测试 ThinkingStep 数据类"""

    def test_create_minimal(self):
        step = ThinkingStep(number=1, type="analysis", content="测试步骤")
        assert step.number == 1
        assert step.type == "analysis"

    def test_defaults(self):
        step = ThinkingStep(number=1, type="analysis", content="test")
        assert isinstance(step.timestamp, datetime)
        assert step.parent_step is None
        assert step.metadata == {}
        assert step.connections == []
        assert step.is_revision is False
        assert step.revises_step is None

    def test_full_fields(self):
        """所有字段均可正常赋值"""
        now = datetime(2025, 1, 1)
        step = ThinkingStep(
            number=3, type="hypothesis", content="假设内容",
            timestamp=now, parent_step=2,
            metadata={"source": "LLM"}, connections=[1, 2],
            is_revision=True, revises_step=2,
        )
        assert step.is_revision is True
        assert step.revises_step == 2

    def test_number_is_int(self):
        step = ThinkingStep(number=5, type="analysis", content="test")
        assert isinstance(step.number, int)


class TestBranch:
    """测试 Branch 数据类"""

    def test_create_branch(self):
        now = datetime(2025, 1, 1)
        branch = Branch(
            id="abc123", from_step=2, created=now,
            alternative_desc="替代路径",
        )
        assert branch.id == "abc123"
        assert branch.steps == []

    def test_with_steps(self):
        step = ThinkingStep(number=1, type="analysis", content="分支步骤")
        branch = Branch(id="xyz", from_step=1, steps=[step])
        assert len(branch.steps) == 1


class TestThinkingSession:
    """测试 ThinkingSession 数据类"""

    def test_defaults(self):
        session = ThinkingSession(id="s1", problem="test")
        assert session.context == {}
        assert session.steps == []
        assert session.branches == {}
        assert session.current_step == 0
        assert session.quality_score == 0.5
        assert session.status == "active"
        assert session.tags == []
        assert session.initial_analysis == ""

    def test_steps_ordered(self):
        s1 = ThinkingStep(number=1, type="analysis", content="步骤一")
        s2 = ThinkingStep(number=2, type="hypothesis", content="步骤二")
        session = ThinkingSession(id="s1", problem="test", steps=[s1, s2])
        assert len(session.steps) == 2
        assert session.steps[0].number == 1


class TestSessionSummary:
    """测试 SessionSummary 数据类"""

    def test_create_summary(self):
        summary = SessionSummary(
            id="s1", problem="问题", step_count=5,
            branch_count=2, status="active", quality_score=0.8,
        )
        assert summary.step_count == 5
        assert summary.branch_count == 2

    def test_defaults(self):
        summary = SessionSummary(id="s1", problem="test")
        assert summary.step_count == 0
        assert summary.quality_score == 0.5


class TestLogicalIssue:
    """测试 LogicalIssue 数据类"""

    def test_create_issue(self):
        issue = LogicalIssue(
            step_number=3, issue_type="无支撑结论",
            description="结论缺乏支撑", severity="中",
            suggestion="关联验证步骤",
        )
        assert issue.step_number == 3
        assert issue.severity == "中"


class TestThinkingPattern:
    """测试 ThinkingPattern 数据类"""

    def test_create_pattern(self):
        pattern = ThinkingPattern(
            name="收敛式推理", frequency=5, confidence=0.9,
        )
        assert pattern.frequency == 5
        assert pattern.confidence == 0.9


class TestAssumption:
    """测试 Assumption 数据类"""

    def test_create_assumption(self):
        assumption = Assumption(
            id="A1", text="假设内容", step_number=2,
            confidence=0.7, critical=True, verified=True,
            verified_by=[3, 4],
        )
        assert assumption.critical is True
        assert assumption.verified_by == [3, 4]

    def test_defaults(self):
        assumption = Assumption(id="A1", text="test", step_number=1)
        assert assumption.confidence == 0.5
        assert assumption.critical is False
        assert assumption.verified is False
        assert assumption.invalidated is False


class TestQualityReport:
    """测试 QualityReport 数据类"""

    def test_create_report(self):
        report = QualityReport(
            overall=0.85, coherence=0.9,
            strengths=["逻辑清晰"], weaknesses=["缺少数据"],
        )
        assert report.overall == 0.85
        assert len(report.strengths) == 1

    def test_defaults(self):
        report = QualityReport()
        assert report.overall == 0.0
        assert report.strengths == []


class TestBiasResult:
    """测试 BiasResult 数据类"""

    def test_create_bias(self):
        bias = BiasResult(name="确认偏见", severity="高")
        assert bias.name == "确认偏见"


class TestConfidenceMeta:
    """测试 ConfidenceMeta 数据类"""

    def test_create_confidence(self):
        meta = ConfidenceMeta(score=0.8, risks=["未考虑边界"])
        assert meta.score == 0.8
        assert len(meta.risks) == 1


class TestMergeResult:
    """测试 MergeResult 数据类"""

    def test_create_merge(self):
        merge = MergeResult(
            synthesis="综合结论", confidence=0.75,
        )
        assert merge.confidence == 0.75


class TestSessionCompare:
    """测试 SessionCompare 数据类"""

    def test_create_compare(self):
        compare = SessionCompare(similarity=0.6)
        assert compare.similarity == 0.6


class TestComplexityEstimate:
    """测试 ComplexityEstimate 数据类"""

    def test_create_estimate(self):
        estimate = ComplexityEstimate(
            level="hard", estimated_steps=20,
            suggested_template="problem_decomposition",
        )
        assert estimate.level == "hard"

    def test_defaults(self):
        estimate = ComplexityEstimate()
        assert estimate.level == "medium"
        assert estimate.estimated_steps == 10


class TestSessionMetrics:
    """测试 SessionMetrics 数据类"""

    def test_create_metrics(self):
        metrics = SessionMetrics(
            total_sessions=10, active_sessions=5,
            completed_sessions=5, average_steps=8.5,
        )
        assert metrics.total_sessions == 10

    def test_defaults_are_zero(self):
        metrics = SessionMetrics()
        assert metrics.total_sessions == 0
        assert metrics.step_type_distribution == {}
        assert metrics.sessions_by_day == {}
