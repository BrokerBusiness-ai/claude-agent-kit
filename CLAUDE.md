# CLAUDE.md

Instrukcje dla Claude Code pracującego w tym repozytorium.

## Czym jest projekt

Zestaw konfiguracji Claude Code: hooki bezpieczeństwa (`.claude/hooks/`), subagenci (`.claude/agents/`), skille (`.claude/skills/`), testy i ewaluacje. Kod jest czystym Pythonem 3.10+ bez zależności runtime.

## Polecenia

| Cel | Polecenie |
|---|---|
| Testy | `pytest -q` |
| Lint | `ruff check . && ruff format --check .` |
| Ewaluacje hooków | `python evals/run_evals.py --min-f1 0.95` |
| Audyt strony | `python .claude/skills/web-security-audit/scripts/audit_site.py <url>` |
| Walidacja RCP | `python .claude/skills/gdpr-doc-validator/scripts/validate_ropa.py <plik.json>` |

## Zasady pracy

1. **Najpierw test, potem zmiana reguły.** Każda nowa reguła hooka dostaje przypadek pozytywny i negatywny w `tests/` oraz w `evals/cases/`.
2. **Logika w czystych funkcjach.** Hook czyta stdin tylko przez `hooklib.run`; decyzja zapada w funkcji `evaluate(event) -> Verdict`, którą da się przetestować bez Claude Code.
3. **Fail open w hookach.** Wyjątek w hooku nie może zablokować sesji. Blokada tylko przez jawny `Verdict.block(powód)`.
4. **Powód blokady mówi, co zrobić zamiast.** Agent czyta stderr i ma z niego wiedzieć, jak kontynuować.
5. **Bez prawdziwych sekretów, także w testach.** Fałszywe klucze składaj z kawałków (patrz `tests/test_secret_scan.py`), żeby nie uruchamiać skanera GitHuba.
6. **Typografia w dokumentacji:** bez półpauzy i pauzy (U+2013, U+2014). Pilnuje tego hook `style_check.py`.

## Zanim powiesz „gotowe”

Uruchom subagenta `verifier`. Zadanie jest skończone dopiero, gdy zwróci `WERDYKT: OK`.

## Działania wymagające zgody

`git push`, publikacja pakietu, wysyłka czegokolwiek na zewnątrz: zgodnie ze skillem `action-guard`, tylko po słowie wykonawczym użytkownika.
