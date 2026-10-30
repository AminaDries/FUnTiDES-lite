"""Estimation de la vitesse de l'onde à partir des snapshots 
"""
import argparse
import csv
import os
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "visualisation"))
from plot_snapshot import lire_snapshot, lister_snapshots


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dossier")
    ap.add_argument("--dt", type=float, default=0.001, help="pas de temps (s)")
    ap.add_argument("--src", type=float, nargs=3, help="position de la source x y z (défaut : centre)")
    ap.add_argument("--rmin", type=float, default=150.0, help="on ignore les nœuds plus proches (m)")
    ap.add_argument("--vref", type=float, default=1500.0, help="vitesse théorique du modèle (m/s)")
    ap.add_argument("--out", default="vitesse_front.csv")
    ap.add_argument("--png", default="vitesse_front.png")
    args = ap.parse_args()

    liste = lister_snapshots(args.dossier)
    pas = np.array([s for s, _ in liste])
    t = pas * args.dt
    P = []
    for _, chemin in liste:
        data = lire_snapshot(chemin)
        P.append(data[:, 3])
    P = np.array(P)
    xyz = data[:, :3]
    nb_snap = len(t)

    src = np.array(args.src) if args.src else (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    r = np.linalg.norm(xyz - src, axis=1)
    print(f"{nb_snap} snapshots, {xyz.shape[0]} nœuds, source en {src}")

    i_pic = np.argmax(np.abs(P), axis=0)
    t_pic = t[i_pic]
    amp = np.abs(P).max(axis=0)

    couches = np.arange(0.0, r.max() + 50.0, 50.0)
    lignes, rmax = [], r.max()
    for lo, hi in zip(couches[:-1], couches[1:]):
        m = (r >= lo) & (r < hi)
        if m.sum() == 0:
            continue
        frac_fin = float(np.mean(i_pic[m] == nb_snap - 1))  # nœuds dont le pic est au dernier snapshot
        lignes.append({"r_min": lo, "r_max": hi, "nb_noeuds": int(m.sum()),
                       "t_pic_median": float(np.median(t_pic[m])),
                       "amp_mediane": float(np.median(amp[m])),
                       "frac_pic_au_dernier": frac_fin})
        if frac_fin > 0.10 and rmax == r.max():
            rmax = lo   # au-delà, l'onde n'est pas encore passée : on s'arrête là
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)

    garde = (r >= args.rmin) & (r < rmax) & (i_pic > 0) & (i_pic < nb_snap - 1)
    v, b = np.polyfit(t_pic[garde], r[garde], 1)
    t0 = -b / v
    print(f"Nœuds gardés : {garde.sum()} (distance entre {args.rmin:.0f} m et {rmax:.0f} m)")
    print(f"Vitesse estimée : {v:.0f} m/s   (modèle : {args.vref:.0f} m/s, écart {100*(v-args.vref)/args.vref:+.1f} %)")
    print(f"Instant d'émission apparent : {t0:.3f} s")

    plt.figure(figsize=(7, 5))
    plt.scatter(t_pic[garde], r[garde], s=6, alpha=0.4, label="nœuds")
    tt = np.array([t.min(), t.max()])
    plt.plot(tt, v * tt + b, "r-", label=f"ajustement : {v:.0f} m/s")
    plt.plot(tt, args.vref * (tt - t0), "g--", label=f"modèle : {args.vref:.0f} m/s")
    plt.ylim(0, rmax * 1.1)
    plt.xlabel("temps d'arrivée du pic (s)")
    plt.ylabel("distance à la source (m)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(args.png, dpi=120)
    print(f"Table -> {args.out} ; figure -> {args.png}")


if __name__ == "__main__":
    main()