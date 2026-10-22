"""Walidator rejestru czynności przetwarzania (RCP, art. 30 RODO).

Wejście: plik JSON z listą czynności (format w examples/ropa_example.json).
Wyjście: lista naruszeń z odwołaniem do przepisu i kod wyjścia 1, jeśli są błędy.

Walidator sprawdza kompletność i spójność formalną. Nie zastępuje oceny
prawnika ani inspektora ochrony danych: mówi, czego brakuje, a nie czy
przetwarzanie jest zgodne z prawem.

Użycie:
    python validate_ropa.py rejestr.json
    python validate_ropa.py rejestr.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_FIELDS: dict[str, str] = {
    "name": "nazwa czynności",
    "purpose": "cel przetwarzania (art. 30 ust. 1 lit. b)",
    "data_subjects": "kategorie osób (art. 30 ust. 1 lit. c)",
    "data_categories": "kategorie danych (art. 30 ust. 1 lit. c)",
    "recipients": "kategorie odbiorców (art. 30 ust. 1 lit. d)",
    "retention": "planowany termin usunięcia (art. 30 ust. 1 lit. f)",
    "security_measures": "opis środków bezpieczeństwa (art. 30 ust. 1 lit. g)",
    "legal_basis": "podstawa prawna (art. 6 ust. 1)",
}

ART6_BASES = {"6.1.a", "6.1.b", "6.1.c", "6.1.d", "6.1.e", "6.1.f"}
ART9_CONDITIONS = {f"9.2.{letter}" for letter in "abcdefghij"}

SPECIAL_CATEGORIES = {
    "zdrowie",
    "dane genetyczne",
    "dane biometryczne",
    "pochodzenie rasowe",
    "pochodzenie etniczne",
    "poglądy polityczne",
    "przekonania religijne",
    "światopogląd",
    "przynależność do związków zawodowych",
    "seksualność",
    "orientacja seksualna",
}

TRANSFER_MECHANISMS = {
    "decyzja stwierdzająca odpowiedni stopień ochrony",
    "SCC",
    "BCR",
    "art. 49",
    "EU-US Data Privacy Framework",
}

# Kryteria z wytycznych WP248 rev.01 (Grupa Robocza art. 29, przyjęte przez EROD).
DPIA_CRITERIA: dict[str, str] = {
    "evaluation_scoring": "ocena lub scoring, w tym profilowanie",
    "automated_decision": "zautomatyzowane decyzje o skutku prawnym",
    "systematic_monitoring": "systematyczne monitorowanie",
    "sensitive_data": "dane szczególnych kategorii lub wysoce osobiste",
    "large_scale": "przetwarzanie na dużą skalę",
    "matching_datasets": "łączenie lub zestawianie zbiorów danych",
    "vulnerable_subjects": "osoby wymagające szczególnej ochrony (dzieci, pacjenci, pracownicy)",
    "innovative_technology": "innowacyjne technologie (np. systemy AI)",
    "prevents_rights": "przetwarzanie uniemożliwiające korzystanie z prawa lub usługi",
}

VAGUE_RETENTION = {"", "bezterminowo", "do odwołania", "zgodnie z przepisami", "tbd", "?"}


@dataclass(frozen=True)
class Issue:
    """Pojedyncze naruszenie znalezione w rejestrze."""

    activity: str
    level: str  # "błąd" albo "ostrzeżenie"
    rule: str
    message: str


def validate_activity(activity: dict) -> list[Issue]:
    """Sprawdza jedną czynność przetwarzania."""
    name = str(activity.get("name") or "(bez nazwy)")
    issues: list[Issue] = []

    def add(level: str, rule: str, message: str) -> None:
        issues.append(Issue(name, level, rule, message))

    for key, label in REQUIRED_FIELDS.items():
        value = activity.get(key)
        if value in (None, "", []):
            add("błąd", "art. 30 ust. 1", f"brak pola: {label}")

    basis = activity.get("legal_basis") or []
    if isinstance(basis, str):
        basis = [basis]
    unknown = [b for b in basis if b not in ART6_BASES]
    if unknown:
        add("błąd", "art. 6 ust. 1", f"nieznana podstawa prawna: {', '.join(unknown)}")

    if "6.1.f" in basis and not activity.get("legitimate_interest_test"):
        add("ostrzeżenie", "art. 6 ust. 1 lit. f", "uzasadniony interes bez udokumentowanego testu równowagi")

    if "6.1.a" in basis and not activity.get("consent_record"):
        add("ostrzeżenie", "art. 7 ust. 1", "zgoda bez opisu, jak administrator ją wykazuje")

    categories = {str(c).lower() for c in activity.get("data_categories") or []}
    special = sorted(categories & SPECIAL_CATEGORIES)
    if special:
        condition = activity.get("art9_condition")
        if condition not in ART9_CONDITIONS:
            add(
                "błąd",
                "art. 9 ust. 2",
                f"dane szczególnych kategorii ({', '.join(special)}) bez przesłanki z art. 9 ust. 2",
            )

    retention = str(activity.get("retention") or "").strip().lower()
    if retention and retention in VAGUE_RETENTION:
        add(
            "ostrzeżenie",
            "art. 5 ust. 1 lit. e",
            f"nieokreślony okres przechowywania: „{activity.get('retention')}”",
        )

    for transfer in activity.get("third_country_transfers") or []:
        country = transfer.get("country", "?") if isinstance(transfer, dict) else str(transfer)
        mechanism = transfer.get("mechanism") if isinstance(transfer, dict) else None
        if mechanism not in TRANSFER_MECHANISMS:
            add(
                "błąd",
                "art. 44-49",
                f"przekazanie do {country} bez wskazanego mechanizmu (SCC, decyzja, BCR, art. 49)",
            )

    flags = activity.get("dpia_criteria") or []
    if special and "sensitive_data" not in flags:
        flags = [*flags, "sensitive_data"]
    met = [DPIA_CRITERIA[f] for f in flags if f in DPIA_CRITERIA]
    if len(met) >= 2 and not activity.get("dpia_done"):
        add(
            "błąd",
            "art. 35 ust. 1",
            f"spełnione {len(met)} kryteria WP248 ({'; '.join(met)}), brak oceny skutków (DPIA)",
        )

    processors = activity.get("processors") or []
    for processor in processors:
        if isinstance(processor, dict) and not processor.get("dpa_signed"):
            add(
                "błąd",
                "art. 28 ust. 3",
                f"podmiot przetwarzający {processor.get('name', '?')} bez umowy powierzenia",
            )

    return issues


def validate_register(register: dict) -> list[Issue]:
    """Sprawdza cały rejestr: dane administratora i każdą czynność."""
    issues: list[Issue] = []
    controller = register.get("controller") or {}
    if not controller.get("name") or not controller.get("contact"):
        issues.append(
            Issue(
                "(administrator)",
                "błąd",
                "art. 30 ust. 1 lit. a",
                "brak nazwy lub danych kontaktowych administratora",
            )
        )

    activities = register.get("activities") or []
    if not activities:
        issues.append(Issue("(rejestr)", "błąd", "art. 30 ust. 1", "rejestr nie zawiera czynności"))

    names = [a.get("name") for a in activities]
    for duplicate in sorted({n for n in names if n and names.count(n) > 1}):
        issues.append(Issue(duplicate, "ostrzeżenie", "spójność", "zduplikowana nazwa czynności"))

    for activity in activities:
        issues.extend(validate_activity(activity))
    return issues


def to_markdown(issues: list[Issue]) -> str:
    errors = sum(1 for i in issues if i.level == "błąd")
    warnings = len(issues) - errors
    lines = [f"Błędy: {errors} · Ostrzeżenia: {warnings}", ""]
    if not issues:
        lines.append("Rejestr kompletny formalnie.")
        return "\n".join(lines)
    lines += ["| Czynność | Poziom | Przepis | Problem |", "|---|---|---|---|"]
    for i in sorted(issues, key=lambda x: (x.level != "błąd", x.activity)):
        lines.append(f"| {i.activity} | {i.level} | {i.rule} | {i.message} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Walidacja rejestru czynności przetwarzania.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    register = json.loads(args.path.read_text(encoding="utf-8"))
    issues = validate_register(register)
    if args.json:
        print(json.dumps([asdict(i) for i in issues], ensure_ascii=False, indent=2))
    else:
        print(to_markdown(issues))
    return 1 if any(i.level == "błąd" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
