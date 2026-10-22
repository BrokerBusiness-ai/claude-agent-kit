# Architektura

## Warstwy kontroli

Agent ma trzy niezależne warstwy, od najmiękkiej do najtwardszej:

```
  instrukcje         CLAUDE.md, skille          model WIE, co ma robić
       │
  uprawnienia        settings.json allow/ask    harness PYTA człowieka
       │
  hooki              PreToolUse / PostToolUse   kod BLOKUJE deterministycznie
```

Instrukcje model może źle zrozumieć. Uprawnienia działają na poziomie całego narzędzia (np. „każdy `git push` wymaga pytania”). Hooki widzą treść konkretnego wywołania i mogą odróżnić `git push origin feature` od `git push --force`. Każda warstwa łapie to, co przepuściła poprzednia.

## Przepływ zdarzenia przez hook

```
Claude Code ──stdin JSON──▶ hook.py ──▶ hooklib.run(evaluate)
                                            │
                                  evaluate(event) -> Verdict
                                            │
                    allowed ──▶ exit 0      │      blocked ──▶ exit 2 + powód na stderr
                                                                 │
                                          agent czyta powód i zmienia plan
```

Decyzje projektowe:

- **Czyste funkcje.** `evaluate` nie dotyka stdin, sieci ani dysku (wyjątek: `style_check` czyta zapisany plik, bo działa po zapisie). Dzięki temu 100% logiki jest pokryte testami jednostkowymi.
- **Fail open.** Wyjątek w hooku zwraca 0 i loguje błąd. Uszkodzony hook nie może zatrzymać pracy; od tego są testy i CI.
- **Segmentacja poleceń.** `guard_bash` dzieli polecenie po `&&`, `||`, `;` i nowych liniach, żeby `pytest && git push --force` nie przeszło dzięki niewinnemu początkowi.
- **Maskowanie sekretów.** `secret_scan` nigdy nie wypisuje pełnej wartości, którą zablokował: powód blokady trafia do kontekstu modelu i logów.

## Subagenci

| Agent | Model | Narzędzia | Rola |
|---|---|---|---|
| `verifier` | sonnet | Read, Grep, Glob, Bash | bramka „gotowe”: lint, testy, ewaluacje, werdykt |
| `code-reviewer` | sonnet | Read, Grep, Glob | przegląd zmian pod kątem błędów i bezpieczeństwa |
| `researcher` | haiku | Read, Grep, Glob, WebFetch, WebSearch | tani odczyt dokumentacji i kodu, bez zapisu |

Zasada: subagent dostaje minimum narzędzi potrzebne do roli. Reviewer nie ma Bash, więc nie „naprawi” niczego po cichu.

## Skille

Każdy skill ma ten sam układ:

```
skill/
  SKILL.md        kiedy używać, procedura, granice
  scripts/        deterministyczna logika (testowana)
  references/     wiedza ładowana tylko wtedy, gdy potrzebna
  examples/       dane wejściowe do demonstracji i testów
```

Model decyduje, CO zrobić; skrypt robi to, co musi być powtarzalne. Walidacja rejestru RODO czy ocena nagłówków HTTP nie powinny zależeć od tego, jak model „czuje” dany przypadek.

## Ewaluacje a testy

Testy (`tests/`) sprawdzają reguły pojedynczo. Ewaluacje (`evals/`) mierzą zachowanie na mieszance realistycznych poleceń i raportują precyzję i czułość. CI wymaga F1 co najmniej 0.95. Pierwsze uruchomienie ewaluacji wykryło realną lukę: `TRUNCATE orders` (bez słowa `TABLE`, poprawne w PostgreSQL) przechodziło przez strażnika. Reguła została poprawiona, przypadek został w zestawie jako test regresji.
