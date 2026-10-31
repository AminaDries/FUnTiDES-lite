"""Vitesse du front à partir des pics par noeud calculés EN IN-SITU par semproxy
(--insitu-vel). Même méthode que vitesse_front.py, sans relire les snapshots."""
import argparse
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fichier", help="CSV écrit par semproxy (x,y,z,max_abs,step_pic,t_pic)")
    ap.add_argument("--interval", type=int, default=10, help="--insitu-interval utilisé")
    ap.add_argument("--dernier", type=int, default=590, help="dernier pas analysé")
    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--src", type=float, nargs=3, help="source x y z (défaut : centre)")
    ap.add_argument("--rmin", type=float, default=150.0)
    ap.add_argument("--vref", type=float, default=1500.0)
    args = ap.parse_args()

    d = np.loadtxt(args.fichier, delimiter=",", skiprows=1)
    xyz = d[:, :3]
    pas = d[:, 4].astype(int)
    i_pic = pas // args.interval              # numéro du "snapshot" du pic
    nb_snap = args.dernier // args.interval + 1
    t_pic = pas * args.dt

    src = np.array(args.src) if args.src else (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    r = np.linalg.norm(xyz - src, axis=1)
    print(f"{nb_snap} analyses, {xyz.shape[0]} nœuds, source en {src}")

    couches = np.arange(0.0, r.max() + 50.0, 50.0)
    rmax = r.max()
    for lo, hi in zip(couches[:-1], couches[1:]):
        m = (r >= lo) & (r < hi)
        if m.sum() == 0:
            continue
        frac_fin = float(np.mean(i_pic[m] == nb_snap - 1))
        if frac_fin > 0.10 and rmax == r.max():
            rmax = lo

    garde = (r >= args.rmin) & (r < rmax) & (i_pic > 0) & (i_pic < nb_snap - 1)
    v, b = np.polyfit(t_pic[garde], r[garde], 1)
    t0 = -b / v
    print(f"Nœuds gardés : {garde.sum()} (distance entre {args.rmin:.0f} m et {rmax:.0f} m)")
    print(f"Vitesse estimée : {v:.0f} m/s   (modèle : {args.vref:.0f} m/s, écart {100*(v-args.vref)/args.vref:+.1f} %)")
    print(f"Instant d'émission apparent : {t0:.3f} s")


if __name__ == "__main__":
    main()
