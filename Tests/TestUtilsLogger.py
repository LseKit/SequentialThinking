# ============================================================================
# Utils/Logger.py 单元测试 — 日志工具
# 路径: Tests/TestUtilsLogger.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import logging
from GitHubSrc.Utils.Logger import setup_logger


class TestSetupLogger:
    """测试 setup_logger()"""

    def test_returns_logger(self):
        log = setup_logger("test_module")
        assert isinstance(log, logging.Logger)

    def test_name_set_correctly(self):
        log = setup_logger("test_module")
        assert "test_module" in log.name

    def test_has_handler(self):
        log = setup_logger("test_module")
        assert len(log.handlers) >= 1

    def test_handler_is_stream_handler(self):
        log = setup_logger("test_module")
        assert any(
            isinstance(h, logging.StreamHandler) for h in log.handlers
        )

    def test_singleton_per_name(self):
        log1 = setup_logger("singleton_test")
        log2 = setup_logger("singleton_test")
        assert log1 is log2

    def test_different_names_are_different_loggers(self):
        log1 = setup_logger("module_a")
        log2 = setup_logger("module_b")
        assert log1 is not log2
