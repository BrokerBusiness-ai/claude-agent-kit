---
name: gdpr-doc-validator
description: Walidacja dokumentacji RODO, przede wszystkim rejestru czynności przetwarzania (art. 30). Używaj, gdy użytkownik przekazuje RCP do sprawdzenia, pyta „czy mój rejestr jest kompletny”, „czy potrzebuję DPIA”, „czego brakuje w dokumentacji RODO”, albo konwertuje rejestr z arkusza do JSON. Wskazuje braki z numerem przepisu; nie wydaje opinii prawnej.
---

# GDPR Doc Validator

Deterministyczna walidacja formalna rejestru czynności przetwarzania. Model nie ocenia „na oko”: skrypt sprawdza reguły, model tłumaczy wynik na język użytkownika i proponuje uzupełnienia.

## Procedura

1. **Doprowadź rejestr do formatu JSON** według `examples/ropa_example.json`. Jeśli użytkownik ma arkusz, zmapuj kolumny na pola i pokaż mapowanie przed konwersją. Brakujących wartości nie wymyślaj: zostaw pole puste, walidator je zgłosi.
2. **Uruchom walidator:**
   ```bash
   python .claude/skills/gdpr-doc-validator/scripts/validate_ropa.py rejestr.json
   ```
   Kod wyjścia 1 oznacza co najmniej jeden błąd.
3. **Przedstaw wynik** w kolejności: błędy (z przepisem), ostrzeżenia, następnie trzy najpilniejsze uzupełnienia.
4. **Do każdego błędu dopisz, kto ma dostarczyć informację** (dział HR, IT, dostawca) i jakie pytanie mu zadać.
5. **Nie twórz brakujących dokumentów bez polecenia.** Jeśli brakuje DPIA lub umowy powierzenia, zaproponuj przygotowanie projektu jako osobne zadanie.

## Reguły walidatora

Pełny opis z podstawą prawną: `references/rules.md`. W skrócie:

| Reguła | Przepis | Poziom |
|---|---|---|
| Komplet pól rejestru | art. 30 ust. 1 | błąd |
| Podstawa prawna z katalogu art. 6 ust. 1 | art. 6 | błąd |
| Uzasadniony interes bez testu równowagi | art. 6 ust. 1 lit. f | ostrzeżenie |
| Zgoda bez sposobu jej wykazania | art. 7 ust. 1 | ostrzeżenie |
| Dane szczególnych kategorii bez przesłanki z art. 9 ust. 2 | art. 9 | błąd |
| Nieokreślony okres przechowywania | art. 5 ust. 1 lit. e | ostrzeżenie |
| Przekazanie poza EOG bez mechanizmu | art. 44-49 | błąd |
| Co najmniej 2 kryteria WP248 bez DPIA | art. 35 | błąd |
| Podmiot przetwarzający bez umowy powierzenia | art. 28 ust. 3 | błąd |

## Granice

Walidator sprawdza kompletność i spójność, nie legalność. Poprawny formalnie rejestr może opisywać przetwarzanie niezgodne z prawem. Zawsze zaznacz to w podsumowaniu jednym zdaniem.
