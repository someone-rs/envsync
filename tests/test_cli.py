import json

import pytest

from envsync.cli import main


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return path


def test_cli_passes_clean_and_reports_missing(capsys, tmp_path):
    example = write(tmp_path, ".env.example", "A=1\nB=2\n")
    env = write(tmp_path, ".env", "A=x\n")
    assert main(["--example", str(example), "--env", str(env)]) == 1
    assert "MISSING" in capsys.readouterr().out

    env.write_text("A=x\nB=y\n")
    assert main(["--example", str(example), "--env", str(env)]) == 0


def test_cli_json_output(capsys, tmp_path):
    example = write(tmp_path, ".env.example", "A=1\n")
    env = write(tmp_path, ".env", "")
    assert main(["--example", str(example), "--env", str(env), "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["findings"][0]["kind"] == "missing"


def test_cli_fix_appends_missing_keys(tmp_path):
    example = write(tmp_path, ".env.example", "A=1\nB=2\n")
    env = write(tmp_path, ".env", "A=x\n")
    assert main(["--example", str(example), "--env", str(env), "--fix"]) == 0
    assert "B=" in env.read_text()


def test_cli_missing_file_is_exit_2(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main(["--example", str(tmp_path / "nope"), "--env", str(tmp_path / "also-nope")])
    assert exc.value.code == 2
