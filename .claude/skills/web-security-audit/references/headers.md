# Nagłówki bezpieczeństwa: interpretacja i konfiguracja

## Zestaw minimalny (nginx)

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
server_tokens off;
```

`always` sprawia, że nagłówki trafiają także do odpowiedzi z błędem (4xx, 5xx).

## Content-Security-Policy: wdrażanie bez psucia strony

1. Zacznij od trybu raportowania:
   `Content-Security-Policy-Report-Only: default-src 'self'; report-uri /csp-report`
2. Zbierz naruszenia przez tydzień i dopisz faktycznie używane źródła.
3. Przełącz na `Content-Security-Policy`.
4. Zastąp `'unsafe-inline'` nonce generowanym per żądanie.

## Wystawione zasoby: blokada w nginx

```nginx
location ~ /\.(git|env|svn|hg) { deny all; return 404; }
location = /phpinfo.php { deny all; return 404; }
location ~* \.(zip|tar|gz|sql|bak)$ { deny all; return 404; }
```

## WordPress: lista użytkowników przez REST API

Endpoint `/wp-json/wp/v2/users` jest domyślnie publiczny i zwraca loginy (pole `slug`). Ogranicz go do zalogowanych użytkowników filtrem `rest_endpoints` albo regułą serwera. Nie wyłączaj całego REST API, bo zepsuje to edytor blokowy.

## Skala wag

| Waga | Znaczenie | Termin naprawy |
|---|---|---|
| krytyczne | bezpośredni wyciek danych lub kodu | dziś |
| wysokie | realny wektor ataku przy niskim koszcie | w tym tygodniu |
| średnie | osłabienie obrony | w tym miesiącu |
| niskie | dobra praktyka, mały wpływ | przy okazji |
| info | do rozważenia | bez terminu |
