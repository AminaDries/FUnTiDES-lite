"""Mesure le coût de l'écriture des snapshots (workflow ad-hoc).

Pour chaque taille de maillage, le script lance le solveur plusieurs fois :
  - "sans"  : sans --snapshots (seuls les sismos sont écrits)
  - "avec"  : avec --snapshots

Il relève les temps affichés par le solveur et la taille des snapshots,
puis écrit :
  DOSSIER_SORTIE/benchmark.csv    une ligne par exécution
  DOSSIER_SORTIE/resume.md        tableau récapitulatif (médianes) à coller dans le rapport
  DOSSIER_SORTIE/benchmark.png    graphique (si matplotlib est installé)

Usage (dans WSL, depuis la racine du projet) :
    python3 benchmark/run_benchmark.py --exe build-release/bin/semproxy

Options :
    --exe CHEMIN        exécutable semproxy (obligatoire)
    --sizes 10 20 30    nombre d'éléments par côté (ex = ey = ez)   [10 20 30]
    --repeats N         nombre d'exécutions par cas                 [3]
    --timemax T         durée simulée en secondes                   [0.2]
    --snap-interval N   un snapshot tous les N pas de temps         [25]
    --out DOSSIER       dossier de sortie                           [benchmark_out]
"""
import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

# Récepteurs placés dans le domaine par défaut (2000 m), près de la source (1000, 1000, 1000)
RECEIVERS = "1200,1000,1000\n1500,1000,1000\n1000,1600,1000\n"

# Lignes affichées par le solveur à la fin de l'exécution
PATTERNS = {
    "kernel_s": r"Elapsed Kernel Time\s*:\s*([0-9.eE+-]+)",
    "output_s": r"Elapsed Output Time\s*:\s*([0-9.eE+-]+)",
    "compute_s": r"Elapsed Compute Time\s*:\s*([0-9.eE+-]+)",
    "total_s": r"Elapsed TotalExe Time\s*:\s*([0-9.eE+-]+)",
}


def taille_dossier(chemin):
    """Taille totale (octets) des fichiers d'un dossier ; 0 s'il n'existe pas."""
    total = 0
    for racine, _, fichiers in os.walk(chemin):
        for f in fichiers:
            total += os.path.getsize(os.path.join(racine, f))
    return total


def extraire(sortie):
    """Lit les temps dans la sortie du solveur ; None si une ligne manque."""
    valeurs = {}
    for nom, motif in PATTERNS.items():
        m = re.search(motif, sortie)
        valeurs[nom] = float(m.group(1)) if m else None
    return valeurs


def lancer(exe, ex, mode, run, args, dossier_run, fichier_rcv):
    """Une exécution du solveur. Retourne un dict de mesures."""
    shutil.rmtree(dossier_run, ignore_errors=True)
    os.makedirs(dossier_run)
    snap = os.path.join(dossier_run, "snapshots")
    cmd = [exe, "--ex", str(ex), "--ey", str(ex), "--ez", str(ex),
           "--timemax", str(args.timemax),
           "--receivers-file", fichier_rcv, "--seismo-dir", dossier_run]
    if mode == "avec":
        cmd += ["--snapshots", "--snap-interval", str(args.snap_interval),
                "--snap-folder", snap]
    debut = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    mur = time.time() - debut
    if p.returncode != 0:
        print(p.stdout[-800:])
        print(p.stderr[-800:])
        sys.exit(f"Le solveur a échoué (code {p.returncode}) : {' '.join(cmd)}")
    mesures = extraire(p.stdout)
    manquants = [k for k, v in mesures.items() if v is None]
    if manquants:
        print(p.stdout[-800:])
        sys.exit(f"Lignes de temps introuvables dans la sortie du solveur : {manquants}")
    mesures.update({
        "ex": ex,
        "elements": ex ** 3,
        "mode": mode,
        "run": run,
        "wall_s": mur,
        "snap_bytes": taille_dossier(snap),
        "snap_files": len(os.listdir(snap)) if os.path.isdir(snap) else 0,
    })
    return mesures


def mediane(lignes, ex, mode, cle):
    vals = [l[cle] for l in lignes if l["ex"] == ex and l["mode"] == mode]
    return statistics.median(vals)


def ecrire_resume(lignes, tailles, chemin):
    """Tableau Markdown (médianes) : à coller dans le rapport."""
    entete = ("| Éléments | Calcul sans (s) | Calcul avec (s) | Écriture snapshots (s) "
              "| Surcoût total (%) | Snapshots (Mo) |\n"
              "|---|---|---|---|---|---|\n")
    corps = ""
    for ex in tailles:
        sans = mediane(lignes, ex, "sans", "total_s")
        avec = mediane(lignes, ex, "avec", "total_s")
        ecr = mediane(lignes, ex, "avec", "output_s")
        mo = mediane(lignes, ex, "avec", "snap_bytes") / 1e6
        surcout = 100.0 * (avec - sans) / sans if sans > 0 else float("nan")
        corps += (f"| {ex}³ = {ex ** 3} | {sans:.2f} | {avec:.2f} | {ecr:.3f} "
                  f"| {surcout:.1f} | {mo:.2f} |\n")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(entete + corps)
    print("\n" + entete + corps)


def tracer(lignes, tailles, chemin):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib absent : pas de graphique.")
        return
    elements = [ex ** 3 for ex in tailles]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    for mode, etiquette in (("sans", "sans snapshots"), ("avec", "avec snapshots")):
        a1.plot(elements, [mediane(lignes, ex, mode, "total_s") for ex in tailles],
                "o-", label=etiquette)
    a1.set_xlabel("nombre d'éléments")
    a1.set_ylabel("temps total (s)")
    a1.set_title("Temps d'exécution")
    a1.legend()
    a1.grid(alpha=0.3)
    a2.plot(elements, [mediane(lignes, ex, "avec", "snap_bytes") / 1e6 for ex in tailles],
            "o-", color="tab:red")
    a2.set_xlabel("nombre d'éléments")
    a2.set_ylabel("taille des snapshots (Mo)")
    a2.set_title("Volume écrit sur disque")
    a2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(chemin, dpi=150)
    print("Graphique écrit :", chemin)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[10, 20, 30])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--timemax", type=float, default=0.2)
    ap.add_argument("--snap-interval", type=int, default=25)
    ap.add_argument("--out", default="benchmark_out")
    args = ap.parse_args()

    exe = os.path.abspath(args.exe)
    if not os.path.isfile(exe):
        sys.exit(f"Exécutable introuvable : {exe}")
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    fichier_rcv = os.path.join(out, "receivers_in.csv")
    with open(fichier_rcv, "w") as f:
        f.write(RECEIVERS)

    lignes = []
    total_runs = len(args.sizes) * 2 * args.repeats
    n = 0
    for ex in args.sizes:
        for mode in ("sans", "avec"):
            for run in range(1, args.repeats + 1):
                n += 1
                print(f"[{n}/{total_runs}] maillage {ex}³, {mode} snapshots, essai {run}", flush=True)
                dossier_run = os.path.join(out, "run_tmp")
                lignes.append(lancer(exe, ex, mode, run, args, dossier_run, fichier_rcv))
    shutil.rmtree(os.path.join(out, "run_tmp"), ignore_errors=True)

    colonnes = ["ex", "elements", "mode", "run", "kernel_s", "output_s", "compute_s",
                "total_s", "wall_s", "snap_files", "snap_bytes"]
    with open(os.path.join(out, "benchmark.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        w.writeheader()
        for l in lignes:
            w.writerow({c: l[c] for c in colonnes})

    ecrire_resume(lignes, args.sizes, os.path.join(out, "resume.md"))
    tracer(lignes, args.sizes, os.path.join(out, "benchmark.png"))
    print("Résultats dans :", out)


if __name__ == "__main__":
    main()