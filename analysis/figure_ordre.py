#!/usr/bin/env python3
import argparse
import glob
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lecture_bin import lire_bin
from ordre_noeuds import lire_entiers, octets_rle, entrelacer

BLEU, ORANGE, TEXTE, GRILLE = "#2a78d6", "#eb6834", "#0b0b0b", "#e3e2de"

def construire_ordres(xyz):
    idx = [np.unique(xyz[:, d], return_inverse=True)[1] for d in range(3)]
    bits = int(max(i.max() for i in idx)).bit_length()
    i, j, k = (x.astype(np.uint64) for x in idx)
    centre = (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    r = np.linalg.norm(xyz - centre, axis=1)
    return {
        "origine": np.arange(xyz.shape[0]),
        "x puis y puis z": np.lexsort((xyz[:, 2], xyz[:, 1], xyz[:, 0])),
        "z puis y puis x": np.lexsort((xyz[:, 0], xyz[:, 1], xyz[:, 2])),
        "Morton": np.argsort(entrelacer(i, j, k, bits), kind="stable"),
        "distance au centre": np.argsort(np.round(r, 6), kind="stable"),
    }

def taux_par_ordre(dossier, ordres):
    fichiers = sorted(glob.glob(os.path.join(dossier, "snapshot_*.bin")))
    brut = 0
    totaux = {nom: 0 for nom in ordres}
    for f in fichiers:
        q, largeur = lire_entiers(f)
        brut += q.size * largeur
        for nom, p in ordres.items():
            totaux[nom] += octets_rle(q[p], largeur)
    return {nom: brut / t for nom, t in totaux.items()}

def nb_series(v):
    return int(1 + np.count_nonzero(v[1:] != v[:-1]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q8", required=True, help="dossier de snapshots q8 sans RLE")
    ap.add_argument("--q16", required=True, help="dossier de snapshots q16 sans RLE")
    ap.add_argument("--coords", required=True)
    ap.add_argument("--pas", type=int, default=300, help="snapshot montre en haut")
    ap.add_argument("--png", default="ordre_noeuds.png")
    a = ap.parse_args()

    _, xyz = lire_bin(a.coords)
    xyz = xyz.reshape(-1, 3).astype(np.float64)
    ordres = construire_ordres(xyz)
    t8 = taux_par_ordre(a.q8, ordres)
    t16 = taux_par_ordre(a.q16, ordres)

    q, _ = lire_entiers(os.path.join(a.q8, f"snapshot_{a.pas:06d}.bin"))
    gauche, droite = q, q[ordres["distance au centre"]]

    plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#8a8984", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e"})
    fig = plt.figure(figsize=(11, 8.2), facecolor="#fcfcfb")
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.5, wspace=0.12)

    for col, (v, titre, c) in enumerate([(gauche, "Ordre d'origine du maillage", BLEU),
                                         (droite, "Ordre par distance au centre", ORANGE)]):
        ax = fig.add_subplot(gs[0, col])
        ax.plot(v, lw=0.6, color=c)
        ax.set_title(f"{titre}\n{nb_series(v):,} séries de valeurs identiques".replace(",", " "),
                     loc="left", fontsize=10.5, color=TEXTE)
        ax.set_xlabel("position dans le fichier (numéro de nœud)")
        ax.set_ylim(-5, 262)
        ax.set_facecolor("#fcfcfb")
        ax.grid(axis="y", color=GRILLE, lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if col == 0:
            ax.set_ylabel("valeur quantifiée (0 à 255)")
        else:
            ax.set_yticklabels([])

    ax = fig.add_subplot(gs[1, :])
    noms = list(ordres.keys())
    x = np.arange(len(noms))
    w = 0.36
    b1 = ax.bar(x - w / 2 - 0.01, [t8[n] for n in noms], w - 0.02, color=BLEU, label="q8 + RLE", zorder=3)
    b2 = ax.bar(x + w / 2 + 0.01, [t16[n] for n in noms], w - 0.02, color=ORANGE, label="q16 + RLE", zorder=3)
    haut = max(max(t8.values()), max(t16.values()))
    for barres in (b1, b2):
        for b in barres:
            v = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, v + haut * 0.015, f"×{v:.2f}".replace(".", ","),
                    ha="center", fontsize=9.5, color=TEXTE)
    ax.set_xticks(x)
    ax.set_xticklabels(noms)
    ax.set_ylabel("taux de compression du RLE")
    ax.set_ylim(0, haut * 1.18)
    ax.set_facecolor("#fcfcfb")
    ax.grid(axis="y", color=GRILLE, lw=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, loc="upper left", ncol=2)
    nb = len(glob.glob(os.path.join(a.q8, "snapshot_*.bin")))
    ax.set_title(f"Taux de compression du RLE selon l'ordre des nœuds ({nb} snapshots)",
                 loc="left", fontsize=10.5, color=TEXTE)
    fig.suptitle("Effet de l'ordre de parcours des nœuds sur le RLE", x=0.07, ha="left",
                 fontsize=13, color=TEXTE, y=0.97)
    fig.text(0.07, 0.015, f"Haut : snapshot du pas {a.pas}, en q8. Bas : tous les snapshots.",
             fontsize=8.5, color="#52514e")
    fig.savefig(a.png, dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"Figure -> {a.png}")

if __name__ == "__main__":
    main()
