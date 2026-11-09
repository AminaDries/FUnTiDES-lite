#!/usr/bin/env python3
import argparse
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TAILLES = ["S", "M", "L"]
LIBELLE = {"S": "S (50³)", "M": "M (100³)", "L": "L (200³)"}
COULEUR = {"q8": "#2a78d6", "q8_rle": "#eb6834", "q16_rle": "#1baf7a", "q8_rle_host": "#6250d6"}
NOM = {"q8": "8 bits", "q8_rle": "8 bits + RLE", "q16_rle": "16 bits + RLE",
       "q8_rle_host": "8 bits + RLE, quantifié sur le processeur"}
ENCRE, ENCRE2, GRILLE, FOND = "#0b0b0b", "#52514e", "#e3e2dd", "#fcfcfb"

plt.rcParams.update({"font.size": 11, "axes.edgecolor": GRILLE, "axes.labelcolor": ENCRE2,
                     "xtick.color": ENCRE2, "ytick.color": ENCRE2, "figure.facecolor": FOND,
                     "axes.facecolor": FOND, "savefig.facecolor": FOND})


def virgule(texte):
    return texte.replace(".", ",")


def style(ax):
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    ax.yaxis.grid(True, color=GRILLE, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_xticks(range(3))
    ax.set_xticklabels([LIBELLE[t] for t in TAILLES])


def barres(ax, modes, valeurs, format_, largeur):
    n = len(modes)
    for j, mode in enumerate(modes):
        xs = [i + (j - (n - 1) / 2) * largeur for i in range(3)]
        for x, v in zip(xs, valeurs[mode]):
            ax.bar(x, v, largeur * 0.88, color=COULEUR[mode], label=NOM[mode] if x == xs[0] else None)
            ax.annotate(format_(v), (x, v), ha="center", va="bottom" if v >= 0 else "top",
                        fontsize=9.5, color=ENCRE, xytext=(0, 3 if v >= 0 else -3),
                        textcoords="offset points")


def enregistrer(fig, titre, note, chemin):
    fig.suptitle(titre, x=0.06, ha="left", fontsize=14, color=ENCRE, fontweight="bold")
    fig.text(0.06, 0.02, note, fontsize=8.5, color=ENCRE2)
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    fig.savefig(chemin, dpi=200)
    plt.close(fig)
    print("écrit :", chemin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("resultats", help="resultats.csv de la campagne GPU")
    ap.add_argument("--out", required=True, help="dossier des figures")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lignes = list(csv.DictReader(open(a.resultats)))

    def med(t, m, col):
        return statistics.median(float(r[col]) for r in lignes if r["taille"] == t and r["mode"] == m)

    def octets_snapshots(t, m):
        noeuds = med(t, m, "nb_nodes")
        return med(t, m, "octets_snapshots") - (12 * noeuds + 32)

    conditions = "Médiane de 5 répétitions, GPU RTX 5050 portable."

    modes = ["q8", "q8_rle", "q16_rle"]
    gain = {m: [octets_snapshots(t, "bin") / octets_snapshots(t, m) for t in TAILLES] for m in modes}
    fig, ax = plt.subplots(figsize=(9, 5.4))
    barres(ax, modes, gain, lambda v: virgule("÷%.1f" % v), 0.26)
    style(ax)
    ax.set_ylabel("Facteur de réduction de la taille des snapshots")
    ax.set_ylim(0, 8)
    ax.legend(frameon=False, loc="upper left", ncol=3, fontsize=10)
    enregistrer(fig, "8 bits + RLE réduit les snapshots d'un facteur 6,4 à 6,9",
                "Référence = snapshots float32 sans compression. Snapshots seuls (coords.bin exclu). 30 snapshots, 1,5 s simulées.\n" + conditions,
                os.path.join(a.out, "fig1_memoire.png"))

    modes = ["q8", "q8_rle", "q16_rle", "q8_rle_host"]
    ecart = {m: [100 * (med(t, m, "wall_s") / med(t, "bin", "wall_s") - 1) for t in TAILLES] for m in modes}
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    barres(ax, modes, ecart,
           lambda v: "0 %" if abs(v) < 0.05 else virgule(("%+.1f %%" % v).replace("-", "−")), 0.2)
    ax.axhline(0, color=ENCRE2, linewidth=1.2)
    style(ax)
    ax.set_ylabel("Variation de la durée totale\nvs sans compression (%)")
    ax.set_ylim(-14, 30)
    ax.legend(frameon=False, loc="upper left", fontsize=9.5, ncol=2)
    enregistrer(fig, "Le 8 bits seul accélère la simulation de 6 à 9 % (M, L) ; le RLE réduit ce gain",
                "Sous 0 = plus rapide que sans compression ; au-dessus = plus lent. Sans fsync.\n" + conditions,
                os.path.join(a.out, "fig2_temps.png"))



if __name__ == "__main__":
    main()
