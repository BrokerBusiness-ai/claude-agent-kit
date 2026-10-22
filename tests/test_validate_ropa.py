import json

from conftest import CONFIG_DIR
from validate_ropa import main, validate_activity, validate_register

EXAMPLE = CONFIG_DIR / "skills/gdpr-doc-validator/examples/ropa_example.json"


def complete_activity(**overrides):
    activity = {
        "name": "Kadry",
        "purpose": "zatrudnienie",
        "data_subjects": ["pracownicy"],
        "data_categories": ["dane identyfikacyjne"],
        "recipients": ["biuro rachunkowe"],
        "retention": "10 lat od ustania zatrudnienia",
        "security_measures": "kontrola dostępu",
        "legal_basis": ["6.1.c"],
    }
    activity.update(overrides)
    return activity


def rules(issues):
    return {i.rule for i in issues}


def test_complete_activity_passes():
    assert validate_activity(complete_activity()) == []


def test_missing_fields_reported():
    issues = validate_activity({"name": "X"})
    assert sum(1 for i in issues if i.rule == "art. 30 ust. 1") == 7


def test_unknown_legal_basis():
    assert "art. 6 ust. 1" in rules(validate_activity(complete_activity(legal_basis=["6.1.z"])))


def test_legitimate_interest_needs_balancing_test():
    issues = validate_activity(complete_activity(legal_basis=["6.1.f"]))
    assert "art. 6 ust. 1 lit. f" in rules(issues)
    ok = validate_activity(complete_activity(legal_basis=["6.1.f"], legitimate_interest_test="LIA-01"))
    assert ok == []


def test_special_category_needs_art9_condition():
    activity = complete_activity(data_categories=["zdrowie"])
    assert "art. 9 ust. 2" in rules(validate_activity(activity))
    activity["art9_condition"] = "9.2.h"
    assert "art. 9 ust. 2" not in rules(validate_activity(activity))


def test_vague_retention_is_warning():
    issues = validate_activity(complete_activity(retention="do odwołania"))
    assert [i.level for i in issues] == ["ostrzeżenie"]


def test_transfer_without_mechanism():
    activity = complete_activity(third_country_transfers=[{"country": "USA", "mechanism": None}])
    assert "art. 44-49" in rules(validate_activity(activity))
    activity["third_country_transfers"][0]["mechanism"] = "SCC"
    assert validate_activity(activity) == []


def test_dpia_triggered_by_two_criteria():
    activity = complete_activity(dpia_criteria=["large_scale", "systematic_monitoring"])
    assert "art. 35 ust. 1" in rules(validate_activity(activity))
    activity["dpia_done"] = True
    assert validate_activity(activity) == []


def test_single_dpia_criterion_is_not_enough():
    assert validate_activity(complete_activity(dpia_criteria=["large_scale"])) == []


def test_special_data_counts_as_dpia_criterion():
    activity = complete_activity(
        data_categories=["zdrowie"], art9_condition="9.2.h", dpia_criteria=["innovative_technology"]
    )
    assert "art. 35 ust. 1" in rules(validate_activity(activity))


def test_processor_without_dpa():
    activity = complete_activity(processors=[{"name": "Chmura", "dpa_signed": False}])
    assert "art. 28 ust. 3" in rules(validate_activity(activity))


def test_register_level_checks():
    issues = validate_register({"activities": [complete_activity(), complete_activity()]})
    assert "art. 30 ust. 1 lit. a" in rules(issues)
    assert "spójność" in rules(issues)


def test_example_file_finds_planted_problems(capsys):
    register = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    found = rules(validate_register(register))
    assert {
        "art. 44-49",
        "art. 28 ust. 3",
        "art. 9 ust. 2",
        "art. 35 ust. 1",
        "art. 5 ust. 1 lit. e",
    } <= found
    assert main([str(EXAMPLE)]) == 1
    assert "Błędy:" in capsys.readouterr().out
