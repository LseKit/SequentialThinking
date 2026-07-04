# ============================================================================
# Core/Templates.py 单元测试 — 9 种思维模板
# 路径: Tests/TestCoreTemplates.py
# 原作者: 小逸 (Da Bai 生成)
# 仓库: https://github.com/LseKit/SequentialThinking
# ============================================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from GitHubSrc.Core.Templates import TEMPLATES, get_template, get_all_templates


class TestTemplates:
    """测试 TEMPLATES 常量字典"""

    def test_has_nine_templates(self):
        assert len(TEMPLATES) == 9

    def test_all_have_required_keys(self):
        required = {"type", "name", "description", "steps"}
        for tid, tmpl in TEMPLATES.items():
            missing = required - set(tmpl.keys())
            assert not missing, f"模板 {tid} 缺少字段: {missing}"

    def test_type_matches_key(self):
        for tid, tmpl in TEMPLATES.items():
            assert tmpl["type"] == tid

    def test_name_not_empty(self):
        for tid, tmpl in TEMPLATES.items():
            assert len(tmpl["name"]) > 0

    def test_description_not_empty(self):
        for tid, tmpl in TEMPLATES.items():
            assert len(tmpl["description"]) > 0

    def test_steps_is_non_empty_list(self):
        for tid, tmpl in TEMPLATES.items():
            assert isinstance(tmpl["steps"], list)
            assert len(tmpl["steps"]) > 0

    def test_steps_are_strings(self):
        for tid, tmpl in TEMPLATES.items():
            for i, step in enumerate(tmpl["steps"]):
                assert isinstance(step, str), f"模板 {tid} 步骤 {i} 不是字符串"


class TestGetTemplate:
    """测试 get_template()"""

    def test_existing_template(self):
        tmpl = get_template("scientific-method")
        assert tmpl is not None
        assert tmpl["type"] == "scientific-method"

    def test_all_templates_accessible(self):
        for tid in TEMPLATES:
            assert get_template(tid) is not None

    def test_nonexistent_returns_none(self):
        assert get_template("nonexistent") is None

    def test_empty_string_returns_none(self):
        assert get_template("") is None


class TestGetAllTemplates:
    """测试 get_all_templates()"""

    def test_returns_full_dict(self):
        all_t = get_all_templates()
        assert all_t is TEMPLATES
        assert len(all_t) == 9

    def test_is_dict(self):
        assert isinstance(get_all_templates(), dict)
