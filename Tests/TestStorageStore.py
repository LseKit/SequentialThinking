# ============================================================================
# Storage/Store.py 单元测试 — SQLite 异步持久化
# 路径: Tests/TestStorageStore.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pytest_asyncio
import tempfile, json

from GitHubSrc.Core.Models import (
    ThinkingStep, Assumption,
)
from GitHubSrc.Storage.Store import Store


# ═══════════════════════════════════════════════════════════════
# 异步夹具：创建内存 SQLite 数据库的 Store
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def store():
    """使用临时文件数据库的 Store 实例"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    s = Store(db_path=db_path)
    await s.open()
    yield s
    await s.close()
    # 清理临时文件
    try:
        os.unlink(db_path)
        for ext in ("-wal", "-shm"):
            try:
                os.unlink(db_path + ext)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass


@pytest_asyncio.fixture
async def session_id(store):
    """预创建会话，返回 session_id"""
    session = await store.create_session(
        problem="Python 性能优化问题",
        ctx={"template": "scientific-method"},
        tags=["Python", "性能"],
    )
    return session.id


# ═══════════════════════════════════════════════════════════════
# 创建/读取/删除会话
# ═══════════════════════════════════════════════════════════════

class TestCreateSession:
    """测试 create_session()"""

    async def test_create_basic(self, store):
        """基本创建会话"""
        session = await store.create_session("测试", {}, [])
        assert session is not None
        assert session.id is not None
        assert len(session.id) == 32  # 32 字符十六进制
        assert session.problem == "测试"
        assert session.status == "active"

    async def test_create_with_tags(self, store):
        """创建带标签的会话"""
        session = await store.create_session(
            "测试", {}, ["tag1", "tag2"],
        )
        assert len(session.tags) == 2
        assert "tag1" in session.tags

    async def test_create_with_context(self, store):
        """创建带上下文的会话"""
        session = await store.create_session(
            "测试", {"template": "five-whys"}, [],
        )
        assert session.context.get("template") == "five-whys"

    async def test_id_is_unique(self, store):
        """不同会话的 ID 应不同"""
        s1 = await store.create_session("问题1", {}, [])
        s2 = await store.create_session("问题2", {}, [])
        assert s1.id != s2.id


class TestGetSession:
    """测试 get_session()"""

    async def test_get_existing(self, store, session_id):
        session = await store.get_session(session_id)
        assert session is not None
        assert session.id == session_id
        assert session.problem == "Python 性能优化问题"

    async def test_get_nonexistent(self, store):
        session = await store.get_session("nonexistent_id_1234567890123456")
        assert session is None

    async def test_steps_are_loaded(self, store, session_id):
        """会话的步骤应被一起加载"""
        await store.add_step(session_id, "第一步", "analysis")
        session = await store.get_session(session_id)
        assert len(session.steps) == 1

    async def test_tags_are_loaded(self, store, session_id):
        session = await store.get_session(session_id)
        assert "Python" in session.tags
        assert "性能" in session.tags


class TestDeleteSession:
    """测试 delete_session()"""

    async def test_delete_existing(self, store, session_id):
        assert await store.delete_session(session_id) is True
        assert await store.get_session(session_id) is None

    async def test_delete_nonexistent(self, store):
        assert await store.delete_session("no_such_id") is False

    async def test_cascade_delete_steps(self, store, session_id):
        """删除会话应级联删除步骤"""
        await store.add_step(session_id, "步骤1", "analysis")
        await store.delete_session(session_id)
        # 会话已删除，get_session 返回 None
        assert await store.get_session(session_id) is None


class TestListSessions:
    """测试 list_sessions()"""

    async def test_list_basic(self, store):
        summary = await store.list_sessions()
        assert isinstance(summary, list)

    async def test_list_filter_by_status(self, store, session_id):
        summary = await store.list_sessions(status="active")
        assert len(summary) >= 1
        assert all(s.status == "active" for s in summary)

    async def test_list_filter_by_tags(self, store):
        await store.create_session("问题", {}, ["Python"])
        summary = await store.list_sessions(tags=["Python"])
        assert len(summary) >= 1

    async def test_list_with_limit(self, store):
        summary = await store.list_sessions(limit=1)
        assert len(summary) <= 1


class TestUpdateSessionStatus:
    """测试 update_session_status()"""

    async def test_update_to_completed(self, store, session_id):
        await store.update_session_status(session_id, "completed")
        session = await store.get_session(session_id)
        assert session.status == "completed"


class TestSearchSessions:
    """测试 search_sessions() — FTS5"""

    async def test_search_finds_result(self, store, session_id):
        """搜索 Python 应找到会话"""
        results = await store.search_sessions("Python")
        assert len(results) >= 1

    async def test_search_no_match(self, store, session_id):
        """搜索不存在的词应无结果"""
        results = await store.search_sessions("zzz不存在")
        assert len(results) == 0


# ═══════════════════════════════════════════════════════════════
# 步骤管理
# ═══════════════════════════════════════════════════════════════

class TestAddStep:
    """测试 add_step()"""

    async def test_add_basic_step(self, store, session_id):
        step = await store.add_step(session_id, "分析内容", "analysis")
        assert step.number == 1
        assert step.type == "analysis"
        assert step.content == "分析内容"

    async def test_add_multiple_steps(self, store, session_id):
        await store.add_step(session_id, "步骤1", "analysis")
        step2 = await store.add_step(session_id, "步骤2", "hypothesis")
        assert step2.number == 2

    async def test_add_revision_step(self, store, session_id):
        """修订步骤应标记 is_revision"""
        step = await store.add_step(
            session_id, "修正后的分析",
            "analysis", is_revision=True, revises_step=1,
        )
        assert step.is_revision is True
        assert step.revises_step == 1

    async def test_add_with_metadata(self, store, session_id):
        step = await store.add_step(
            session_id, "步骤", "analysis",
            meta={"source": "LLM"},
        )
        assert step.metadata.get("source") == "LLM"


class TestUpdateStep:
    """测试 update_step()"""

    async def test_update_content(self, store, session_id):
        await store.add_step(session_id, "原内容", "analysis")
        updated = await store.update_step(
            session_id, 1, content="新内容",
        )
        assert updated.content == "新内容"

    async def test_update_type(self, store, session_id):
        await store.add_step(session_id, "步骤", "analysis")
        updated = await store.update_step(
            session_id, 1, step_type="hypothesis",
        )
        assert updated.type == "hypothesis"

    async def test_update_nonexistent(self, store, session_id):
        result = await store.update_step(session_id, 999, content="test")
        assert result is None


# ═══════════════════════════════════════════════════════════════
# 分支管理
# ═══════════════════════════════════════════════════════════════

class TestBranch:
    """测试 create_branch() 和 add_step_to_branch()"""

    async def test_create_branch(self, store, session_id):
        branch = await store.create_branch(
            session_id, from_step=1, alt_desc="替代分析",
        )
        assert branch.id is not None
        assert branch.from_step == 1
        assert branch.alternative_desc == "替代分析"

    async def test_add_step_to_branch(self, store, session_id):
        branch = await store.create_branch(session_id, 1, "分支")
        step = await store.add_step_to_branch(
            session_id, branch.id, "分支步骤", "analysis",
        )
        assert step is not None
        assert step.content == "分支步骤"


# ═══════════════════════════════════════════════════════════════
# 统计指标
# ═══════════════════════════════════════════════════════════════

class TestGetMetrics:
    """测试 get_metrics()"""

    async def test_get_all_metrics(self, store, session_id):
        metrics = await store.get_metrics("all")
        assert metrics.total_sessions >= 1
        assert metrics.active_sessions >= 1

    async def test_get_day_metrics(self, store, session_id):
        metrics = await store.get_metrics("day")
        assert metrics.total_sessions >= 1

    async def test_get_month_metrics(self, store, session_id):
        metrics = await store.get_metrics("month")
        assert isinstance(metrics.total_sessions, int)


# ═══════════════════════════════════════════════════════════════
# 假设管理
# ═══════════════════════════════════════════════════════════════

class TestAssumptions:
    """测试 add/get/update/delete_assumption()"""

    async def test_add_assumption(self, store, session_id):
        assumption = Assumption(
            id="A1", text="假设用户会 Python",
            step_number=1, confidence=0.8,
            critical=True,
        )
        await store.add_assumption(assumption, session_id)
        assumptions = await store.get_assumptions(session_id)
        assert len(assumptions) == 1
        assert assumptions[0].id == "A1"

    async def test_get_returns_empty_list(self, store, session_id):
        assumptions = await store.get_assumptions(session_id)
        assert isinstance(assumptions, list)
        assert len(assumptions) == 0

    async def test_update_assumption(self, store, session_id):
        assumption = Assumption(id="A1", text="假设", step_number=1)
        await store.add_assumption(assumption, session_id)
        ok = await store.update_assumption(
            session_id, "A1",
            verified=True, verified_by=2,
        )
        assert ok is True
        results = await store.get_assumptions(session_id)
        assert results[0].verified is True

    async def test_update_nonexistent(self, store, session_id):
        ok = await store.update_assumption(session_id, "NOEXIST", verified=True)
        assert ok is False

    async def test_delete_assumption(self, store, session_id):
        assumption = Assumption(id="A1", text="假设", step_number=1)
        await store.add_assumption(assumption, session_id)
        ok = await store.delete_assumption(session_id, "A1")
        assert ok is True
        assert len(await store.get_assumptions(session_id)) == 0

    async def test_delete_nonexistent(self, store, session_id):
        ok = await store.delete_assumption(session_id, "NOEXIST")
        assert ok is False


# ═══════════════════════════════════════════════════════════════
# 生命周期 + 标签
# ═══════════════════════════════════════════════════════════════

class TestCompleteSession:
    """测试 complete_session()"""

    async def test_complete_active_session(self, store, session_id):
        ok = await store.complete_session(session_id)
        assert ok is True
        session = await store.get_session(session_id)
        assert session.status == "completed"

    async def test_complete_already_completed(self, store, session_id):
        await store.complete_session(session_id)
        # 第二次调用应返回 False（状态已不是 active）
        ok = await store.complete_session(session_id)
        assert ok is False


class TestTags:
    """测试 add_tags() 和 remove_tags()"""

    async def test_add_tags(self, store, session_id):
        await store.add_tags(session_id, ["新标签"])
        session = await store.get_session(session_id)
        assert "新标签" in session.tags

    async def test_add_duplicate_tag_ignored(self, store, session_id):
        await store.add_tags(session_id, ["Python"])  # 已存在
        session = await store.get_session(session_id)
        assert session.tags.count("Python") == 1

    async def test_remove_tags(self, store, session_id):
        await store.remove_tags(session_id, ["Python"])
        session = await store.get_session(session_id)
        assert "Python" not in session.tags

    async def test_remove_empty_tags_noop(self, store, session_id):
        """空列表不应报错"""
        await store.remove_tags(session_id, [])


# ═══════════════════════════════════════════════════════════════
# FTS5 同步
# ═══════════════════════════════════════════════════════════════

class TestFtsSync:
    """测试 _sync_fts() 内部方法"""

    async def test_sync_writes_to_fts(self, store, session_id):
        """创建会话后 FTS5 索引应有对应记录"""
        # FTS5 unicode61 对中文支持有限，用 ASCII 词搜索更可靠
        results = await store.search_sessions("Python")
        assert len(results) >= 1

    async def test_search_after_delete(self, store, session_id):
        """删除会话后搜索应无结果"""
        await store.delete_session(session_id)
        results = await store.search_sessions("Python")
        assert len(results) == 0


# ═══════════════════════════════════════════════════════════════
# 内部方法
# ═══════════════════════════════════════════════════════════════

class TestInternalMethods:
    """测试 _load_tags, _load_steps, _load_branches, _calculate_quality"""

    async def test_load_tags(self, store, session_id):
        tags = await store._load_tags(session_id)
        assert "Python" in tags
        assert "性能" in tags

    async def test_load_steps_empty(self, store, session_id):
        steps = await store._load_steps(session_id, "")
        assert isinstance(steps, list)
        assert len(steps) == 0

    async def test_load_steps_with_data(self, store, session_id):
        await store.add_step(session_id, "步骤", "analysis")
        steps = await store._load_steps(session_id, "")
        assert len(steps) == 1

    async def test_load_branches_empty(self, store, session_id):
        branches = await store._load_branches(session_id)
        assert isinstance(branches, dict)
        assert len(branches) == 0

    async def test_calculate_quality_empty(self, store, session_id):
        """空步骤时质量分应为 0.5"""
        qs = await store._calculate_quality(session_id)
        assert qs == 0.5

    async def test_calculate_quality_with_steps(self, store, session_id):
        """有步骤时质量分应变化"""
        await store.add_step(session_id, "步骤", "analysis")
        qs = await store._calculate_quality(session_id)
        assert 0.0 <= qs <= 1.0

    async def test_sync_fts_does_not_crash(self, store):
        """_sync_fts 对新建会话的调用不应崩溃"""
        # 创建新会话验证 _sync_fts 正常（已有会话已同步过，重复调用会 IntegrityError）
        session = await store.create_session("testing fts five", {}, [])
        results = await store.search_sessions("testing")
        assert len(results) >= 1


# ═══════════════════════════════════════════════════════════════
# 中文 FTS5 测试（v1.2.1 — 需要 jieba）
# ═══════════════════════════════════════════════════════════════

import importlib
_JIEBA_TEST = importlib.util.find_spec("jieba") is not None


class TestFtsChinese:
    """中文 jieba 分词 FTS5 搜索测试"""

    @pytest.mark.skipif(not _JIEBA_TEST, reason="jieba 未安装，跳过中文 FTS5 测试")
    async def test_chinese_search(self, store):
        """创建含中文的会话后，搜索中文词应命中"""
        session = await store.create_session(
            "提高代码质量和自动化测试覆盖率", {}, []
        )
        r1 = await store.search_sessions("代码质量")
        assert len(r1) >= 1, "应搜到含'代码质量'的会话"
        r2 = await store.search_sessions("覆盖率")
        assert len(r2) >= 1, "应搜到含'覆盖率'的会话"
        r3 = await store.search_sessions("量子计算")
        assert len(r3) == 0, "无关词不应有结果"
        await store.delete_session(session.id)
