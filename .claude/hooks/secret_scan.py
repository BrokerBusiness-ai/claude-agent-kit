"""PreToolUse dla Write, Edit i MultiEdit: nie pozwala zapisać sekretu w pliku.

Agent kopiujący przykład z dokumentacji potrafi wkleić prawdziwy klucz do
kodu. Hook sprawdza treść przed zapisem i blokuje zapis, jeśli znajdzie coś,
co wygląda na klucz, token albo klucz prywatny. Zaślepki w plikach
przykładowych przechodzą.
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hooklib import Verdict, run, tool_text

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("klucz API Anthropic", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("klucz API OpenAI", re.compile(r"\bsk-(proj-)?[A-Za-z0-9]{32,}\b")),
    ("token GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("klucz dostępu AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("klucz Google API", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("klucz prywatny", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]

# Przypisanie do zmiennej o nazwie sugerującej sekret, z wartością o wysokiej
# entropii. Łapie klucze, których formatu nie znamy z góry.
ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|APIKEY)[A-Z0-9_]*)"
    r"\s*[:=]\s*['\"]?([^\s'\"]{16,})"
)

PLACEHOLDERS = re.compile(
    r"(?i)(changeme|your[_-]|example|placeholder|dummy|xxx+|<[^>]+>|\$\{|\$[A-Z_]+|\.\.\.)"
)

ENTROPY_THRESHOLD = 3.5


def shannon_entropy(value: str) -> float:
    """Entropia w bitach na znak. Losowe klucze mają zwykle powyżej 3.5."""
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum(n / total * math.log2(n / total) for n in counts.values())


def mask(secret: str) -> str:
    """Pokazuje tylko początek i koniec, żeby komunikat nie ujawnił sekretu."""
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}...{secret[-2:]}"


def find_secrets(text: str) -> list[str]:
    """Zwraca listę opisów znalezionych sekretów. Pusta lista oznacza czysto."""
    findings: list[str] = []
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            if not PLACEHOLDERS.search(match.group(0)):
                findings.append(f"{label}: {mask(match.group(0))}")
    for match in ASSIGNMENT.finditer(text):
        name, value = match.group(1), match.group(3)
        if PLACEHOLDERS.search(value):
            continue
        if shannon_entropy(value) >= ENTROPY_THRESHOLD:
            findings.append(f"wartość zmiennej {name}: {mask(value)}")
    return findings


def evaluate(event: dict) -> Verdict:
    if event.get("tool_name") not in {"Write", "Edit", "MultiEdit"}:
        return Verdict.allow()
    findings = find_secrets(tool_text(event))
    if not findings:
        return Verdict.allow()
    path = (event.get("tool_input") or {}).get("file_path", "?")
    listing = "\n".join(f"- {item}" for item in findings)
    return Verdict.block(
        f"Zablokowany zapis do {path}: treść wygląda na sekret.\n{listing}\n"
        "Użyj zmiennej środowiskowej i odczytaj ją w kodzie. W plikach "
        "przykładowych zostaw zaślepkę, np. ANTHROPIC_API_KEY=your-key-here."
    )


if __name__ == "__main__":
    sys.exit(run(evaluate))
