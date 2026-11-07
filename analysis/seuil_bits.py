#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import numpy as np

from lecture_bin import lire_bin
from ordre_noeuds import octets_rle

def quantifier_reconstruire(p, nbits):
    lo, hi = float(p.min()), float(p.max())
    niveaux = 2 ** nbits - 1
    if hi <= lo:
        return np.full(p.shape, lo, dtype=np.float64), np.zeros(p.shape, dtype=np.uint16)
    marche = (hi - lo) / niveaux
    q = np.clip(np.floor((p.astype(np.float64) - lo) / marche + 0.5), 0, niveaux).astype(np.uint16)
    return lo + q * marche, q

def analyse(champs, pas, borne, bins, xyz, src, dt, rmin):
    nb = len(champs)
    amp = np.abs(champs[0]).astype(np.float64)
    i_pic = np.zeros(amp.size, dtype=np.int32)
    energies, classes = [], []
    hist = np.zeros(bins)
    for k, p in enumerate(champs):
        a = np.abs(p)
        if k:
            plus = a > amp
            amp[plus] = a[plus]
            i_pic[plus] = k
        energies.append(float(np.sum(p ** 2)))
        c = np.clip(((p + borne) / (2 * borne) * bins).astype(int), -1, bins)
        classes.append(c)
        hist += np.bincount(c[(c >= 0) & (c < bins)], minlength=bins)
    t = np.array(pas) * dt
    r = np.linalg.norm(xyz - src, axis=1)
    t_pic = t[i_pic]
    rmax = r.max()
    for lo in np.arange(0.0, r.max() + 50.0, 50.0)[:-1]:
        m = (r >= lo) & (r < lo + 50.0)
        if m.sum() and np.mean(i_pic[m] == nb - 1) > 0.10 and rmax == r.max():
            rmax = lo
    garde = (r >= rmin) & (r < rmax) & (i_pic > 0) & (i_pic < nb - 1)
    v = float(np.polyfit(t_pic[garde], r[garde], 1)[0]) if garde.sum() > 2 else float("nan")
    return dict(amp=amp, i_pic=i_pic, energies=np.array(energies), classes=classes, hist=hist, vitesse=v)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref", help="dossier de reference (--snap-format bin)")
    ap.add_argument("--bits", type=int, nargs="+", default=[2, 3, 4, 5, 6, 8, 16])
    ap.add_argument("--dt", type=float, default=0.001)
    ap.add_argument("--rmin", type=float, default=150.0)
    ap.add_argument("--bins", type=int, default=51)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    fichiers = sorted(glob.glob(os.path.join(a.ref, "snapshot_*.bin")))
    champs = [lire_bin(f)[1].astype(np.float64) for f in fichiers]
    pas = [int(os.path.basename(f)[9:15]) for f in fichiers]
    _, xyz = lire_bin(os.path.join(a.ref, "coords.bin"))
    xyz = xyz.reshape(-1, 3).astype(np.float64)
    src = (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    borne = max(float(np.abs(c).max()) for c in champs)

    ref = analyse(champs, pas, borne, a.bins, xyz, src, a.dt, a.rmin)
    ipic = int(np.argmax(ref["energies"]))
    atteint = ref["amp"] > 0.01 * ref["amp"].max()
    print(f"{len(champs)} snapshots, {xyz.shape[0]} noeuds, vitesse de reference {ref['vitesse']:.1f} m/s")
    print(f"{'bits':>4} {'err max/max|p|':>15} {'energie pic':>12} {'pic t different':>16} {'vitesse':>9} {'ecart v':>9} {'dist. hist':>11} {'taux RLE':>9}")
    lignes = []
    for nbits in a.bits:
        rec = []
        taille = 0
        pire = 0.0
        for p in champs:
            r_, q = quantifier_reconstruire(p, nbits)
            rec.append(r_)
            taille += octets_rle(q.astype("<u1" if nbits <= 8 else "<u2"), 1 if nbits <= 8 else 2)
            amp_p = float(np.abs(p).max())
            if amp_p > 0:
                pire = max(pire, float(np.abs(r_ - p).max()) / amp_p)
        t = analyse(rec, pas, borne, a.bins, xyz, src, a.dt, a.rmin)
        err_en = (t["energies"][ipic] - ref["energies"][ipic]) / ref["energies"][ipic]
        tdiff = float(np.mean(ref["i_pic"][atteint] != t["i_pic"][atteint]))
        ecart_v = (t["vitesse"] - ref["vitesse"]) / ref["vitesse"]
        dist = 0.5 * np.abs(ref["hist"] - t["hist"]).sum() / ref["hist"].sum()
        brut = len(champs) * champs[0].size * (1 if nbits <= 8 else 2)
        lignes.append(dict(bits=nbits, pire_err_sur_max=pire, err_energie_pic=err_en,
                           frac_instant_pic_different=tdiff, vitesse=t["vitesse"],
                           ecart_vitesse=ecart_v, dist_histogramme=float(dist), taux_rle=brut / taille))
        print(f"{nbits:>4} {pire:>15.2e} {err_en:>+12.2e} {tdiff:>16.2%} {t['vitesse']:>9.1f} {ecart_v:>+9.2%} {dist:>11.2e} {brut / taille:>9.2f}")
    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)
        print(f"Mesures ecrites dans {a.out}")

if __name__ == "__main__":
    main()
