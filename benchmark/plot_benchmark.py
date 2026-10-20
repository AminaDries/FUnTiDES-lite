#!/usr/bin/env python3
"""Figures et tableau de synthese a partir d'un fichier de metriques semproxy.

Usage :
    /usr/bin/python3 plot_benchmark.py gpu.csv --out figures --label "Portable GPU"

Sortie : temps.png, volume_debit.png, scaling.png, summary.csv
Les valeurs tracees sont les medianes ; les barres d'erreur donnent min et max.
"""
import argparse
import csv
import math
import os
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    """Regroupe les runs par (N, snapshots actifs ou non)."""
    groups = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            n = int(r["ex"])
            snap = int(r["snapshots"])
            compute = float(r["compute_time_s"])
            write = float(r["snapshot_write_time_s"])
            nbytes = int(r["snapshot_bytes"])
            groups.setdefault((n, snap), []).append(
                {
                    "compute": compute,
                    "write": write,
                    "total": compute + write,
                    "bytes": nbytes,
                    "rate": nbytes / 1e6 / write if write > 0 else 0.0,
                }
            )
    return groups


def stats(runs, key):
    vals = [r[key] for r in runs]
    return st.median(vals), min(vals), max(vals)


def yerr(med, lo, hi):
    return [[med - lo], [hi - med]]


def write_summary(groups, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["N", "snapshots", "runs", "compute_med", "compute_min", "compute_max",
             "write_med", "total_med", "total_min", "total_max",
             "volume_GB", "rate_MBps_med", "rate_MBps_min", "rate_MBps_max"]
        )
        for (n, snap), runs in sorted(groups.items()):
            c = stats(runs, "compute")
            wr = stats(runs, "write")
            t = stats(runs, "total")
            b = stats(runs, "bytes")
            rt = stats(runs, "rate")
            w.writerow([n, snap, len(runs), *[f"{x:.3f}" for x in c],
                        f"{wr[0]:.3f}", *[f"{x:.3f}" for x in t],
                        f"{b[0] / 1e9:.3f}", *[f"{x:.2f}" for x in rt]])


def fig_temps(groups, sizes, out, label):
    """Temps par taille : calcul seul, et calcul + ecriture des snapshots."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    width = 0.38
    for i, n in enumerate(sizes):
        x0, x1 = i - width / 2, i + width / 2
        if (n, 0) in groups:
            c = stats(groups[(n, 0)], "compute")
            ax.bar(x0, c[0], width, color="#4c78a8",
                   label="Calcul (sans snapshots)" if i == 0 else None)
            ax.errorbar(x0, c[0], yerr=yerr(*c), color="k", capsize=3)
        if (n, 1) in groups:
            c = stats(groups[(n, 1)], "compute")
            w = stats(groups[(n, 1)], "write")
            t = stats(groups[(n, 1)], "total")
            ax.bar(x1, c[0], width, color="#4c78a8", alpha=0.6,
                   label="Calcul (avec snapshots)" if i == 0 else None)
            ax.bar(x1, w[0], width, bottom=c[0], color="#e45756",
                   label="Ecriture des snapshots" if i == 0 else None)
            ax.errorbar(x1, t[0], yerr=yerr(*t), color="k", capsize=3)
            ax.text(x1, t[0] * 1.15, f"{t[0]:.0f} s", ha="center", fontsize=8)
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([f"{n}$^3$" for n in sizes])
    ax.set_yscale("log")
    ax.set_ylabel("Temps (s), echelle log")
    ax.set_xlabel("Maillage (elements)")
    ax.set_title(f"Temps d'execution : {label}")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "temps.png"), dpi=150)
    plt.close(fig)


def fig_volume_debit(groups, sizes, out, label):
    """Volume ecrit et debit d'ecriture (runs avec snapshots)."""
    sn = [n for n in sizes if (n, 1) in groups]
    if not sn:
        return
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    for i, n in enumerate(sn):
        b = stats(groups[(n, 1)], "bytes")
        a1.bar(i, b[0] / 1e9, 0.5, color="#72b7b2")
        a1.text(i, b[0] / 1e9 * 1.02, f"{b[0] / 1e9:.1f} Go", ha="center", fontsize=9)
        r = stats(groups[(n, 1)], "rate")
        a2.bar(i, r[0], 0.5, color="#f58518")
        a2.errorbar(i, r[0], yerr=yerr(*r), color="k", capsize=3)
        a2.text(i, r[2] * 1.03, f"{r[0]:.0f} Mo/s", ha="center", fontsize=9)
    for a in (a1, a2):
        a.set_xticks(range(len(sn)))
        a.set_xticklabels([f"{n}$^3$" for n in sn])
        a.set_xlabel("Maillage (elements)")
        a.grid(axis="y", alpha=0.3)
    a1.set_ylabel("Volume total des snapshots (Go)")
    a1.set_title("Volume ecrit")
    a2.set_ylabel("Debit d'ecriture (Mo/s)")
    a2.set_title("Debit effectif (barres : min/max)")
    fig.suptitle(label)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "volume_debit.png"), dpi=150)
    plt.close(fig)


def fig_scaling(groups, sizes, out, label):
    """Temps de calcul (sans snapshots) en fonction de N, log-log."""
    pts = [(n, stats(groups[(n, 0)], "compute")[0]) for n in sizes if (n, 0) in groups]
    if len(pts) < 2:
        return
    xs = [math.log(n) for n, _ in pts]
    ys = [math.log(t) for _, t in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.loglog([n for n, _ in pts], [t for _, t in pts], "o-", label="Mesure (mediane)")
    n0, t0 = pts[0]
    for p, style in ((3, "--"), (4, ":")):
        ax.loglog([n for n, _ in pts], [t0 * (n / n0) ** p for n, _ in pts],
                  style, color="gray", label=f"Reference $N^{p}$")
    ax.set_xlabel("N (elements par direction)")
    ax.set_ylabel("Temps de calcul (s)")
    ax.set_title(f"Mise a l'echelle du calcul : pente {slope:.2f}\n{label}")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "scaling.png"), dpi=150)
    plt.close(fig)
    print(f"Pente log-log du calcul : {slope:.2f} "
          "(3 si le nombre de pas est fixe, 4 si dt suit la CFL)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="fichier de metriques (gpu.csv)")
    ap.add_argument("--out", default="figures", help="dossier de sortie")
    ap.add_argument("--label", default="", help="nom de la machine / configuration")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    groups = load(args.csv)
    if not groups:
        raise SystemExit("Aucune ligne lue dans " + args.csv)
    sizes = sorted({n for n, _ in groups})

    write_summary(groups, os.path.join(args.out, "summary.csv"))
    fig_temps(groups, sizes, args.out, args.label)
    fig_volume_debit(groups, sizes, args.out, args.label)
    fig_scaling(groups, sizes, args.out, args.label)
    print("Ecrit dans", args.out + "/ :", ", ".join(sorted(os.listdir(args.out))))


if __name__ == "__main__":
    main()
