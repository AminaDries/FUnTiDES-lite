#!/usr/bin/env python3
"""Figure de mise a l'echelle a partir d'un CSV semproxy (runs sans snapshots, --auto-dt).

Usage : /usr/bin/python3 plot_scaling.py cfl.csv --out figures --label "Portable GPU"
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
    g = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            if int(r["snapshots"]) != 0:
                continue
            n = int(r["ex"])
            g.setdefault(n, []).append(
                {
                    "compute": float(r["compute_time_s"]),
                    "steps": int(r["nb_steps"]),
                    "nodes": int(r["nb_nodes"]),
                }
            )
    return g


def med_min_max(vals):
    return st.median(vals), min(vals), max(vals)


def slope(xs, ys):
    lx, ly = [math.log(x) for x in xs], [math.log(y) for y in ys]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


def errbars(ax, xs, stats):
    med = [s[0] for s in stats]
    lo = [s[0] - s[1] for s in stats]
    hi = [s[2] - s[0] for s in stats]
    ax.errorbar(xs, med, yerr=[lo, hi], fmt="o-", capsize=3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    g = load(a.csv)
    sizes = sorted(g)
    if len(sizes) < 3:
        raise SystemExit("Il faut au moins 3 tailles pour une pente exploitable.")
    os.makedirs(a.out, exist_ok=True)

    comp = [med_min_max([r["compute"] for r in g[n]]) for n in sizes]
    steps = [g[n][0]["steps"] for n in sizes]
    nodes = [g[n][0]["nodes"] for n in sizes]
    per = [med_min_max([r["compute"] / (r["nodes"] * r["steps"]) * 1e9 for r in g[n]])
           for n in sizes]

    s_comp = slope(sizes, [c[0] for c in comp])
    s_steps = slope(sizes, steps)
    # pente sur les 3 plus grandes tailles : la ou le GPU est sature
    s_big = slope(sizes[-3:], [c[0] for c in comp[-3:]])

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))

    errbars(ax[0], sizes, comp)
    n0, t0 = sizes[0], comp[0][0]
    for p, st_, col in ((3, "--", "gray"), (4, ":", "black")):
        ax[0].plot(sizes, [t0 * (n / n0) ** p for n in sizes], st_, color=col,
                   label=f"Prediction $N^{p}$")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_title(f"Temps de calcul\npente globale {s_comp:.2f}, 3 plus grandes {s_big:.2f}")
    ax[0].set_ylabel("Temps de calcul (s)")
    ax[0].legend()

    ax[1].plot(sizes, steps, "o-", label="Mesure")
    ax[1].plot(sizes, [steps[0] * n / n0 for n in sizes], "--", color="gray",
               label="Prediction CFL $\\propto N$")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_title(f"Nombre de pas de temps\npente {s_steps:.2f}")
    ax[1].set_ylabel("Pas de temps")
    ax[1].legend()

    errbars(ax[2], sizes, per)
    ax[2].set_xscale("log")
    ax[2].set_title("Cout par noeud et par pas")
    ax[2].set_ylabel("ns / (noeud x pas)")

    for x in ax:
        x.set_xlabel("N (elements par direction)")
        x.set_xticks(sizes)
        x.set_xticklabels([str(n) for n in sizes])
        x.grid(True, which="both", alpha=0.3)
    fig.suptitle(a.label)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out, "scaling.png"), dpi=150)

    print("N, noeuds, pas, calcul_med(s), ns/(noeud*pas)")
    for n, nd, s, c, p in zip(sizes, nodes, steps, comp, per):
        print(f"{n}, {nd}, {s}, {c[0]:.2f}, {p[0]:.2f}")
    print(f"Pente temps {s_comp:.2f} (3 plus grandes : {s_big:.2f}), pente pas {s_steps:.2f}")

if __name__ == "__main__":
    main()
