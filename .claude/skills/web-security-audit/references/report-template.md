# Szablon raportu dla klienta

```markdown
# Raport bezpieczeństwa: {domena}

Data: {data} · Zakres: audyt pasywny z zewnątrz · Ocena: {wynik}/100

## Do zrobienia dziś
1. {najpoważniejsze ustalenie, jednym zdaniem, z poprawką}
2. ...
3. ...

## Wszystkie ustalenia
{tabela z audit_site.py}

## Czego ten audyt nie obejmuje
Audyt pasywny nie testuje logiki aplikacji, haseł ani podatności wymagających
aktywnych prób. Wysoka ocena nie oznacza, że strona jest odporna na włamanie.

## Następny krok
{jedna rekomendacja: np. test penetracyjny formularzy, przegląd wtyczek}
```

Zasady:
- Język klienta, nie żargon. „Przeglądarka może połączyć się bez szyfrowania” zamiast „brak HSTS”.
- Bez wartości haseł, kluczy i danych osobowych, nawet jeśli audyt je zobaczył.
- Każde ustalenie ma właściciela naprawy: hosting, administrator WordPress, programista.
