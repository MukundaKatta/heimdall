"""Tests for heimdall.core — SystemPrompt, PromptLibrary, PromptAnalyzer."""

import pytest
from heimdall.core import SystemPrompt, PromptLibrary, PromptAnalyzer, estimate_token_count


# ---------------------------------------------------------------------------
# SystemPrompt
# ---------------------------------------------------------------------------

class TestSystemPrompt:
    def test_auto_token_count(self):
        sp = SystemPrompt(name="test", content="Hello world this is a test")
        assert sp.token_count > 0

    def test_explicit_token_count_preserved(self):
        sp = SystemPrompt(name="t", content="hi", token_count=42)
        assert sp.token_count == 42

    def test_defaults(self):
        sp = SystemPrompt(name="t", content="c")
        assert sp.category == "general"
        assert sp.model_target == "any"
        assert sp.effectiveness_score == 0.0
        assert sp.tags == []


# ---------------------------------------------------------------------------
# estimate_token_count
# ---------------------------------------------------------------------------

class TestTokenEstimate:
    def test_empty_string(self):
        assert estimate_token_count("") == 0

    def test_punctuation_adds_tokens(self):
        plain = estimate_token_count("hello world")
        punct = estimate_token_count("hello, world! yes? no.")
        assert punct > plain


# ---------------------------------------------------------------------------
# PromptLibrary
# ---------------------------------------------------------------------------

def _make_prompt(name="p1", content="You are a helpful assistant.", category="general", tags=None):
    return SystemPrompt(name=name, content=content, category=category, tags=tags or [])


class TestPromptLibrary:
    def test_add_and_get(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("alpha"))
        assert lib.get("alpha") is not None
        assert lib.size == 1

    def test_add_empty_name_raises(self):
        lib = PromptLibrary()
        with pytest.raises(ValueError, match="non-empty name"):
            lib.add(SystemPrompt(name="", content="c"))

    def test_add_empty_content_raises(self):
        lib = PromptLibrary()
        with pytest.raises(ValueError, match="non-empty content"):
            lib.add(SystemPrompt(name="x", content=""))

    def test_remove(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("rm"))
        assert lib.remove("rm") is True
        assert lib.remove("rm") is False

    def test_search_by_name(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("coder", content="Write code.", category="coding"))
        lib.add(_make_prompt("writer", content="Write essays.", category="writing"))
        results = lib.search("coder")
        assert len(results) == 1
        assert results[0].name == "coder"

    def test_search_by_content(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a", content="You are a Python expert."))
        lib.add(_make_prompt("b", content="You are a chef."))
        results = lib.search("Python")
        assert len(results) == 1

    def test_by_category(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a", category="coding"))
        lib.add(_make_prompt("b", category="writing"))
        assert len(lib.by_category("coding")) == 1

    def test_by_tag(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a", tags=["python", "coding"]))
        lib.add(_make_prompt("b", tags=["writing"]))
        assert len(lib.by_tag("python")) == 1

    def test_compare(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a", tags=["shared"], content="Short."))
        lib.add(_make_prompt("b", tags=["shared", "extra"], content="A much longer prompt with more words."))
        cmp = lib.compare("a", "b")
        assert cmp["category_match"] is True
        assert "shared" in cmp["shared_tags"]
        assert isinstance(cmp["token_diff"], int)

    def test_compare_missing_raises(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a"))
        with pytest.raises(KeyError):
            lib.compare("a", "nonexistent")

    def test_stats_empty(self):
        lib = PromptLibrary()
        s = lib.stats()
        assert s["count"] == 0

    def test_stats_populated(self):
        lib = PromptLibrary()
        lib.add(_make_prompt("a"))
        lib.add(_make_prompt("b"))
        s = lib.stats()
        assert s["count"] == 2
        assert s["avg_tokens"] > 0


# ---------------------------------------------------------------------------
# PromptAnalyzer
# ---------------------------------------------------------------------------

class TestPromptAnalyzer:
    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_instruction_density_high(self):
        text = "You must respond. You should always provide detail. Never skip steps."
        density = self.analyzer.instruction_density(text)
        assert density >= 0.8

    def test_instruction_density_low(self):
        text = "The sky is blue. Grass is green."
        density = self.analyzer.instruction_density(text)
        assert density < 0.5

    def test_specificity_short_prompt(self):
        score = self.analyzer.specificity_score("Be helpful.")
        assert score < 50

    def test_specificity_detailed_prompt(self):
        text = (
            "You are an expert Python developer.\n"
            "Role: senior engineer with 10 years experience.\n"
            "Constraints: use only stdlib.\n"
            "Examples: \"def foo(): pass\"\n"
            "Output format: provide code in markdown blocks.\n"
            "- Always include type hints.\n"
            "- Never use global variables.\n"
        )
        score = self.analyzer.specificity_score(text)
        assert score > 60

    def test_structure_analysis(self):
        text = "Role: assistant.\nConstraints: be concise.\nExamples: see below."
        result = self.analyzer.structure_analysis(text)
        assert "role" in result["sections_found"]
        assert "constraints" in result["sections_found"]

    def test_analyze_returns_all_keys(self):
        sp = SystemPrompt(name="t", content="You must always respond helpfully.")
        report = self.analyzer.analyze(sp)
        assert "token_count" in report
        assert "instruction_density" in report
        assert "specificity_score" in report
        assert "structure" in report
        assert "quality_rating" in report

    def test_quality_rating_values(self):
        sp = SystemPrompt(name="t", content="Hi.")
        rating = self.analyzer.quality_rating(sp)
        assert rating in ("excellent", "good", "fair", "poor")
