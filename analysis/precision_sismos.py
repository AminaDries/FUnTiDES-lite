"""Précision de l'in-situ des sismos : compare les résultats in-situ et ad-hoc
d'un MÊME run (deux runs GPU différents ne donnent pas exactement les mêmes floats).

Usage :
    python3 analysis/precision_sismos.py DOSSIER

DOSSIER contient :
    stats_sismos.csv, velocity_sismos.csv                  (ad-hoc : sismos_adhoc.py)
    insitu_sismos.csv, insitu_velocity_sismos.csv          (in-situ : --insitu-sismos)
Écrit DOSSIER/precision_sismos.csv : écart relatif maximal par grandeur.
"""
import os
import sys

import numpy as np


def ecart_relatif(a, b):
    """|a - b| / |b|, avec 0 si les deux valent 0 (pas de division par 0)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    denom = np.where(b != 0, np.abs(b), 1.0)
    return np.abs(a - b) / denom


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dossier = sys.argv[1]
    lire = lambda nom: np.genfromtxt(os.path.join(dossier, nom), delimiter=",",
                                     names=True, dtype=None, encoding="utf-8")

    adhoc, insitu = lire("stats_sismos.csv"), lire("insitu_sismos.csv")
    lignes = []

    # 1) statistiques par récepteur : colonnes présentes dans les deux fichiers
    for col in insitu.dtype.names:
        if col in ("receiver", "x", "y", "z") or col not in adhoc.dtype.names:
            continue
        lignes.append((col, ecart_relatif(insitu[col], adhoc[col]).max()))

    # 2) vitesses estimées par régression
    v_adhoc, v_insitu = lire("velocity_sismos.csv"), lire("insitu_velocity_sismos.csv")
    for i, methode in enumerate(v_adhoc["method"]):
        for col in ("velocity", "t0"):
            e = ecart_relatif(v_insitu[col][i], v_adhoc[col][i])
            lignes.append((f"{col}_{methode}", float(e)))

    sortie = os.path.join(dossier, "precision_sismos.csv")
    with open(sortie, "w") as f:
        f.write("quantity,max_rel_error\n")
        for nom, e in lignes:
            f.write(f"{nom},{e:.3g}\n")

    for nom, e in lignes:
        print(f"{nom:20s} écart relatif max = {e:.3g}")
    print(f"Résultat écrit dans {sortie}")


if __name__ == "__main__":
    main()
