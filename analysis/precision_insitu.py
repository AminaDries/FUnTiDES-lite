"""Precision in-situ contre ad-hoc des analyses de snapshots, sur UN MEME run.

Le run doit avoir ete lance avec --snapshots ET --insitu-stats --insitu-hist,
meme intervalle (--snap-interval = --insitu-interval) et memes bornes/classes
d'histogramme. Puis stats_adhoc.py et histogramme_adhoc.py sur les snapshots.

Compare pas par pas :
  - stats : min, max, mean, var, max_abs, energie (ecart relatif au max |valeur|)
  - histogramme : nombre de noeuds classes differemment (somme |diff| / 2)

Usage :
  python3 analysis/precision_insitu.py --stats-adhoc stats_adhoc.csv \
      --stats-insitu insitu_stats.csv --hist-adhoc hist_adhoc.csv \
      --hist-insitu insitu_hist.csv [--out precision_insitu.txt]
"""
import argparse
import csv


def lire(fichier):
    with open(fichier) as f:
        return {int(float(l["step"])): l for l in csv.DictReader(f)}


def comptes(ligne, nbins):
    return [int(float(ligne[f"count_{i}"])) for i in range(nbins)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats-adhoc", required=True)
    ap.add_argument("--stats-insitu", required=True)
    ap.add_argument("--hist-adhoc")
    ap.add_argument("--hist-insitu")
    ap.add_argument("--out")
    a = ap.parse_args()
    lignes = []

    sa, si = lire(a.stats_adhoc), lire(a.stats_insitu)
    pas = sorted(set(sa) & set(si))
    lignes.append(f"Pas communs : {len(pas)} (ad-hoc {len(sa)}, in-situ {len(si)})")
    for c in ["min", "max", "mean", "var", "max_abs", "energie"]:
        echelle = max(abs(float(si[p][c])) for p in pas) or 1.0
        ecart = max(abs(float(sa[p][c]) - float(si[p][c])) for p in pas)
        lignes.append(f"  {c:8s} ecart max {ecart:.3e}  (relatif {ecart / echelle:.3e})")

    if a.hist_adhoc and a.hist_insitu:
        ha, hi = lire(a.hist_adhoc), lire(a.hist_insitu)
        pas_h = sorted(set(ha) & set(hi))
        nb = int(float(hi[pas_h[0]]["nb_bins"]))
        pire, total, noeuds = 0, 0, 0
        for p in pas_h:
            ca, ci = comptes(ha[p], nb), comptes(hi[p], nb)
            d = sum(abs(x - y) for x, y in zip(ca, ci)) // 2
            pire, total = max(pire, d), total + d
            noeuds = max(noeuds, sum(ci) + int(float(hi[p]["sous"])) + int(float(hi[p]["sur"])))
        lignes.append(f"Histogramme : {len(pas_h)} pas, {nb} classes, {noeuds} noeuds par pas")
        lignes.append(f"  noeuds classes differemment : max {pire} par pas, total {total}")
        lignes.append("  (ecarts possibles a la frontiere d'une classe : les snapshots CSV"
                      " sont arrondis a l'ecriture)")

    texte = "\n".join(lignes)
    print(texte)
    if a.out:
        with open(a.out, "w") as f:
            f.write(texte + "\n")


if __name__ == "__main__":
    main()
