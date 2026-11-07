#!/usr/bin/env python3
import argparse
import csv
import glob
import os
import struct

import numpy as np

from lecture_bin import lire_bin, TAILLE_ENTETE, FORMAT_ENTETE

def lire_entiers(chemin):
    with open(chemin, "rb") as f:
        magic, version, nb, pas, codec, nbits, vmin, vmax = struct.unpack(FORMAT_ENTETE, f.read(TAILLE_ENTETE))
        reste = f.read()
    if codec != 2:
        raise SystemExit(f"{chemin} : pas un fichier quantifie sans RLE")
    return np.frombuffer(reste, dtype="<u1" if nbits == 8 else "<u2", count=nb), nbits // 8

def octets_rle(v, largeur):
    if v.size == 0:
        return 0
    debuts = np.flatnonzero(np.concatenate(([True], v[1:] != v[:-1])))
    longueurs = np.diff(np.concatenate((debuts, [v.size])))
    taille_run = 1 + (longueurs >= 128) + (longueurs >= 16384) + (longueurs >= 2097152)
    return int(taille_run.sum() + largeur * longueurs.size)

def entrelacer(i, j, k, bits):
    m = np.zeros(i.shape, dtype=np.uint64)
    for b in range(bits):
        m |= ((i >> b) & 1).astype(np.uint64) << np.uint64(3 * b)
        m |= ((j >> b) & 1).astype(np.uint64) << np.uint64(3 * b + 1)
        m |= ((k >> b) & 1).astype(np.uint64) << np.uint64(3 * b + 2)
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier", help="dossier de snapshots quantifies SANS RLE (ex : d_q8)")
    ap.add_argument("--coords", required=True, help="coords.bin")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    _, xyz = lire_bin(a.coords)
    xyz = xyz.reshape(-1, 3).astype(np.float64)
    idx = [np.unique(xyz[:, d], return_inverse=True)[1] for d in range(3)]
    bits = int(max(i.max() for i in idx)).bit_length()
    i, j, k = (x.astype(np.uint64) for x in idx)

    centre = (xyz.min(axis=0) + xyz.max(axis=0)) / 2
    r = np.linalg.norm(xyz - centre, axis=1)
    ordres = {
        "origine": np.arange(xyz.shape[0]),
        "x puis y puis z": np.lexsort((xyz[:, 2], xyz[:, 1], xyz[:, 0])),
        "z puis y puis x": np.lexsort((xyz[:, 0], xyz[:, 1], xyz[:, 2])),
        "Morton (Z-order)": np.argsort(entrelacer(i, j, k, bits), kind="stable"),
        "distance au centre": np.argsort(np.round(r, 6), kind="stable"),
    }

    fichiers = sorted(glob.glob(os.path.join(a.dossier, "snapshot_*.bin")))
    brut = 0
    totaux = {nom: 0 for nom in ordres}
    for f in fichiers:
        q, largeur = lire_entiers(f)
        brut += q.size * largeur
        for nom, p in ordres.items():
            totaux[nom] += octets_rle(q[p], largeur)

    print(f"{len(fichiers)} snapshots, {xyz.shape[0]} noeuds, {brut} octets sans RLE")
    print(f"{'ordre':<20} {'octets RLE':>12} {'taux':>8} {'gain vs origine':>16}")
    lignes = []
    ref = totaux["origine"]
    for nom, t in totaux.items():
        print(f"{nom:<20} {t:>12d} {brut / t:>8.2f} {ref / t:>16.2f}")
        lignes.append(dict(ordre=nom, octets_rle=t, taux=brut / t, gain_vs_origine=ref / t))
    if a.out:
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
            w.writeheader()
            w.writerows(lignes)
        print(f"Mesures ecrites dans {a.out}")

if __name__ == "__main__":
    main()
