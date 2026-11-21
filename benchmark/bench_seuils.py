"""TP3 piste B : comment choisir les seuils, et que risque-t-on de manquer ?

1. un run complet de reference (sismos seuls, 1,5 s) : pic de |p| et instant
   du pic a chaque recepteur, energie enregistree ;
2. pour chaque seuil : un run avec declenchement + arret anticipe (sans ecrire
   de snapshot sur le disque pour aller vite : seul le pas de declenchement
   compte ici, les snapshots sont effaces).

Pour chaque seuil on mesure : recepteurs declenches (sur 7), arret ou non,
pas d'arret, avance du declenchement sur le pic, vitesse apparente deduite des
instants de declenchement, et part de l'energie enregistree aux recepteurs
apres l'arret (ce que l'arret fait manquer).

Usage :
  python3 benchmark/bench_seuils.py --exe build-release/bin/semproxy --taille 100 \
      --out benchmark/results/tp3_seuils
"""
import argparse
import csv
import os
import shutil
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SEUILS = [1e-4, 1e-3, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.08]
V = 1500.0


def lancer(c, d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "solveur.log"), "w") as log:
        subprocess.run(c, stdout=log, stderr=subprocess.STDOUT, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build-release/bin/semproxy")
    ap.add_argument("--taille", type=int, default=100)
    ap.add_argument("--timemax", type=float, default=1.5)
    ap.add_argument("--delai", type=float, default=0.3)
    ap.add_argument("--receivers", default="analysis/receivers_line.txt")
    ap.add_argument("--seuils", type=float, nargs="+", default=SEUILS)
    ap.add_argument("--out", default="benchmark/results/tp3_seuils")
    a = ap.parse_args()
    exe, rec, out = (os.path.abspath(x) for x in (a.exe, a.receivers, a.out))
    os.makedirs(out, exist_ok=True)
    n = str(a.taille)
    base = [exe, "--ex", n, "--ey", n, "--ez", n, "--timemax", str(a.timemax),
            "--quiet", "--receivers-file", rec]

    # 1. reference complete
    dref = os.path.join(out, "ref")
    print("reference complete", flush=True)
    lancer(base + ["--seismo-dir", dref, "--metrics-file", os.path.join(dref, "metrics.csv")], dref)
    s = np.loadtxt(os.path.join(dref, "seismos.csv"), delimiter=",", skiprows=1)
    t, p = s[:, 0], s[:, 1:]
    dt = t[1] - t[0]
    pic = np.max(np.abs(p), axis=0)
    t_pic = t[np.argmax(np.abs(p), axis=0)]
    energie = np.sum(p ** 2, axis=0)

    # 2. un run par seuil
    lignes, par_recepteur = [], []
    for seuil in a.seuils:
        d = os.path.join(out, f"seuil_{seuil:g}")
        shutil.rmtree(d, ignore_errors=True)
        print(f"seuil {seuil:g}", flush=True)
        lancer(base + ["--seismo-dir", d, "--metrics-file", os.path.join(d, "metrics.csv"),
                       "--trigger-threshold", str(seuil), "--trigger-folder", os.path.join(d, "trig"),
                       "--stop-after-receivers", str(a.delai), "--stop-threshold", str(seuil)], d)
        with open(os.path.join(d, "trig", "triggers.csv")) as f:
            tr = list(csv.DictReader(f))
        for x in os.listdir(os.path.join(d, "trig")):
            if x.startswith("snapshot_"):
                os.remove(os.path.join(d, "trig", x))
        with open(os.path.join(d, "metrics.csv")) as f:
            m = list(csv.DictReader(f))[-1]
        dist = np.array([float(r["distance"]) for r in tr])
        td = np.array([float(r["t"]) for r in tr])
        ok = td >= 0
        stop_step = int(float(m["stop_step"]))
        t_stop = stop_step * dt if stop_step >= 0 else t[-1]
        perdu = np.sum(p[t > t_stop] ** 2, axis=0) / energie  # energie apres l'arret
        # onde directe : fenetre de +-0,15 s autour du pic de chaque recepteur
        fen = np.abs(t[:, None] - t_pic[None, :]) <= 0.15
        directe = np.sum((p ** 2) * fen, axis=0)
        directe_perdue = np.sum((p ** 2) * fen * (t[:, None] > t_stop), axis=0) / directe
        v_app = np.nan
        if ok.sum() >= 3:
            pente = np.polyfit(dist[ok], td[ok], 1)[0]
            v_app = 1.0 / pente
        avance = np.where(ok, t_pic - td, np.nan)  # >0 : declenche avant le pic
        lignes.append({
            "seuil": seuil, "declenches": int(ok.sum()), "recepteurs": len(tr),
            "arret": m["stop_reason"], "pas_calcules": int(float(m["nb_steps"])),
            "pas_prevus": int(float(m["planned_steps"])),
            "avance_mediane_s": float(np.nanmedian(avance)) if ok.any() else np.nan,
            "v_apparente": v_app,
            "energie_perdue_max": float(np.max(perdu)) if stop_step >= 0 else 0.0,
            "onde_directe_perdue_max": float(np.max(directe_perdue)) if stop_step >= 0 else 0.0,
        })
        for r in range(len(tr)):
            par_recepteur.append({"seuil": seuil, "recepteur": r, "distance": dist[r],
                                  "pic": pic[r], "t_pic": t_pic[r], "t_declenche": td[r],
                                  "energie_apres_arret": perdu[r] if stop_step >= 0 else 0.0})

    for nom, rows in (("seuils.csv", lignes), ("seuils_par_recepteur.csv", par_recepteur)):
        with open(os.path.join(out, nom), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    with open(os.path.join(out, "resume_seuils.md"), "w") as f:
        f.write(f"# Choix du seuil, maillage {n}^3, delai d'arret {a.delai} s\n\n")
        f.write("Pic de |p| aux recepteurs (reference) : "
                + ", ".join(f"{d:.0f} m : {x:.4f}" for d, x in zip(dist, pic)) + "\n\n")
        f.write("| seuil | recepteurs declenches | arret | pas calcules | avance sur le pic (s) | "
                "vitesse apparente (m/s) | energie apres l'arret (max) | dont onde directe (max) |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for l in lignes:
            f.write(f"| {l['seuil']:g} | {l['declenches']}/{l['recepteurs']} | {l['arret']} | "
                    f"{l['pas_calcules']}/{l['pas_prevus']} | {l['avance_mediane_s']:.3f} | "
                    f"{l['v_apparente']:.0f} | {100 * l['energie_perdue_max']:.1f} % | "
                    f"{100 * l['onde_directe_perdue_max']:.1f} % |\n")
    print(open(os.path.join(out, "resume_seuils.md")).read())

    # figure : seuil (log) en abscisse
    S = np.array([l["seuil"] for l in lignes])
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    ax[0].plot(S, [l["declenches"] for l in lignes], "o-", color="#00798c")
    for x in pic:
        ax[0].axvline(x, color="#c8ccd2", lw=0.8, zorder=0)
    ax[0].set_ylabel("recepteurs declenches (sur 7)")
    ax[0].set_title("Recepteurs atteints\n(traits gris : pic de |p| de chaque recepteur)")
    ax[1].plot(S, [l["v_apparente"] for l in lignes], "o-", color="#d1495b")
    ax[1].axhline(V, color="#4c566a", ls="--", lw=1)
    ax[1].text(S[0], V * 1.01, "1500 m/s (modele)", fontsize=8, color="#4c566a")
    ax[1].set_ylabel("vitesse apparente (m/s)")
    ax[1].set_title("Vitesse deduite des declenchements")
    ax[2].plot(S, [100 * l["energie_perdue_max"] for l in lignes], "o-", color="#edae49",
               label="energie totale (surtout reflexions)")
    ax[2].plot(S, [100 * l["onde_directe_perdue_max"] for l in lignes], "s--", color="#4c566a",
               label="onde directe")
    ax[2].legend(frameon=False, fontsize=8)
    ax[2].set_ylabel("energie apres l'arret (%)")
    ax[2].set_title("Ce que l'arret fait manquer\n(max sur les recepteurs)")
    for x in ax:
        x.set_xscale("log")
        x.set_xlabel("seuil sur |p|")
        x.grid(alpha=0.3)
        x.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "tp3_seuils.png"), dpi=150)
    print("Figure :", os.path.join(out, "tp3_seuils.png"))


if __name__ == "__main__":
    main()
