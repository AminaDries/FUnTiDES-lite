import argparse
import csv
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "visualisation"))
from plot_snapshot import lire_snapshot, lister_snapshots

def stats_snapshot(p):
    """Statistiques d'un snapshot : p = tableau 1D des pressions de tous les nœuds."""
    return {
        "min": p.min(),
        "max": p.max(),
        "mean": p.mean(),
        "var": p.var(),
        "max_abs": np.abs(p).max(),
        "energie": np.sum(p**2),  
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dossier")
    ap.add_argument("--dt", type=float, default=0.001, help="pas de temps de la simulation (s)")
    ap.add_argument("--out", default="stats_snapshots.csv")
    args = ap.parse_args()

    lignes = []
    for pas, chemin in lister_snapshots(args.dossier):
        t0 = time.perf_counter()
        data = lire_snapshot(chemin)          
        t1 = time.perf_counter()
        p = data[:, 3].astype(np.float64)     
        s = stats_snapshot(p)
        t2 = time.perf_counter()
        lignes.append({"step": pas, "t": pas * args.dt, **s,
                       "read_s": t1 - t0, "analysis_s": t2 - t1})

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)

    print(f"{len(lignes)} snapshots analysés -> {args.out}")
    print(f"{'step':>6} {'t(s)':>7} {'max_abs':>10} {'energie':>12}")
    for l in lignes[::6]:
        print(f"{l['step']:>6} {l['t']:>7.3f} {l['max_abs']:>10.4f} {l['energie']:>12.4e}")

if __name__ == "__main__":
    main()