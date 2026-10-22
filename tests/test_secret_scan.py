import pytest
from secret_scan import evaluate, find_secrets, mask, shannon_entropy

# Fałszywe klucze budowane w locie, żeby sam plik testów nie wyglądał jak wyciek.
FAKE_ANTHROPIC = "sk-ant-" + "api03-" + "Zx8Qw2Lm9Rt4Vb7Np1Kd6Hs3Jf5Gy0Ua" * 2
FAKE_GITHUB = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
FAKE_AWS = "AKIA" + "QWERTYUIOPASDFGH"


@pytest.mark.parametrize("secret", [FAKE_ANTHROPIC, FAKE_GITHUB, FAKE_AWS])
def test_detects_known_formats(secret):
    assert find_secrets(f"key = '{secret}'")


def test_detects_high_entropy_assignment():
    assert find_secrets('API_KEY = "q8Zr2Lp9Xv4Tn7Wm1Kc6Bd3"')


@pytest.mark.parametrize(
    "text",
    [
        'API_KEY = "your-api-key-here"',
        "API_KEY = os.environ['API_KEY']",
        'PASSWORD = "changeme"',
        "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
        "print('hello world')",
    ],
)
def test_ignores_placeholders_and_code(text):
    assert not find_secrets(text)


def test_mask_hides_middle():
    masked = mask(FAKE_GITHUB)
    assert FAKE_GITHUB not in masked
    assert masked.startswith(FAKE_GITHUB[:4])


def test_entropy_orders_random_above_repetitive():
    assert shannon_entropy("aaaaaaaaaaaa") < shannon_entropy("q8Zr2Lp9Xv4T")


def test_blocks_write_with_secret_and_masks_reason():
    event = {"tool_name": "Write", "tool_input": {"file_path": "cfg.py", "content": f"K='{FAKE_GITHUB}'"}}
    verdict = evaluate(event)
    assert not verdict.allowed
    assert FAKE_GITHUB not in verdict.reason


def test_checks_multiedit():
    event = {"tool_name": "MultiEdit", "tool_input": {"edits": [{"new_string": FAKE_AWS}]}}
    assert not evaluate(event).allowed


def test_allows_clean_edit():
    event = {"tool_name": "Edit", "tool_input": {"new_string": "x = 1"}}
    assert evaluate(event).allowed
