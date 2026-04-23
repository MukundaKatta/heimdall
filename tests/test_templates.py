"""Tests for heimdall.templates — PromptTemplate, TemplateEngine, built-ins."""

import pytest
from heimdall.templates import (
    PromptTemplate,
    TemplateEngine,
    create_default_engine,
)


class TestPromptTemplate:
    def test_extract_variables(self):
        tpl = PromptTemplate(name="t", template="Hello {name}, you are {role}.")
        assert tpl.extract_variables() == ["name", "role"]

    def test_render_basic(self):
        tpl = PromptTemplate(name="t", template="Hi {name}!")
        assert tpl.render({"name": "Alice"}) == "Hi Alice!"

    def test_render_missing_required_raises(self):
        tpl = PromptTemplate(name="t", template="{a} and {b}")
        with pytest.raises(ValueError, match="Missing required"):
            tpl.render({"a": "x"})

    def test_render_with_defaults(self):
        tpl = PromptTemplate(
            name="t",
            template="{greeting} {name}!",
            default_vars={"greeting": "Hello"},
        )
        assert tpl.render({"name": "Bob"}) == "Hello Bob!"

    def test_validate_reports_missing(self):
        tpl = PromptTemplate(name="t", template="{x} {y}", required_vars=["x", "y"])
        problems = tpl.validate({"x": "1"})
        assert any("y" in p for p in problems)

    def test_validate_reports_extra(self):
        tpl = PromptTemplate(name="t", template="{x}")
        problems = tpl.validate({"x": "1", "z": "extra"})
        assert any("z" in p for p in problems)


class TestTemplateEngine:
    def test_register_and_list(self):
        engine = TemplateEngine()
        engine.register(PromptTemplate(name="a", template="hi"))
        engine.register(PromptTemplate(name="b", template="bye"))
        assert engine.list_templates() == ["a", "b"]

    def test_render_by_name(self):
        engine = TemplateEngine()
        engine.register(PromptTemplate(name="greet", template="Hello {who}!"))
        assert engine.render("greet", {"who": "world"}) == "Hello world!"

    def test_render_missing_template_raises(self):
        engine = TemplateEngine()
        with pytest.raises(KeyError):
            engine.render("nope")

    def test_render_chain(self):
        engine = TemplateEngine()
        engine.register(PromptTemplate(name="a", template="Part A"))
        engine.register(PromptTemplate(name="b", template="Part B"))
        result = engine.render_chain(["a", "b"], separator=" | ")
        assert result == "Part A | Part B"


class TestBuiltinTemplates:
    def test_builtins_registered(self):
        engine = create_default_engine()
        names = engine.list_templates()
        assert "system_prompt" in names
        assert "few_shot" in names
        assert "chain_of_thought" in names
        assert "role_play" in names

    def test_system_prompt_renders(self):
        engine = create_default_engine()
        result = engine.render("system_prompt", {
            "role": "a coding assistant",
            "context": "Python projects",
            "instructions": "Write clean code.",
            "constraints": "No external deps",
        })
        assert "coding assistant" in result
        assert "Constraints" in result

    def test_chain_of_thought_uses_default_role(self):
        engine = create_default_engine()
        result = engine.render("chain_of_thought", {"question": "Why is the sky blue?"})
        assert "analytical" in result
        assert "sky blue" in result
