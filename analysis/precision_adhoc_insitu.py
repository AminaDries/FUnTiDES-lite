"""Precision de l'ad-hoc (snapshots tous les k pas) par rapport a l'in-situ (tous les pas),
sur UN SEUL run : il faut un run avec --snapshots --snap-interval 1 ET
--insitu-stats --insitu-interval 1. Entrees : sortie de stats_adhoc.py et insitu_stats.csv."""
import argparse
import csv

import numpy as np


def lire(fichier):
    with open(fichier) as f:
        lignes = list(csv.DictReader(f))
    return {c: np.array([float(l[c]) for l in lignes]) for c in lignes[0].keys()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("adhoc", help="CSV de stats_adhoc.py")
    ap.add_argument("insitu", help="CSV in-situ (--insitu-file)")
    ap.add_argument("--k", type=int, nargs="+", default=[1, 5, 10, 20, 50, 100],
                    help="intervalles de snapshots simules (en pas de temps)")
    ap.add_argument("--out", default="precision.csv")
    a = ap.parse_args()

    ad, ins = lire(a.adhoc), lire(a.insitu)
    pa = {int(s): i for i, s in enumerate(ad["step"])}
    pi = {int(s): i for i, s in enumerate(ins["step"])}
    steps = np.array(sorted(set(pa) & set(pi)))
    assert len(steps) > 1, "aucun pas commun entre les deux fichiers"
    A = {c: ad[c][[pa[s] for s in steps]] for c in ad}
    I = {c: ins[c][[pi[s] for s in steps]] for c in ins}
    print(f"{len(steps)} pas communs (de {steps[0]} a {steps[-1]})\n")

    print("1) Ecart de format, meme pas, meme run : ad-hoc (CSV arrondi) contre in-situ")
    for c in ("min", "max", "mean", "var", "max_abs", "energie"):
        if c == "mean":   # la moyenne est ~0 : on la rapporte a l'amplitude
            ref, note = np.maximum(np.abs(I["max_abs"]), 1e-30), "(rapporte a max_abs)"
        else:
            ref, note = np.maximum(np.abs(I[c]), 1e-30), ""
        print(f"   {c:8s} ecart relatif max : {np.max(np.abs(A[c] - I[c]) / ref):.2e} {note}")

    i_vrai = int(np.argmax(I["max_abs"]))
    pic_vrai, pas_vrai = I["max_abs"][i_vrai], steps[i_vrai]
    moy_amp, moy_en = I["max_abs"].mean(), I["energie"].mean()
    print(f"\n2) Echantillonnage. Verite (in-situ, tous les pas) : pic de max_abs = {pic_vrai:.5e} au pas {pas_vrai}\n")
    print(f"   {'k':>4s} {'points':>7s} {'pic ad-hoc':>12s} {'pas du pic':>10s} {'err pic %':>10s} {'err moy amp %':>14s} {'err moy energie %':>18s}")
    lignes = []
    for k in a.k:
        sel = steps % k == 0
        if sel.sum() < 2:
            continue
        ma, en = A["max_abs"][sel], A["energie"][sel]
        j = int(np.argmax(ma))
        l = {"k": k, "points": int(sel.sum()), "pic_adhoc": float(ma[j]), "pas_pic": int(steps[sel][j]),
             "err_pic_pct": 100 * (pic_vrai - ma[j]) / pic_vrai,
             "err_moy_amp_pct": 100 * (ma.mean() - moy_amp) / moy_amp,
             "err_moy_energie_pct": 100 * (en.mean() - moy_en) / moy_en}
        lignes.append(l)
        print(f"   {k:4d} {l['points']:7d} {l['pic_adhoc']:12.5e} {l['pas_pic']:10d} {l['err_pic_pct']:10.3f} {l['err_moy_amp_pct']:14.3f} {l['err_moy_energie_pct']:18.3f}")

    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print(f"\nTable -> {a.out}")


if __name__ == "__main__":
    main()
