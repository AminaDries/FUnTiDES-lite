#!/usr/bin/env python3
import argparse
import csv
import glob
import os

import numpy as np

from lecture_bin import lire_bin
from ordre_noeuds import octets_rle

def quantifier(p, vmin, vmax, nbits):
    niveaux = np.float32(2 ** nbits - 1)
    plage = np.float32(vmax) - np.float32(vmin)
    echelle = niveaux / plage if plage > 0 else np.float32(0)
    q = (p.astype(np.float32) - np.float32(vmin)) * echelle + np.float32(0.5)
    q = np.clip(q, 0, niveaux)
    return q.astype("<u1" if nbits == 8 else "<u2")

def erreurs(champs, quant, bornes, nbits, gmax_abs):
    niveaux = 2 ** nbits - 1
    pire_snap = 0.0
    pire_glob = 0.0
    for c, q, (lo, hi) in zip(champs, quant, bornes):
        rec = np.float32(lo) + q.astype(np.float32) * ((np.float32(hi) - np.float32(lo)) / np.float32(niveaux))
        e = float(np.abs(rec.astype(np.float64) - c.astype(np.float64)).max())
        amp = float(np.abs(c).max())
        if amp > 0:
            pire_snap = max(pire_snap, e / amp)
        pire_glob = max(pire_glob, e / gmax_abs)
    return pire_snap, pire_glob

def delta(a, nbits):
    d = np.empty_like(a)
    d[0] = a[0]
    d[1:] = a[1:] - a[:-1]
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref", help="dossier de reference (--snap-format bin)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    fichiers = sorted(glob.glob(os.path.join(a.ref, "snapshot_*.bin")))
    champs = [lire_bin(f)[1] for f in fichiers]
    nb = len(champs)
    n = champs[0].size
    gmin = min(float(c.min()) for c in champs)
    gmax = max(float(c.max()) for c in champs)
    _, xyz = lire_bin(os.path.join(a.ref, "coords.bin"))
    xyz = xyz.reshape(-1, 3).astype(np.float64)
    r = np.linalg.norm(xyz - (xyz.min(axis=0) + xyz.max(axis=0)) / 2, axis=1)
    p_rad = np.argsort(np.round(r, 6), kind="stable")

    lignes = []
    print(f"{nb} snapshots, {n} noeuds, bornes globales [{gmin:.4f}, {gmax:.4f}]")
    gabs = max(abs(gmin), abs(gmax))
    print(f"{'bits':>4} {'methode':<48} {'octets':>10} {'taux':>8} {'err/max|p| snap':>16} {'err/max|p| global':>18}")
    for nbits in (8, 16):
        larg = nbits // 8
        brut = nb * n * larg
        par_snap = [quantifier(c, c.min(), c.max(), nbits) for c in champs]
        global_ = [quantifier(c, gmin, gmax, nbits) for c in champs]
        err_ps = erreurs(champs, par_snap, [(c.min(), c.max()) for c in champs], nbits, gabs)
        err_gl = erreurs(champs, global_, [(gmin, gmax)] * nb, nbits, gabs)

        def total(listes, ordre=None, mode="aucun"):
            t = 0
            for k, q in enumerate(listes):
                v = q if ordre is None else q[ordre]
                if mode == "spatial":
                    v = delta(v, nbits)
                elif mode == "temporel":
                    prec = listes[k - 1] if k else np.zeros_like(q)
                    prec = prec if ordre is None else prec[ordre]
                    v = (v - prec).astype(q.dtype)
                t += octets_rle(v, larg)
            return t

        for k in range(1, nb):
            d = (global_[k] - global_[k - 1]).astype(global_[k].dtype)
            assert np.array_equal((global_[k - 1] + d).astype(d.dtype), global_[k])
        v = delta(global_[0], nbits)
        assert np.array_equal(np.cumsum(v, dtype=v.dtype), global_[0])

        cas = [
            ("RLE seul, bornes de chaque snapshot", total(par_snap), err_ps),
            ("delta spatial + RLE", total(par_snap, mode="spatial"), err_ps),
            ("delta temporel + RLE, bornes de chaque snapshot", total(par_snap, mode="temporel"), err_ps),
            ("RLE seul, bornes globales fixes", total(global_), err_gl),
            ("delta temporel + RLE, bornes globales fixes", total(global_, mode="temporel"), err_gl),
            ("RLE, bornes globales, ordre distance au centre", total(global_, ordre=p_rad), err_gl),
            ("delta temporel + RLE, globales, ordre distance", total(global_, ordre=p_rad, mode="temporel"), err_gl),
        ]
        for nom, t, (es, eg) in cas:
            print(f"{nbits:>4} {nom:<48} {t:>10d} {brut / t:>8.2f} {es:>16.2e} {eg:>18.2e}")
            lignes.append(dict(bits=nbits, methode=nom, octets=t, taux=brut / t,
                               pire_err_sur_max_snapshot=es, pire_err_sur_max_global=eg))
    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)
        print(f"Mesures ecrites dans {a.out}")

if __name__ == "__main__":
    main()
