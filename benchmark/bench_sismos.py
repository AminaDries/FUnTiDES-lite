"""Benchmark des sismos : workflow ad-hoc vs in-situ (TP2, étape 4).

Pour chaque taille (ex = ey = ez) et chaque répétition, le script lance :
  - "sans"   : la simulation seule (sismos écrits, pas d'in-situ)
  - "avec"   : la simulation avec --insitu-sismos, puis sur CE MÊME run
               l'analyse ad-hoc (sismos_adhoc.py) et la précision (precision_sismos.py)
Les deux modes sont alternés à chaque répétition (limite l'effet d'une dérive
de la machine). Une exécution de chauffe (run 0) est faite avant les mesures
et n'est pas comptée (initialisation CUDA/Kokkos, cache froid : annexe §5).

Usage (depuis la racine du dépôt) :
    python3 benchmark/bench_sismos.py --exe build-release/bin/semproxy

Options :
    --exe CHEMIN       exécutable semproxy (obligatoire)
    --sizes 50 100 200 nombre d'éléments par côté (S, M, L)       [50 100 200]
    --repeats N        exécutions mesurées par cas (annexe : >= 5)   [5]
    --timemax T        durée simulée (s) ; >= 0.8 pour que l'onde
                       atteigne le récepteur le plus loin (800 m)   [1.5]
    --receivers F      fichier des récepteurs     [analysis/receivers_line.txt]
    --out DOSSIER      dossier de sortie          [benchmark/results/sismos_gpu]

Fichiers produits dans DOSSIER :
    raw.csv     une ligne par exécution (toutes les mesures, données brutes)
    resume.md   médiane [min - max] par taille et par phase, pour le rapport
    machine.txt machine, GPU, système de fichiers, commit, options de compilation
"""
import argparse
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.join(ICI, "..", "analysis")


def sortie_cmd(cmd):
    """Sortie texte d'une commande, ou 'indisponible' si elle échoue."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout.strip() or "indisponible"
    except OSError:
        return "indisponible"


def lire_csv(chemin):
    with open(chemin) as f:
        return list(csv.DictReader(f))


def lancer(args, ex, mode, run):
    """Une exécution. Retourne un dict de mesures."""
    dossier = os.path.join(args.out, "runs", f"{ex}_{mode}_{run}")
    shutil.rmtree(dossier, ignore_errors=True)
    os.makedirs(dossier)
    metrics = os.path.join(dossier, "metrics.csv")
    cmd = [args.exe, "--ex", str(ex), "--ey", str(ex), "--ez", str(ex),
           "--timemax", str(args.timemax), "--receivers-file", args.receivers,
           "--seismo-dir", dossier, "--metrics-file", metrics]
    if mode == "avec":
        cmd += ["--insitu-sismos", "--insitu-sismos-file",
                os.path.join(dossier, "insitu_sismos.csv")]

    debut = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True)
    mur = time.perf_counter() - debut
    if p.returncode != 0:
        print(p.stdout[-800:], p.stderr[-800:])
        sys.exit(f"Le solveur a échoué : {' '.join(cmd)}")

    m = lire_csv(metrics)[-1]
    res = {"ex": ex, "mode": mode, "run": run, "wall_s": mur}
    for col in ("nb_nodes", "nb_steps", "nb_receivers", "compute_time_s",
                "max_rss_kb", "seismo_write_time_s", "seismo_fsync_time_s",
                "seismo_bytes", "insitu_sismos_loop_s", "insitu_sismos_final_s"):
        res[col] = m[col]

    if mode == "avec":
        # ad-hoc sur le même run (lecture "à chaud" : fichiers juste écrits)
        for script in ("sismos_adhoc.py", "precision_sismos.py"):
            subprocess.run([sys.executable, os.path.join(ANALYSIS, script), dossier],
                           check=True, capture_output=True)
        t = lire_csv(os.path.join(dossier, "adhoc_times.csv"))[0]
        res["adhoc_read_s"] = t["read_time_s"]
        res["adhoc_analysis_s"] = t["analysis_time_s"]
        prec = lire_csv(os.path.join(dossier, "precision_sismos.csv"))
        res["max_rel_error"] = max(float(r["max_rel_error"]) for r in prec)
    return res


COLONNES = ["ex", "mode", "run", "wall_s", "nb_nodes", "nb_steps", "nb_receivers",
            "compute_time_s", "max_rss_kb", "seismo_write_time_s",
            "seismo_fsync_time_s", "seismo_bytes", "insitu_sismos_loop_s",
            "insitu_sismos_final_s", "adhoc_read_s", "adhoc_analysis_s",
            "max_rel_error"]


def resume(lignes, chemin):
    """Tableau médiane [min - max] des runs mesurés (run >= 1)."""
    def stat(ex, mode, col, ms=False):
        v = [float(l[col]) for l in lignes
             if l["ex"] == ex and l["mode"] == mode and l["run"] >= 1 and l.get(col) not in (None, "")]
        if not v:
            return "-"
        k = 1000.0 if ms else 1.0
        return f"{statistics.median(v)*k:.3g} [{min(v)*k:.3g} - {max(v)*k:.3g}]"

    tailles = sorted({l["ex"] for l in lignes})
    with open(chemin, "w") as f:
        f.write("Médiane [min - max] sur les runs mesurés (la chauffe, run 0, est exclue).\n")
        f.write("Écriture = temps vu par l'application ; persistance = écriture + fsync.\n")
        f.write("Lecture ad-hoc à chaud (fichiers juste écrits, servis par le cache).\n\n")
        f.write("## Temps par phase (ms)\n\n")
        f.write("| Taille | Écriture sismos | fsync | Lecture ad-hoc | Analyse ad-hoc | In-situ boucle | In-situ fin |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for ex in tailles:
            f.write(f"| {ex}³ | {stat(ex,'avec','seismo_write_time_s',1)} | "
                    f"{stat(ex,'avec','seismo_fsync_time_s',1)} | {stat(ex,'avec','adhoc_read_s',1)} | "
                    f"{stat(ex,'avec','adhoc_analysis_s',1)} | {stat(ex,'avec','insitu_sismos_loop_s',1)} | "
                    f"{stat(ex,'avec','insitu_sismos_final_s',1)} |\n")
        f.write("\n## Impact sur la simulation (s)\n\n")
        f.write("| Taille | Calcul sans in-situ | Calcul avec in-situ | Total sans | Total avec |\n")
        f.write("|---|---|---|---|---|\n")
        for ex in tailles:
            f.write(f"| {ex}³ | {stat(ex,'sans','compute_time_s')} | {stat(ex,'avec','compute_time_s')} | "
                    f"{stat(ex,'sans','wall_s')} | {stat(ex,'avec','wall_s')} |\n")
        f.write("\n## Volume et précision\n\n")
        f.write("| Taille | Nœuds | Pas | seismos.csv (octets) | Écart relatif max in-situ / ad-hoc |\n")
        f.write("|---|---|---|---|---|\n")
        for ex in tailles:
            l = next(l for l in lignes if l["ex"] == ex and l["mode"] == "avec")
            err = max(float(x["max_rel_error"]) for x in lignes
                      if x["ex"] == ex and x["mode"] == "avec" and x["run"] >= 1)
            f.write(f"| {ex}³ | {l['nb_nodes']} | {l['nb_steps']} | {l['seismo_bytes']} | {err:.2g} |\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 200])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--timemax", type=float, default=1.5)
    ap.add_argument("--receivers", default=os.path.join(ANALYSIS, "receivers_line.txt"))
    ap.add_argument("--out", default=os.path.join(ICI, "results", "sismos_gpu"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # informations demandées par l'annexe (§4 et §8)
    build = os.path.dirname(os.path.dirname(os.path.abspath(args.exe)))
    with open(os.path.join(args.out, "machine.txt"), "w") as f:
        f.write(f"date : {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"commit : {sortie_cmd('git rev-parse --short HEAD')}\n")
        f.write(f"CPU : {sortie_cmd('lscpu | grep \"Model name\" | cut -d: -f2')}\n")
        f.write(f"GPU : {sortie_cmd('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader')}\n")
        f.write(f"RAM : {sortie_cmd('free -h | grep Mem | tr -s \" \" | cut -d\" \" -f2')}\n")
        f.write(f"système de fichiers : {sortie_cmd('df -T ' + args.out + ' | tail -1')}\n")
        f.write(f"compilation : {sortie_cmd('grep -E \"CMAKE_BUILD_TYPE|ENABLE_CUDA|USE_KOKKOS|Kokkos_ARCH\" ' + build + '/CMakeCache.txt | grep -v ADVANCED')}\n")
        f.write(f"timemax : {args.timemax} s, répétitions : {args.repeats} (+1 chauffe)\n")

    lignes = []
    for ex in args.sizes:
        for run in range(args.repeats + 1):  # run 0 = chauffe
            for mode in ("sans", "avec"):
                r = lancer(args, ex, mode, run)
                lignes.append(r)
                print(f"{ex}³ {mode} run {run} : {r['wall_s']:.2f} s")
            with open(os.path.join(args.out, "raw.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLONNES)
                w.writeheader()
                w.writerows(lignes)

    resume(lignes, os.path.join(args.out, "resume.md"))
    shutil.rmtree(os.path.join(args.out, "runs"), ignore_errors=True)  # gros fichiers inutiles
    print(f"Résultats dans {args.out} (raw.csv, resume.md, machine.txt)")


if __name__ == "__main__":
    main()
