"""Analyse ad-hoc des sismogrammes (TP2, étape 1).

Usage :
    python analysis/sismos_adhoc.py DOSSIER

DOSSIER contient seismos.csv (time,rcv0,rcv1,...) et receivers.csv (id,x,y,z).
Écrit DOSSIER/stats_sismos.csv : une ligne par récepteur
(statistiques + temps d'arrivée de l'onde)
et DOSSIER/velocity_sismos.csv : vitesse de propagation estimée.
"""
import os
import sys
import time

import numpy as np

SEUIL = 0.1  # seuil de détection de la première arrivée (10 % du max de |p|)
NFFT = 8192
FENETRE = 0.2
SOURCE = (1010.0, 1010.0, 1010.0)  # position de la source (valeurs par défaut de srcx, srcy, srcz)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dossier = sys.argv[1]

    # --- 1) Lecture des fichiers (chronométrée à part : c'est le coût du workflow ad-hoc)
    t_debut = time.perf_counter()
    data = np.genfromtxt(os.path.join(dossier, "seismos.csv"), delimiter=",", names=True)
    rec = np.genfromtxt(os.path.join(dossier, "receivers.csv"), delimiter=",", names=True)
    t_lecture = time.perf_counter() - t_debut

    noms = data.dtype.names        # ('time', 'rcv0', 'rcv1', ...)
    t = data[noms[0]]
    dt = t[1] - t[0]
    rec = np.atleast_1d(rec)       # garde un tableau même s'il n'y a qu'un récepteur

    # --- 2) Statistiques et temps d'arrivée par récepteur
    t_debut = time.perf_counter()
    lignes = []
    for r, nom in enumerate(noms[1:]):
        p = data[nom]
        amp = np.abs(p)

        # temps du pic : instant où |p| est maximal (le lobe central de l'onde directe)
        t_pic = t[np.argmax(amp)]
        # premier dépassement : premier instant où |p| dépasse SEUIL x le maximum
        t_seuil = t[np.argmax(amp > SEUIL * amp.max())]

        
        # spectre : module de la FFT, puis fréquence où il est maximal
        spectre = np.abs(np.fft.rfft(p, n=NFFT))
        freqs = np.fft.rfftfreq(NFFT, d=dt)
        f_dom = freqs[np.argmax(spectre)]
	
        # spectre de l'onde directe seule : on garde +/- FENETRE autour du pic, le reste à 0
        fenetre = np.abs(t - t_pic) < FENETRE
        spectre_dir = np.abs(np.fft.rfft(p * fenetre, n=NFFT))
        f_dom_dir = freqs[np.argmax(spectre_dir)]

        lignes.append([
            r, rec["x"][r], rec["y"][r], rec["z"][r],
            p.min(), p.max(), p.mean(),
            p.var(),                 # variance (division par n)
            np.sum(p ** 2) * dt,     # énergie du signal : somme de p² dt
            t_pic, t_seuil, f_dom, f_dom_dir
        ])

    # --- 3) Vitesse de propagation : régression linéaire t_arrivée = t0 + d / v
    tab = np.array(lignes)
    d = np.sqrt((tab[:, 1] - SOURCE[0]) ** 2 + (tab[:, 2] - SOURCE[1]) ** 2
                + (tab[:, 3] - SOURCE[2]) ** 2)   # distance source -> récepteur
    vitesses = []
    for nom_col, col in (("t_peak", 9), ("t_first", 10)):
        pente, t0 = np.polyfit(d, tab[:, col], 1)  # droite t = pente * d + t0
        vitesses.append([nom_col, 1.0 / pente, t0])
    t_analyse = time.perf_counter() - t_debut

    # --- 4) Écriture des résultats
    sortie = os.path.join(dossier, "stats_sismos.csv")
    np.savetxt(sortie, np.array(lignes), delimiter=",", fmt="%.9g",
               header="receiver,x,y,z,min,max,mean,var,energy,t_peak,t_first,f_dom,f_dom_direct", comments="")

    sortie_v = os.path.join(dossier, "velocity_sismos.csv")
    with open(sortie_v, "w") as f:
        f.write("method,velocity,t0\n")
        for nom_col, v, t0 in vitesses:
            f.write(f"{nom_col},{v:.6g},{t0:.6g}\n")

    print(f"{len(lignes)} récepteurs, {len(t)} pas de temps (dt = {dt:g} s)")
    print(f"Temps de lecture : {t_lecture:.4f} s")
    print(f"Temps d'analyse  : {t_analyse:.4f} s")
    for nom_col, v, t0 in vitesses:
        print(f"Vitesse estimée avec {nom_col} : {v:.1f} m/s (t0 = {t0:.4f} s)")
    print(f"Résultats écrits dans {sortie} et {sortie_v}")


if __name__ == "__main__":
    main()
