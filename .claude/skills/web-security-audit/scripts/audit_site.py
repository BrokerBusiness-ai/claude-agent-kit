"""Zewnętrzny audyt bezpieczeństwa strony WWW: nagłówki, TLS, wystawione zasoby.

Tylko pasywne sprawdzenia, takie same, jakie wykonuje przeglądarka: żądania
GET i HEAD do publicznych adresów, odczyt certyfikatu. Żadnego skanowania
portów, fuzzingu ani prób logowania.

Uruchamiaj wyłącznie wobec stron, do których masz uprawnienia.

Użycie:
    python audit_site.py https://example.com
    python audit_site.py https://example.com --json
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

USER_AGENT = "claude-agent-kit-audit/1.0 (+passive security check)"
TIMEOUT = 10

SEVERITY_ORDER = {"krytyczne": 0, "wysokie": 1, "średnie": 2, "niskie": 3, "info": 4}


@dataclass(frozen=True)
class Finding:
    """Pojedyncze ustalenie audytu."""

    check_id: str
    severity: str
    title: str
    detail: str
    fix: str


@dataclass
class Report:
    """Wynik audytu jednej strony."""

    url: str
    checked_at: str
    findings: list[Finding] = field(default_factory=list)

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))

    def score(self) -> int:
        """Prosta ocena 0-100: 100 minus kary za ustalenia."""
        penalty = {"krytyczne": 30, "wysokie": 15, "średnie": 7, "niskie": 3, "info": 0}
        total = sum(penalty.get(f.severity, 0) for f in self.findings)
        return max(0, 100 - total)


# ---------------------------------------------------------------------------
# Analiza nagłówków: czysta funkcja, testowalna bez sieci
# ---------------------------------------------------------------------------


def analyze_headers(headers: dict[str, str], is_https: bool) -> list[Finding]:
    """Ocenia nagłówki odpowiedzi HTTP. Nazwy nagłówków bez rozróżnienia wielkości liter."""
    h = {k.lower(): v for k, v in headers.items()}
    findings: list[Finding] = []

    if is_https:
        hsts = h.get("strict-transport-security", "")
        if not hsts:
            findings.append(
                Finding(
                    "hsts-missing",
                    "wysokie",
                    "Brak HSTS",
                    "Przeglądarka może połączyć się po HTTP i paść ofiarą ataku downgrade.",
                    "Strict-Transport-Security: max-age=31536000; includeSubDomains",
                )
            )
        else:
            max_age = _directive_int(hsts, "max-age")
            if max_age is not None and max_age < 15552000:
                findings.append(
                    Finding(
                        "hsts-short",
                        "niskie",
                        "HSTS z krótkim max-age",
                        f"max-age={max_age}, zalecane co najmniej 15552000 (180 dni).",
                        "Zwiększ max-age do 31536000.",
                    )
                )

    csp = h.get("content-security-policy", "")
    if not csp:
        findings.append(
            Finding(
                "csp-missing",
                "średnie",
                "Brak Content-Security-Policy",
                "Brak drugiej linii obrony przed XSS i wstrzykiwaniem skryptów.",
                "Zacznij od Content-Security-Policy-Report-Only i zawężaj źródła.",
            )
        )
    elif "'unsafe-inline'" in csp and "script-src" in csp:
        findings.append(
            Finding(
                "csp-unsafe-inline",
                "niskie",
                "CSP dopuszcza 'unsafe-inline' dla skryptów",
                "Polityka istnieje, ale nie blokuje wstrzykniętych skryptów inline.",
                "Zastąp 'unsafe-inline' nonce lub hashami.",
            )
        )

    frame_ok = h.get("x-frame-options") or "frame-ancestors" in csp
    if not frame_ok:
        findings.append(
            Finding(
                "clickjacking",
                "średnie",
                "Brak ochrony przed osadzaniem w ramce",
                "Strona może zostać osadzona w obcej ramce (clickjacking).",
                "X-Frame-Options: DENY lub CSP frame-ancestors 'none'.",
            )
        )

    if h.get("x-content-type-options", "").lower() != "nosniff":
        findings.append(
            Finding(
                "nosniff-missing",
                "niskie",
                "Brak X-Content-Type-Options: nosniff",
                "Przeglądarka może zgadywać typ treści i wykonać plik jako skrypt.",
                "X-Content-Type-Options: nosniff",
            )
        )

    if not h.get("referrer-policy"):
        findings.append(
            Finding(
                "referrer-missing",
                "niskie",
                "Brak Referrer-Policy",
                "Pełne adresy, także z parametrami, mogą wyciekać do stron trzecich.",
                "Referrer-Policy: strict-origin-when-cross-origin",
            )
        )

    if not h.get("permissions-policy"):
        findings.append(
            Finding(
                "permissions-missing",
                "info",
                "Brak Permissions-Policy",
                "Nie ograniczono dostępu do kamery, mikrofonu i geolokalizacji.",
                "Permissions-Policy: camera=(), microphone=(), geolocation=()",
            )
        )

    for name in ("server", "x-powered-by", "x-aspnet-version", "x-generator"):
        value = h.get(name, "")
        if value and any(ch.isdigit() for ch in value):
            findings.append(
                Finding(
                    f"disclosure-{name}",
                    "niskie",
                    f"Ujawniona wersja oprogramowania ({name})",
                    f"{name}: {value}. Ułatwia dopasowanie znanych podatności.",
                    f"Usuń nagłówek {name} albo wartość wersji.",
                )
            )

    cookies = [v for k, v in headers.items() if k.lower() == "set-cookie"]
    for cookie in cookies:
        cookie_name = cookie.split("=", 1)[0].strip()
        lower = cookie.lower()
        missing = [flag for flag in ("secure", "httponly", "samesite") if flag not in lower]
        if is_https and missing:
            findings.append(
                Finding(
                    f"cookie-{cookie_name}",
                    "średnie",
                    f"Ciasteczko {cookie_name} bez flag",
                    f"Brakuje: {', '.join(missing)}.",
                    "Ustaw Secure; HttpOnly; SameSite=Lax (lub Strict).",
                )
            )

    return findings


def _directive_int(header_value: str, directive: str) -> int | None:
    for part in header_value.split(";"):
        key, _, value = part.strip().partition("=")
        if key.lower() == directive:
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None


# ---------------------------------------------------------------------------
# Ocena certyfikatu: czysta funkcja na danych z ssl.getpeercert()
# ---------------------------------------------------------------------------


def analyze_certificate(cert: dict, now: datetime | None = None) -> list[Finding]:
    """Ocenia certyfikat TLS na podstawie słownika z ssl.getpeercert()."""
    now = now or datetime.now(timezone.utc)
    not_after = cert.get("notAfter")
    if not not_after:
        return [Finding("tls-unknown", "info", "Nie odczytano daty ważności certyfikatu", "", "")]
    expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    days = (expires - now).days
    if days < 0:
        return [
            Finding(
                "tls-expired",
                "krytyczne",
                "Certyfikat wygasł",
                f"Wygasł {-days} dni temu.",
                "Odnów certyfikat natychmiast.",
            )
        ]
    if days < 14:
        return [
            Finding(
                "tls-expiring",
                "wysokie",
                "Certyfikat wkrótce wygaśnie",
                f"Zostało {days} dni.",
                "Sprawdź automatyczne odnawianie (np. certbot).",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Wystawione zasoby: lista ścieżek, które nie powinny być publiczne
# ---------------------------------------------------------------------------

SENSITIVE_PATHS: list[tuple[str, str, str]] = [
    ("/.git/HEAD", "krytyczne", "Publiczne repozytorium .git pozwala pobrać kod źródłowy."),
    ("/.env", "krytyczne", "Plik .env zwykle zawiera hasła do bazy i klucze API."),
    ("/wp-json/wp/v2/users", "średnie", "Publiczna lista użytkowników WordPress ułatwia atak na hasła."),
    ("/server-status", "średnie", "Status serwera Apache ujawnia ruch i adresy wewnętrzne."),
    ("/phpinfo.php", "wysokie", "phpinfo ujawnia konfigurację, ścieżki i wersje."),
    ("/backup.zip", "wysokie", "Kopia zapasowa dostępna publicznie."),
]


def exposed_path_finding(path: str, status: int, body_start: str) -> Finding | None:
    """Decyduje, czy odpowiedź dla wrażliwej ścieżki oznacza realne wystawienie."""
    if status != 200:
        return None
    for known, severity, why in SENSITIVE_PATHS:
        if known != path:
            continue
        # Ochrona przed fałszywym alarmem: wiele stron zwraca 200 ze stroną błędu.
        if path == "/.git/HEAD" and not body_start.startswith("ref:"):
            return None
        if path == "/.env" and "=" not in body_start:
            return None
        if path == "/wp-json/wp/v2/users" and not body_start.lstrip().startswith("["):
            return None
        return Finding(
            f"exposed{path}",
            severity,
            f"Publicznie dostępne: {path}",
            why,
            "Zablokuj dostęp w konfiguracji serwera (nginx: location ... { deny all; }).",
        )
    return None


# ---------------------------------------------------------------------------
# Warstwa sieciowa
# ---------------------------------------------------------------------------


def fetch(url: str, method: str = "GET", limit: int = 512) -> tuple[int, dict[str, str], str]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read(limit).decode("utf-8", errors="replace") if method == "GET" else ""
            return response.status, _header_dict(response.headers), body
    except urllib.error.HTTPError as err:
        return err.code, _header_dict(err.headers), ""


def _header_dict(headers) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        result[key] = f"{result[key]}, {value}" if key in result and key.lower() != "set-cookie" else value
    return result


def get_certificate(host: str, port: int = 443) -> dict:
    context = ssl.create_default_context()
    with (
        socket.create_connection((host, port), timeout=TIMEOUT) as sock,
        context.wrap_socket(sock, server_hostname=host) as tls,
    ):
        return tls.getpeercert()


def audit(url: str) -> Report:
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    report = Report(url=url, checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))

    _, headers, _ = fetch(url)
    report.findings.extend(analyze_headers(headers, is_https))

    if is_https:
        try:
            report.findings.extend(analyze_certificate(get_certificate(parsed.hostname)))
        except (OSError, ssl.SSLError) as err:
            report.findings.append(
                Finding(
                    "tls-error",
                    "wysokie",
                    "Błąd połączenia TLS",
                    str(err),
                    "Sprawdź łańcuch certyfikatów i konfigurację serwera.",
                )
            )
    else:
        report.findings.append(
            Finding(
                "no-https",
                "krytyczne",
                "Strona bez HTTPS",
                "Dane przesyłane są otwartym tekstem.",
                "Włącz TLS i przekierowanie 301 z HTTP na HTTPS.",
            )
        )

    for path, _, _ in SENSITIVE_PATHS:
        try:
            status, _, body = fetch(urljoin(url, path))
        except (OSError, urllib.error.URLError):
            continue
        finding = exposed_path_finding(path, status, body)
        if finding:
            report.findings.append(finding)

    return report


def to_markdown(report: Report) -> str:
    lines = [
        f"# Audyt: {report.url}",
        f"Data: {report.checked_at} · Ocena: **{report.score()}/100** · Ustaleń: {len(report.findings)}",
        "",
        "| Waga | Problem | Szczegóły | Naprawa |",
        "|---|---|---|---|",
    ]
    for f in report.sorted_findings():
        lines.append(f"| {f.severity} | {f.title} | {f.detail} | {f.fix} |")
    if not report.findings:
        lines.append("| - | Brak ustaleń | | |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pasywny audyt bezpieczeństwa strony WWW.")
    parser.add_argument("url")
    parser.add_argument("--json", action="store_true", help="wynik w formacie JSON")
    args = parser.parse_args(argv)

    report = audit(args.url)
    if args.json:
        payload = {
            "url": report.url,
            "checked_at": report.checked_at,
            "score": report.score(),
            "findings": [asdict(f) for f in report.sorted_findings()],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
