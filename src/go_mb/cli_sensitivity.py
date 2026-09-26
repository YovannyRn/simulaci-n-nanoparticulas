"""Ejecutar estudios de sensibilidad (GO o AC) desde la CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from go_mb.config import SimulationConfig
from go_mb.io import save_study
from go_mb.sensitivity import (
    parse_float_list,
    parse_int_list,
    parse_seed_list,
    sweep_sigma,
    sweep_sigma_steps_grid,
    sweep_steps,
)


def run_sensitivity_command(args: Any, config: SimulationConfig) -> dict[str, Any]:
    seeds = parse_seed_list(args.seeds, args.seed)
    study_name = args.study_name
    plot_dir = Path(args.out) / "figures"

    if args.sens_cmd == "sigma":
        sigmas = parse_float_list(args.sigmas)
        study = sweep_sigma(
            sigmas=sigmas,
            seeds=seeds,
            n_steps=args.steps,
            config=config,
            p_ads=args.p_ads,
            output_dir=args.out,
        )
        study_name = study_name or f"study_sigma_steps_{args.steps}"
    elif args.sens_cmd == "steps":
        steps_list = parse_int_list(args.steps_list)
        study = sweep_steps(
            steps_list=steps_list,
            seeds=seeds,
            sigma_px=args.sigma,
            config=config,
            p_ads=args.p_ads,
            output_dir=args.out,
        )
        study_name = study_name or f"study_sigma_{args.sigma:g}_steps"
    elif args.sens_cmd == "grid":
        sigmas = parse_float_list(args.sigmas)
        steps_list = parse_int_list(args.steps_list)
        study = sweep_sigma_steps_grid(
            sigmas=sigmas,
            steps_list=steps_list,
            seeds=seeds,
            config=config,
            p_ads=args.p_ads,
            output_dir=args.out,
        )
        study_name = study_name or "study_sigma_steps_grid"
    else:
        raise ValueError(f"Comando de sensibilidad desconocido: {args.sens_cmd}")

    study_path = save_study(study, args.out, study_name)
    figures: list[str] = []
    if args.plot:
        from go_mb.viz import plot_sensitivity_study

        figures = plot_sensitivity_study(study, plot_dir)
    return {
        "study_path": study_path,
        "n_runs": study["study"]["n_runs"],
        "material": study["study"].get("material"),
        "analysis": study["analysis"],
        "figures": figures,
    }


def print_sensitivity_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, default=str))
