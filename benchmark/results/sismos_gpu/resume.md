Médiane [min - max] sur les runs mesurés (la chauffe, run 0, est exclue).
Écriture = temps vu par l'application ; persistance = écriture + fsync.
Lecture ad-hoc à chaud (fichiers juste écrits, servis par le cache).

## Temps par phase (ms)

| Taille | Écriture sismos | fsync | Lecture ad-hoc | Analyse ad-hoc | In-situ boucle | In-situ fin |
|---|---|---|---|---|---|---|
| 50³ | 2.39 [2.37 - 2.4] | 4.96 [4.6 - 5.7] | 7.29 [7.26 - 7.36] | 2.68 [2.64 - 2.76] | 0.0934 [0.0931 - 0.0945] | 91.6 [91.5 - 91.8] |
| 100³ | 2.37 [2.35 - 2.41] | 4.99 [3.51 - 5.23] | 7.26 [7.09 - 7.38] | 2.71 [2.66 - 3.05] | 0.103 [0.101 - 0.114] | 91.7 [91.6 - 91.8] |
| 200³ | 2.34 [2.33 - 2.37] | 12.7 [5.55 - 13.5] | 7.19 [7.13 - 7.24] | 2.72 [2.67 - 2.76] | 0.107 [0.102 - 0.11] | 91.7 [91.5 - 91.9] |

## Impact sur la simulation (s)

| Taille | Calcul sans in-situ | Calcul avec in-situ | Total sans | Total avec |
|---|---|---|---|---|
| 50³ | 0.588 [0.584 - 0.589] | 0.585 [0.583 - 0.592] | 0.899 [0.88 - 0.933] | 0.969 [0.959 - 0.98] |
| 100³ | 6.44 [6.41 - 6.48] | 6.46 [6.4 - 6.48] | 6.91 [6.89 - 6.96] | 7.04 [6.99 - 7.04] |
| 200³ | 52 [51.8 - 52.2] | 52.1 [51.9 - 52.2] | 53.5 [53.2 - 53.7] | 53.6 [53.4 - 53.7] |

## Volume et précision

| Taille | Nœuds | Pas | seismos.csv (octets) | Écart relatif max in-situ / ad-hoc |
|---|---|---|---|---|
| 50³ | 1030301 | 1499 | 167906 | 9e-09 |
| 100³ | 8120601 | 1499 | 161680 | 9e-09 |
| 200³ | 64481201 | 1499 | 154325 | 1.1e-08 |
