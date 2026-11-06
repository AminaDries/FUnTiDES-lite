#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import numpy as np

from lecture_bin import lire_bin

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ref", help="dossier de reference (--snap-format bin)")
    ap.add_argument("test", help="dossier du codage a evaluer")
    ap.add_argument("--out", default="", help="ecrit les mesures dans ce CSV")
    a = ap.parse_args()

    fichiers = sorted(glob.glob(os.path.join(a.ref, "snapshot_*.bin")))
    if not fichiers:
        raise SystemExit(f"aucun snapshot_*.bin dans {a.ref}")

    lignes = []
    taille_ref = taille_test = 0
    print(f"{'pas':>6} {'max|p|':>10} {'RMSE/max|p|':>13} {'errmax/max|p|':>14} {'octets/noeud':>13}")
    for fr in fichiers:
        ft = os.path.join(a.test, os.path.basename(fr))
        if not os.path.isfile(ft):
            raise SystemExit(f"manque {ft}")
        er, vr = lire_bin(fr)
        et, vt = lire_bin(ft)
        if vr.size != vt.size:
            raise SystemExit(f"{fr} : {vr.size} valeurs, {ft} : {vt.size}")
        diff = vt.astype(np.float64) - vr.astype(np.float64)
        amp = float(np.abs(vr).max())
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        emax = float(np.abs(diff).max())
        tr, tt = os.path.getsize(fr), os.path.getsize(ft)
        taille_ref += tr
        taille_test += tt
        l = dict(pas=er["timestep"], max_abs=amp,
                 rmse_sur_max=rmse / amp if amp > 0 else 0.0,
                 errmax_sur_max=emax / amp if amp > 0 else 0.0,
                 octets=tt, octets_par_noeud=tt / vr.size, taux=tr / tt)
        lignes.append(l)
        print(f"{l['pas']:6d} {amp:10.5f} {l['rmse_sur_max']:13.3e} {l['errmax_sur_max']:14.3e} {l['octets_par_noeud']:13.3f}")

    print(f"\nTotal : {taille_test} octets contre {taille_ref} en reference : taux de compression x{taille_ref / taille_test:.2f}")
    print(f"Pire RMSE/max|p| : {max(l['rmse_sur_max'] for l in lignes):.3e} | "
          f"pire erreur max/max|p| : {max(l['errmax_sur_max'] for l in lignes):.3e}")

    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)
        print(f"Mesures ecrites dans {a.out}")

if __name__ == "__main__":
    main()
