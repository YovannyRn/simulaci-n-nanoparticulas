"""Ejecuta la campaña de caracterización AC–MB (no validación experimental)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from go_mb.cli import main

STEPS_LIST = "200,400,600,800,1000,1500,2000"
SIGMAS_FULL = "0.5,1,1.5,2"
SIGMAS_PAIR = "1,1.5"
STEPS_SEEDS = "200,400"


def run(argv: list[str]) -> None:
    code = main(argv)
    if code != 0:
        raise SystemExit(code)


if __name__ == "__main__":
    base = "data/sensitivity/ac"
    run(
        [
            "ac",
            "sensitivity",
            "sigma",
            "--seed",
            "1",
            "--steps",
            "400",
            "--sigmas",
            SIGMAS_FULL,
            "--out",
            f"{base}/sigma",
            "--study-name",
            "study_ac_sigma_steps_400",
            "--plot",
        ]
    )
    for sigma in ("1.0", "1.5"):
        tag = sigma.replace(".", "_")
        run(
            [
                "ac",
                "sensitivity",
                "steps",
                "--seed",
                "1",
                "--sigma",
                sigma,
                "--steps-list",
                STEPS_LIST,
                "--out",
                f"{base}/steps_sigma_{tag}",
                "--study-name",
                f"study_ac_sigma_{tag}_steps",
                "--plot",
            ]
        )
    run(
        [
            "ac",
            "sensitivity",
            "grid",
            "--seed",
            "1",
            "--sigmas",
            SIGMAS_PAIR,
            "--steps-list",
            STEPS_LIST,
            "--out",
            f"{base}/grid",
            "--study-name",
            "study_ac_sigma_steps_grid",
            "--plot",
        ]
    )
    run(
        [
            "ac",
            "sensitivity",
            "grid",
            "--seed",
            "1",
            "--seeds",
            "1,2,3,4,5",
            "--sigmas",
            SIGMAS_PAIR,
            "--steps-list",
            STEPS_SEEDS,
            "--out",
            f"{base}/seeds",
            "--study-name",
            "study_ac_seeds",
            "--plot",
        ]
    )
    print("AC sensitivity batch complete.")
