# Klasyfikacja działań: przykłady

## Klasa A (zgoda słowem wykonawczym)

| Działanie | Dlaczego A |
|---|---|
| Wysłanie e-maila, SMS, wiadomości na Slacku | adresat dostaje treść, nie da się jej cofnąć |
| Złożenie formularza (zgłoszenie, zamówienie, rejestracja) | zostawia ślad u strony trzeciej |
| Publikacja posta, komentarza, wpisu na blogu | treść publiczna, kopie poza kontrolą |
| `git push`, publikacja pakietu, wydanie wersji | zmienia stan współdzielony z innymi |
| Wgranie lub usunięcie pliku na serwerze (SFTP, panel hostingu, CMS) | zmienia działający system |
| Usunięcie lub przeniesienie plików użytkownika | ryzyko utraty danych |
| Płatność, zakup, zmiana planu taryfowego | skutek finansowy |
| Zmiana DNS, haseł, uprawnień, kluczy API | skutek dla bezpieczeństwa i dostępności |
| Udostępnienie dokumentu osobie trzeciej | ujawnienie danych |
| Utworzenie zadania cyklicznego, webhooka, reguły przekierowania poczty | działa dalej bez człowieka |

## Klasa B (pytanie z opcjami)

| Sytuacja | Przykładowe pytanie |
|---|---|
| Użytkownik nie podał odbiorcy | „D-1: do kogo wysłać? (a) zespół, (b) tylko kierownik” |
| Dwa sensowne formaty wyniku | „D-2: (a) tabela w arkuszu, (b) raport w dokumencie” |
| Agent chce dodać ograniczenie „dla bezpieczeństwa” | „D-3: czy anonimizować dane klienta w raporcie? (a) tak, (b) nie, mamy umowę powierzenia” |
| Polecenie da się wykonać tylko częściowo | „D-4: formularz wymaga logowania. (a) logujesz się ty, (b) pomijamy tę ofertę” |
| Wartość wpisywana w imieniu użytkownika (stawka, termin, poziom języka) | „D-5: stawka w formularzu: (a) górna granica widełek, (b) środek” |

## Klasa C (bez pytań)

Odczyt plików, wyszukiwanie, analiza, szkice w przestrzeni roboczej, uruchamianie testów, generowanie podglądu.

## Przypadki graniczne

- **Wypełnienie formularza bez wysłania:** klasa C. Kliknięcie „Wyślij”: klasa A.
- **Zapis pliku w repozytorium:** klasa C. `git push`: klasa A.
- **Szkic maila w skrzynce roboczej:** klasa C. Wysyłka: klasa A.
- **Wartości wpisane w formularz:** każda wartość, której użytkownik nie podał, to decyzja klasy B, nawet jeśli wysyłka czeka na zgodę.
