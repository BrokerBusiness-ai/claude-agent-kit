"""Udostępnia moduły z katalogu konfiguracji Claude Code testom.

Repozytorium trzyma konfigurację w `.claude/`. Przed pierwszym wypchnięciem
katalog może jeszcze nazywać się `dot-claude/` (patrz JAK_WRZUCIC_NA_GITHUB.md),
dlatego testy szukają obu nazw.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = next((ROOT / name for name in (".claude", "dot-claude") if (ROOT / name).is_dir()), None)

if CONFIG_DIR is None:
    raise RuntimeError("Nie znaleziono katalogu .claude ani dot-claude")

for sub in (
    "hooks",
    "skills/web-security-audit/scripts",
    "skills/gdpr-doc-validator/scripts",
):
    sys.path.insert(0, str(CONFIG_DIR / sub))
