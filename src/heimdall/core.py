"""Core module for Heimdall prompt library.

Provides the SystemPrompt dataclass, PromptLibrary for managing collections,
and PromptAnalyzer for evaluating prompt quality.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SystemPrompt:
    """Represents a single AI system prompt with metadata.

    Attributes:
        name: Human-readable identifier for the prompt.
        content: The full text of the system prompt.
        category: High-level grouping (e.g. 'coding', 'writing', 'analysis').
        tags: Freeform labels for fine-grained filtering.
        model_target: Which model family the prompt is designed for.
        token_count: Approximate token count (auto-calculated if omitted).
        effectiveness_score: Optional 0-100 quality rating.
    """

    name: str
    content: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    model_target: str = "any"
    token_count: int = 0
    effectiveness_score: float = 0.0

    def __post_init__(self) -> None:
        if self.token_count == 0:
            self.token_count = estimate_token_count(self.content)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_token_count(text: str) -> int:
    """Estimate token count using a simple word/punctuation heuristic.

    Roughly 1 token per word plus extra tokens for punctuation and special chars.
    This avoids any external dependency on tokeniser libraries.
    """
    words = text.split()
    punctuation_extra = len(re.findall(r"[^\w\s]", text))
    return len(words) + punctuation_extra // 3


# ---------------------------------------------------------------------------
# PromptLibrary
# ---------------------------------------------------------------------------

class PromptLibrary:
    """Manages a searchable, categorised collection of system prompts.

    Example::

        lib = PromptLibrary()
        lib.add(SystemPrompt(name="Coder", content="You are a coding assistant.", category="coding"))
        results = lib.search("coding")
    """

    def __init__(self) -> None:
        self._prompts: Dict[str, SystemPrompt] = {}

    # -- basic CRUD --------------------------------------------------------

    def add(self, prompt: SystemPrompt) -> None:
        """Add a prompt to the library, keyed by name."""
        if not prompt.name:
            raise ValueError("Prompt must have a non-empty name")
        if not prompt.content:
            raise ValueError("Prompt must have non-empty content")
        self._prompts[prompt.name] = prompt

    def get(self, name: str) -> Optional[SystemPrompt]:
        """Retrieve a prompt by exact name, or None."""
        return self._prompts.get(name)

    def remove(self, name: str) -> bool:
        """Remove a prompt by name. Returns True if it existed."""
        return self._prompts.pop(name, None) is not None

    def list_all(self) -> List[SystemPrompt]:
        """Return all prompts sorted by name."""
        return sorted(self._prompts.values(), key=lambda p: p.name)

    @property
    def size(self) -> int:
        """Number of prompts currently stored."""
        return len(self._prompts)

    # -- search & filter ---------------------------------------------------

    def search(self, query: str) -> List[SystemPrompt]:
        """Full-text search across name, content, category and tags.

        Case-insensitive substring matching.  Returns matches ordered by
        relevance (number of field hits).
        """
        q = query.lower()
        scored: List[Tuple[int, SystemPrompt]] = []
        for prompt in self._prompts.values():
            score = 0
            if q in prompt.name.lower():
                score += 3
            if q in prompt.content.lower():
                score += 2
            if q in prompt.category.lower():
                score += 2
            for tag in prompt.tags:
                if q in tag.lower():
                    score += 1
            if score > 0:
                scored.append((score, prompt))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [p for _, p in scored]

    def by_category(self, category: str) -> List[SystemPrompt]:
        """Return prompts belonging to *category* (case-insensitive)."""
        cat = category.lower()
        return [p for p in self._prompts.values() if p.category.lower() == cat]

    def by_tag(self, tag: str) -> List[SystemPrompt]:
        """Return prompts that carry *tag* (case-insensitive)."""
        t = tag.lower()
        return [
            p for p in self._prompts.values()
            if any(pt.lower() == t for pt in p.tags)
        ]

    def by_model(self, model: str) -> List[SystemPrompt]:
        """Return prompts targeting a specific model family."""
        m = model.lower()
        return [
            p for p in self._prompts.values()
            if p.model_target.lower() == m or p.model_target.lower() == "any"
        ]

    # -- comparison --------------------------------------------------------

    def compare(self, name_a: str, name_b: str) -> Dict[str, object]:
        """Compare two prompts side-by-side.

        Returns a dict with keys:
            token_diff, category_match, shared_tags, score_diff,
            length_ratio, prompt_a, prompt_b.
        """
        a = self._prompts.get(name_a)
        b = self._prompts.get(name_b)
        if a is None:
            raise KeyError(f"Prompt '{name_a}' not found")
        if b is None:
            raise KeyError(f"Prompt '{name_b}' not found")

        shared = set(t.lower() for t in a.tags) & set(t.lower() for t in b.tags)
        len_max = max(len(a.content), len(b.content), 1)

        return {
            "prompt_a": a.name,
            "prompt_b": b.name,
            "token_diff": abs(a.token_count - b.token_count),
            "category_match": a.category.lower() == b.category.lower(),
            "shared_tags": sorted(shared),
            "score_diff": round(abs(a.effectiveness_score - b.effectiveness_score), 2),
            "length_ratio": round(min(len(a.content), len(b.content)) / len_max, 2),
        }

    # -- statistics --------------------------------------------------------

    def stats(self) -> Dict[str, object]:
        """Aggregate statistics about the library."""
        if not self._prompts:
            return {"count": 0, "categories": [], "avg_tokens": 0}
        prompts = list(self._prompts.values())
        categories = sorted({p.category for p in prompts})
        avg_tokens = sum(p.token_count for p in prompts) / len(prompts)
        avg_score = sum(p.effectiveness_score for p in prompts) / len(prompts)
        return {
            "count": len(prompts),
            "categories": categories,
            "avg_tokens": round(avg_tokens, 1),
            "avg_score": round(avg_score, 1),
            "total_tokens": sum(p.token_count for p in prompts),
        }


# ---------------------------------------------------------------------------
# PromptAnalyzer
# ---------------------------------------------------------------------------

class PromptAnalyzer:
    """Static analysis of prompt quality and structure.

    All methods are pure functions that accept a SystemPrompt (or raw text)
    and return metrics without side effects.
    """

    # Instruction verbs commonly found in high-quality prompts
    INSTRUCTION_VERBS = [
        "must", "should", "always", "never", "ensure", "avoid",
        "respond", "provide", "generate", "analyze", "explain",
        "format", "include", "exclude", "follow", "return",
        "use", "do not", "consider", "maintain", "keep",
    ]

    STRUCTURAL_SECTIONS = [
        "role", "context", "constraints", "instructions",
        "examples", "output format", "tone", "audience",
    ]

    # ---- top-level analysis -----------------------------------------------

    def analyze(self, prompt: SystemPrompt) -> Dict[str, object]:
        """Full analysis returning all available metrics."""
        return {
            "name": prompt.name,
            "token_count": prompt.token_count,
            "instruction_density": self.instruction_density(prompt.content),
            "specificity_score": self.specificity_score(prompt.content),
            "structure": self.structure_analysis(prompt.content),
            "readability": self.readability_score(prompt.content),
            "quality_rating": self.quality_rating(prompt),
        }

    # ---- individual metrics -----------------------------------------------

    def instruction_density(self, text: str) -> float:
        """Fraction of sentences containing instruction verbs (0.0-1.0)."""
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0
        hits = 0
        for sentence in sentences:
            lower = sentence.lower()
            if any(verb in lower for verb in self.INSTRUCTION_VERBS):
                hits += 1
        return round(hits / len(sentences), 2)

    def specificity_score(self, text: str) -> float:
        """Score 0-100 reflecting how specific and concrete a prompt is.

        Heuristics:
        * Presence of numbers/quantifiers adds specificity.
        * Quoted examples add specificity.
        * Concrete nouns (detected by capitalised words) help.
        * Very short prompts are penalised.
        """
        score = 50.0  # baseline

        # length bonus / penalty
        word_count = len(text.split())
        if word_count < 20:
            score -= 15
        elif word_count > 100:
            score += 10

        # numbers / quantifiers
        numbers = re.findall(r"\b\d+\b", text)
        score += min(len(numbers) * 3, 15)

        # quoted strings (examples)
        quotes = re.findall(r'"[^"]{3,}"', text) + re.findall(r"'[^']{3,}'", text)
        score += min(len(quotes) * 5, 15)

        # bullet / numbered lists
        list_items = re.findall(r"(?m)^[\s]*[-*\d]+[.)]\s", text)
        score += min(len(list_items) * 2, 10)

        # structural keywords
        for section in self.STRUCTURAL_SECTIONS:
            if section.lower() in text.lower():
                score += 2

        return round(max(0.0, min(100.0, score)), 1)

    def structure_analysis(self, text: str) -> Dict[str, object]:
        """Detect which structural sections are present."""
        found = []
        missing = []
        for section in self.STRUCTURAL_SECTIONS:
            if section.lower() in text.lower():
                found.append(section)
            else:
                missing.append(section)

        has_lists = bool(re.search(r"(?m)^[\s]*[-*\d]+[.)]\s", text))
        has_examples = "example" in text.lower() or bool(
            re.findall(r'"[^"]{3,}"', text)
        )
        paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

        return {
            "sections_found": found,
            "sections_missing": missing,
            "has_lists": has_lists,
            "has_examples": has_examples,
            "paragraph_count": paragraph_count,
        }

    def readability_score(self, text: str) -> float:
        """Simplified Flesch-like readability score (0-100, higher = easier)."""
        sentences = self._split_sentences(text)
        words = text.split()
        if not sentences or not words:
            return 0.0

        avg_sentence_len = len(words) / len(sentences)
        avg_word_len = sum(len(w) for w in words) / len(words)

        # Simplified formula inspired by Flesch Reading Ease
        score = 206.835 - (1.015 * avg_sentence_len) - (84.6 * (avg_word_len / 5))
        return round(max(0.0, min(100.0, score)), 1)

    def quality_rating(self, prompt: SystemPrompt) -> str:
        """Qualitative rating: 'excellent', 'good', 'fair', or 'poor'."""
        density = self.instruction_density(prompt.content)
        specificity = self.specificity_score(prompt.content)
        structure = self.structure_analysis(prompt.content)
        sections_found = len(structure["sections_found"])

        composite = (
            density * 30
            + specificity * 0.4
            + sections_found * 5
            + (10 if structure["has_examples"] else 0)
        )

        if composite >= 60:
            return "excellent"
        elif composite >= 40:
            return "good"
        elif composite >= 20:
            return "fair"
        return "poor"

    # ---- helpers ----------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Rough sentence splitter: split on . ! ? followed by space or EOL."""
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in parts if s.strip()]
