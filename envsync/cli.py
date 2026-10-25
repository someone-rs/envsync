"""Command-line interface for envsync."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checker import check, is_failure
from .parser import parse_env

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"envsync: error: file not found: {path}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR) from None
    except OSError as exc:
        print(f"envsync: error: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR) from None


def _render_text(report, *, example_path: Path, env_path: Path) -> str:
    lines = [
        f"example: {example_path} ({report.example_keys} keys)",
        f"env:     {env_path} ({report.env_keys} keys)",
        "",
    ]
    if not report.findings:
        lines.append("OK — .env covers every key in .env.example.")
        return "\n".join(lines)
    for finding in report.findings:
        label = finding.key or "(line)"
        lines.append(f"  {finding.kind.upper():<10} {label} — {finding.detail}")
    lines.append("")
    lines.append(f"{len(report.missing)} missing, {len(report.findings)} findings total.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envsync",
        description="Check that .env covers every key in .env.example.",
    )
    parser.add_argument("--example", default=".env.example",
                        help="path to the example file (default: .env.example)")
    parser.add_argument("--env", default=".env",
                        help="path to the env file (default: .env)")
    parser.add_argument("--json", action="store_true",
                        help="emit the report as JSON instead of a table")
    parser.add_argument("--strict", action="store_true",
                        help="also fail on extra keys and empty values")
    parser.add_argument("--ignore", default="",
                        help="comma-separated keys to skip")
    parser.add_argument("--fix", action="store_true",
                        help="append missing keys (as KEY=) to the env file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    example_path = Path(args.example)
    env_path = Path(args.env)
    ignore = frozenset(k.strip() for k in args.ignore.split(",") if k.strip())

    example = parse_env(_read(example_path))
    env = parse_env(_read(env_path))
    report = check(example, env, ignore=ignore, strict=args.strict)

    if args.fix and report.missing:
        existing = env_path.read_text(encoding="utf-8")
        additions = "".join(f"{f.key}=\n" for f in report.missing)
        if existing and not existing.endswith("\n"):
            additions = "\n" + additions
        env_path.write_text(existing + additions, encoding="utf-8")
        print(f"envsync: added {len(report.missing)} missing key(s) to {env_path}")
        # Re-check so the report reflects the fixed file.
        env = parse_env(env_path.read_text(encoding="utf-8"))
        report = check(example, env, ignore=ignore, strict=args.strict)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(_render_text(report, example_path=example_path, env_path=env_path))
    return EXIT_ISSUES if is_failure(report, strict=args.strict) else EXIT_OK
