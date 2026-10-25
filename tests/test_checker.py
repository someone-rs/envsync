from envsync.checker import check, is_failure
from envsync.parser import parse_env


def test_missing_and_empty_reported():
    report = check(parse_env("A=1\nB=2\nC=3\n"), parse_env("A=x\nB=\n"))
    kinds = {f.key: f.kind for f in report.findings}
    assert kinds == {"B": "empty", "C": "missing"}
    assert is_failure(report) is True  # missing fails even though empty alone would not


def test_clean_passes_and_extra_ignored_by_default():
    report = check(parse_env("A=1\n"), parse_env("A=x\nEXTRA=y\n"))
    assert report.findings == []
    assert is_failure(report) is False


def test_strict_fails_on_extra_and_empty():
    report = check(parse_env("A=1\n"), parse_env("A=\nEXTRA=y\n"), strict=True)
    kinds = sorted(f.kind for f in report.findings)
    assert kinds == ["empty", "extra"]
    assert is_failure(report, strict=True) is True


def test_ignore_skips_keys():
    report = check(parse_env("A=1\nOPTIONAL=1\n"), parse_env("A=x\n"),
                   ignore=frozenset({"OPTIONAL"}))
    assert report.findings == []


def test_duplicates_fail():
    report = check(parse_env("A=1\n"), parse_env("A=x\nA=y\n"))
    assert any(f.kind == "duplicate" for f in report.findings)
    assert is_failure(report) is True
