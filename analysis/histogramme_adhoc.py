"""Histogrammes ad-hoc de la pression

Pour chaque snapshot, on compte combien de noeuds ont une pression dans chaque classe.
Les bornes sont FIXES et identiques pour tous les snapshots : [-borne, +borne].

"""
import argparse
import csv
import os
import sys
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "visualisation"))
from plot_snapshot import lire_snapshot, lister_snapshots


def borne_depuis_stats(fichier):
    """Plus grand max_abs de toute la simulation, lu dans stats_snapshots.csv."""
    with open(fichier) as f:
        return max(float(ligne["max_abs"]) for ligne in csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dossier")
    ap.add_argument("--stats", help="stats_snapshots.csv : sert à fixer la borne")
    ap.add_argument("--borne", type=float, help="borne choisie à la main (prioritaire)")
    ap.add_argument("--bins", type=int, default=50, help="nombre de classes")
    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--out", default="histogrammes.csv")
    ap.add_argument("--png", default="histogrammes.png")
    args = ap.parse_args()

    if args.borne is not None:
        borne = args.borne
    elif args.stats:
        borne = borne_depuis_stats(args.stats)
    else:
        sys.exit("Il faut --borne ou --stats pour connaître les bornes de l'histogramme.")
    print(f"Bornes de l'histogramme : [-{borne:.4f}, +{borne:.4f}], {args.bins} classes")

    lignes, histos, energies = [], [], []
    for pas, chemin in lister_snapshots(args.dossier):
        t0 = time.perf_counter()
        data = lire_snapshot(chemin)
        t1 = time.perf_counter()
        p = data[:, 3].astype(np.float64)
        comptes, bords = np.histogram(p, bins=args.bins, range=(-borne, borne))
        t2 = time.perf_counter()
        histos.append(comptes)
        energies.append(float(np.sum(p**2)))
        ligne = {"step": pas, "t": pas * args.dt, "borne": borne, "nb_bins": args.bins,
                 "hors_bornes": len(p) - int(comptes.sum()),
                 "read_s": t1 - t0, "hist_s": t2 - t1}
        ligne.update({f"count_{k}": int(c) for k, c in enumerate(comptes)})
        lignes.append(ligne)

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print(f"{len(lignes)} histogrammes -> {args.out}")

    ipic = int(np.argmax(energies))
    cas = [(f"Pic d'énergie (t = {lignes[ipic]['t']:.3f} s)", histos[ipic]),
           (f"Dernier snapshot (t = {lignes[-1]['t']:.3f} s)", histos[-1]),
           ("Cumul de tous les snapshots", np.sum(histos, axis=0))]
    centres = (bords[:-1] + bords[1:]) / 2
    largeur = bords[1] - bords[0]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (titre, c) in zip(axes, cas):
        ax.bar(centres, c, width=largeur)
        ax.set_yscale("log")
        ax.set_title(titre)
        ax.set_xlabel("pression")
        ax.set_ylabel("nombre de nœuds (échelle log)")
    fig.tight_layout()
    fig.savefig(args.png, dpi=120)
    print(f"Figure -> {args.png}")


if __name__ == "__main__":
    main()