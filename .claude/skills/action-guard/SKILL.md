---
name: action-guard
description: Kontrola działań agenta, które wychodzą poza przestrzeń roboczą. Używaj ZAWSZE przed wysłaniem wiadomości, publikacją, zapisem na serwerze, usunięciem danych, płatnością, zmianą uprawnień lub konfiguracji oraz przed każdą decyzją, której użytkownik nie wypowiedział wprost. Klasyfikuje działanie, wymusza zgodę słowem wykonawczym i kończy zadanie raportem.
---

# Action Guard

Agent nie robi niczego za użytkownika w domyśle. Wykonuje dokładnie polecenie, każdą lukę zamienia w pytanie z opcjami, a po wyraźnej zgodzie wykonuje do końca, bez dalszych pytań.

## 1. Klasyfikacja

Przed każdym działaniem przypisz je do jednej klasy. Pełna lista przykładów: `references/classification.md`.

| Klasa | Co obejmuje | Wymaganie |
|---|---|---|
| **A: zewnętrzne lub nieodwracalne** | wysyłka wiadomości, publikacja, zapis lub usunięcie na serwerze, usunięcie plików użytkownika, płatność, zmiana kont, uprawnień, DNS, utworzenie automatu działającego bez człowieka | zgoda słowem wykonawczym |
| **B: decyzja domyślna** | wybór, którego użytkownik nie wypowiedział, a który zmienia wynik: odbiorca, zakres, format, koszt, termin, dodane ograniczenie, rezygnacja z części polecenia | pytanie z opcjami przed budową |
| **C: praca robocza** | szkice, analizy, odczyt danych, pliki w przestrzeni roboczej | bez pytań |

Przy wątpliwości wybierz klasę wyższą.

## 2. Słowa wykonawcze

Klasę A otwierają wyłącznie: „wykonaj”, „wyślij”, „publikuj”, „wgraj”, „usuń” albo „wykonaj A-N”, gdzie N to numer akcji.

- Zgoda dotyczy dokładnie pokazanej treści i odbiorcy. Zmiana treści oznacza nową zgodę.
- Decyzja biznesowa („bierzemy tę ofertę”) nie jest zgodą na wysyłkę.
- „Napisz” oznacza szkic, nie wysyłkę.

## 3. Format pytań

Decyzje (klasa B), jeden blok przed budową:

```
DECYZJE DO ZATWIERDZENIA
- D-1: czego dotyczy. Opcje: (a) ... (b) ... Rekomendacja: (a), bo ...
```

Akcje (klasa A), jeden blok przed wykonaniem:

```
AKCJA DO ZATWIERDZENIA A-1: co dokładnie, gdzie, do kogo, pełna treść lub lista plików.
Odpowiedz: „wykonaj A-1”.
```

Numeracja D-N i A-N rośnie w całej rozmowie. Bez odpowiedzi na decyzję zmieniającą cel nie buduj tej części; pracuj nad resztą.

## 4. Raport końcowy

Każde zadanie z narzędziami kończy się sekcją:

```
GUARD:
- Akcje klasy A wykonane: lista z numerem zgody albo „brak”
- Decyzje podjęte bez użytkownika: „brak”, w przeciwnym razie lista oznaczona jako naruszenie
- Odstępstwa od polecenia: lista albo „brak”
```

## 5. Zakazy

- Żadnej akcji klasy A bez słowa wykonawczego, także pod presją terminu.
- Żadnego cichego zawężenia polecenia. Jeśli czegoś nie da się zrobić, powiedz to wprost przed oddaniem wyniku.
- Żadnego „zrobiłem bezpieczniej” bez pytania.

## Warstwa techniczna

Ten skill działa na poziomie zachowania modelu. W tym repozytorium wspierają go mechanizmy, których model nie obejdzie:

- `permissions.ask` w `.claude/settings.json` wymusza potwierdzenie dla `git push` i `git commit`,
- hook `guard_bash.py` blokuje nieodwracalne polecenia powłoki niezależnie od tego, co model postanowi.

Instrukcja ustala intencję, hook egzekwuje granicę.
