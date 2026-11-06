"""Figures du benchmark des sismos : workflow ad-hoc vs in-situ, configurations S/M/L.

Lit les raw.csv produits par bench_sismos.py (une ou plusieurs campagnes) et trace :
  fig_sismos_cout.png     cout total de chaque workflow (ms) par taille,
                          mediane + barre min-max (runs mesures, chauffe exclue)
  fig_sismos_surcout.png  ce cout rapporte au temps de calcul de la simulation (%)

  ad-hoc  = ecriture de seismos.csv + fsync + lecture Python + analyse Python
  in-situ = mise a jour en flux dans la boucle + analyses de fin de simulation

Usage (depuis la racine du depot) :
    python3 benchmark/plot_sismos_bench.py benchmark/results/campagne_gpu_*/sismos/raw.csv
Options :
    --out DOSSIER   dossier des figures   [benchmark/results/figures_sismos]
"""
import argparse
import csv
import os
import statistics

import matplotlib

matplotlib.use("Agg")  # pas de fenetre : on enregistre directement les images
import matplotlib.pyplot as plt

NOMS = {50: "S", 100: "M", 200: "L"}
COULEUR = {"adhoc": "#2a78d6", "insitu": "#eb6834"}   # bleu / orange
TEXTE, TEXTE_2, GRILLE = "#0b0b0b", "#52514e", "#e4e3df"
ETIQUETTE = {"adhoc": "ad-hoc (écriture + fsync + lecture + analyse)",
             "insitu": "in-situ (flux dans la boucle + analyses de fin)"}


def lire(fichiers):
    """Une ligne par run mesure du mode 'avec' (la chauffe, run 0, est exclue)."""
    runs = []
    for f in fichiers:
        for r in csv.DictReader(open(f)):
            if r["mode"] != "avec" or int(r["run"]) < 1:
                continue
            x = lambda c: float(r[c])
            runs.append({
                "ex": int(r["ex"]),
                "nodes": int(r["nb_nodes"]),
                "calcul": x("compute_time_s"),
                "adhoc": x("seismo_write_time_s") + x("seismo_fsync_time_s")
                         + x("adhoc_read_s") + x("adhoc_analysis_s"),
                "insitu": x("insitu_sismos_loop_s") + x("insitu_sismos_final_s"),
            })
    return runs


def stats(valeurs):
    return statistics.median(valeurs), min(valeurs), max(valeurs)


def style(ax, titre_y):
    ax.set_ylabel(titre_y, color=TEXTE_2)
    ax.grid(axis="y", color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
    ax.tick_params(colors=TEXTE_2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="+", help="fichiers raw.csv de bench_sismos.py")
    ap.add_argument("--out", default=os.path.join("benchmark", "results", "figures_sismos"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    runs = lire(args.raw)
    tailles = sorted({r["ex"] for r in runs})
    noms = [f"{NOMS.get(t, t)} ({t}³)\n{next(r['nodes'] for r in runs if r['ex'] == t) / 1e6:.1f} M nœuds"
            for t in tailles]

    # --- Figure 1 : cout de chaque workflow (ms), barres groupees + min-max
    fig, ax = plt.subplots(figsize=(7, 4.2))
    largeur = 0.36
    for k, (wf, dx) in enumerate((("adhoc", -largeur / 2), ("insitu", largeur / 2))):
        med, bas, haut = zip(*[stats([r[wf] * 1000 for r in runs if r["ex"] == t]) for t in tailles])
        xs = [i + dx for i in range(len(tailles))]
        ax.bar(xs, med, width=largeur - 0.04, color=COULEUR[wf], label=ETIQUETTE[wf])
        ax.errorbar(xs, med, yerr=[[m - b for m, b in zip(med, bas)], [h - m for m, h in zip(med, haut)]],
                    fmt="none", ecolor=TEXTE_2, capsize=3, linewidth=1)
        for x, m, h in zip(xs, med, haut):
            ax.annotate(f"{m:.0f} ms", (x, h), xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=8, color=TEXTE)
    ax.set_xticks(range(len(tailles)), noms)
    style(ax, "temps (ms)")
    ax.set_title("Sismos : coût du workflow ad-hoc et de l'in-situ\n"
                 "médiane, barre = min–max (5 runs, chauffe exclue)", color=TEXTE, fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.4)
    fig.tight_layout()
    f1 = os.path.join(args.out, "fig_sismos_cout.png")
    fig.savefig(f1, dpi=150)

    # --- Figure 2 : cout rapporte au temps de calcul (%), echelle log
    fig, ax = plt.subplots(figsize=(7, 4.2))
    nodes = [next(r["nodes"] for r in runs if r["ex"] == t) for t in tailles]
    for wf, marque in (("adhoc", "o"), ("insitu", "s")):
        med, bas, haut = zip(*[stats([100 * r[wf] / r["calcul"] for r in runs if r["ex"] == t]) for t in tailles])
        ax.plot(nodes, med, color=COULEUR[wf], linewidth=2, marker=marque, markersize=8, label=ETIQUETTE[wf])
        ax.fill_between(nodes, bas, haut, color=COULEUR[wf], alpha=0.15, linewidth=0)
        ax.annotate(f"{med[-1]:.2g} %", (nodes[-1], med[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=8, color=TEXTE)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(nodes, noms)
    ax.minorticks_off()
    style(ax, "coût / temps de calcul (%)")
    ax.set_title("Sismos : surcoût relatif au calcul de la simulation\n"
                 "le coût est constant, le calcul croît avec le maillage", color=TEXTE, fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    f2 = os.path.join(args.out, "fig_sismos_surcout.png")
    fig.savefig(f2, dpi=150)

    # tableau des valeurs tracees (meme contenu que les figures, en texte)
    with open(os.path.join(args.out, "valeurs.csv"), "w") as f:
        f.write("taille,nodes,calcul_s,adhoc_ms,insitu_ms,adhoc_pct,insitu_pct\n")
        for t, n in zip(tailles, nodes):
            rs = [r for r in runs if r["ex"] == t]
            c = statistics.median(r["calcul"] for r in rs)
            a = statistics.median(r["adhoc"] for r in rs)
            i = statistics.median(r["insitu"] for r in rs)
            f.write(f"{NOMS.get(t, t)},{n},{c:.4g},{a*1000:.4g},{i*1000:.4g},{100*a/c:.3g},{100*i/c:.3g}\n")
    print("Figures :", f1, "et", f2)
    print("Valeurs :", os.path.join(args.out, "valeurs.csv"))


if __name__ == "__main__":
    main()
