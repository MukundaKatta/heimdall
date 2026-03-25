# Heimdall — AI Prompt Library

> **Norse Mythology: Watchman of the Gods** | System prompt management and optimization

[![GitHub Pages](https://img.shields.io/badge/Live_Demo-Visit_Site-blue?style=for-the-badge)](https://MukundaKatta.github.io/heimdall/)
[![GitHub](https://img.shields.io/github/license/MukundaKatta/heimdall?style=flat-square)](LICENSE)

## Overview

Heimdall is a curated collection of AI system prompts — an educational resource for prompt engineering. It provides a prompt library with search, categorization, analysis, and optimization tools.

**Tech Stack:** Python 3.9+, no external dependencies

## Features

- **Prompt Library** — store, search, filter, and compare system prompts
- **Prompt Analyzer** — measure instruction density, specificity, structure, and readability
- **Template Engine** — reusable prompt skeletons with variable substitution (system prompt, few-shot, chain-of-thought, role-play)
- **Prompt Optimizer** — actionable suggestions to improve clarity and reduce token count

## Quick Start

```python
from heimdall import SystemPrompt, PromptLibrary, PromptAnalyzer

# Build a library
lib = PromptLibrary()
lib.add(SystemPrompt(
    name="Python Expert",
    content="You are a senior Python developer. Always use type hints.",
    category="coding",
    tags=["python", "engineering"],
))

# Search and analyze
results = lib.search("python")
analyzer = PromptAnalyzer()
report = analyzer.analyze(results[0])
```

## Project Structure

```
heimdall/
├── src/heimdall/
│   ├── __init__.py
│   ├── core.py          # SystemPrompt, PromptLibrary, PromptAnalyzer
│   ├── templates.py     # PromptTemplate, TemplateEngine, built-ins
│   └── optimizer.py     # PromptOptimizer, OptimizationReport
├── tests/
│   ├── test_core.py
│   ├── test_templates.py
│   └── test_optimizer.py
├── pyproject.toml
└── README.md
```

## Running Tests

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

## Live Demo

Visit the landing page: **https://MukundaKatta.github.io/heimdall/**

## License

MIT License — Officethree Technologies

## Part of the Mythological Portfolio

This is project **#heimdall** in the [100-project Mythological Portfolio](https://github.com/MukundaKatta) by Officethree Technologies.
