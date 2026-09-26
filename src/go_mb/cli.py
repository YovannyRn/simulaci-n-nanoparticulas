"""CLI headless. La vista no es el experimento."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from go_mb.config import SimulationConfig, ac_config
from go_mb.engine import run_simulation
from go_mb.experiments import run_campaign
from go_mb.cli_sensitivity import print_sensitivity_result, run_sensitivity_command
from go_mb.io import load_run, load_study, save_run


def _add_run_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--sigma", type=float, required=True, help="D/σ browniano en px/paso (PENDIENTE en el PDF)")
    p.add_argument("--steps", type=int, required=True, help="P pasos (PENDIENTE en el PDF)")
    p.add_argument(
        "--p-ads",
        type=float,
        default=None,
        help=(
            "P_ads inyectado en [0,1]. Defecto None = decisión provisional P_ads=1 "
            "tras contacto y capacidad; NO es un valor de literatura"
        ),
    )
    p.add_argument("--out", type=str, default="data/results")


def _add_sensitivity_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, required=True, help="Semilla base (o única si no se pasa --seeds)")
    p.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Lista opcional de semillas separadas por comas para estudiar variabilidad",
    )
    p.add_argument("--p-ads", type=float, default=None)
    p.add_argument("--out", type=str, default="data/sensitivity")
    p.add_argument("--study-name", type=str, default=None, help="Nombre del JSON agregado del estudio")
    p.add_argument(
        "--plot",
        action="store_true",
        help="Generar figuras de sensibilidad (Matplotlib, separado del motor)",
    )


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
    camp.add_argument(
        "--p-ads",
        type=float,
        default=None,
        help=(
            "P_ads inyectado en [0,1]. Defecto None = decisión provisional P_ads=1 "
            "tras contacto y capacidad; NO es un valor de literatura"
        ),
    )
    camp.add_argument("--out", type=str, default="data/results")

    plot_p = sub.add_parser("plot", help="Graficar un JSON ya escrito")
    plot_p.add_argument("--input", type=str, required=True)
    plot_p.add_argument("--out", type=str, default="figures")

    sens = sub.add_parser(
        "sensitivity",
        help="Calibración y sensibilidad (no validación experimental)",
    )
    sens_sub = sens.add_subparsers(dest="sens_cmd", required=True)

    sens_sigma = sens_sub.add_parser("sigma", help="Barrido de σ a pasos fijos")
    _add_sensitivity_common(sens_sigma)
    sens_sigma.add_argument("--steps", type=int, required=True)
    sens_sigma.add_argument(
        "--sigmas",
        type=str,
        required=True,
        help="Valores de σ separados por comas (inyectados, no defaults científicos)",
    )

    sens_steps = sens_sub.add_parser("steps", help="Barrido de pasos a σ fijo")
    _add_sensitivity_common(sens_steps)
    sens_steps.add_argument("--sigma", type=float, required=True)
    sens_steps.add_argument(
        "--steps-list",
        type=str,
        required=True,
        help="Números de pasos separados por comas",
    )

    sens_grid = sens_sub.add_parser("grid", help="Matriz σ × pasos")
    _add_sensitivity_common(sens_grid)
    sens_grid.add_argument("--sigmas", type=str, required=True)
    sens_grid.add_argument("--steps-list", type=str, required=True)

    sens_plot = sens_sub.add_parser("plot", help="Graficar un estudio de sensibilidad guardado")
    sens_plot.add_argument("--input", type=str, required=True)
    sens_plot.add_argument("--out", type=str, default="figures/sensitivity")

    ac_p = sub.add_parser("ac", help="Simulación 2D AC–MB (carbón activo fijo)")
    ac_sub = ac_p.add_subparsers(dest="ac_cmd", required=True)
    ac_run = ac_sub.add_parser("run", help="Una corrida AC–MB")
    _add_run_args(ac_run)
    ac_run.add_argument("--plot", action="store_true")

    ac_sens = ac_sub.add_parser("sensitivity", help="Sensibilidad AC–MB (mismo protocolo que GO)")
    ac_sens_sub = ac_sens.add_subparsers(dest="sens_cmd", required=True)
    ac_sens_sigma = ac_sens_sub.add_parser("sigma", help="Barrido σ")
    _add_sensitivity_common(ac_sens_sigma)
    ac_sens_sigma.add_argument("--steps", type=int, required=True)
    ac_sens_sigma.add_argument("--sigmas", type=str, required=True)
    ac_sens_steps = ac_sens_sub.add_parser("steps", help="Barrido de pasos")
    _add_sensitivity_common(ac_sens_steps)
    ac_sens_steps.add_argument("--sigma", type=float, required=True)
    ac_sens_steps.add_argument("--steps-list", type=str, required=True)
    ac_sens_grid = ac_sens_sub.add_parser("grid", help="Matriz σ×pasos")
    _add_sensitivity_common(ac_sens_grid)
    ac_sens_grid.add_argument("--sigmas", type=str, required=True)
    ac_sens_grid.add_argument("--steps-list", type=str, required=True)
    ac_sens_plot = ac_sens_sub.add_parser("plot", help="Graficar estudio AC guardado")
    ac_sens_plot.add_argument("--input", type=str, required=True)
    ac_sens_plot.add_argument("--out", type=str, default="figures/sensitivity/ac")

    hom = sub.add_parser(
        "homogeneous",
        help="Campaña temporal homogénea GO+AC (misma malla σ×P×seeds)",
    )
    hom.add_argument(
        "--out",
        type=str,
        default=None,
        help="Salida (defecto: homogeneous_temporal_wiam_geometry si --geometry-era wiam)",
    )
    hom.add_argument(
        "--geometry-era",
        choices=["wiam_geometry", "legacy_geometry"],
        default="wiam_geometry",
        help="wiam_geometry = campaña principal actual; legacy_geometry no sobrescribe histórico",
    )
    hom.add_argument(
        "--only",
        choices=["GO", "AC", "both"],
        default="both",
        help="Ejecutar solo un material o ambos",
    )
    hom.add_argument("--plot", action="store_true", default=True)
    hom.add_argument("--no-plot", action="store_false", dest="plot")

    fcamp_p = sub.add_parser(
        "final-campaign",
        help="Campaña final 40 GO + 40 AC (σ=1.5, P=2000, P_ads=1)",
    )
    fcamp_p.add_argument("--out", type=str, default="data/final_campaign")
    fcamp_p.add_argument("--plot", action="store_true", default=True)
    fcamp_p.add_argument("--no-plot", action="store_false", dest="plot")

    ftemp_p = sub.add_parser(
        "final-temporal-reference",
        help="PSO GO/AC, α exploratorio, S* contextual, P_ads=0.55 (sin campaña 40+40)",
    )
    ftemp_p.add_argument(
        "--campaign",
        type=str,
        default="data/sensitivity/homogeneous_temporal_wiam_geometry",
    )
    ftemp_p.add_argument(
        "--p-ads-sensitivity",
        type=str,
        default="data/sensitivity/p_ads_sensitivity",
    )
    ftemp_p.add_argument(
        "--out",
        type=str,
        default="data/analysis/final_temporal_reference",
    )
    ftemp_p.add_argument("--plot", action="store_true", default=True)
    ftemp_p.add_argument("--no-plot", action="store_false", dest="plot")
    ftemp_p.add_argument(
        "--skip-pads-055-runs",
        action="store_true",
        help="No simular P_ads=0.55 (solo análisis temporal)",
    )

    pads_p = sub.add_parser(
        "p-ads-sensitivity",
        help="Sensibilidad computacional P_ads (0.25–1.0, σ×seeds, P=2000)",
    )
    pads_p.add_argument("--out", type=str, default="data/sensitivity/p_ads_sensitivity")
    pads_p.add_argument("--plot", action="store_true", default=True)
    pads_p.add_argument("--no-plot", action="store_false", dest="plot")

    fprot_p = sub.add_parser(
        "final-protocol",
        help="Análisis P=2000 y propuesta de protocolo (descriptivo, sin re-simular)",
    )
    fprot_p.add_argument(
        "--campaign",
        type=str,
        default="data/sensitivity/homogeneous_temporal_wiam_geometry",
    )
    fprot_p.add_argument(
        "--calibration",
        type=str,
        default="data/analysis/temporal_calibration",
    )
    fprot_p.add_argument("--out", type=str, default="data/analysis/final_protocol")
    fprot_p.add_argument("--plot", action="store_true", default=True)
    fprot_p.add_argument("--no-plot", action="store_false", dest="plot")

    tcal_p = sub.add_parser(
        "temporal-calibration",
        help="Calibración temporal exploratoria (pasos vs PSO GO) desde JSON Wiam",
    )
    tcal_p.add_argument(
        "--input",
        type=str,
        default="data/sensitivity/homogeneous_temporal_wiam_geometry",
    )
    tcal_p.add_argument("--out", type=str, default="data/analysis/temporal_calibration")
    tcal_p.add_argument("--plot", action="store_true", default=True)
    tcal_p.add_argument("--no-plot", action="store_false", dest="plot")

    geo_p = sub.add_parser(
        "geometry-pilot",
        help="Piloto σ=1.0, P=200, seeds 1–3 (geometría Wiam vs homogénea anterior)",
    )
    geo_p.add_argument("--out", type=str, default="data/sensitivity/geometry_update_pilot")
    geo_p.add_argument(
        "--legacy-root",
        type=str,
        default="data/sensitivity/homogeneous_temporal",
        help="Carpeta de la campaña homogénea con geometría anterior",
    )

    cmp_p = sub.add_parser(
        "compare",
        help="Comparación descriptiva GO vs AC desde JSON existentes (no re-simula)",
    )
    cmp_p.add_argument("--out", type=str, default="data/comparison/go_vs_ac")
    cmp_p.add_argument("--go-seeds-study", type=str, default=None)
    cmp_p.add_argument("--ac-seeds-study", type=str, default=None)
    cmp_p.add_argument("--plot", action="store_true", default=True)
    cmp_p.add_argument("--no-plot", action="store_false", dest="plot")

    view_p = sub.add_parser("view", help="Visualización interactiva 2D (capa sobre el motor)")
    view_p.add_argument("--material", choices=["GO", "AC"], default="GO")
    view_p.add_argument("--seed", type=int, default=1)
    view_p.add_argument("--sigma", type=float, default=1.5)
    view_p.add_argument("--steps", type=int, default=400)
    view_p.add_argument("--p-ads", type=float, default=None)
    view_p.add_argument("--interval-ms", type=int, default=30)

    args = parser.parse_args(argv)
    cfg = SimulationConfig()

    if args.cmd == "final-campaign":
        from go_mb.final_campaign import run_final_campaign

        result = run_final_campaign(output_dir=Path(args.out), plot=args.plot)
        print(json.dumps(result, indent=2, default=str))
        return 0

    if args.cmd == "final-temporal-reference":
        from go_mb.final_temporal_reference import run_final_temporal_reference

        result = run_final_temporal_reference(
            campaign_root=Path(args.campaign),
            sensitivity_root=Path(args.p_ads_sensitivity),
            output_dir=Path(args.out),
            plot=args.plot,
            run_pads_055=not args.skip_pads_055_runs,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "p-ads-sensitivity":
        from go_mb.p_ads_sensitivity import run_p_ads_sensitivity_campaign

        result = run_p_ads_sensitivity_campaign(
            output_dir=Path(args.out),
            plot=args.plot,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "final-protocol":
        from go_mb.final_protocol_analysis import run_final_protocol_analysis

        result = run_final_protocol_analysis(
            campaign_root=Path(args.campaign),
            calibration_root=Path(args.calibration),
            output_dir=Path(args.out),
            plot=args.plot,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "temporal-calibration":
        from go_mb.temporal_calibration import run_temporal_calibration

        result = run_temporal_calibration(
            campaign_root=Path(args.input),
            output_dir=Path(args.out),
            plot=args.plot,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "geometry-pilot":
        from go_mb.geometry_update_pilot import run_geometry_pilot

        result = run_geometry_pilot(
            output_dir=Path(args.out),
            legacy_root=Path(args.legacy_root),
        )
        print(
            json.dumps(
                {
                    "total_runs": result["total_runs"],
                    "classification": result["provenance"]["geometry_alignment_classification"],
                    "comparison": result.get("comparison"),
                    "materials": {
                        k: {"n_runs": v["n_runs"], "comparison_json": v["comparison_json"]}
                        for k, v in result["materials"].items()
                    },
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "homogeneous":
        from go_mb.config import HOMOGENEOUS_LEGACY_DIR, HOMOGENEOUS_WIAM_DIR
        from go_mb.homogeneous_temporal import run_homogeneous_campaign

        out = args.out
        if out is None:
            out = (
                HOMOGENEOUS_WIAM_DIR
                if args.geometry_era == "wiam_geometry"
                else HOMOGENEOUS_LEGACY_DIR
            )
        result = run_homogeneous_campaign(
            base_dir=Path(out),
            plot=args.plot,
            run_go=args.only in ("GO", "both"),
            run_ac=args.only in ("AC", "both"),
            geometry_era=args.geometry_era,
        )
        print(
            json.dumps(
                {
                    "total_runs": result["total_runs"],
                    "materials": result["materials"],
                    "comparison": result.get("comparison"),
                    "classification": result["provenance"]["homogeneous_temporal_classification"],
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "compare":
        from go_mb.compare import run_descriptive_comparison

        result = run_descriptive_comparison(
            go_seeds_study=Path(args.go_seeds_study) if args.go_seeds_study else None,
            ac_seeds_study=Path(args.ac_seeds_study) if args.ac_seeds_study else None,
            output_dir=Path(args.out),
            plot=args.plot,
        )
        print(json.dumps({k: result[k] for k in ("json", "csv", "figures")}, indent=2))
        return 0

    if args.cmd == "view":
        from go_mb.interactive import launch_interactive_viewer

        launch_interactive_viewer(
            material=args.material,
            seed=args.seed,
            sigma_px=args.sigma,
            n_steps=args.steps,
            p_ads=args.p_ads,
            interval_ms=args.interval_ms,
        )
        return 0

    if args.cmd == "ac":
        ac_cfg = ac_config()
        if args.ac_cmd == "sensitivity":
            if args.sens_cmd == "plot":
                from go_mb.viz import plot_sensitivity_study

                study = load_study(args.input)
                paths = plot_sensitivity_study(study, args.out)
                print(json.dumps({"figures": paths}, indent=2))
                return 0
            payload = run_sensitivity_command(args, ac_cfg)
            print_sensitivity_result(payload)
            return 0
        if args.ac_cmd == "run":
            result = run_simulation(
                ac_cfg,
                seed=args.seed,
                sigma_px=args.sigma,
                n_steps=args.steps,
                p_ads=args.p_ads,
            )
            paths = save_run(result, args.out, f"ac_seed_{args.seed}")
            if args.plot:
                from go_mb.viz import plot_run, plot_snapshot

                plot_run(result, Path("figures/ac") / f"ac_seed_{args.seed}_series.png")
                plot_snapshot(result, Path("figures/ac") / f"ac_seed_{args.seed}_snap.png")
            print(json.dumps({"paths": paths, "summary": result["summary"], "reference": result["reference"]}, indent=2))
            return 0
        return 1

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
            from go_mb.viz import plot_run, plot_snapshot

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
        summary_path.write_text(json.dumps(dump, indent=2, default=str))
        print(
            json.dumps(
                {
                    "n_rep": campaign["n_rep"],
                    "seeds": campaign["stats"]["seeds"],
                    "summary": summary_path.as_posix(),
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "plot":
        from go_mb.viz import plot_run, plot_snapshot

        result = load_run(args.input)
        stem = Path(args.input).stem
        s = plot_run(result, Path(args.out) / f"{stem}_series.png")
        p = plot_snapshot(result, Path(args.out) / f"{stem}_snap.png")
        print(json.dumps({"series": s, "snapshot": p}))
        return 0

    if args.cmd == "sensitivity":
        if args.sens_cmd == "plot":
            from go_mb.viz import plot_sensitivity_study

            study = load_study(args.input)
            paths = plot_sensitivity_study(study, args.out)
            print(json.dumps({"figures": paths}, indent=2))
            return 0

        payload = run_sensitivity_command(args, cfg)
        print_sensitivity_result(payload)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
