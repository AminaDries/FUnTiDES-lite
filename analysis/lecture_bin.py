#!/usr/bin/env python3
import argparse
import struct

import numpy as np

FORMAT_ENTETE = "<4sIIIIIff"
TAILLE_ENTETE = struct.calcsize(FORMAT_ENTETE)
NOMS_CODEC = {0: "float32 brut"}

def lire_bin(chemin):
    with open(chemin, "rb") as f:
        brut = f.read(TAILLE_ENTETE)
        magic, version, nb, pas, codec, nbits, vmin, vmax = struct.unpack(FORMAT_ENTETE, brut)
        if magic != b"FTD1":
            raise ValueError(f"{chemin} : mauvais format (magic = {magic!r})")
        if codec != 0:
            raise NotImplementedError(f"codec {codec} pas encore gere par ce script")
        valeurs = np.fromfile(f, dtype="<f4", count=nb)
    if valeurs.size != nb:
        raise ValueError(f"{chemin} : {valeurs.size} valeurs lues, {nb} attendues")
    entete = dict(version=version, nb_values=nb, timestep=pas, codec=codec,
                  nbits=nbits, vmin=vmin, vmax=vmax)
    return entete, valeurs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fichier")
    ap.add_argument("--csv")
    a = ap.parse_args()

    e, v = lire_bin(a.fichier)
    print(f"{a.fichier}")
    print(f"  pas {e['timestep']} | {e['nb_values']} valeurs | codec : {NOMS_CODEC.get(e['codec'], e['codec'])} | {e['nbits']} bits")
    print(f"  min {v.min():.6g} | max {v.max():.6g} | max|p| {np.abs(v).max():.6g}")

    if a.csv:
        csv = np.loadtxt(a.csv, delimiter=",", skiprows=1, usecols=3)
        if csv.size != v.size:
            raise SystemExit(f"  ERREUR : {csv.size} valeurs dans le CSV, {v.size} dans le .bin")
        ecart = np.abs(v.astype(np.float64) - csv)
        amp = np.abs(csv).max()
        print(f"  comparaison au CSV : ecart max {ecart.max():.3e}"
              f" ({ecart.max() / amp:.3e} de max|p|), noeuds differents a plus de 1e-5 : {(ecart > 1e-5 * max(amp, 1e-30)).sum()}")

if __name__ == "__main__":
    main()
