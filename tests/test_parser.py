from envsync.parser import parse_env


def test_basic_and_export_and_comments():
    parsed = parse_env(
        "# comment\n"
        "export DATABASE_URL=postgres://localhost/app\n"
        "DEBUG=true  # inline comment\n"
        "EMPTY=\n"
    )
    values = parsed.as_dict()
    assert values["DATABASE_URL"] == "postgres://localhost/app"
    assert values["DEBUG"] == "true"
    assert values["EMPTY"] == ""
    assert not parsed.malformed


def test_quotes():
    parsed = parse_env('A="hello world"\nB=\'it\'s\'\nC="line\\nbreak"\n')
    assert parsed.as_dict()["A"] == "hello world"
    assert parsed.as_dict()["C"] == "line\nbreak"


def test_quoted_hash_is_not_a_comment():
    parsed = parse_env('TOKEN="abc#def"\n')
    assert parsed.as_dict()["TOKEN"] == "abc#def"


def test_duplicates_and_malformed_reported():
    parsed = parse_env("A=1\nA=2\nNOT_A_PAIR\n9BAD=x\n")
    assert parsed.duplicates == {"A": [1, 2]}
    assert len(parsed.malformed) == 2
    assert parsed.as_dict()["A"] == "1"  # first occurrence wins


def test_unterminated_quote_is_malformed():
    parsed = parse_env('A="oops\n')
    assert len(parsed.malformed) == 1
    assert parsed.as_dict() == {}
