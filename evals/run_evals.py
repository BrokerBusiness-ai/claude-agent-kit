"""Ewaluacje hooków na zestawie realistycznych przypadków.

Testy jednostkowe sprawdzają pojedyncze reguły. Ewaluacje odpowiadają na inne
pytanie: jak hook zachowuje się na mieszance poleceń, które agent faktycznie
generuje w pracy. Raport podaje precyzję i czułość blokad oraz listę pomyłek.

Użycie:
    python evals/run_evals.py
    python evals/run_evals.py --min-f1 0.95   # próg dla CI
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = next(ROOT / n for n in (".claude", "dot-claude") if (ROOT / n).is_dir())
sys.path.insert(0, str(CONFIG_DIR / "hooks"))

import guard_bash  # noqa: E402
import secret_scan  # noqa: E402

HOOKS = {"guard_bash": guard_bash.evaluate, "secret_scan": secret_scan.evaluate}


@dataclass
class Score:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 1.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def _assemble(tool_input: dict) -> dict:
    """Skleja pola *_parts w pełne wartości.

    Fałszywe klucze w przypadkach testowych są pocięte na kawałki, żeby skaner
    sekretów GitHuba (push protection) nie blokował wypchnięcia repozytorium.
    """
    result = dict(tool_input)
    for key in ("content", "new_string"):
        parts = result.pop(f"{key}_parts", None)
        if parts is not None:
            result[key] = "".join(parts)
    edits = result.pop("edits_parts", None)
    if edits is not None:
        result["edits"] = [{"new_string": "".join(p)} for p in edits]
    return result


def load_cases(path: Path) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for case in cases:
        case["event"]["tool_input"] = _assemble(case["event"].get("tool_input") or {})
    return cases


def evaluate_suite(hook: str, cases: list[dict]) -> tuple[Score, list[str]]:
    score, misses = Score(), []
    for case in cases:
        blocked = not HOOKS[hook](case["event"]).allowed
        expected = case["expect"] == "block"
        if blocked and expected:
            score.tp += 1
        elif blocked and not expected:
            score.fp += 1
            misses.append(f"fałszywy alarm: {case['id']}")
        elif not blocked and expected:
            score.fn += 1
            misses.append(f"przepuszczone: {case['id']}")
        else:
            score.tn += 1
    return score, misses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-f1", type=float, default=0.0)
    args = parser.parse_args(argv)

    worst = 1.0
    print("| Hook | Przypadki | Precyzja | Czułość | F1 |")
    print("|---|---|---|---|---|")
    all_misses: list[str] = []
    for path in sorted((ROOT / "evals" / "cases").glob("*.jsonl")):
        hook = path.stem
        cases = load_cases(path)
        score, misses = evaluate_suite(hook, cases)
        worst = min(worst, score.f1)
        all_misses += [f"{hook}: {m}" for m in misses]
        print(f"| {hook} | {len(cases)} | {score.precision:.2f} | {score.recall:.2f} | {score.f1:.2f} |")

    if all_misses:
        print("\nPomyłki:")
        for miss in all_misses:
            print(f"- {miss}")
    return 0 if worst >= args.min_f1 else 1


if __name__ == "__main__":
    sys.exit(main())
