Médiane [min - max] sur les runs mesurés (la chauffe, run 0, est exclue).
Écriture = temps vu par l'application ; persistance = écriture + fsync.
Lecture ad-hoc à chaud (fichiers juste écrits, servis par le cache).

## Temps par phase (ms)

| Taille | Écriture sismos | fsync | Lecture ad-hoc | Analyse ad-hoc | In-situ boucle | In-situ fin |
|---|---|---|---|---|---|---|
| 50³ | 1.85 [1.84 - 1.86] | 4.9 [4.74 - 5.9] | 6.23 [6.21 - 6.25] | 2.38 [2.33 - 2.39] | 0.0735 [0.0709 - 0.0743] | 71.2 [71 - 72] |
| 100³ | 1.87 [1.83 - 1.99] | 4.72 [4.32 - 4.83] | 6.15 [6.14 - 6.24] | 2.35 [2.34 - 2.37] | 0.0798 [0.0782 - 0.0839] | 71.1 [70.9 - 71.3] |

## Impact sur la simulation (s)

| Taille | Calcul sans in-situ | Calcul avec in-situ | Total sans | Total avec |
|---|---|---|---|---|
| 50³ | 0.589 [0.584 - 0.593] | 0.585 [0.582 - 0.593] | 0.872 [0.863 - 0.873] | 0.937 [0.927 - 0.953] |
| 100³ | 6.42 [6.4 - 6.45] | 6.45 [6.4 - 6.46] | 6.85 [6.83 - 6.94] | 6.95 [6.9 - 6.98] |

## Volume et précision

| Taille | Nœuds | Pas | seismos.csv (octets) | Écart relatif max in-situ / ad-hoc |
|---|---|---|---|---|
| 50³ | 1030301 | 1499 | 167884 | 8.5e-09 |
| 100³ | 8120601 | 1499 | 161685 | 9.8e-09 |
