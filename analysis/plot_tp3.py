"""Figures du TP3 piste B (sorties pilotees par la simulation).

A partir du dossier ecrit par benchmark/bench_tp3.py :
  tp3_repartition.png  ou passe le temps, par mode, pour la plus grande taille
  tp3_declenchement.png  sismos des recepteurs, instants des snapshots declenches,
                         instants des snapshots periodiques et instant d'arret

Usage :
  python3 analysis/plot_tp3.py benchmark/results/tp3_sorties_pilotees [--taille 200]
"""
import argparse
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODES = [("ref", "sismos seuls"), ("periodique", "snapshots periodiques"),
         ("declenche", "snapshots declenches"), ("declenche_stop", "declenches + arret")]
LABEL = {50: "S", 100: "M", 200: "L"}


def f(l, k):
    try:
        return float(l.get(k, ""))
    except ValueError:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier")
    ap.add_argument("--taille", type=int, help="taille pour les figures (defaut : la plus grande)")
    a = ap.parse_args()
    d = a.dossier
    with open(os.path.join(d, "runs.csv")) as fr:
        runs = list(csv.DictReader(fr))
    taille = a.taille or max(int(r["taille"]) for r in runs)
    nom = f"{LABEL.get(taille, taille)} ({taille}³)"

    # ---- Figure 1 : repartition du temps total ----------------------------
    parts = [("calcul", "#4c566a"), ("ecriture des snapshots", "#d1495b"),
             ("copie GPU->hote", "#edae49"), ("reste (init, sismos, fin)", "#c8ccd2")]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    totaux, textes = [], []
    for k, (mode, label) in enumerate(MODES):
        g = [r for r in runs if int(r["taille"]) == taille and r["mode"] == mode]
        if not g:
            continue
        calcul = statistics.median(f(r, "compute_time_s") for r in g)
        ecr = statistics.median(f(r, "snapshot_write_time_s") + f(r, "trigger_write_time_s") for r in g)
        copie = statistics.median(f(r, "snapshot_copy_s") + f(r, "trigger_copy_s") for r in g)
        total = statistics.median(f(r, "wall_s") for r in g)
        ecr -= copie  # la copie est comptee dans le temps d'ecriture du snapshot
        vals = [calcul, ecr, copie, max(total - calcul - ecr - copie, 0.0)]
        gauche = 0.0
        for v, (pn, c) in zip(vals, parts):
            ax.barh(k, v, left=gauche, color=c, edgecolor="white", linewidth=1,
                    label=pn if k == 0 else None)
            gauche += v
        pas = statistics.median(f(r, "nb_steps") for r in g)
        totaux.append(gauche)
        textes.append((k, gauche, f"{total:.0f} s  ({pas:.0f} pas)"))
    xmax = max(totaux)
    for k, x, txt in textes:
        ax.text(x + 0.01 * xmax, k, txt, va="center", fontsize=8)
    ax.set_xlim(0, 1.22 * xmax)
    ax.set_yticks(range(len(MODES)), [l for _, l in MODES])
    ax.invert_yaxis()
    ax.set_xlabel("temps (s), mediane des runs")
    ax.set_title(f"Ou passe le temps, {nom}, GPU")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.4, -0.22))
    fig.tight_layout()
    fig.savefig(os.path.join(d, "tp3_repartition.png"), dpi=150)

    # ---- Figure 2 : quand la simulation ecrit et quand elle s'arrete --------
    base = os.path.join(d, str(taille))
    sis = os.path.join(base, "declenche_stop", "run1", "seismos.csv")
    if not os.path.isfile(sis):
        sis = os.path.join(base, "declenche", "run1", "seismos.csv")
    trig = os.path.join(base, "declenche_stop", "run1", "triggers", "triggers.csv")
    ref = os.path.join(base, "ref", "run1", "seismos.csv")
    if os.path.isfile(ref) and os.path.isfile(trig):
        s = np.loadtxt(ref, delimiter=",", skiprows=1)
        with open(trig) as ft:
            tr = list(csv.DictReader(ft))
        g = [r for r in runs if int(r["taille"]) == taille and r["mode"] == "declenche_stop"]
        dt = f(g[0], "dt")
        t_stop = statistics.median(f(r, "stop_step") for r in g) * dt
        interval = f(next(r for r in runs if r["mode"] == "periodique"), "snap_interval")
        t, p = s[:, 0], s[:, 1:]
        ech = 0.45 / np.max(np.abs(p), axis=0)  # chaque trace normalisee
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        for k in np.arange(0, t[-1], interval * dt):
            ax.axvline(k, color="#d1495b", alpha=0.18, lw=1)
        for r in range(p.shape[1]):
            dist = float(tr[r]["distance"])
            ax.plot(t, r + p[:, r] * ech[r], color="#4c566a", lw=0.8)
            tt = float(tr[r]["t"])
            if tt >= 0:
                ax.plot([tt, tt], [r - 0.45, r + 0.45], color="#edae49", lw=2.2)
            ax.text(-0.02, r, f"{dist:.0f} m", ha="right", va="center", fontsize=8)
        ax.axvspan(t_stop, t[-1], color="#00798c", alpha=0.12)
        ax.set_ylim(-0.7, p.shape[1] + 0.05)
        ax.text(t_stop + 0.01, p.shape[1] - 0.2, f"arret anticipe, t = {t_stop:.3f} s",
                fontsize=8, color="#00798c", va="center")
        ax.set_yticks([])
        ax.set_xlim(-0.12, t[-1])
        ax.set_xlabel("temps (s)")
        ax.set_title(f"Sismos et instants d'ecriture, {nom}")
        ax.spines[["top", "right", "left"]].set_visible(False)
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch
        ax.legend(handles=[Line2D([], [], color="#d1495b", alpha=0.5, label="snapshot periodique (30)"),
                           Line2D([], [], color="#edae49", lw=2.2, label="snapshot declenche (1 par recepteur)"),
                           Patch(color="#00798c", alpha=0.25, label="pas non calcules (arret)")],
                  frameon=False, fontsize=8, loc="upper center", ncol=3,
                  bbox_to_anchor=(0.5, -0.13))
        fig.tight_layout()
        fig.savefig(os.path.join(d, "tp3_declenchement.png"), dpi=150)
    print("Figures ecrites dans", d)


if __name__ == "__main__":
    main()
