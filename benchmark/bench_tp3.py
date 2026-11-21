"""TP3 piste B : sorties pilotees par la simulation, campagne de mesures.

Modes compares (memes recepteurs, memes reglages que le TP2) :
  ref             sismos seulement (reference)
  periodique      + un snapshot tous les --snap-interval pas (approche classique)
  declenche       + un snapshot a l'arrivee de l'onde a chaque recepteur
  declenche_stop  + arret anticipe --stop-delay s apres le dernier recepteur

Pour chaque taille : 1 chauffe non mesuree, puis --repeats runs par mode.
Les snapshots sont effaces apres chaque run (seule leur taille est gardee).

Usage :
  python3 benchmark/bench_tp3.py --exe build-release/bin/semproxy \
      --sizes 50 100 200 --repeats 5 --out bench_tp3
"""
import argparse
import csv
import os
import shutil
import statistics
import subprocess
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODES = ["ref", "periodique", "declenche", "declenche_stop"]
NOMS = {"ref": "sismos seuls (reference)", "periodique": "snapshots periodiques",
        "declenche": "snapshots declenches", "declenche_stop": "declenches + arret anticipe"}
COULEURS = {"ref": "#9aa0a6", "periodique": "#d1495b", "declenche": "#edae49",
            "declenche_stop": "#00798c"}
LABEL = {50: "S", 100: "M", 200: "L"}


def commande(a, n, mode, d):
    c = [a.exe, "--ex", str(n), "--ey", str(n), "--ez", str(n),
         "--timemax", str(a.timemax), "--quiet",
         "--receivers-file", a.receivers, "--seismo-dir", d,
         "--metrics-file", os.path.join(d, "metrics.csv")]
    if mode == "periodique":
        c += ["--snapshots", "--snap-interval", str(a.snap_interval),
              "--snap-folder", os.path.join(d, "snapshots")]
    if mode.startswith("declenche"):
        c += ["--trigger-threshold", str(a.threshold),
              "--trigger-folder", os.path.join(d, "triggers")]
    if mode == "declenche_stop":
        c += ["--stop-after-receivers", str(a.stop_delay),
              "--stop-threshold", str(a.threshold)]
    return c


def lancer(c, d):
    os.makedirs(d, exist_ok=True)
    t0 = time.perf_counter()
    with open(os.path.join(d, "solveur.log"), "w") as log:
        subprocess.run(c, stdout=log, stderr=subprocess.STDOUT, check=True)
    return time.perf_counter() - t0


def f(l, k):
    v = l.get(k, "")
    try:
        return float(v)
    except ValueError:
        return 0.0


def stat(vals):
    return statistics.median(vals), min(vals), max(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build-release/bin/semproxy")
    ap.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 200])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--timemax", type=float, default=1.5)
    ap.add_argument("--snap-interval", type=int, default=50)
    ap.add_argument("--threshold", type=float, default=0.01)
    ap.add_argument("--stop-delay", type=float, default=0.3)
    ap.add_argument("--receivers", default="analysis/receivers_line.txt")
    ap.add_argument("--modes", nargs="+", default=MODES)
    ap.add_argument("--out", default="bench_tp3")
    a = ap.parse_args()
    a.exe = os.path.abspath(a.exe)
    a.receivers = os.path.abspath(a.receivers)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    lignes = []
    for n in a.sizes:
        print(f"[{LABEL.get(n, n)}={n}] chauffe", flush=True)
        dc = os.path.join(out, "chauffe")
        lancer(commande(a, n, "ref", dc), dc)
        shutil.rmtree(dc, ignore_errors=True)
        for mode in a.modes:
            for run in range(1, a.repeats + 1):
                print(f"[{LABEL.get(n, n)}={n}] mode={mode} run={run}/{a.repeats}", flush=True)
                d = os.path.join(out, f"{n}", mode, f"run{run}")
                shutil.rmtree(d, ignore_errors=True)
                wall = lancer(commande(a, n, mode, d), d)
                with open(os.path.join(d, "metrics.csv")) as fm:
                    m = list(csv.DictReader(fm))[-1]
                m.update({"taille": n, "mode": mode, "run": run, "wall_s": wall})
                lignes.append(m)
                # on ne garde que les petits fichiers (metriques, triggers.csv, log)
                shutil.rmtree(os.path.join(d, "snapshots"), ignore_errors=True)
                tr = os.path.join(d, "triggers")
                if os.path.isdir(tr):
                    for x in os.listdir(tr):
                        if x.startswith("snapshot_"):
                            os.remove(os.path.join(tr, x))
                if run > 1 and os.path.isfile(os.path.join(d, "seismos.csv")):
                    os.remove(os.path.join(d, "seismos.csv"))

    cles = list(lignes[0].keys())
    with open(os.path.join(out, "runs.csv"), "w", newline="") as fr:
        w = csv.DictWriter(fr, fieldnames=cles)
        w.writeheader()
        w.writerows(lignes)

    # ---- resume : mediane [min ; max] ----
    res = []
    for n in a.sizes:
        for mode in a.modes:
            g = [l for l in lignes if l["taille"] == n and l["mode"] == mode]
            if not g:
                continue
            res.append({
                "taille": n, "mode": mode, "runs": len(g),
                "wall": stat([l["wall_s"] for l in g]),
                "calcul": stat([f(l, "compute_time_s") for l in g]),
                "pas": statistics.median(f(l, "nb_steps") for l in g),
                "prevus": statistics.median(f(l, "planned_steps") for l in g),
                "nb_snap": statistics.median(f(l, "snapshot_count") + f(l, "trigger_count") for l in g),
                "volume_mo": statistics.median(f(l, "snapshot_bytes") + f(l, "trigger_bytes")
                                               + f(l, "seismo_bytes") for l in g) / 1e6,
                "ecriture": stat([f(l, "snapshot_write_time_s") + f(l, "trigger_write_time_s") for l in g]),
                "copie": statistics.median(f(l, "snapshot_copy_s") + f(l, "trigger_copy_s") for l in g),
                "tests_ms": statistics.median(1e3 * (f(l, "trigger_check_time_s")
                                                     + f(l, "stop_check_time_s")) for l in g),
            })
    fmt = lambda t: f"{t[0]:.3f} [{t[1]:.3f} ; {t[2]:.3f}]"
    with open(os.path.join(out, "resume_tp3.md"), "w") as fr:
        fr.write("# TP3 piste B : sorties pilotees par la simulation\n\n")
        fr.write(f"Recepteurs : {os.path.basename(a.receivers)} ; seuil {a.threshold} ; "
                 f"arret {a.stop_delay} s apres le dernier recepteur ; snapshots periodiques "
                 f"tous les {a.snap_interval} pas ; timemax {a.timemax} s ; "
                 f"{a.repeats} runs + 1 chauffe ; mediane [min ; max].\n\n")
        fr.write("| taille | mode | total (s) | calcul (s) | pas calcules / prevus | snapshots | "
                 "volume ecrit (Mo) | ecriture snapshots (s) | copie GPU->hote (s) | tests (ms) |\n")
        fr.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in res:
            fr.write(f"| {LABEL.get(r['taille'], r['taille'])} | {r['mode']} | {fmt(r['wall'])} | "
                     f"{fmt(r['calcul'])} | {r['pas']:.0f} / {r['prevus']:.0f} | {r['nb_snap']:.0f} | "
                     f"{r['volume_mo']:.1f} | {fmt(r['ecriture'])} | {r['copie']:.3f} | "
                     f"{r['tests_ms']:.3f} |\n")
    print(open(os.path.join(out, "resume_tp3.md")).read())

    # ---- figure : temps total et volume, par taille et par mode ----
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    largeur = 0.2
    for ax, cle, titre in ((axes[0], "wall", "Duree totale (s, echelle log)"),
                           (axes[1], "volume_mo", "Volume ecrit (Mo, echelle log)")):
        for i, mode in enumerate(a.modes):
            xs, ys = [], []
            for j, n in enumerate(a.sizes):
                r = next((r for r in res if r["taille"] == n and r["mode"] == mode), None)
                if r:
                    xs.append(j + (i - (len(a.modes) - 1) / 2) * largeur)
                    ys.append(r[cle][0] if cle == "wall" else r[cle])
            b = ax.bar(xs, ys, largeur * 0.92, color=COULEURS.get(mode), label=NOMS.get(mode, mode))
            ax.bar_label(b, labels=[f"{y:.0f}" if y >= 10 else f"{y:.1f}" for y in ys],
                         fontsize=7, padding=2)
        ax.set_yscale("log")
        ax.set_xticks(range(len(a.sizes)), [f"{LABEL.get(n, n)} ({n}³)" for n in a.sizes])
        ax.set_title(titre)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "tp3_sorties_pilotees.png"), dpi=150)
    print("Figure :", os.path.join(out, "tp3_sorties_pilotees.png"))


if __name__ == "__main__":
    main()
