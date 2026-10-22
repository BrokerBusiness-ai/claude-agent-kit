---
name: web-security-audit
description: Pasywny audyt bezpieczeństwa strony WWW z zewnątrz. Używaj, gdy użytkownik pyta „czy moja strona jest bezpieczna”, prosi o sprawdzenie nagłówków, certyfikatu, wycieku plików .git lub .env, albo przygotowuje raport bezpieczeństwa dla klienta. Tylko dla stron, do których użytkownik ma uprawnienia.
---

# Web Security Audit

Audyt z zewnątrz, takimi samymi żądaniami, jakie wysyła przeglądarka. Bez skanowania portów, fuzzingu i prób logowania. Wynik: raport z oceną, priorytetami i konkretną poprawką do każdego ustalenia.

## Kiedy NIE używać

- Strona nie należy do użytkownika i nie ma pisemnej zgody właściciela. Zapytaj o to wprost, zanim cokolwiek uruchomisz.
- Użytkownik prosi o testy aktywne (próby logowania, fuzzing, skanowanie portów). To inny zakres i inna zgoda.

## Procedura

1. **Potwierdź zakres:** adres i to, że użytkownik ma prawo do testu.
2. **Uruchom skrypt:**
   ```bash
   python .claude/skills/web-security-audit/scripts/audit_site.py https://example.com
   ```
   Dla dalszej obróbki: dodaj `--json`.
3. **Zweryfikuj ustalenia krytyczne ręcznie,** zanim je zgłosisz. Skrypt odfiltrowuje typowe fałszywe alarmy (strona błędu zwracająca 200), ale wystawiony `.git` lub `.env` potwierdź jednym żądaniem i opisz, co faktycznie widać.
4. **Ułóż raport** według `references/report-template.md`: najpierw trzy rzeczy do zrobienia dziś, potem pełna tabela.
5. **Nie publikuj surowych danych:** jeśli w `.env` widać hasło, raport mówi „plik zawiera dane uwierzytelniające”, bez wartości.

## Co sprawdza skrypt

| Obszar | Kontrole |
|---|---|
| Nagłówki | HSTS (obecność i max-age), CSP (obecność, `unsafe-inline`), ochrona przed ramkami, `nosniff`, Referrer-Policy, Permissions-Policy, ujawnione wersje oprogramowania |
| Ciasteczka | flagi Secure, HttpOnly, SameSite |
| TLS | ważność certyfikatu, bliskie wygaśnięcie, błędy łańcucha |
| Wystawione zasoby | `.git/HEAD`, `.env`, lista użytkowników WordPress, `server-status`, `phpinfo.php`, `backup.zip` |

Interpretacja nagłówków i gotowe konfiguracje nginx: `references/headers.md`.

## Ograniczenia

Audyt pasywny nie wykryje podatności w logice aplikacji, SQL injection ani słabych haseł. W raporcie napisz to wprost, żeby klient nie odebrał wysokiej oceny jako certyfikatu bezpieczeństwa.
