#!/usr/bin/env python3
"""CLI for adding a reference to the project's refs index.

Usage:
    python3 add_ref_handler.py <url_or_path> --name <name> --topic <topic> [--tags tag1 tag2 ...]
    [--cwd <project_root>]

Exits 0 on success, non-zero on error.
Prints the registered relative path to stdout on success.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ref_fetcher import detect_input_type, fetch_url, copy_file
from ref_io import add_entry, get_refs_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a reference to the project refs index")
    parser.add_argument("source", help="URL or local file path")
    parser.add_argument("--name", required=True, help="Short identifier for this reference")
    parser.add_argument("--topic", required=True, help="Topic subfolder under .claude/refs/")
    parser.add_argument("--tags", nargs="*", default=[], help="Optional tags")
    parser.add_argument("--cwd", default="", help="Project root (defaults to CLAUDE_PROJECT_DIR or os.getcwd())")
    args = parser.parse_args()

    cwd = args.cwd or os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()

    refs_base = get_refs_dir(cwd).resolve()
    dest_dir = (refs_base / args.topic).resolve()
    try:
        dest_dir.relative_to(refs_base)
    except ValueError:
        print("Error: --topic escapes the refs directory", file=sys.stderr)
        sys.exit(1)

    if "\n" in args.name or "\r" in args.name:
        print("Error: --name must not contain newlines", file=sys.stderr)
        sys.exit(1)
    if any("\n" in t or "\r" in t for t in args.tags):
        print("Error: --tags must not contain newlines", file=sys.stderr)
        sys.exit(1)

    input_type = detect_input_type(args.source)
    try:
        if input_type == "url":
            saved_path = fetch_url(args.source, dest_dir)
        else:
            saved_path = copy_file(args.source, dest_dir)
        rel_path = str(saved_path.resolve().relative_to(Path(cwd).resolve()))
        add_entry(cwd, args.name, rel_path, args.tags)
        print(rel_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
