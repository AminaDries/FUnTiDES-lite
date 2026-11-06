"""Trace les sismogrammes (pression en fonction du temps, un par récepteur).

Usage :
    python visualisation/plot_sismos.py DOSSIER [SORTIE.png]

DOSSIER contient :
    seismos.csv    -> time,rcv0,rcv1,...
    receivers.csv  -> id,x,y,z        (optionnel : sert à la légende)

Exemples :
    python visualisation/plot_sismos.py output_fake
    python visualisation/plot_sismos.py output_fake mes_sismos.png
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")  # pas de fenêtre : on enregistre directement une image
import matplotlib.pyplot as plt
import numpy as np


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    dossier = sys.argv[1]
    sortie = sys.argv[2] if len(sys.argv) > 2 else os.path.join(dossier, "sismos.png")

    # --- 1) Lire seismos.csv : 1ère colonne = temps, les autres = récepteurs
    chemin = os.path.join(dossier, "seismos.csv")
    if not os.path.exists(chemin):
        sys.exit(f"Fichier introuvable : {chemin}")
    data = np.genfromtxt(chemin, delimiter=",", names=True)
    noms = data.dtype.names           # ('time', 'rcv0', 'rcv1', ...)
    t = data[noms[0]]

    # --- 2) Lire receivers.csv si présent : positions pour la légende
    positions = {}
    chemin_rcv = os.path.join(dossier, "receivers.csv")
    if os.path.exists(chemin_rcv):
        r = np.genfromtxt(chemin_rcv, delimiter=",", names=True)
        r = np.atleast_1d(r)          # cas d'un seul récepteur
        for ligne in r:
            positions[f"rcv{int(ligne['id'])}"] = (ligne["x"], ligne["y"], ligne["z"])

    # --- 3) Tracer : un sous-graphique par récepteur, même échelle de temps
    n = len(noms) - 1
    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(8, 2.2 * n + 1), squeeze=False)
    for ax, nom in zip(axes[:, 0], noms[1:]):
        ax.plot(t, data[nom], linewidth=1.2)
        etiquette = nom
        if nom in positions:
            x, y, z = positions[nom]
            etiquette += f"  ({x:g}, {y:g}, {z:g})"
        ax.set_ylabel("pression")
        ax.set_title(etiquette, fontsize=9, loc="left")
        ax.grid(alpha=0.3)
    axes[-1, 0].set_xlabel("temps (s)")
    fig.suptitle("Sismogrammes")
    fig.tight_layout()
    fig.savefig(sortie, dpi=150)
    print("Image écrite :", sortie)


if __name__ == "__main__":
    main()