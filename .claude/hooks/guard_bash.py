"""PreToolUse dla Bash: blokuje polecenia nieodwracalne i ryzykowne.

Lista uprawnień w settings.json działa na prefiksach poleceń. Nie złapie
`rm -rf` ukrytego w środku łańcucha ani `curl ... | sh`. Ten hook analizuje
całe polecenie, także części połączone przez &&, || i średnik.

Zasada: agent może wszystko, co da się cofnąć. To, czego cofnąć się nie da,
wymaga człowieka.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hooklib import Verdict, run, tool_text

# (wzorzec, powód). Wzorce dopasowujemy do pojedynczych segmentów polecenia.
RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+-[a-zA-Z]*(rf|fr)[a-zA-Z]*\s+(/|~|\$HOME|\*|\.)(\s|$|/\*)"),
        "rekursywne usuwanie katalogu głównego, domowego lub wszystkiego naraz",
    ),
    (
        re.compile(r"\bgit\s+push\b.*\s(--force|--force-with-lease|-f)(\s|$)"),
        "wymuszony push nadpisuje historię zdalnego repozytorium",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        "reset --hard kasuje niezatwierdzone zmiany",
    ),
    (
        re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f"),
        "git clean -f usuwa nieśledzone pliki bez kosza",
    ),
    (
        re.compile(r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?)\b"),
        "pobieranie i wykonywanie skryptu z sieci bez wglądu w treść",
    ),
    (
        # PostgreSQL przyjmuje TRUNCATE bez słowa TABLE, stąd osobna gałąź.
        re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b|\bTRUNCATE\s+(TABLE\s+)?\w", re.IGNORECASE),
        "nieodwracalna operacja na bazie danych",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\s+\w+\s*;?\s*['\"]?\s*$", re.IGNORECASE),
        "DELETE bez klauzuli WHERE usuwa całą tabelę",
    ),
    (
        re.compile(r"\bmkfs\b|\bdd\s+if=|\bshred\b"),
        "operacja niszcząca dane na poziomie dysku",
    ),
    (
        re.compile(r"\bchmod\s+(-R\s+)?0?777\b"),
        "uprawnienia 777 otwierają pliki dla wszystkich",
    ),
    (
        re.compile(r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b"),
        "publikacja pakietu jest nieodwracalna",
    ),
    (
        re.compile(r"\bterraform\s+(apply|destroy)\b(?!.*-target)"),
        "zmiana infrastruktury bez zawężenia celu",
    ),
]

SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\n")


def segments(command: str) -> list[str]:
    """Dzieli polecenie na segmenty. Potoki zostają razem, bo `curl | sh`
    jest groźne właśnie jako całość."""
    return [part.strip() for part in SEGMENT_SPLIT.split(command) if part.strip()]


def evaluate_command(command: str) -> Verdict:
    """Ocenia polecenie powłoki. Czysta funkcja, testowalna bez Claude Code."""
    for segment in segments(command):
        for pattern, reason in RULES:
            if pattern.search(segment):
                return Verdict.block(
                    f"Zablokowane: {reason}.\n"
                    f"Polecenie: {segment}\n"
                    "To działanie wymaga decyzji człowieka. Opisz, co chcesz "
                    "zrobić i dlaczego, i poczekaj na zgodę."
                )
    return Verdict.allow()


def evaluate(event: dict) -> Verdict:
    if event.get("tool_name") != "Bash":
        return Verdict.allow()
    return evaluate_command(tool_text(event))


if __name__ == "__main__":
    sys.exit(run(evaluate))
