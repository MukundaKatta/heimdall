# Heimdall — curated system prompt library

[![PyPI](https://img.shields.io/badge/pypi-heimdall--prompts-blue)](https://pypi.org/project/heimdall-prompts/)
[![license](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

> Norse mythology: Heimdall watches from the gateway of the gods. Here: a small Python library + CLI for managing, searching, and analyzing AI system prompts. Ships with 10 opinionated starter prompts.

## Install

```bash
pip install heimdall-prompts
```

## CLI

```bash
heimdall list                          # show all prompts (built-in + local)
heimdall list --category coding
heimdall list --tag tdd

heimdall show code-review-thorough     # metadata + content
heimdall show code-review-thorough --content-only   # just the prompt body

heimdall search TDD                    # fuzzy search

heimdall analyze code-review-thorough  # quality stats (density, structure, readability)

heimdall categories                    # list categories with counts
```

## Library

```python
from heimdall import SystemPrompt, PromptLibrary, PromptAnalyzer

lib = PromptLibrary()
lib.add(SystemPrompt(
    name="my-reviewer",
    content="You are a senior engineer...",
    category="coding",
    tags=["review"],
))

# Search, filter, analyze
results = lib.search("review")
print(PromptAnalyzer().analyze(lib.get("my-reviewer")))
```

## Starter prompts

Ships with 10 opinionated system prompts:

| Category | Prompt |
|---|---|
| coding | `code-review-thorough`, `bug-repro-minimizer`, `tdd-strict` |
| writing | `api-doc-generator`, `pr-description-writer`, `terse-explainer` |
| analysis | `research-synthesizer` |
| thinking | `rubber-duck`, `devil-advocate` |
| career | `interview-star-coach` |

Each is deliberate about what *not* to include (no hedging, no history-dumping, no empty praise). Read them in `src/heimdall/data/starter_prompts.json`.

## Adding your own prompts

Drop JSON files in `~/.heimdall/` (or set `HEIMDALL_DIR=/path/to/prompts`). Each file can be a single prompt object or an array. Schema:

```json
[
  {
    "name": "my-prompt",
    "content": "You are...",
    "category": "coding",
    "tags": ["example"],
    "model_target": "claude"
  }
]
```

`heimdall list` picks them up automatically.

## What Heimdall isn't

- Not a prompt-engineering framework. No chains, no templates-of-templates.
- Not an LLM wrapper. The prompts are text — you send them wherever.
- Not opinionated about *which* LLM. `model_target` is metadata, not enforcement.

## Development

```bash
git clone https://github.com/MukundaKatta/heimdall.git
cd heimdall
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
heimdall list
```

## License

MIT
