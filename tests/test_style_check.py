from style_check import evaluate, find_violations

EM = "\u2014"
EN = "\u2013"


def test_finds_em_and_en_dash_with_line_numbers():
    text = f"ok\nzdanie {EM} wtrącenie\nlata 2020{EN}2024"
    found = find_violations(text)
    assert len(found) == 2
    assert found[0].startswith("linia 2")
    assert found[1].startswith("linia 3")


def test_clean_text_passes():
    assert find_violations("Zwykły tekst, z dywizem - i przecinkami.") == []


def test_checks_markdown_files(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(f"Tytuł {EM} podtytuł", encoding="utf-8")
    event = {"tool_name": "Write", "tool_input": {"file_path": str(path)}}
    assert not evaluate(event).allowed


def test_skips_code_files(tmp_path):
    path = tmp_path / "module.py"
    path.write_text(f"# komentarz {EM}", encoding="utf-8")
    event = {"tool_name": "Write", "tool_input": {"file_path": str(path)}}
    assert evaluate(event).allowed


def test_missing_file_is_not_an_error(tmp_path):
    event = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "nope.md")}}
    assert evaluate(event).allowed
