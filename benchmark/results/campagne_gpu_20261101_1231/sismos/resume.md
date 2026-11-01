Médiane [min - max] sur les runs mesurés (la chauffe, run 0, est exclue).
Écriture = temps vu par l'application ; persistance = écriture + fsync.
Lecture ad-hoc à chaud (fichiers juste écrits, servis par le cache).

## Temps par phase (ms)

| Taille | Écriture sismos | fsync | Lecture ad-hoc | Analyse ad-hoc | In-situ boucle | In-situ fin |
|---|---|---|---|---|---|---|
| 200³ | 1.82 [1.81 - 1.83] | 11.9 [5.1 - 12.6] | 6.12 [6.09 - 6.16] | 2.36 [2.32 - 2.38] | 0.0811 [0.0795 - 0.0878] | 71 [71 - 71.1] |

## Impact sur la simulation (s)

| Taille | Calcul sans in-situ | Calcul avec in-situ | Total sans | Total avec |
|---|---|---|---|---|
| 200³ | 51.2 [51.1 - 51.4] | 51.3 [51.2 - 51.5] | 52.3 [52.3 - 52.5] | 52.6 [52.5 - 52.7] |

## Volume et précision

| Taille | Nœuds | Pas | seismos.csv (octets) | Écart relatif max in-situ / ad-hoc |
|---|---|---|---|---|
| 200³ | 64481201 | 1499 | 154397 | 9e-09 |
