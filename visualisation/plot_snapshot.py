"""Affiche une coupe 2D du champ de pression (snapshot), ou une animation de tous les snapshots.

Les fichiers lus sont ceux écrits par le solveur : snapshot_XXXXXX.csv avec les colonnes
    x,y,z,pressure      (une ligne par nœud)

Usage :
    python visualisation/plot_snapshot.py DOSSIER_SNAPSHOTS [options]

Options :
    --step N          numéro du pas de temps à afficher (défaut : le snapshot du milieu)
    --axis x|y|z      axe perpendiculaire à la coupe (défaut : z)
    --pos VALEUR      position de la coupe le long de l'axe (défaut : milieu du domaine)
    --receivers FICH  receivers.csv (id,x,y,z) : affiche les récepteurs sur la carte
    --out FICHIER     image de sortie (défaut : DOSSIER/coupe_stepN.png)
    --anim FICHIER    crée à la place une animation GIF avec TOUS les snapshots

Exemples :
    python visualisation/plot_snapshot.py output_fake/snapshots
    python visualisation/plot_snapshot.py output_fake/snapshots --step 100 --axis y
    python visualisation/plot_snapshot.py output_fake/snapshots --anim onde.gif
"""
import argparse
import glob
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")  # pas de fenêtre : on enregistre directement une image
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

AXES = {"x": 0, "y": 1, "z": 2}


def lister_snapshots(dossier):
    """Retourne [(numéro_de_pas, chemin), ...] triés par pas de temps."""
    fichiers = glob.glob(os.path.join(dossier, "snapshot_*.csv"))
    liste = []
    for f in fichiers:
        m = re.search(r"snapshot_(\d+)\.csv$", f)
        if m:
            liste.append((int(m.group(1)), f))
    if not liste:
        sys.exit(f"Aucun fichier snapshot_*.csv dans : {dossier}")
    return sorted(liste)


def lire_snapshot(chemin):
    """Lit un snapshot : retourne un tableau (nb_noeuds, 4) = x, y, z, pression."""
    return np.loadtxt(chemin, delimiter=",", skiprows=1)


def choisir_plan(coord, pos):
    """Choisit le plan de nœuds le plus proche de `pos` (milieu si pos est None)."""
    if pos is None:
        pos = (coord.min() + coord.max()) / 2
    valeurs = np.unique(np.round(coord, 6))
    return valeurs[np.argmin(np.abs(valeurs - pos))]


def extraire_coupe(data, axe, plan):
    """Garde les nœuds situés sur le plan, retourne (u, v, pression)."""
    tol = 1e-4 * (data[:, axe].max() - data[:, axe].min() + 1e-12)
    masque = np.abs(data[:, axe] - plan) <= tol
    autres = [i for i in range(3) if i != axe]
    return data[masque, autres[0]], data[masque, autres[1]], data[masque, 3]


def dessiner(ax, u, v, p, vmax, noms_axes, titre, recepteurs=None):
    niveaux = np.linspace(-vmax, vmax, 51)
    cs = ax.tricontourf(u, v, np.clip(p, -vmax, vmax), levels=niveaux, cmap="seismic")
    ax.set_aspect("equal")
    ax.set_xlabel(f"{noms_axes[0]} (m)")
    ax.set_ylabel(f"{noms_axes[1]} (m)")
    ax.set_title(titre, fontsize=10)
    if recepteurs is not None:
        ax.plot(recepteurs[0], recepteurs[1], "k^", markersize=7, markerfacecolor="yellow")
    return cs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("dossier")
    ap.add_argument("--step", type=int, default=None)
    ap.add_argument("--axis", choices=AXES.keys(), default="z")
    ap.add_argument("--pos", type=float, default=None)
    ap.add_argument("--receivers", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--anim", default=None)
    a = ap.parse_args()

    axe = AXES[a.axis]
    autres = [i for i in range(3) if i != axe]
    noms_axes = [list(AXES)[i] for i in autres]
    snaps = lister_snapshots(a.dossier)

    # Plan de coupe : calculé une fois sur le premier snapshot (le maillage ne change pas)
    premier = lire_snapshot(snaps[0][1])
    plan = choisir_plan(premier[:, axe], a.pos)

    # Récepteurs (optionnel) : on les projette sur le plan de la coupe
    recepteurs = None
    if a.receivers:
        r = np.atleast_2d(np.loadtxt(a.receivers, delimiter=",", skiprows=1))
        recepteurs = (r[:, 1 + autres[0]], r[:, 1 + autres[1]])

    if a.anim:
        # Échelle de couleur COMMUNE à toutes les images, sinon on ne voit plus l'onde évoluer
        coupes = []
        vmax = 0.0
        for pas, chemin in snaps:
            d = lire_snapshot(chemin)
            u, v, p = extraire_coupe(d, axe, plan)
            coupes.append((pas, u, v, p))
            vmax = max(vmax, np.abs(p).max())
        vmax = max(vmax, 1e-12)

        fig, ax = plt.subplots(figsize=(6, 5.2))
        # colorbar construite une fois, à partir de la première image
        cs0 = dessiner(ax, *coupes[0][1:], vmax, noms_axes, "", recepteurs)
        fig.colorbar(cs0, ax=ax, label="pression")

        def image(i):
            ax.clear()
            pas, u, v, p = coupes[i]
            dessiner(ax, u, v, p, vmax, noms_axes,
                     f"pas de temps {pas}  (coupe {a.axis} = {plan:g})", recepteurs)

        ani = animation.FuncAnimation(fig, image, frames=len(coupes), interval=400)
        ani.save(a.anim, writer=animation.PillowWriter(fps=3))
        print("Animation écrite :", a.anim)
        return

    # Image fixe : un seul snapshot
    if a.step is None:
        pas, chemin = snaps[len(snaps) // 2]
    else:
        choix = [s for s in snaps if s[0] == a.step]
        if not choix:
            sys.exit(f"Pas {a.step} introuvable. Disponibles : {[s[0] for s in snaps]}")
        pas, chemin = choix[0]

    d = lire_snapshot(chemin)
    u, v, p = extraire_coupe(d, axe, plan)
    vmax = max(np.abs(p).max(), 1e-12)

    fig, ax = plt.subplots(figsize=(6, 5.2))
    cs = dessiner(ax, u, v, p, vmax, noms_axes,
                  f"pas de temps {pas}  (coupe {a.axis} = {plan:g})", recepteurs)
    fig.colorbar(cs, ax=ax, label="pression")
    fig.tight_layout()
    sortie = a.out or os.path.join(a.dossier, f"coupe_step{pas}.png")
    fig.savefig(sortie, dpi=150)
    print("Image écrite :", sortie)


if __name__ == "__main__":
    main()