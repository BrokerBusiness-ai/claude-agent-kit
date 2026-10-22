"""Wspólna warstwa dla hooków Claude Code.

Hook dostaje na stdin JSON opisujący zdarzenie (nazwa narzędzia, jego wejście,
katalog projektu). Kod wyjścia steruje zachowaniem:

- 0: przepuść,
- 2: zablokuj; treść ze stderr trafia do agenta jako informacja zwrotna.

Logika decyzyjna jest w czystych funkcjach, żeby dało się ją testować bez
uruchamiania Claude Code. Ten moduł tylko czyta zdarzenie i zamienia werdykt
na kod wyjścia.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

ALLOW = 0
BLOCK = 2


@dataclass(frozen=True)
class Verdict:
    """Wynik oceny zdarzenia przez hook."""

    allowed: bool
    reason: str = ""

    @classmethod
    def allow(cls) -> Verdict:
        return cls(True)

    @classmethod
    def block(cls, reason: str) -> Verdict:
        return cls(False, reason)


def read_event(stream: Any = None) -> dict[str, Any]:
    """Czyta zdarzenie hooka. Pusty lub uszkodzony JSON daje pusty słownik."""
    stream = stream or sys.stdin
    raw = stream.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    # Windows PowerShell potrafi dokleić BOM do potoku; bez tego JSON by się nie
    # sparsował, a hook po cichu przepuściłby wszystko.
    raw = raw.lstrip("﻿")
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def run(evaluate: Callable[[dict[str, Any]], Verdict], stream: Any = None) -> int:
    """Uruchamia ocenę i zwraca kod wyjścia zgodny z protokołem hooków.

    Błąd w samym hooku nie blokuje pracy agenta (fail open), ale jest
    raportowany na stderr.
    """
    try:
        verdict = evaluate(read_event(stream))
    except Exception as exc:
        print(f"[hook] błąd wewnętrzny: {exc}", file=sys.stderr)
        return ALLOW
    if verdict.allowed:
        return ALLOW
    print(verdict.reason, file=sys.stderr)
    return BLOCK


def tool_text(event: dict[str, Any]) -> str:
    """Zwraca treść, którą narzędzie zapisze lub wykona.

    Obsługuje Write (content), Edit (new_string), MultiEdit (edits) i Bash
    (command).
    """
    tool_input = event.get("tool_input") or {}
    parts: list[str] = []
    for key in ("content", "new_string", "command"):
        value = tool_input.get(key)
        if isinstance(value, str):
            parts.append(value)
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return "\n".join(parts)
