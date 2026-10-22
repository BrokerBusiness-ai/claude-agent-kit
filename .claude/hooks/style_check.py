"""PostToolUse dla Write i Edit: pilnuje reguł redakcyjnych w dokumentach.

Przykład reguły, której model nie trzyma się sam z siebie: zakaz pauzy
(U+2014) i półpauzy (U+2013) w tekstach. Instrukcja w CLAUDE.md działa
w większości przypadków, hook domyka resztę: po zapisie sprawdza plik
i odsyła agentowi konkretne linie do poprawy.

PostToolUse nie cofa zapisu. Kod wyjścia 2 przekazuje agentowi informację
zwrotną, a agent poprawia plik w kolejnym kroku.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hooklib import Verdict, run

CHECKED_SUFFIXES = {".md", ".txt", ".rst"}
FORBIDDEN = {
    "\u2014": "pauza (U+2014)",
    "\u2013": "półpauza (U+2013)",
}
MAX_REPORTED = 10


def find_violations(text: str) -> list[str]:
    """Zwraca opisy naruszeń w formacie 'linia N: znak'."""
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for char, label in FORBIDDEN.items():
            if char in line:
                found.append(f"linia {number}: {label}")
    return found


def evaluate(event: dict) -> Verdict:
    if event.get("tool_name") not in {"Write", "Edit", "MultiEdit"}:
        return Verdict.allow()
    path = Path((event.get("tool_input") or {}).get("file_path", ""))
    if path.suffix.lower() not in CHECKED_SUFFIXES or not path.is_file():
        return Verdict.allow()
    violations = find_violations(path.read_text(encoding="utf-8", errors="replace"))
    if not violations:
        return Verdict.allow()
    shown = "\n".join(f"- {v}" for v in violations[:MAX_REPORTED])
    extra = len(violations) - MAX_REPORTED
    tail = f"\n- i {extra} więcej" if extra > 0 else ""
    return Verdict.block(
        f"{path.name} narusza regułę redakcyjną projektu:\n{shown}{tail}\n"
        "Zastąp pauzę przecinkiem, dwukropkiem, kropką, nawiasem albo dywizem (-)."
    )


if __name__ == "__main__":
    sys.exit(run(evaluate))
