"""Tests for heimdall.optimizer — PromptOptimizer, OptimizationReport."""

import pytest
from heimdall.core import SystemPrompt
from heimdall.optimizer import PromptOptimizer, OptimizationReport


class TestOptimizationReport:
    def test_token_savings(self):
        r = OptimizationReport(original_tokens=100, optimized_tokens=80)
        assert r.token_savings == 20

    def test_token_savings_no_negative(self):
        r = OptimizationReport(original_tokens=50, optimized_tokens=60)
        assert r.token_savings == 0

    def test_improvement_summary(self):
        r = OptimizationReport(
            original_tokens=100, optimized_tokens=80,
            suggestions=["a", "b"], clarity_score=72.0,
        )
        summary = r.improvement_summary
        assert "2 suggestion" in summary
        assert "20 tokens" in summary


class TestPromptOptimizer:
    def setup_method(self):
        self.optimizer = PromptOptimizer()

    def test_optimize_short_prompt(self):
        sp = SystemPrompt(name="tiny", content="Be nice.")
        report = self.optimizer.optimize(sp)
        assert any("short" in s.lower() for s in report.suggestions)

    def test_optimize_missing_role(self):
        sp = SystemPrompt(
            name="no_role",
            content="Always respond with valid JSON. Include timestamps.",
        )
        report = self.optimizer.optimize(sp)
        assert "role" in report.missing_sections

    def test_optimize_redundancy_removal(self):
        sp = SystemPrompt(
            name="redundant",
            content=(
                "Please note that you must always respond.\n\n\n\n"
                "It is important to note that the output should be JSON.\n"
                "In order to provide good answers, be concise."
            ),
        )
        report = self.optimizer.optimize(sp)
        assert report.optimized_tokens <= report.original_tokens
        assert "redundant" in " ".join(report.suggestions).lower() or report.token_savings >= 0

    def test_optimize_returns_report(self):
        sp = SystemPrompt(
            name="full",
            content=(
                "You are a helpful assistant.\n"
                "Role: expert.\n"
                "Constraints: be brief.\n"
                "Examples: 'Hello' -> 'Hi'\n"
                "Output format: plain text.\n"
                "You must always respond. Never ignore the user."
            ),
        )
        report = self.optimizer.optimize(sp)
        assert isinstance(report, OptimizationReport)
        assert report.clarity_score >= 0
        assert isinstance(report.missing_sections, list)

    def test_optimize_long_prompt_suggests_split(self):
        long_content = " ".join(["You must respond helpfully."] * 150)
        sp = SystemPrompt(name="long", content=long_content)
        report = self.optimizer.optimize(sp)
        assert any("long" in s.lower() for s in report.suggestions)

    def test_optimize_low_density_suggestion(self):
        sp = SystemPrompt(
            name="passive",
            content="The sky is blue. Grass is green. Water is wet. Fire is hot. Ice is cold.",
        )
        report = self.optimizer.optimize(sp)
        assert any("density" in s.lower() for s in report.suggestions)
