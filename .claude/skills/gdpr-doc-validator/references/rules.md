# Reguły walidacji z podstawą prawną

## 1. Komplet pól (art. 30 ust. 1)

Rejestr administratora zawiera: nazwę i dane kontaktowe administratora (lit. a), cele (lit. b), kategorie osób i danych (lit. c), kategorie odbiorców (lit. d), przekazania do państw trzecich (lit. e), planowane terminy usunięcia (lit. f), ogólny opis środków bezpieczeństwa (lit. g). Lit. f i g mają w przepisie zastrzeżenie „jeżeli jest to możliwe”, ale w praktyce organu nadzorczego brak tych pól jest typowym zarzutem, dlatego walidator traktuje je jako wymagane.

Podstawa prawna nie jest wymieniona w art. 30, ale bez niej nie da się wykazać zgodności (zasada rozliczalności, art. 5 ust. 2). Walidator wymaga jej jako pola.

## 2. Podstawa prawna (art. 6 ust. 1)

Dopuszczalne wartości: `6.1.a` zgoda, `6.1.b` umowa, `6.1.c` obowiązek prawny, `6.1.d` żywotne interesy, `6.1.e` zadanie publiczne, `6.1.f` uzasadniony interes.

- `6.1.f` wymaga udokumentowanego testu równowagi (pole `legitimate_interest_test`).
- `6.1.a` wymaga opisu, jak administrator wykazuje zgodę (pole `consent_record`, art. 7 ust. 1).

## 3. Dane szczególnych kategorii (art. 9)

Jeśli `data_categories` zawiera kategorię z art. 9 ust. 1, czynność musi mieć pole `art9_condition` z wartością `9.2.a` do `9.2.j`. Podstawa z art. 6 nie wystarcza.

## 4. Okres przechowywania (art. 5 ust. 1 lit. e)

Wartości „bezterminowo”, „do odwołania”, „zgodnie z przepisami” są ostrzeżeniem: zasada ograniczenia przechowywania wymaga terminu lub kryterium jego ustalenia, np. „6 lat od końca roku podatkowego (art. 86 Ordynacji podatkowej)”.

## 5. Przekazanie poza EOG (rozdział V, art. 44-49)

Każde przekazanie wymaga mechanizmu: decyzja stwierdzająca odpowiedni stopień ochrony (art. 45, w tym EU-US Data Privacy Framework dla certyfikowanych odbiorców), standardowe klauzule umowne SCC (art. 46), wiążące reguły korporacyjne BCR (art. 47) albo wyjątek z art. 49.

## 6. Ocena skutków (art. 35, wytyczne WP248 rev.01)

Wytyczne wskazują dziewięć kryteriów. Spełnienie co najmniej dwóch zwykle oznacza obowiązek DPIA. Walidator automatycznie dolicza kryterium „dane wrażliwe”, gdy czynność obejmuje kategorie z art. 9. Pozostałe kryteria wskazuje się w polu `dpia_criteria`:

`evaluation_scoring`, `automated_decision`, `systematic_monitoring`, `sensitive_data`, `large_scale`, `matching_datasets`, `vulnerable_subjects`, `innovative_technology`, `prevents_rights`.

Uwaga praktyczna: krajowe organy nadzorcze publikują własne wykazy operacji wymagających DPIA (w Polsce komunikat Prezesa UODO). Walidator ich nie koduje; sprawdź je ręcznie przy wątpliwości.

## 7. Umowa powierzenia (art. 28 ust. 3)

Każdy podmiot w polu `processors` musi mieć `dpa_signed: true`.

## Czego walidator nie sprawdza

Legalności celu, proporcjonalności, jakości klauzul informacyjnych, faktycznego wdrożenia środków bezpieczeństwa. To zadania dla człowieka z uprawnieniami (IOD, prawnik).
