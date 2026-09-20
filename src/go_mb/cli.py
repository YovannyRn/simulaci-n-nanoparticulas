"""CLI headless. La vista no es el experimento."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from go_mb.config import SimulationConfig
from go_mb.engine import run_simulation
from go_mb.experiments import run_campaign
from go_mb.io import load_run, save_run
from go_mb.viz import plot_run, plot_snapshot


def _add_run_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--sigma", type=float, required=True, help="D/σ browniano en px/paso (PENDIENTE en el PDF)")
    p.add_argument("--steps", type=int, required=True, help="P pasos (PENDIENTE en el PDF)")
    p.add_argument("--p-ads", type=float, default=None, help="P_ads opcional en [0,1]; por defecto regla de capacidad")
    p.add_argument("--out", type=str, default="data/results")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulación 2D GO–MB (motor científico)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Una corrida")
    _add_run_args(run_p)
    run_p.add_argument("--plot", action="store_true")

    camp = sub.add_parser("campaign", help="N repeticiones")
    camp.add_argument("--n-rep", type=int, required=True, help="Nrep (PENDIENTE 30 vs 40 en el PDF)")
    camp.add_argument("--base-seed", type=int, required=True)
    camp.add_argument("--sigma", type=float, required=True)
    camp.add_argument("--steps", type=int, required=True)
    camp.add_argument("--p-ads", type=float, default=None)
    camp.add_argument("--out", type=str, default="data/results")

    plot_p = sub.add_parser("plot", help="Graficar un JSON ya escrito")
    plot_p.add_argument("--input", type=str, required=True)
    plot_p.add_argument("--out", type=str, default="figures")

    args = parser.parse_args(argv)
    cfg = SimulationConfig()

    if args.cmd == "run":
        result = run_simulation(
            cfg,
            seed=args.seed,
            sigma_px=args.sigma,
            n_steps=args.steps,
            p_ads=args.p_ads,
        )
        paths = save_run(result, args.out, f"go_seed_{args.seed}")
        if args.plot:
            plot_run(result, Path("figures") / f"go_seed_{args.seed}_series.png")
            plot_snapshot(result, Path("figures") / f"go_seed_{args.seed}_snap.png")
        print(json.dumps({"paths": paths, "summary": result["summary"]}, indent=2))
        return 0

    if args.cmd == "campaign":
        campaign = run_campaign(
            n_rep=args.n_rep,
            base_seed=args.base_seed,
            sigma_px=args.sigma,
            n_steps=args.steps,
            config=cfg,
            p_ads=args.p_ads,
            output_dir=args.out,
        )
        summary_path = Path(args.out) / "campaign_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        dump = {k: v for k, v in campaign.items() if k != "stats"}
        dump["stats"] = campaign["stats"]
        # values lists are json-serializable
        summary_path.write_text(json.dumps(dump, indent=2, default=str))
        print(json.dumps({"n_rep": campaign["n_rep"], "seeds": campaign["stats"]["seeds"], "summary": summary_path.as_posix()}, indent=2))
        return 0

    if args.cmd == "plot":
        result = load_run(args.input)
        stem = Path(args.input).stem
        s = plot_run(result, Path(args.out) / f"{stem}_series.png")
        p = plot_snapshot(result, Path(args.out) / f"{stem}_snap.png")
        print(json.dumps({"series": s, "snapshot": p}))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
