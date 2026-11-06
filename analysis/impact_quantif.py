#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import numpy as np

from lecture_bin import lire_bin

def lister(dossier):
    fichiers = sorted(glob.glob(os.path.join(dossier, "snapshot_*.bin")))
    if not fichiers:
        raise SystemExit(f"aucun snapshot_*.bin dans {dossier}")
    return fichiers

def analyse(dossier, borne, bins, xyz, src, dt, rmin):
    fichiers = lister(dossier)
    nb = len(fichiers)
    amp = None
    i_pic = None
    energies, classes, hist_cumul = [], [], np.zeros(bins)
    for k, f in enumerate(fichiers):
        _, v = lire_bin(f)
        p = v.astype(np.float64)
        a = np.abs(p)
        if amp is None:
            amp = a.copy()
            i_pic = np.zeros(a.size, dtype=np.int32)
        else:
            plus = a > amp
            amp[plus] = a[plus]
            i_pic[plus] = k
        energies.append(float(np.sum(p ** 2)))
        c = np.clip(((p + borne) / (2 * borne) * bins).astype(int), -1, bins)
        classes.append(c)
        hist_cumul += np.bincount(c[(c >= 0) & (c < bins)], minlength=bins)
    pas = np.array([int(os.path.basename(f)[9:15]) for f in fichiers])
    t = pas * dt
    r = np.linalg.norm(xyz - src, axis=1)
    t_pic = t[i_pic]
    rmax = r.max()
    for lo in np.arange(0.0, r.max() + 50.0, 50.0)[:-1]:
        m = (r >= lo) & (r < lo + 50.0)
        if m.sum() and np.mean(i_pic[m] == nb - 1) > 0.10 and rmax == r.max():
            rmax = lo
    garde = (r >= rmin) & (r < rmax) & (i_pic > 0) & (i_pic < nb - 1)
    vitesse = float(np.polyfit(t_pic[garde], r[garde], 1)[0]) if garde.sum() > 2 else float("nan")
    return dict(amp=amp, i_pic=i_pic, energies=np.array(energies), classes=classes,
                hist=hist_cumul, vitesse=vitesse, nb_garde=int(garde.sum()))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ref", help="dossier de reference (--snap-format bin)")
    ap.add_argument("tests", nargs="+", help="dossiers des codages a evaluer")
    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--bins", type=int, default=51)
    ap.add_argument("--rmin", type=float, default=150.0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    _, xyz = lire_bin(os.path.join(a.ref, "coords.bin"))
    xyz = xyz.reshape(-1, 3).astype(np.float64)
    src = (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    borne = max(float(np.abs(lire_bin(f)[1]).max()) for f in lister(a.ref))

    ref = analyse(a.ref, borne, a.bins, xyz, src, a.dt, a.rmin)
    ipic = int(np.argmax(ref["energies"]))
    print(f"Reference : {len(ref['energies'])} snapshots, {xyz.shape[0]} noeuds, borne histogramme +-{borne:.4f}")
    print(f"Vitesse du front (reference) : {ref['vitesse']:.1f} m/s ({ref['nb_garde']} noeuds)")
    print(f"Pic d'energie au snapshot {ipic}\n")

    entete = f"{'dossier':<10} {'pic amp.':>10} {'energie pic':>12} {'classes':>9} {'dist. hist':>11} {'pic t different':>16} {'vitesse':>9} {'ecart v':>9}"
    print(entete)
    lignes = []
    for d in a.tests:
        t = analyse(d, borne, a.bins, xyz, src, a.dt, a.rmin)
        err_pic = (t["amp"].max() - ref["amp"].max()) / ref["amp"].max()
        err_en = (t["energies"][ipic] - ref["energies"][ipic]) / ref["energies"][ipic]
        chg = np.mean([np.mean(cr != ct) for cr, ct in zip(ref["classes"], t["classes"])])
        dist = 0.5 * np.abs(ref["hist"] - t["hist"]).sum() / ref["hist"].sum()
        atteint = ref["amp"] > 0.01 * ref["amp"].max()
        tdiff = float(np.mean(ref["i_pic"][atteint] != t["i_pic"][atteint]))
        ecart_v = (t["vitesse"] - ref["vitesse"]) / ref["vitesse"]
        l = dict(dossier=os.path.basename(os.path.normpath(d)), err_pic_amplitude=err_pic, err_energie_pic=err_en,
                 frac_noeuds_classe_change=float(chg), dist_histogramme=float(dist),
                 frac_noeuds_instant_pic_different=tdiff, vitesse=t["vitesse"], ecart_vitesse=ecart_v)
        lignes.append(l)
        print(f"{l['dossier']:<10} {err_pic:>+10.2e} {err_en:>+12.2e} {chg:>9.2%} {dist:>11.2e} {tdiff:>16.2%} {t['vitesse']:>9.1f} {ecart_v:>+9.2%}")

    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)
        print(f"\nMesures ecrites dans {a.out}")

if __name__ == "__main__":
    main()
