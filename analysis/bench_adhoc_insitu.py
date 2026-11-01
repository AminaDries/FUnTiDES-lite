#!/usr/bin/env python3
"""Benchmark ad-hoc contre in-situ (analyses des snapshots), selon l'annexe
« Methodologie de mesure ».

Pour chaque configuration (S, M, L...) et chaque mode, le script lance le solveur
N fois (5 par defaut) et releve les temps PAR PHASE :

  mode           ce qui tourne
  -------------  ---------------------------------------------------------------
  sans           simulation seule (reference)
  adhoc          simulation + snapshots CSV, puis stats_adhoc.py,
                 histogramme_adhoc.py et vitesse_front.py sur ces snapshots
  adhoc_fsync    pareil, avec --fsync (ecriture reellement sur le disque)
  insitu         simulation + stats, histogramme et pics par noeud en in-situ
  insitu_fsync   pareil, avec --fsync

Fichiers produits dans --out :
  meta.json        machine, systeme de fichiers, options de compilation, hash du commit
  runs.csv         une ligne par execution (donnees brutes)
  resume.md        medianes, min, max par configuration et par mode

Usage (depuis la racine du projet) :
    python3 analysis/bench_adhoc_insitu.py --exe build-kokkos/bin/semproxy \
        --config S=50 --repeats 5 --out bench_out/S

Le dossier --out doit etre sur un vrai disque (pas /tmp si c'est un tmpfs).
"""
import argparse
import csv
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSE = os.path.join(RACINE, "analysis")

# memes recepteurs que benchmark/run_benchmark.py (TP1)
RECEIVERS = "1200,1000,1000\n1500,1000,1000\n1000,1600,1000\n"

MODES = ["sans", "adhoc", "adhoc_fsync", "insitu", "insitu_fsync", "insitu_host"]
MODES_DEFAUT = ["sans", "adhoc", "adhoc_fsync", "insitu", "insitu_fsync"]

# colonnes de metrics.csv recopiees dans runs.csv
COLONNES_METRICS = [
    "nb_nodes", "nb_elements", "dt", "nb_steps", "threads",
    "compute_time_s", "snapshot_write_time_s", "snapshot_sync_time_s",
    "snapshot_count", "snapshot_bytes", "max_rss_kb", "seismo_write_time_s",
    "insitu_stats_s", "insitu_hist_s", "insitu_vel_s", "insitu_write_s",
]
COLONNES_PY = ["py_stats_s", "py_hist_s", "py_vel_s", "py_total_s"]
COLONNES = (["config", "ex", "mode", "run", "wall_s", "initial_s", "kernel_s",
             "output_s", "total_exe_s", "insitu_bytes", "lecture", "moved_bytes"]
            + COLONNES_METRICS + COLONNES_PY)


def sortie(cmd, **kw):
    """Sortie texte d'une commande, ou 'inconnu' si elle echoue."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                              **kw).stdout.strip() or "inconnu"
    except Exception:
        return "inconnu"


def systeme_fichiers(dossier):
    """Ligne de `df -T` pour le dossier (type de systeme de fichiers, annexe section 4)."""
    brut = sortie(["df", "-T", dossier])
    return brut.splitlines()[-1] if brut != "inconnu" else "inconnu"


def infos_machine(args, dossier_sortie):
    """Ce que l'annexe (section 8) demande d'indiquer avec chaque resultat."""
    meta = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "machine": platform.node(),
        "noyau": platform.release(),
        "cpu": sortie(["sh", "-c", "lscpu | grep 'Model name' | sed 's/.*: *//'"]),
        "nproc": os.cpu_count(),
        "omp_num_threads": args.threads,
        "memoire": sortie(["sh", "-c", "free -h | awk '/Mem:/ {print $2}'"]),
        "gpu": sortie(["sh", "-c", "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null"]),
        "systeme_fichiers": systeme_fichiers(dossier_sortie),
        "commit": sortie(["git", "rev-parse", "HEAD"], cwd=RACINE),
        "modifications_non_commitees": bool(sortie(["git", "status", "--porcelain",
                                                    "--untracked-files=no"], cwd=RACINE)
                                            not in ("", "inconnu")),
        "configs": args.config,
        "repetitions": args.repeats,
        "timemax": args.timemax,
        "snap_interval": args.snap_interval,
        "insitu_interval": args.insitu_interval,
        "hist_bound": args.hist_bound,
        "executable": os.path.abspath(args.exe),
    }
    cache = os.path.join(args.build_dir, "CMakeCache.txt")
    options = {}
    if os.path.isfile(cache):
        cles = ("CMAKE_BUILD_TYPE", "CMAKE_CXX_FLAGS", "CMAKE_CXX_FLAGS_RELEASE",
                "Kokkos_ENABLE_OPENMP", "Kokkos_ENABLE_CUDA", "Kokkos_ENABLE_SERIAL")
        for ligne in open(cache, errors="replace"):
            nom = ligne.split(":", 1)[0]
            if nom in cles:
                options[nom] = ligne.split("=", 1)[-1].strip()
            elif nom.startswith("Kokkos_ARCH_") and ligne.rstrip().endswith("=ON"):
                options[nom] = "ON"
    meta["options_compilation"] = options or "CMakeCache.txt introuvable"
    return meta


def vider_cache():
    """Vide le cache disque du systeme (lectures 'a froid'). Retourne True si reussi."""
    try:
        r = subprocess.run(["sudo", "-n", "sh", "-c",
                            "sync; echo 3 > /proc/sys/vm/drop_caches"],
                           capture_output=True, timeout=60)
        return r.returncode == 0
    except Exception:
        return False


def taille_fichiers(chemins):
    return sum(os.path.getsize(c) for c in chemins if os.path.isfile(c))


def lire_metrics(chemin):
    with open(chemin, newline="") as f:
        lignes = list(csv.DictReader(f))
    if not lignes:
        raise RuntimeError("metrics.csv vide : " + chemin)
    return lignes[-1]


def extraire_temps(texte):
    """Temps affiches par semproxy : 'Elapsed Initial Time : 0.12 seconds.'"""
    out = {}
    for cle, nom in (("Initial", "initial_s"), ("Kernel", "kernel_s"),
                     ("Output", "output_s"), ("TotalExe", "total_exe_s")):
        m = re.search(r"Elapsed " + cle + r" Time\s*:\s*([0-9.eE+-]+)", texte)
        out[nom] = float(m.group(1)) if m else None
    return out


def chrono(cmd, env=None):
    """Lance une commande ; retourne la duree en s, ou None si elle echoue."""
    t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duree = time.perf_counter() - t0
    if p.returncode != 0:
        print("  [!] echec :", " ".join(cmd))
        print("     ", (p.stderr or p.stdout)[-300:].strip())
        return None
    return duree


def une_execution(args, ex, label, mode, run, dossier, fichier_rcv, froid):
    """Une execution complete (simulation + analyses ad-hoc eventuelles)."""
    rep = os.path.join(dossier, label, mode, f"run{run}")
    shutil.rmtree(rep, ignore_errors=True)
    os.makedirs(rep)
    metrics = os.path.join(rep, "metrics.csv")
    snaps = os.path.join(rep, "snapshots")
    f_stats = os.path.join(rep, "insitu_stats.csv")
    f_hist = os.path.join(rep, "insitu_hist.csv")
    f_vel = os.path.join(rep, "insitu_vel.csv")

    cmd = [args.exe, "--ex", str(ex), "--ey", str(ex), "--ez", str(ex),
           "--timemax", str(args.timemax), "--receivers-file", fichier_rcv,
           "--seismo-dir", rep, "--metrics-file", metrics]
    if mode.startswith("adhoc"):
        cmd += ["--snapshots", "--snap-interval", str(args.snap_interval),
                "--snap-folder", snaps]
    if mode.startswith("insitu"):
        cmd += ["--insitu-stats", "--insitu-hist", "--insitu-vel",
                "--insitu-interval", str(args.insitu_interval),
                "--insitu-hist-bound", str(args.hist_bound),
                "--insitu-hist-bins", str(args.hist_bins),
                "--insitu-file", f_stats, "--insitu-hist-file", f_hist,
                "--insitu-vel-file", f_vel]
    if mode == "insitu_host":
        cmd += ["--insitu-mode", "host"]
    if mode.endswith("fsync"):
        cmd += ["--fsync"]

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(args.threads)

    t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    wall = time.perf_counter() - t0
    if p.returncode != 0:
        print(p.stdout[-600:])
        print(p.stderr[-600:])
        sys.exit("Le solveur a echoue : " + " ".join(cmd))

    ligne = {k: None for k in COLONNES}
    ligne.update(config=label, ex=ex, mode=mode, run=run, wall_s=wall)
    ligne.update(extraire_temps(p.stdout))
    mv = re.search(r"Data moved to host\s*:\s*(\d+)", p.stdout)
    ligne["moved_bytes"] = int(mv.group(1)) if mv else None
    m = lire_metrics(metrics)
    for k in COLONNES_METRICS:
        ligne[k] = float(m[k]) if m.get(k) not in (None, "") else None
    ligne["insitu_bytes"] = taille_fichiers([f_stats, f_hist, f_vel])
    if run > 1 and not args.garder and os.path.isfile(f_vel):
        os.remove(f_vel)  # evite des dizaines de Go a L (on garde celui du run 1)
    ligne["lecture"] = ""

    if mode.startswith("adhoc"):
        if froid:
            froid = vider_cache()
        ligne["lecture"] = "froid" if froid else "chaud"
        if not args.no_python:
            env_py = dict(env, MPLBACKEND="Agg")
            t_stats = chrono([sys.executable, os.path.join(ANALYSE, "stats_adhoc.py"), snaps,
                              "--out", os.path.join(rep, "stats_adhoc.csv")], env_py)
            t_hist = chrono([sys.executable, os.path.join(ANALYSE, "histogramme_adhoc.py"), snaps,
                             "--borne", str(args.hist_bound), "--bins", str(args.hist_bins),
                             "--out", os.path.join(rep, "hist_adhoc.csv"),
                             "--png", os.path.join(rep, "hist_adhoc.png")], env_py)
            t_vel = chrono([sys.executable, os.path.join(ANALYSE, "vitesse_front.py"), snaps,
                            "--out", os.path.join(rep, "vel_adhoc.csv"),
                            "--png", os.path.join(rep, "vel_adhoc.png")], env_py)
            ligne.update(py_stats_s=t_stats, py_hist_s=t_hist, py_vel_s=t_vel)
            if None not in (t_stats, t_hist, t_vel):
                ligne["py_total_s"] = t_stats + t_hist + t_vel
        if not args.garder:
            shutil.rmtree(snaps, ignore_errors=True)  # libere le disque
    return ligne


def medianes(valeurs):
    v = [x for x in valeurs if x is not None]
    if not v:
        return None
    return statistics.median(v), min(v), max(v)


def retenir(lignes):
    """Ecarte la 1re execution si elle est nettement plus lente (annexe, section 5)."""
    if len(lignes) < 3:
        return lignes, False
    premiere, autres = lignes[0], lignes[1:]
    ref = statistics.median(l["wall_s"] for l in autres)
    if premiere["wall_s"] > 1.3 * ref:
        return autres, True
    return lignes, False


def ecrire_resume(toutes, meta, chemin):
    T = [
        ("wall_s", "total (s)"), ("kernel_s", "calcul (s)"),
        ("snapshot_write_time_s", "ecriture snapshots (s)"),
        ("snapshot_sync_time_s", "dont fsync (s)"),
        ("insitu_stats_s", "in-situ stats (s)"), ("insitu_hist_s", "in-situ hist (s)"),
        ("insitu_vel_s", "in-situ vitesse (s)"), ("insitu_write_s", "ecriture in-situ (s)"),
        ("py_total_s", "Python ad-hoc (s)"),
    ]
    texte = "# Resume des mesures\n\n"
    texte += (f"- machine : {meta['machine']} ({meta['cpu']}, {meta['nproc']} threads logiques, "
              f"OMP_NUM_THREADS={meta['omp_num_threads']})\n"
              f"- GPU : {meta['gpu']}\n"
              f"- systeme de fichiers : `{meta['systeme_fichiers']}`\n"
              f"- commit : `{meta['commit']}` (modifications non commitees : "
              f"{meta['modifications_non_commitees']})\n"
              f"- repetitions : {meta['repetitions']} ; mediane [min ; max]\n\n")
    configs = sorted({(l["config"], l["ex"]) for l in toutes}, key=lambda c: c[1])
    for label, ex in configs:
        texte += f"## {label} ({ex}^3 elements)\n\n"
        texte += "| mode | runs | " + " | ".join(t for _, t in T) + " | volume ecrit |\n"
        texte += "|---|---|" + "---|" * (len(T) + 1) + "\n"
        for mode in MODES:
            lg = [l for l in toutes if l["config"] == label and l["mode"] == mode]
            if not lg:
                continue
            gardees, ecartee = retenir(sorted(lg, key=lambda l: l["run"]))
            cases = []
            for cle, _ in T:
                r = medianes([l[cle] for l in gardees])
                cases.append("-" if r is None else f"{r[0]:.3f} [{r[1]:.3f} ; {r[2]:.3f}]")
            vol = medianes([(l["snapshot_bytes"] or 0) + (l["insitu_bytes"] or 0)
                            for l in gardees])
            lec = {l["lecture"] for l in gardees if l["lecture"]}
            note = f"{len(gardees)}" + (" (1re ecartee)" if ecartee else "")
            if lec:
                note += f", lectures {'/'.join(sorted(lec))}"
            texte += (f"| {mode} | {note} | " + " | ".join(cases)
                      + f" | {vol[0] / 1e6:.2f} Mo |\n")
        texte += "\n"
    texte += ("Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts "
              "Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, "
              "le temps d'ecriture est celui vu par l'application (copie dans le cache du "
              "systeme) ; avec `fsync` c'est le temps de persistance.\n")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    print("\n" + texte)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", required=True, help="executable semproxy")
    ap.add_argument("--build-dir", default="build-kokkos", help="dossier de build (options)")
    ap.add_argument("--config", nargs="+", default=["S=50"],
                    help="configurations NOM=nb_elements_par_cote (ex : S=50 M=100)")
    ap.add_argument("--modes", nargs="+", default=MODES_DEFAUT, choices=MODES,
                    help="insitu_host = analyses in-situ calculees sur l'hote")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--timemax", type=float, default=1.5, help="duree simulee (s)")
    ap.add_argument("--snap-interval", type=int, default=50)
    ap.add_argument("--insitu-interval", type=int, default=None,
                    help="pas entre deux analyses in-situ (defaut : = snap-interval)")
    ap.add_argument("--hist-bound", type=float, default=2.23736)
    ap.add_argument("--hist-bins", type=int, default=51)
    ap.add_argument("--threads", type=int, default=os.cpu_count(), help="OMP_NUM_THREADS")
    ap.add_argument("--froid", action="store_true",
                    help="vider le cache avant la lecture Python (demande sudo sans mot de passe)")
    ap.add_argument("--no-python", action="store_true",
                    help="ne pas lancer les scripts Python ad-hoc (trop longs pour M et L)")
    ap.add_argument("--garder", action="store_true", help="garder les snapshots apres mesure")
    ap.add_argument("--out", default="bench_out")
    args = ap.parse_args()
    if args.insitu_interval is None:
        args.insitu_interval = args.snap_interval

    if not os.path.isfile(args.exe):
        sys.exit("executable introuvable : " + args.exe)
    os.makedirs(args.out, exist_ok=True)
    dossier = os.path.abspath(args.out)
    fichier_rcv = os.path.join(dossier, "receivers.txt")
    with open(fichier_rcv, "w") as f:
        f.write(RECEIVERS)

    meta = infos_machine(args, dossier)
    with open(os.path.join(dossier, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print("Systeme de fichiers :", meta["systeme_fichiers"])
    if meta["systeme_fichiers"].split()[1:2] == ["tmpfs"]:
        print("[!] Le dossier de sortie est sur tmpfs (memoire) : choisissez un vrai disque.")

    froid = args.froid
    if froid and not vider_cache():
        print("[!] Impossible de vider le cache (sudo requis) : lectures 'a chaud'.")
        froid = False

    toutes = []
    chemin_csv = os.path.join(dossier, "runs.csv")
    with open(chemin_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for c in args.config:
            label, ex = c.split("=")
            for mode in args.modes:
                for run in range(1, args.repeats + 1):
                    print(f"[{label}={ex}] mode={mode} run={run}/{args.repeats}", flush=True)
                    l = une_execution(args, int(ex), label, mode, run, dossier,
                                      fichier_rcv, froid)
                    w.writerow(l)
                    f.flush()
                    toutes.append(l)
    ecrire_resume(toutes, meta, os.path.join(dossier, "resume.md"))
    print("Donnees brutes :", chemin_csv)


if __name__ == "__main__":
    main()
