# claude-agent-kit

Konfiguracja Claude Code do pracy produkcyjnej: agent, który ma realne uprawnienia, ale nie może zrobić rzeczy nieodwracalnej bez człowieka.

![CI](https://github.com/BrokerBusiness-ai/claude-agent-kit/actions/workflows/ci.yml/badge.svg)

> **English summary.** A production-grade Claude Code setup: deterministic safety hooks (dangerous shell commands, secret leaks, typography), least-privilege subagents, and three skills backed by tested Python scripts (action approval protocol, passive web security audit, GDPR record-of-processing validator). 76 unit tests, an eval suite with precision/recall reporting, CI on Python 3.10 to 3.13. Zero runtime dependencies.

## Co jest w środku

| Element | Plik | Co robi |
|---|---|---|
| Hook | `.claude/hooks/guard_bash.py` | blokuje `rm -rf /`, `git push --force`, `curl \| sh`, `DROP TABLE`, `DELETE` bez `WHERE`, publikację pakietów i 10 innych wzorców |
| Hook | `.claude/hooks/secret_scan.py` | blokuje zapis kluczy API (Anthropic, OpenAI, GitHub, AWS, Slack, Google), kluczy prywatnych i haseł o wysokiej entropii; ignoruje placeholdery i `${ZMIENNE}` |
| Hook | `.claude/hooks/style_check.py` | po zapisie dokumentacji zgłasza zakazane znaki typograficzne z numerem linii |
| Uprawnienia | `.claude/settings.json` | allow / ask / deny: testy bez pytania, commit i push z pytaniem, `.env` i `sudo` zablokowane |
| Subagent | `.claude/agents/verifier.md` | bramka „gotowe”: lint, testy, ewaluacje, jednoznaczny werdykt |
| Subagent | `.claude/agents/code-reviewer.md` | przegląd bez prawa zapisu |
| Subagent | `.claude/agents/researcher.md` | tani research na Haiku, tylko odczyt |
| Skill | `.claude/skills/action-guard/` | protokół zgody: klasy działań A/B/C, słowa wykonawcze, raport na końcu zadania |
| Skill | `.claude/skills/web-security-audit/` | pasywny audyt strony: nagłówki, ciasteczka, TLS, wystawione `.git` i `.env`, raport z oceną |
| Skill | `.claude/skills/gdpr-doc-validator/` | walidacja rejestru czynności przetwarzania (art. 30 RODO): podstawy prawne, art. 9, transfery, DPIA wg WP248, umowy powierzenia |
| MCP | `.mcp.json` | serwer GitHub, token tylko ze zmiennej środowiskowej |

## Dlaczego tak

Same instrukcje w promptcie to prośba, nie gwarancja. Ten zestaw łączy trzy warstwy: instrukcje mówią modelowi, co ma robić, uprawnienia każą pytać człowieka o całe kategorie narzędzi, a hooki deterministycznie blokują konkretne wywołania. Szczegóły: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Szybki start

```bash
git clone https://github.com/BrokerBusiness-ai/claude-agent-kit.git
cd claude-agent-kit
pip install -e ".[dev]"
pytest -q                                   # 76 testów
python evals/run_evals.py --min-f1 0.95     # ewaluacje hooków
```

Użycie we własnym projekcie: skopiuj katalog `.claude/` (i opcjonalnie `CLAUDE.md`) do korzenia repozytorium. Claude Code wczyta hooki, agentów i skille przy następnym uruchomieniu.

## Przykłady

**Hook zatrzymuje wymuszony push:**

```bash
$ echo '{"tool_name":"Bash","tool_input":{"command":"pytest && git push --force"}}' \
    | python .claude/hooks/guard_bash.py
Zablokowane: wymuszony push nadpisuje historię zdalnego repozytorium.
Polecenie: git push --force
To działanie wymaga decyzji człowieka. Opisz, co chcesz zrobić i dlaczego, i poczekaj na zgodę.
$ echo $?
2
```

**Walidator rejestru RODO na przykładowych danych:**

```bash
$ python .claude/skills/gdpr-doc-validator/scripts/validate_ropa.py \
    .claude/skills/gdpr-doc-validator/examples/ropa_example.json
```

Wykrywa m.in.: przekazanie danych do USA bez mechanizmu (art. 44-49), dostawcę bez umowy powierzenia (art. 28), dane o zdrowiu bez przesłanki z art. 9 ust. 2 oraz system AI przetwarzający dane pacjentów bez oceny skutków (art. 35, dwa kryteria WP248).

**Audyt nagłówków bezpieczeństwa:**

```bash
$ python .claude/skills/web-security-audit/scripts/audit_site.py https://example.com
```

Wynik to tabela ustaleń z wagą i gotową poprawką (konfiguracje nginx w `references/headers.md`).

## Ewaluacje

| Hook | Przypadki | Precyzja | Czułość | F1 |
|---|---|---|---|---|
| guard_bash | 30 | 1.00 | 1.00 | 1.00 |
| secret_scan | 15 | 1.00 | 1.00 | 1.00 |

Dwie realne luki znalezione w trakcie budowy, obie zostały jako testy regresji:

1. **Ewaluacje:** pierwsze uruchomienie dało czułość 0.93 dla `guard_bash`, bo `TRUNCATE orders` bez słowa `TABLE` (poprawne w PostgreSQL) przechodziło.
2. **Test procesu na Windows:** PowerShell dokleja BOM do potoku. JSON się nie parsował, hook działający w trybie fail open przepuszczał wszystko, a testy jednostkowe tego nie widziały, bo nie przechodzą przez stdin. Teraz `hooklib` usuwa BOM, a CI uruchamia hooki jako prawdziwe procesy.

## Ograniczenia

- Hook analizuje tekst polecenia, nie jego semantykę. Celowo zaciemnione polecenie (np. przez zmienne lub `eval`) może przejść. Hooki chronią przed pomyłką agenta, nie przed atakującym z dostępem do powłoki.
- Audyt WWW jest pasywny. Nie zastępuje testu penetracyjnego.
- Walidator RODO sprawdza kompletność formalną, nie zgodność z prawem.

## Licencja

MIT
