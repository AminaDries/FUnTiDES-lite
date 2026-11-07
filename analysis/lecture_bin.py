#!/usr/bin/env python3
import argparse
import struct

import numpy as np

FORMAT_ENTETE = "<4sIIIIIff"
TAILLE_ENTETE = struct.calcsize(FORMAT_ENTETE)
NOMS_CODEC = {0: "float32 brut", 1: "float16", 2: "entiers quantifies"}
DRAPEAU_RLE = 0x100

def decoder_rle(brut, largeur, nb):
    sortie = bytearray()
    i = 0
    total = 0
    while i < len(brut):
        run = 0
        decalage = 0
        while True:
            b = brut[i]
            i += 1
            run |= (b & 0x7F) << decalage
            if b < 0x80:
                break
            decalage += 7
        sortie += bytes(brut[i:i + largeur]) * run
        i += largeur
        total += run
    if total != nb:
        raise ValueError(f"RLE : {total} valeurs decodees, {nb} attendues")
    return bytes(sortie)

def lire_bin(chemin):
    with open(chemin, "rb") as f:
        brut = f.read(TAILLE_ENTETE)
        magic, version, nb, pas, codec, nbits, vmin, vmax = struct.unpack(FORMAT_ENTETE, brut)
        if magic != b"FTD1":
            raise ValueError(f"{chemin} : mauvais format (magic = {magic!r})")
        rle = bool(codec & DRAPEAU_RLE)
        base = codec & 0xFF
        reste = f.read()
    if base == 0:
        largeur, dtype = 4, "<f4"
    elif base == 1:
        largeur, dtype = 2, "<f2"
    elif base == 2:
        if nbits not in (8, 16):
            raise ValueError(f"{chemin} : {nbits} bits non gere")
        largeur, dtype = nbits // 8, "<u1" if nbits == 8 else "<u2"
    else:
        raise NotImplementedError(f"codec {base} pas encore gere par ce script")
    if rle:
        reste = decoder_rle(reste, largeur, nb)
    donnees = np.frombuffer(reste, dtype=dtype, count=nb)
    if base == 2:
        niveaux = np.float32(2 ** nbits - 1)
        marche = (np.float32(vmax) - np.float32(vmin)) / niveaux
        valeurs = np.float32(vmin) + donnees.astype(np.float32) * marche
    else:
        valeurs = donnees.astype(np.float32)
    entete = dict(version=version, nb_values=nb, timestep=pas, codec=base, rle=rle,
                  nbits=nbits, vmin=vmin, vmax=vmax)
    return entete, valeurs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fichier", help="fichier .bin (snapshot ou coords.bin)")
    ap.add_argument("--csv", help="snapshot CSV a comparer (colonnes x,y,z,pressure)")
    a = ap.parse_args()

    e, v = lire_bin(a.fichier)
    print(f"{a.fichier}")
    print(f"  pas {e['timestep']} | {e['nb_values']} valeurs | codec : {NOMS_CODEC.get(e['codec'], e['codec'])}"
          f"{' + RLE' if e['rle'] else ''} | {e['nbits']} bits"
          + (f" | bornes [{e['vmin']:.6g}, {e['vmax']:.6g}]" if e["codec"] == 2 else ""))
    print(f"  min {v.min():.6g} | max {v.max():.6g} | max|p| {np.abs(v).max():.6g}")

    if a.csv:
        csv = np.loadtxt(a.csv, delimiter=",", skiprows=1, usecols=3)
        if csv.size != v.size:
            raise SystemExit(f"  ERREUR : {csv.size} valeurs dans le CSV, {v.size} dans le .bin")
        ecart = np.abs(v.astype(np.float64) - csv)
        amp = np.abs(csv).max()
        print(f"  comparaison au CSV : ecart max {ecart.max():.3e}"
              f" ({ecart.max() / max(amp, 1e-30):.3e} de max|p|)")

if __name__ == "__main__":
    main()
