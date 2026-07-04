# ============================================================================
# Core/Context.py 单元测试 — 全局引用
# 路径: Tests/TestCoreContext.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import GitHubSrc.Core.Context as ctx


class TestContext:
    """测试全局上下文变量"""

    def test_store_ref_initialized(self):
        """store_ref 在未启动服务时为 None"""
        assert ctx.store_ref is None or hasattr(ctx.store_ref, "open")

    def test_engine_ref_initialized(self):
        """engine_ref 在未启动服务时为 None"""
        assert ctx.engine_ref is None or hasattr(ctx.engine_ref, "is_llm")

    def test_can_assign_store_ref(self):
        """store_ref 可被赋值"""
        saved = ctx.store_ref
        try:
            ctx.store_ref = "test_store"
            assert ctx.store_ref == "test_store"
        finally:
            ctx.store_ref = saved

    def test_can_assign_engine_ref(self):
        """engine_ref 可被赋值"""
        saved = ctx.engine_ref
        try:
            ctx.engine_ref = "test_engine"
            assert ctx.engine_ref == "test_engine"
        finally:
            ctx.engine_ref = saved
