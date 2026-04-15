"""Heimdall command-line interface.

Usage:
    heimdall list                        # list all prompts (built-in + local)
    heimdall list --category coding      # filter by category
    heimdall list --tag tdd              # filter by tag
    heimdall show <name>                 # print a prompt's content
    heimdall search <query>              # fuzzy search across prompts
    heimdall analyze <name>              # print PromptAnalyzer stats
    heimdall categories                  # list all available categories

Local prompts: a directory of JSON files at $HEIMDALL_DIR or ~/.heimdall/.
Each JSON file can be a single prompt object or a list of them (same schema
as starter_prompts.json).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable

from heimdall.core import PromptAnalyzer, PromptLibrary, SystemPrompt


def _data_dir() -> Path:
    return Path(__file__).parent / "data"


def _user_dir() -> Path:
    custom = os.environ.get("HEIMDALL_DIR")
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".heimdall"


def _load_prompts_from_json(path: Path) -> list[SystemPrompt]:
    with path.open() as fh:
        raw = json.load(fh)
    items = raw if isinstance(raw, list) else [raw]
    prompts: list[SystemPrompt] = []
    for item in items:
        prompts.append(SystemPrompt(**item))
    return prompts


def _load_all() -> PromptLibrary:
    lib = PromptLibrary()
    # Built-in starters
    builtin = _data_dir() / "starter_prompts.json"
    if builtin.exists():
        for p in _load_prompts_from_json(builtin):
            lib.add(p)
    # User directory
    user = _user_dir()
    if user.exists():
        for jf in sorted(user.glob("*.json")):
            try:
                for p in _load_prompts_from_json(jf):
                    lib.add(p)
            except Exception as exc:  # pragma: no cover
                print(f"warning: failed to load {jf}: {exc}", file=sys.stderr)
    return lib


def _print_row(p: SystemPrompt) -> None:
    tags = f" [{','.join(p.tags)}]" if p.tags else ""
    print(f"  {p.name:30s} {p.category:12s} {p.token_count:>5}t{tags}")


def cmd_list(args: argparse.Namespace) -> int:
    lib = _load_all()
    results: Iterable[SystemPrompt] = lib.list_all()
    if args.category:
        results = [p for p in results if p.category == args.category]
    if args.tag:
        results = [p for p in results if args.tag in p.tags]
    results = sorted(results, key=lambda p: (p.category, p.name))
    print(f"{len(list(results))} prompt(s):")
    for p in results:
        _print_row(p)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    lib = _load_all()
    p = lib.get(args.name)
    if p is None:
        print(f"no prompt named {args.name!r}", file=sys.stderr)
        return 1
    if args.content_only:
        print(p.content)
    else:
        print(f"# {p.name}")
        print(f"category: {p.category}")
        if p.tags:
            print(f"tags: {', '.join(p.tags)}")
        print(f"model_target: {p.model_target}")
        print(f"tokens (est): {p.token_count}")
        print()
        print(p.content)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    lib = _load_all()
    matches = lib.search(args.query)
    if not matches:
        print(f"no matches for {args.query!r}")
        return 1
    print(f"{len(matches)} match(es) for {args.query!r}:")
    for p in matches:
        _print_row(p)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    lib = _load_all()
    p = lib.get(args.name)
    if p is None:
        print(f"no prompt named {args.name!r}", file=sys.stderr)
        return 1
    report = PromptAnalyzer().analyze(p)
    for key, value in report.items():
        print(f"  {key}: {value}")
    return 0


def cmd_categories(args: argparse.Namespace) -> int:
    lib = _load_all()
    cats: dict[str, int] = {}
    for p in lib.list_all():
        cats[p.category] = cats.get(p.category, 0) + 1
    for cat, n in sorted(cats.items()):
        print(f"  {cat}: {n}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="heimdall", description="Curated system prompt library CLI.")
    sub = ap.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list prompts")
    p_list.add_argument("--category", help="filter by category")
    p_list.add_argument("--tag", help="filter by tag")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="show a prompt by name")
    p_show.add_argument("name")
    p_show.add_argument("--content-only", action="store_true", help="print just the prompt text")
    p_show.set_defaults(func=cmd_show)

    p_search = sub.add_parser("search", help="fuzzy search prompts")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_an = sub.add_parser("analyze", help="analyze prompt quality")
    p_an.add_argument("name")
    p_an.set_defaults(func=cmd_analyze)

    p_cat = sub.add_parser("categories", help="list categories")
    p_cat.set_defaults(func=cmd_categories)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
