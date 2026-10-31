"""Benchmark du workflow ad-hoc : solveur (metrics.csv) + visualisation.

Pour chaque taille de maillage (et chaque nombre de threads si --threads est
donné), le script lance le solveur plusieurs fois :
  - "sans"  : sans --snapshots (seuls les sismos sont écrits)
  - "avec"  : avec --snapshots

Les mesures du solveur sont lues dans le fichier metrics.csv qu'il écrit
lui-même (option --metrics-file). Le script chronomètre ensuite les scripts de
visualisation (plot_snapshot.py, plot_sismos.py) pour avoir le workflow complet.

Fichiers produits dans DOSSIER_SORTIE :
  benchmark.csv         une ligne par exécution (toutes les mesures)
  resume.md             tableaux récapitulatifs (médianes) pour le rapport
  benchmark.png         graphiques (si matplotlib est installé)
  benchmark_speedup.png accélération (si plusieurs nombres de threads)

Usage (depuis la racine du projet) :
    python3 benchmark/run_benchmark.py --exe build-release/bin/semproxy

Options :
    --exe CHEMIN        exécutable semproxy (obligatoire)
    --sizes 10 20 30    nombre d'éléments par côté (ex = ey = ez)   [10 20 30]
    --threads 1 2 4     nombres de threads (variable OMP_NUM_THREADS) [non fixé]
    --repeats N         nombre d'exécutions par cas                 [3]
    --timemax T         durée simulée en secondes                   [0.2]
    --snap-interval N   un snapshot tous les N pas de temps         [25]
    --viz-dir DOSSIER   dossier des scripts de visualisation        [visualisation]
    --no-viz            ne pas chronométrer la visualisation
    --out DOSSIER       dossier de sortie                           [benchmark_out]
"""
import argparse
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time
from matplotlib.ticker import NullFormatter

# Récepteurs placés dans le domaine par défaut (2000 m), près de la source (1000, 1000, 1000)
RECEIVERS = "1200,1000,1000\n1500,1000,1000\n1000,1600,1000\n"

# Colonnes de metrics.csv converties en nombres
COLONNES_NOMBRES = [
    "ex", "ey", "ez", "order", "nb_nodes", "nb_elements", "dt", "timemax",
    "nb_steps", "threads", "snapshots", "snap_interval", "compute_time_s",
    "snapshot_write_time_s", "snapshot_count", "snapshot_bytes", "max_rss_kb",
    "nb_receivers", "seismo_write_time_s", "seismo_bytes",
    "slices", "slice_pos", "slice_write_time_s", "slice_count", "slice_bytes",
    "slice_extract_time_s",
]

# Colonnes écrites dans benchmark.csv
COLONNES_SORTIE = [
    "ex", "elements", "threads", "mode", "run", "wall_s",
    "compute_time_s", "snapshot_write_time_s", "seismo_write_time_s",
    "snapshot_count", "snapshot_bytes", "seismo_bytes", "max_rss_kb",
    "nb_nodes", "nb_steps", "viz_snapshot_s", "viz_sismos_s", "viz_s",
    "slice_write_time_s", "slice_count", "slice_bytes", "slice_extract_time_s",
]


def lire_metrics(chemin):
    """Dernière ligne de metrics.csv sous forme de dict de nombres."""
    if not os.path.isfile(chemin):
        sys.exit(f"metrics.csv introuvable : {chemin}\n"
                 "Le solveur ne connaît peut-être pas --metrics-file "
                 "(mauvaise branche ou ancien exécutable ?).")
    with open(chemin, newline="") as f:
        lignes = list(csv.DictReader(f))
    if not lignes:
        sys.exit(f"metrics.csv est vide : {chemin}")
    brut = lignes[-1]
    return {k: (float(v) if k in COLONNES_NOMBRES else v) for k, v in brut.items()}


def chronometrer(cmd, env=None):
    """Lance une commande ; retourne la durée en secondes, ou None si elle échoue."""
    debut = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duree = time.time() - debut
    if p.returncode != 0:
        print("  [!] échec :", " ".join(cmd))
        print("     ", (p.stderr or p.stdout)[-400:].strip())
        return None
    return duree


def mesurer_visu(viz_dir, dossier_run, mode):
    """Temps des scripts de visualisation. Retourne (snapshot, sismos, total)."""
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"  # pas de fenêtre graphique
    t_snap = 0.0
    if mode == "avec":
        t_snap = chronometrer([sys.executable, os.path.join(viz_dir, "plot_snapshot.py"),
                        os.path.join(dossier_run, "snapshots")], env)
    if mode == "slices":
        t_snap = chronometrer([sys.executable, os.path.join(viz_dir, "plot_snapshot.py"),
                        os.path.join(dossier_run, "slices")], env)
        
    t_sis = chronometrer([sys.executable, os.path.join(viz_dir, "plot_sismos.py"),
                          dossier_run], env)
    if t_snap is None or t_sis is None:
        return t_snap, t_sis, None
    return t_snap, t_sis, t_snap + t_sis


def lancer(exe, ex, threads, mode, run, args, dossier_run, fichier_rcv):
    """Une exécution du solveur. Retourne un dict de mesures."""
    shutil.rmtree(dossier_run, ignore_errors=True)
    os.makedirs(dossier_run)
    snap = os.path.join(dossier_run, "snapshots")
    metrics = os.path.join(dossier_run, "metrics.csv")
    cmd = [exe, "--ex", str(ex), "--ey", str(ex), "--ez", str(ex),
           "--timemax", str(args.timemax),
           "--receivers-file", fichier_rcv, "--seismo-dir", dossier_run,
           "--metrics-file", metrics]
    if mode == "avec":
        cmd += ["--snapshots", "--snap-interval", str(args.snap_interval),
                "--snap-folder", snap]
        
    if mode == "slices":
        cmd += ["--slices", "--snap-interval", str(args.snap_interval),
                "--slice-pos", "1000",
                "--slice-folder", os.path.join(dossier_run, "slices")]
    env = os.environ.copy()
    if threads:
        env["OMP_NUM_THREADS"] = str(threads)

    debut = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    mur = time.time() - debut
    if p.returncode != 0:
        print(p.stdout[-800:])
        print(p.stderr[-800:])
        sys.exit(f"Le solveur a échoué (code {p.returncode}) : {' '.join(cmd)}")

    mesures = lire_metrics(metrics)
    mesures.update({
        "ex": ex,
        "elements": ex ** 3,
        "mode": mode,
        "run": run,
        "wall_s": mur,
        "threads": int(mesures["threads"]),  # valeur réelle vue par le solveur
        "viz_snapshot_s": None, "viz_sismos_s": None, "viz_s": None,
    })
    if args.viz_dir:
        t_snap, t_sis, t_tot = mesurer_visu(args.viz_dir, dossier_run, mode)
        mesures.update({"viz_snapshot_s": t_snap, "viz_sismos_s": t_sis, "viz_s": t_tot})
    return mesures


def med(lignes, cle, **filtre):
    """Médiane de la colonne `cle` sur les lignes qui vérifient le filtre (NaN si aucune)."""
    vals = [l[cle] for l in lignes
            if all(l[k] == v for k, v in filtre.items()) and l[cle] is not None]
    return statistics.median(vals) if vals else float("nan")


def ecrire_resume(lignes, tailles, chemin):
    """Tableaux Markdown (médianes) : à coller dans le rapport."""
    threads_vus = sorted({l["threads"] for l in lignes})
    texte = ""

    entete = ("| Éléments | Threads | Sans snapshots (s) | Avec snapshots (s) "
              "| Écriture snapshots (s) | Surcoût (%) | Snapshots total (Mo) "
              "| Moyenne/snapshot (Mo) | Débit écriture (Mo/s) | RAM max (Mo) "
              "| Visualisation (s) |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|\n")
    corps = ""
    for ex in tailles:
        for th in threads_vus:
            f_sans = dict(ex=ex, threads=th, mode="sans")
            f_avec = dict(ex=ex, threads=th, mode="avec")
            sans = med(lignes, "wall_s", **f_sans)
            avec = med(lignes, "wall_s", **f_avec)
            ecr = med(lignes, "snapshot_write_time_s", **f_avec)
            mo = med(lignes, "snapshot_bytes", **f_avec) / 1e6
            nb = med(lignes, "snapshot_count", **f_avec)
            ram = med(lignes, "max_rss_kb", **f_avec) / 1024
            visu = med(lignes, "viz_s", **f_avec)
            surcout = 100.0 * (avec - sans) / sans if sans > 0 else float("nan")
            moy = mo / nb if nb > 0 else float("nan")
            debit = mo / ecr if ecr > 0 else float("nan")
            corps += (f"| {ex}³ = {ex ** 3} | {th} | {sans:.2f} | {avec:.2f} | {ecr:.3f} "
                      f"| {surcout:.1f} | {mo:.2f} | {moy:.2f} | {debit:.1f} "
                      f"| {ram:.0f} | {visu:.2f} |\n")
    texte += "## Coût du workflow ad-hoc\n\n" + entete + corps


    # ----- Tableau 2 : snapshots vs slices -----
    entete2 = ("| Éléments | Threads | Snapshots (Mo) | Slices (Mo) | Rapport taille "
               "| Écriture snap. (s) | Extraction slices (s) | Écriture slices (s) | Rapport écriture "
               "| Image snap. (s) | Image slice (s) "
               "| Workflow snap. (s) | Workflow slice (s) |\n"
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    corps2 = ""
    for ex in tailles:
        for th in threads_vus:
            f_avec = dict(ex=ex, threads=th, mode="avec")
            f_sl = dict(ex=ex, threads=th, mode="slices")

            # tailles écrites (en Mo)
            mo_snap = med(lignes, "snapshot_bytes", **f_avec) / 1e6
            mo_sl = med(lignes, "slice_bytes", **f_sl) / 1e6

            # temps d'écriture pendant la simulation
            ecr_snap = med(lignes, "snapshot_write_time_s", **f_avec)
            ecr_sl = med(lignes, "slice_write_time_s", **f_sl)
            ext_sl = med(lignes, "slice_extract_time_s", **f_sl)

            # temps pour faire l'image après la simulation
            img_snap = med(lignes, "viz_snapshot_s", **f_avec)
            img_sl = med(lignes, "viz_snapshot_s", **f_sl)

            # temps total du workflow = simulation + image
            wf_snap = med(lignes, "wall_s", **f_avec) + img_snap
            wf_sl = med(lignes, "wall_s", **f_sl) + img_sl

            # rapports (combien de fois mieux)
            r_taille = mo_snap / mo_sl if mo_sl > 0 else float("nan")
            cout_sl = ext_sl + ecr_sl   # coût total d'une slice pendant la simulation
            r_ecr = ecr_snap / cout_sl if cout_sl > 0 else float("nan")

            corps2 += (f"| {ex}³ | {th} | {mo_snap:.2f} | {mo_sl:.3f} | ×{r_taille:.0f} "
                       f"| {ecr_snap:.3f} | {ext_sl:.4f} | {ecr_sl:.4f} | ×{r_ecr:.0f} "
                       f"| {img_snap:.2f} | {img_sl:.2f} "
                       f"| {wf_snap:.2f} | {wf_sl:.2f} |\n")
    texte += "\n## Snapshots vs slices\n\n" + entete2 + corps2

    if len(threads_vus) > 1:
        ref = threads_vus[0]
        texte += (f"\n## Accélération (référence : {ref} thread(s))\n\n"
                  "| Éléments | Threads | Accél. sans snapshots | Accél. avec snapshots "
                  "| Efficacité avec (%) |\n|---|---|---|---|---|\n")
        for ex in tailles:
            ref_sans = med(lignes, "wall_s", ex=ex, threads=ref, mode="sans")
            ref_avec = med(lignes, "wall_s", ex=ex, threads=ref, mode="avec")
            for th in threads_vus:
                a_sans = ref_sans / med(lignes, "wall_s", ex=ex, threads=th, mode="sans")
                a_avec = ref_avec / med(lignes, "wall_s", ex=ex, threads=th, mode="avec")
                eff = 100.0 * a_avec / (th / ref)
                texte += f"| {ex}³ | {th} | {a_sans:.2f} | {a_avec:.2f} | {eff:.0f} |\n"

    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    print("\n" + texte)


def tracer(lignes, tailles, dossier):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib absent : pas de graphique.")
        return
    threads_vus = sorted({l["threads"] for l in lignes})
    th = threads_vus[-1]  # courbes pour le plus grand nombre de threads
    elements = [ex ** 3 for ex in tailles]

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14, 4))
    for mode, etiquette in (("sans", "sans snapshots"), ("avec", "avec snapshots")):
        a1.plot(elements, [med(lignes, "wall_s", ex=ex, threads=th, mode=mode) for ex in tailles],
                "o-", label=etiquette)
    a1.set_xlabel("nombre d'éléments")
    a1.set_ylabel("temps du solveur (s)")
    a1.set_title(f"Temps d'exécution ({th} thread(s))")
    a1.legend()
    a1.grid(alpha=0.3)

    a2.plot(elements, [med(lignes, "snapshot_bytes", ex=ex, threads=th, mode="avec") / 1e6
                       for ex in tailles], "o-", color="tab:red")
    a2.set_xlabel("nombre d'éléments")
    a2.set_ylabel("taille des snapshots (Mo)")
    a2.set_title("Volume écrit sur disque")
    a2.grid(alpha=0.3)

    debit = []
    for ex in tailles:
        mo = med(lignes, "snapshot_bytes", ex=ex, threads=th, mode="avec") / 1e6
        t = med(lignes, "snapshot_write_time_s", ex=ex, threads=th, mode="avec")
        debit.append(mo / t if t > 0 else float("nan"))
    a3.plot(elements, debit, "o-", color="tab:green")
    a3.set_xlabel("nombre d'éléments")
    a3.set_ylabel("débit d'écriture (Mo/s)")
    a3.set_title("Débit d'écriture des snapshots")
    a3.grid(alpha=0.3)
    fig.tight_layout()
    chemin = os.path.join(dossier, "benchmark.png")
    fig.savefig(chemin, dpi=150)
    print("Graphique écrit :", chemin)

    # ----- Figure 2 : snapshots vs slices -----
    fig, (b1, b2, b3) = plt.subplots(1, 3, figsize=(14, 4))
    cas = [
        # (mode, colonne taille, colonne écriture, nom de la courbe)
        ("avec", "snapshot_bytes", "snapshot_write_time_s", "snapshots"),
        ("slices", "slice_bytes", "slice_write_time_s", "slices"),
    ]
    for mode, col_taille, col_ecriture, nom in cas:
        tailles_mo = [med(lignes, col_taille, ex=ex, threads=th, mode=mode) / 1e6
                      for ex in tailles]
        ecritures = [med(lignes, col_ecriture, ex=ex, threads=th, mode=mode)
                     + (med(lignes, "slice_extract_time_s", ex=ex, threads=th, mode=mode)
                        if mode == "slices" else 0)
                     for ex in tailles]
        totaux = [med(lignes, "wall_s", ex=ex, threads=th, mode=mode)
                  + med(lignes, "viz_snapshot_s", ex=ex, threads=th, mode=mode)
                  for ex in tailles]
        b1.plot(elements, tailles_mo, "o-", label=nom)
        b2.plot(elements, ecritures, "o-", label=nom)
        b3.plot(elements, totaux, "o-", label=nom)

    b2.plot(elements, [med(lignes, "slice_extract_time_s", ex=ex, threads=th, mode="slices")
                    for ex in tailles], "o--", label="slices : extraction seule")

    b1.set_title("Volume écrit sur disque")
    b1.set_ylabel("taille (Mo)")
    b2.set_title("Coût de la sortie pendant la simulation")
    b2.set_ylabel("temps (s)")
    b3.set_title("Workflow total (simulation + image)")
    b3.set_ylabel("temps (s)")
    for b in (b1, b2, b3):
        b.set_xlabel("nombre d'éléments")
        b.set_xscale("log")
        b.legend()
        b.grid(alpha=0.3)
        b.set_xticks(elements)
        b.set_xticklabels([f"{ex}³" for ex in tailles])
        b.xaxis.set_minor_formatter(NullFormatter())
    b1.set_yscale("log")
    b2.set_yscale("log")
    fig.tight_layout()
    chemin = os.path.join(dossier, "benchmark_slices.png")
    fig.savefig(chemin, dpi=150)
    print("Graphique écrit :", chemin)    

    if len(threads_vus) > 1:
        ref = threads_vus[0]
        fig, ax = plt.subplots(figsize=(5, 4))
        for ex in tailles:
            r = med(lignes, "wall_s", ex=ex, threads=ref, mode="avec")
            ax.plot(threads_vus,
                    [r / med(lignes, "wall_s", ex=ex, threads=t, mode="avec")
                     for t in threads_vus], "o-", label=f"{ex}³")
        ax.plot(threads_vus, [t / ref for t in threads_vus], "k--", label="idéal")
        ax.set_xlabel("threads")
        ax.set_ylabel("accélération (avec snapshots)")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        chemin = os.path.join(dossier, "benchmark_speedup.png")
        fig.savefig(chemin, dpi=150)
        print("Graphique écrit :", chemin)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[10, 20, 30])
    ap.add_argument("--threads", type=int, nargs="+", default=None)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--timemax", type=float, default=0.2)
    ap.add_argument("--snap-interval", type=int, default=25)
    ap.add_argument("--viz-dir", default="visualisation")
    ap.add_argument("--no-viz", action="store_true")
    ap.add_argument("--out", default="benchmark_out")
    args = ap.parse_args()

    exe = os.path.abspath(args.exe)
    if not os.path.isfile(exe):
        sys.exit(f"Exécutable introuvable : {exe}")
    if args.no_viz:
        args.viz_dir = None
    elif not os.path.isdir(args.viz_dir):
        print(f"Dossier de visualisation introuvable ({args.viz_dir}) : "
              "temps de visualisation non mesuré.")
        args.viz_dir = None
    else:
        args.viz_dir = os.path.abspath(args.viz_dir)

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    fichier_rcv = os.path.join(out, "receivers_in.csv")
    with open(fichier_rcv, "w") as f:
        f.write(RECEIVERS)

    liste_threads = args.threads or [None]
    lignes = []
    total_runs = len(args.sizes) * len(liste_threads) * 3 * args.repeats
    n = 0
    dossier_run = os.path.join(out, "run_tmp")
    for ex in args.sizes:
        for th in liste_threads:
            for mode in ("sans", "avec", "slices"):
                for run in range(1, args.repeats + 1):
                    n += 1
                    print(f"[{n}/{total_runs}] maillage {ex}³, threads={th or 'défaut'}, "
                          f"mode {mode}, essai {run}", flush=True)
                    lignes.append(lancer(exe, ex, th, mode, run, args, dossier_run, fichier_rcv))
    shutil.rmtree(dossier_run, ignore_errors=True)

    with open(os.path.join(out, "benchmark.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES_SORTIE)
        w.writeheader()
        for l in lignes:
            w.writerow({c: ("" if l[c] is None else l[c]) for c in COLONNES_SORTIE})

    ecrire_resume(lignes, args.sizes, os.path.join(out, "resume.md"))
    tracer(lignes, args.sizes, out)
    print("Résultats dans :", out)


if __name__ == "__main__":
    main()