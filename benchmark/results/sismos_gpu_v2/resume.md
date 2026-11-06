Médiane [min - max] sur les runs mesurés (la chauffe, run 0, est exclue).
Écriture = temps vu par l'application ; persistance = écriture + fsync.
Lecture ad-hoc à chaud (fichiers juste écrits, servis par le cache).

## Temps par phase (ms)

| Taille | Extraction récepteurs (UVM) | Écriture sismos | fsync | Lecture ad-hoc | Analyse ad-hoc | In-situ boucle | In-situ fin |
|---|---|---|---|---|---|---|---|
| 50³ | 10.7 [10.3 - 11.5] | 1.98 [1.92 - 2.01] | 3.75 [3.41 - 4.7] | 6.23 [6.19 - 6.45] | 2.35 [2.26 - 2.35] | 0.0677 [0.066 - 0.0699] | 70.8 [70.7 - 72] |
| 100³ | 76.4 [75.8 - 78] | 1.85 [1.83 - 1.92] | 5.01 [3.75 - 5.74] | 6.18 [6.15 - 6.2] | 2.33 [2.32 - 2.36] | 0.0754 [0.0734 - 0.0795] | 70.8 [70.7 - 72.3] |
| 200³ | 94.1 [93.8 - 94.5] | 1.83 [1.82 - 1.87] | 12.5 [5.58 - 14.4] | 6.09 [6.06 - 6.12] | 2.33 [2.3 - 2.4] | 0.0785 [0.0749 - 0.0797] | 70.7 [70.7 - 70.9] |

## Impact sur la simulation (s)

Référence = aucune sortie (--no-seismos). L'écart de calcul entre référence et « sans in-situ » montre le retour des pages UVM vers le GPU après l'extraction (annexe 2).

| Taille | Calcul référence | Calcul sans in-situ | Calcul avec in-situ | Total référence | Total sans | Total avec |
|---|---|---|---|---|---|---|
| 50³ | 0.546 [0.545 - 0.547] | 0.575 [0.574 - 0.576] | 0.574 [0.573 - 0.577] | 0.803 [0.794 - 0.818] | 0.863 [0.852 - 0.886] | 0.921 [0.917 - 0.953] |
| 100³ | 6.36 [6.35 - 6.37] | 6.44 [6.39 - 6.48] | 6.45 [6.43 - 6.48] | 6.71 [6.7 - 6.72] | 6.89 [6.83 - 6.91] | 6.97 [6.96 - 6.98] |
| 200³ | 51.4 [51.3 - 51.5] | 51.6 [51.5 - 51.6] | 51.5 [51.5 - 51.6] | 52.5 [52.4 - 52.6] | 52.8 [52.7 - 52.8] | 52.8 [52.7 - 52.9] |

## Volume et précision

| Taille | Nœuds | Pas | seismos.csv (octets) | Écart relatif max in-situ / ad-hoc |
|---|---|---|---|---|
| 50³ | 1030301 | 1499 | 167793 | 9e-09 |
| 100³ | 8120601 | 1499 | 161670 | 9e-09 |
| 200³ | 64481201 | 1499 | 154396 | 9e-09 |
