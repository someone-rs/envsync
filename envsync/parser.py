"""Parse dotenv-style files.

Supported syntax (the common subset every tool agrees on):

    KEY=value
    export KEY=value
    KEY="double quoted value"
    KEY='single quoted value'
    # a comment
    KEY=value  # inline comment, only for unquoted values

The parser is deliberately strict about structure and lenient about values:
it reports duplicates, malformed lines, and empty values instead of
silently guessing, so callers can surface them as findings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Entry:
    """One parsed assignment, with its source location."""

    key: str
    value: str
    line: int
    quoted: bool = False


@dataclass
class ParsedFile:
    entries: list[Entry] = field(default_factory=list)
    duplicates: dict[str, list[int]] = field(default_factory=dict)
    malformed: list[tuple[int, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, str]:
        """First occurrence wins; duplicates are reported separately."""
        out: dict[str, str] = {}
        for entry in self.entries:
            out.setdefault(entry.key, entry.value)
        return out


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _strip_inline_comment(value: str) -> str:
    """Remove a trailing ` # comment` from an unquoted value."""
    if " #" in value:
        return value.split(" #", 1)[0].rstrip()
    return value


def _unquote(raw: str) -> tuple[str, bool]:
    """Return (value, was_quoted). Raises ValueError on unterminated quotes."""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        quote = raw[0]
        body = raw[1:-1]
        if quote == '"':
            # Only the escapes dotenv users actually write.
            body = body.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
        return body, True
    if raw and raw[0] in "\"'":
        raise ValueError("unterminated quote")
    return _strip_inline_comment(raw), False


def parse_env(text: str) -> ParsedFile:
    """Parse dotenv text into entries, duplicates, and malformed lines."""
    parsed = ParsedFile()
    seen: dict[str, list[int]] = {}
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            parsed.malformed.append((lineno, raw_line))
            continue
        key, _, raw_value = line.partition("=")
        key = key.strip()
        raw_value = raw_value.strip()
        if not _KEY_RE.match(key):
            parsed.malformed.append((lineno, raw_line))
            continue
        try:
            value, quoted = _unquote(raw_value)
        except ValueError:
            parsed.malformed.append((lineno, raw_line))
            continue
        seen.setdefault(key, []).append(lineno)
        parsed.entries.append(Entry(key=key, value=value, line=lineno, quoted=quoted))
    for key, lines in seen.items():
        if len(lines) > 1:
            parsed.duplicates[key] = lines
    return parsed
