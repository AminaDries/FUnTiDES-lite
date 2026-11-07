#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lecture_bin import lire_bin

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("formats", nargs="+", help="noms des formats, ex : bin q8 q16")
    ap.add_argument("--racine", default=".", help="dossier contenant d_<format> et d_<format>rle")
    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--out", default="taux_rle.csv")
    ap.add_argument("--png", default="taux_rle.png")
    a = ap.parse_args()

    fichiers = sorted(glob.glob(os.path.join(a.racine, f"d_{a.formats[0]}", "snapshot_*.bin")))
    noms = [os.path.basename(f) for f in fichiers]
    pas = np.array([int(n[9:15]) for n in noms])
    lignes = [dict(pas=int(p)) for p in pas]
    taux = {}
    print(f"{'format':<8} {'sans RLE':>12} {'avec RLE':>12} {'taux':>8} {'identique':>10}")
    for fmt in a.formats:
        d0 = os.path.join(a.racine, f"d_{fmt}")
        d1 = os.path.join(a.racine, f"d_{fmt}rle")
        identique = True
        t = []
        s0 = s1 = 0
        for n in noms:
            identique &= bool(np.array_equal(lire_bin(os.path.join(d0, n))[1], lire_bin(os.path.join(d1, n))[1]))
            b0 = os.path.getsize(os.path.join(d0, n))
            b1 = os.path.getsize(os.path.join(d1, n))
            s0 += b0
            s1 += b1
            t.append(b0 / b1)
        taux[fmt] = np.array(t)
        for l, v in zip(lignes, t):
            l[f"taux_{fmt}"] = v
        print(f"{fmt:<8} {s0:>12d} {s1:>12d} {s0 / s1:>8.2f} {str(identique):>10}")

    zeros = np.array([np.mean(lire_bin(os.path.join(a.racine, "d_bin", n))[1] == 0) for n in noms])
    for l, z in zip(lignes, zeros):
        l["fraction_zeros_exacts"] = float(z)

    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)

    t = pas * a.dt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for fmt in a.formats:
        ax.plot(t, taux[fmt], marker="o", ms=3, label=f"{fmt} + RLE")
    ax.set_yscale("log")
    ax.set_xlabel("temps (s)")
    ax.set_ylabel("taux de compression du RLE (sans RLE / avec RLE)")
    ax2 = ax.twinx()
    ax2.plot(t, 100 * zeros, "k--", label="part de nœuds à 0 exact (référence)")
    ax2.set_ylabel("nœuds à 0 exact (%)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right")
    fig.tight_layout()
    fig.savefig(a.png, dpi=130)
    print(f"Table -> {a.out} ; figure -> {a.png}")

if __name__ == "__main__":
    main()
