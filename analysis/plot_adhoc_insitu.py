"""Fusion des deux campagnes GPU du TP2 et figures ad-hoc contre in-situ.

La campagne de la nuit (dossiers S, M, L) a des lignes in-situ GPU faites avec
la premiere version de l'histogramme (contention des atomiques) : on n'en garde
que sans / adhoc / adhoc_fsync / insitu_host. Les modes in-situ GPU viennent de
la reprise (dossiers S_insitu, M_insitu, L_insitu). Le Python ad-hoc a L vient
de L_python (1 run).

Usage :
  python3 analysis/plot_adhoc_insitu.py benchmark/results/campagne_gpu_tp2_final

Ecrit dans ce dossier : fusion.csv, resume_fusion.md, workflow.png, repartition_L.png
"""
import argparse
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TAILLES = ["S", "M", "L"]
NUIT = {"sans", "adhoc", "adhoc_fsync", "insitu_host"}
MODES = ["sans", "adhoc", "adhoc_fsync", "insitu_host", "insitu", "insitu_fsync"]


def lire(fichier):
    if not os.path.isfile(fichier):
        return []
    with open(fichier) as f:
        return list(csv.DictReader(f))


def val(ligne, cle):
    v = ligne.get(cle, "")
    return float(v) if v not in ("", None) else 0.0


def med(lignes, cle):
    return statistics.median(val(l, cle) for l in lignes)


def collecter(dossier):
    """{(taille, mode): [lignes]} selon les regles de fusion."""
    runs = {}
    for t in TAILLES:
        for l in lire(os.path.join(dossier, t, "runs.csv")):
            if l["mode"] in NUIT:
                runs.setdefault((t, l["mode"]), []).append(l)
        host_nuit = (t, "insitu_host") in runs
        for l in lire(os.path.join(dossier, f"{t}_insitu", "runs.csv")):
            # insitu_host de la nuit deja present en S et M : on garde celui-la
            if l["mode"] == "insitu_host" and host_nuit:
                continue
            runs.setdefault((t, l["mode"]), []).append(l)
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier")
    a = ap.parse_args()
    d = a.dossier
    runs = collecter(d)
    py_L = lire(os.path.join(d, "L_python", "runs.csv"))

    lignes = []
    for t in TAILLES:
        for m in MODES:
            r = runs.get((t, m))
            if not r:
                continue
            py = med(r, "py_total_s")
            if t == "L" and m.startswith("adhoc") and py == 0.0 and py_L:
                py = val(py_L[0], "py_total_s")  # 1 seul run a L
            lignes.append({
                "taille": t, "mode": m, "runs": len(r),
                "total_s": med(r, "wall_s"),
                "calcul_s": med(r, "compute_time_s"),
                "ecriture_s": med(r, "snapshot_write_time_s") + med(r, "insitu_write_s"),
                "fsync_s": med(r, "snapshot_sync_time_s"),
                "analyses_insitu_s": med(r, "insitu_stats_s") + med(r, "insitu_hist_s")
                                     + med(r, "insitu_vel_s"),
                "copie_gpu_hote_s": med(r, "snapshot_copy_s") + med(r, "insitu_copy_s"),
                "python_s": py,
                "workflow_s": med(r, "wall_s") + py,
                "volume_mo": (med(r, "snapshot_bytes") + med(r, "insitu_bytes")) / 1e6,
            })

    cles = list(lignes[0].keys())
    with open(os.path.join(d, "fusion.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cles)
        w.writeheader()
        w.writerows(lignes)

    with open(os.path.join(d, "resume_fusion.md"), "w") as f:
        f.write("# Ad-hoc contre in-situ, GPU, mediane des runs (campagnes fusionnees)\n\n")
        f.write("Workflow = simulation (total) + scripts Python (ad-hoc). "
                "Python a L : 1 seul run (L_python).\n\n")
        f.write("| taille | mode | runs | total (s) | calcul (s) | ecriture (s) | "
                "analyses in-situ (s) | copie GPU->hote (s) | Python (s) | workflow (s) | volume (Mo) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
        for l in lignes:
            f.write(f"| {l['taille']} | {l['mode']} | {l['runs']} | {l['total_s']:.2f} | "
                    f"{l['calcul_s']:.2f} | {l['ecriture_s']:.2f} | {l['analyses_insitu_s']:.3f} | "
                    f"{l['copie_gpu_hote_s']:.3f} | {l['python_s']:.1f} | {l['workflow_s']:.1f} | "
                    f"{l['volume_mo']:.0f} |\n")

    # --- Figure 1 : duree du workflow complet, par taille et par mode ---------
    montres = [("sans", "sans sortie", "#9aa0a6"),
               ("adhoc", "ad-hoc (snapshots + Python)", "#d1495b"),
               ("insitu_host", "in-situ sur l'hote", "#edae49"),
               ("insitu", "in-situ sur le GPU", "#00798c")]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    largeur = 0.2
    for i, (m, nom, c) in enumerate(montres):
        xs, ys = [], []
        for j, t in enumerate(TAILLES):
            l = next((l for l in lignes if l["taille"] == t and l["mode"] == m), None)
            if l:
                xs.append(j + (i - 1.5) * largeur)
                ys.append(l["workflow_s"])
        barres = ax.bar(xs, ys, largeur * 0.92, label=nom, color=c)
        ax.bar_label(barres, labels=[f"{y:.0f}" if y >= 10 else f"{y:.1f}" for y in ys],
                     fontsize=7, padding=2)
    ax.set_yscale("log")
    ax.set_xticks(range(len(TAILLES)), [f"{t} ({e}³)" for t, e in zip(TAILLES, (50, 100, 200))])
    ax.set_ylabel("duree du workflow (s, echelle log)")
    ax.set_title("Workflow complet : simulation + analyses (GPU, mediane)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(d, "workflow.png"), dpi=150)

    # --- Figure 2 : repartition du temps a L ----------------------------------
    parts = [("calcul_s", "calcul", "#4c566a"),
             ("ecriture_s", "ecriture (snapshots / pics)", "#d1495b"),
             ("copie_gpu_hote_s", "copie GPU->hote", "#edae49"),
             ("analyses_insitu_s", "analyses in-situ", "#00798c"),
             ("python_s", "scripts Python", "#8f6bb0")]
    modes_L = [("adhoc", "ad-hoc"), ("insitu_host", "in-situ hote"), ("insitu", "in-situ GPU")]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for k, (m, nom) in enumerate(modes_L):
        l = next((l for l in lignes if l["taille"] == "L" and l["mode"] == m), None)
        if not l:
            continue
        gauche = 0.0
        for cle, nom_p, c in parts:
            v = l[cle]
            ax.barh(k, v, left=gauche, color=c, edgecolor="white", linewidth=1,
                    label=nom_p if k == 0 else None)
            gauche += v
        ax.text(gauche + 15, k, f"{l['workflow_s']:.0f} s", va="center", fontsize=8)
    ax.set_yticks(range(len(modes_L)), [n for _, n in modes_L])
    ax.set_xlabel("temps (s)")
    ax.set_title("Ou passe le temps a L (200³), GPU")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.25))
    fig.tight_layout()
    fig.savefig(os.path.join(d, "repartition_L.png"), dpi=150)
    print("Ecrit :", ", ".join(os.path.join(d, n) for n in
                                ("fusion.csv", "resume_fusion.md", "workflow.png", "repartition_L.png")))


if __name__ == "__main__":
    main()
