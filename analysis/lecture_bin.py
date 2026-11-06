#!/usr/bin/env python3
import argparse
import struct

import numpy as np

FORMAT_ENTETE = "<4sIIIIIff"
TAILLE_ENTETE = struct.calcsize(FORMAT_ENTETE)
NOMS_CODEC = {0: "float32 brut", 1: "float16", 2: "entiers quantifies"}

def lire_bin(chemin):
    with open(chemin, "rb") as f:
        brut = f.read(TAILLE_ENTETE)
        magic, version, nb, pas, codec, nbits, vmin, vmax = struct.unpack(FORMAT_ENTETE, brut)
        if magic != b"FTD1":
            raise ValueError(f"{chemin} : mauvais format (magic = {magic!r})")
        if codec == 0:
            valeurs = np.fromfile(f, dtype="<f4", count=nb)
        elif codec == 1:
            valeurs = np.fromfile(f, dtype="<f2", count=nb).astype(np.float32)
        elif codec == 2:
            if nbits not in (8, 16):
                raise ValueError(f"{chemin} : {nbits} bits non gere")
            q = np.fromfile(f, dtype="<u1" if nbits == 8 else "<u2", count=nb)
            niveaux = np.float32(2 ** nbits - 1)
            marche = (np.float32(vmax) - np.float32(vmin)) / niveaux
            valeurs = np.float32(vmin) + q.astype(np.float32) * marche
        else:
            raise NotImplementedError(f"codec {codec} pas encore gere par ce script")
    if valeurs.size != nb:
        raise ValueError(f"{chemin} : {valeurs.size} valeurs lues, {nb} attendues")
    entete = dict(version=version, nb_values=nb, timestep=pas, codec=codec,
                  nbits=nbits, vmin=vmin, vmax=vmax)
    return entete, valeurs.astype(np.float32, copy=False)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichier", help="fichier .bin (snapshot ou coords.bin)")
    ap.add_argument("--csv", help="snapshot CSV a comparer (colonnes x,y,z,pressure)")
    a = ap.parse_args()

    e, v = lire_bin(a.fichier)
    print(f"{a.fichier}")
    print(f"  pas {e['timestep']} | {e['nb_values']} valeurs | codec : {NOMS_CODEC.get(e['codec'], e['codec'])} | {e['nbits']} bits"
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
