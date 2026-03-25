"""Prompt optimization and improvement suggestions.

Analyzes prompts and produces actionable recommendations to improve
clarity, reduce token count, and ensure structural completeness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict

from heimdall.core import SystemPrompt, PromptAnalyzer


@dataclass
class OptimizationReport:
    """Container for optimization results.

    Attributes:
        original_tokens: Token count of the original prompt.
        optimized_tokens: Token count after suggested edits.
        suggestions: Human-readable improvement suggestions.
        missing_sections: Structural sections not found in the prompt.
        clarity_score: 0-100 score for prompt clarity.
        optimized_content: The rewritten prompt text (best-effort).
    """

    original_tokens: int = 0
    optimized_tokens: int = 0
    suggestions: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    clarity_score: float = 0.0
    optimized_content: str = ""

    @property
    def token_savings(self) -> int:
        """How many tokens the optimization would save."""
        return max(0, self.original_tokens - self.optimized_tokens)

    @property
    def improvement_summary(self) -> str:
        """One-line human-readable summary."""
        n = len(self.suggestions)
        savings = self.token_savings
        return (
            f"{n} suggestion(s), potential saving of {savings} tokens, "
            f"clarity {self.clarity_score}/100"
        )


class PromptOptimizer:
    """Suggests improvements to system prompts.

    Uses ``PromptAnalyzer`` internally and applies heuristic rewriting
    rules that never require an LLM call.
    """

    def __init__(self) -> None:
        self._analyzer = PromptAnalyzer()

    def optimize(self, prompt: SystemPrompt) -> OptimizationReport:
        """Run all optimization passes and return a report."""
        suggestions: List[str] = []
        content = prompt.content

        # --- structural completeness --------------------------------------
        structure = self._analyzer.structure_analysis(content)
        missing = structure["sections_missing"]
        if "role" in missing:
            suggestions.append(
                "Add a role definition (e.g. 'You are a helpful assistant')."
            )
        if "constraints" in missing:
            suggestions.append(
                "Add explicit constraints to bound the model's behaviour."
            )
        if "examples" in missing and not structure["has_examples"]:
            suggestions.append(
                "Include at least one example to ground the expected output."
            )
        if "output format" in missing:
            suggestions.append(
                "Specify the desired output format (JSON, markdown, plain text, etc.)."
            )

        # --- redundancy reduction -----------------------------------------
        optimized = self._reduce_redundancy(content)
        if len(optimized) < len(content):
            suggestions.append("Removed redundant whitespace and filler phrases.")

        # --- clarity checks -----------------------------------------------
        clarity = self._clarity_score(optimized)
        if clarity < 50:
            suggestions.append(
                "Prompt clarity is low. Use shorter sentences and active voice."
            )

        # --- instruction density ------------------------------------------
        density = self._analyzer.instruction_density(content)
        if density < 0.3:
            suggestions.append(
                "Instruction density is low. Add more directive statements "
                "(must, should, always, never)."
            )

        # --- length checks ------------------------------------------------
        word_count = len(content.split())
        if word_count < 15:
            suggestions.append(
                "Prompt is very short. Consider adding context and constraints."
            )
        if word_count > 500:
            suggestions.append(
                "Prompt is very long. Consider splitting into sections or "
                "removing low-value content."
            )

        from heimdall.core import estimate_token_count

        return OptimizationReport(
            original_tokens=prompt.token_count,
            optimized_tokens=estimate_token_count(optimized),
            suggestions=suggestions,
            missing_sections=list(missing),
            clarity_score=clarity,
            optimized_content=optimized,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reduce_redundancy(text: str) -> str:
        """Remove filler phrases and normalise whitespace."""
        filler = [
            r"\bplease note that\b",
            r"\bit is important to note that\b",
            r"\bas mentioned (earlier|above|before)\b",
            r"\bin order to\b",
            r"\bbasically\b",
            r"\bsimply\b",
        ]
        result = text
        for pattern in filler:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        # Collapse multiple blank lines / spaces
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"[ \t]{2,}", " ", result)
        return result.strip()

    @staticmethod
    def _clarity_score(text: str) -> float:
        """Heuristic clarity: short sentences, active verbs, low jargon."""
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if not sentences:
            return 0.0

        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)

        # Penalise very long or very short average sentence length
        length_score = max(0, 100 - abs(avg_len - 15) * 3)

        # Bonus for imperative / active voice openers
        active_openers = sum(
            1 for s in sentences
            if re.match(r"^(You|Do|Always|Never|Ensure|Provide|Use|Return)\b", s, re.I)
        )
        active_ratio = active_openers / len(sentences)

        return round(min(100.0, length_score * 0.7 + active_ratio * 30), 1)
