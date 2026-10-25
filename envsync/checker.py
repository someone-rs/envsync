"""Compare a project's .env against its .env.example."""

from __future__ import annotations

from dataclasses import dataclass, field

from .parser import ParsedFile


@dataclass
class Finding:
    kind: str  # missing | extra | empty | duplicate | malformed
    key: str
    detail: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    example_keys: int = 0
    env_keys: int = 0

    @property
    def missing(self) -> list[Finding]:
        return [f for f in self.findings if f.kind == "missing"]

    @property
    def has_problems(self) -> bool:
        return bool(self.findings)

    def to_dict(self) -> dict:
        return {
            "example_keys": self.example_keys,
            "env_keys": self.env_keys,
            "findings": [
                {"kind": f.kind, "key": f.key, "detail": f.detail}
                for f in self.findings
            ],
        }


def check(
    example: ParsedFile,
    env: ParsedFile,
    *,
    ignore: frozenset[str] | None = None,
    strict: bool = False,
) -> Report:
    """Build a report. Missing keys always fail; extras fail only in --strict.

    Empty values are always reported (an example key set to nothing is
    usually a forgotten secret), but they never fail the check on their
    own — use --strict to make them fail too.
    """
    ignore = ignore or frozenset()
    example_map = example.as_dict()
    env_map = env.as_dict()
    report = Report(example_keys=len(example_map), env_keys=len(env_map))

    for key in sorted(example_map):
        if key in ignore:
            continue
        if key not in env_map:
            report.findings.append(
                Finding("missing", key, "present in .env.example, absent from .env")
            )
        elif env_map[key] == "":
            report.findings.append(
                Finding("empty", key, "present in .env but set to an empty value")
            )

    if strict:
        for key in sorted(env_map):
            if key not in example_map and key not in ignore:
                report.findings.append(
                    Finding("extra", key, "present in .env, absent from .env.example")
                )

    for key, lines in sorted(env.duplicates.items()):
        if key in ignore:
            continue
        report.findings.append(
            Finding(
                "duplicate",
                key,
                f"defined {len(lines)} times in .env (lines {', '.join(map(str, lines))})",
            )
        )
    for lineno, raw in env.malformed:
        report.findings.append(
            Finding("malformed", "", f".env line {lineno} could not be parsed: {raw!r}")
        )
    return report


def is_failure(report: Report, *, strict: bool = False) -> bool:
    """Exit-code rule: missing/duplicates/malformed always fail.

    Extras only fail in strict mode; empties only fail in strict mode.
    """
    failing = {"missing", "duplicate", "malformed"}
    if strict:
        failing |= {"extra", "empty"}
    return any(f.kind in failing for f in report.findings)
