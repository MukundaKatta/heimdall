"""Prompt templates with variable substitution.

Provides reusable prompt skeletons for common AI interaction patterns:
system prompts, few-shot learning, chain-of-thought, and role-play.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# PromptTemplate
# ---------------------------------------------------------------------------

@dataclass
class PromptTemplate:
    """A prompt skeleton with ``{variable}`` placeholders.

    Attributes:
        name: Template identifier.
        template: Text with ``{var}`` slots.
        description: What the template is for.
        required_vars: Variables that *must* be supplied at render time.
        default_vars: Fallback values for optional variables.
    """

    name: str
    template: str
    description: str = ""
    required_vars: List[str] = field(default_factory=list)
    default_vars: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Auto-detect required vars from template if not explicitly set
        if not self.required_vars:
            detected = self.extract_variables()
            self.required_vars = [v for v in detected if v not in self.default_vars]

    def extract_variables(self) -> List[str]:
        """Return an ordered, deduplicated list of ``{var}`` names."""
        seen: Set[str] = set()
        result: List[str] = []
        for match in re.finditer(r"\{(\w+)\}", self.template):
            var = match.group(1)
            if var not in seen:
                seen.add(var)
                result.append(var)
        return result

    def render(self, variables: Optional[Dict[str, str]] = None) -> str:
        """Substitute variables into the template.

        Raises ``ValueError`` if any required variable is missing.
        """
        variables = variables or {}
        merged = {**self.default_vars, **variables}

        missing = [v for v in self.required_vars if v not in merged]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        result = self.template
        for var_name, value in merged.items():
            result = result.replace("{" + var_name + "}", str(value))
        return result

    def validate(self, variables: Dict[str, str]) -> List[str]:
        """Return a list of problems (empty means valid)."""
        problems: List[str] = []
        for v in self.required_vars:
            if v not in variables and v not in self.default_vars:
                problems.append(f"Missing required variable: {v}")
        extra = set(variables) - set(self.extract_variables())
        for e in sorted(extra):
            problems.append(f"Unknown variable: {e}")
        return problems


# ---------------------------------------------------------------------------
# TemplateEngine
# ---------------------------------------------------------------------------

class TemplateEngine:
    """Registry of named templates with batch rendering support."""

    def __init__(self) -> None:
        self._templates: Dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Add a template to the engine."""
        if not template.name:
            raise ValueError("Template must have a non-empty name")
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a template by name."""
        return self._templates.get(name)

    def list_templates(self) -> List[str]:
        """Return sorted list of registered template names."""
        return sorted(self._templates.keys())

    def render(self, name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """Render a registered template by name.

        Raises ``KeyError`` if the template is not found.
        """
        tpl = self._templates.get(name)
        if tpl is None:
            raise KeyError(f"Template '{name}' not found")
        return tpl.render(variables)

    def render_chain(
        self, names: List[str], variables: Optional[Dict[str, str]] = None,
        separator: str = "\n\n"
    ) -> str:
        """Render several templates and join them."""
        parts = [self.render(n, variables) for n in names]
        return separator.join(parts)


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

BUILTIN_SYSTEM_PROMPT = PromptTemplate(
    name="system_prompt",
    template=(
        "You are {role}.\n\n"
        "## Context\n{context}\n\n"
        "## Instructions\n{instructions}\n\n"
        "## Constraints\n- {constraints}\n\n"
        "## Output Format\n{output_format}"
    ),
    description="Standard system prompt skeleton with role, context, instructions, constraints, and output format.",
    default_vars={"output_format": "Respond in plain text."},
)

BUILTIN_FEW_SHOT = PromptTemplate(
    name="few_shot",
    template=(
        "You are {role}. Below are examples of the expected input/output pattern.\n\n"
        "### Examples\n{examples}\n\n"
        "### Task\n{task}"
    ),
    description="Few-shot template with example demonstrations.",
)

BUILTIN_CHAIN_OF_THOUGHT = PromptTemplate(
    name="chain_of_thought",
    template=(
        "You are {role}.\n\n"
        "When answering, think step by step:\n"
        "1. Identify the key elements of the question.\n"
        "2. Break the problem into sub-problems.\n"
        "3. Solve each sub-problem.\n"
        "4. Combine into a final answer.\n\n"
        "## Question\n{question}"
    ),
    description="Chain-of-thought reasoning template.",
    default_vars={"role": "a careful analytical assistant"},
)

BUILTIN_ROLE_PLAY = PromptTemplate(
    name="role_play",
    template=(
        "You are {character}.\n\n"
        "## Background\n{background}\n\n"
        "## Personality Traits\n- {traits}\n\n"
        "## Scenario\n{scenario}\n\n"
        "Stay in character at all times. "
        "Respond as {character} would, maintaining consistent voice and perspective."
    ),
    description="Role-play / persona template for character-based interactions.",
)

BUILTIN_TEMPLATES: List[PromptTemplate] = [
    BUILTIN_SYSTEM_PROMPT,
    BUILTIN_FEW_SHOT,
    BUILTIN_CHAIN_OF_THOUGHT,
    BUILTIN_ROLE_PLAY,
]


def create_default_engine() -> TemplateEngine:
    """Return a TemplateEngine pre-loaded with all built-in templates."""
    engine = TemplateEngine()
    for tpl in BUILTIN_TEMPLATES:
        engine.register(tpl)
    return engine
