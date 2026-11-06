## Coût du workflow ad-hoc

| Éléments | Threads | Sans snapshots (s) | Avec snapshots (s) | Écriture snapshots (s) | Surcoût (%) | Snapshots total (Mo) | Moyenne/snapshot (Mo) | Débit écriture (Mo/s) | RAM max (Mo) | Visualisation (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 200³ = 8000000 | 30720 | 7.56 | 266.12 | 257.847 | 3420.0 | 8039.69 | 1004.96 | 31.2 | 461 | 18.28 |

## Snapshots vs slices

| Éléments | Threads | Snapshots (Mo) | Slices (Mo) | Rapport taille | Écriture snap. (s) | Extraction slices (s) | Écriture slices (s) | fsync slices (s) | Rapport écriture | Image snap. (s) | Image slice (s) | Workflow snap. (s) | Workflow slice (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 200³ | 30720 | 8039.69 | 21.708 | ×370 | 257.847 | 1.8386 | 0.6362 | 0.0386 | ×104 | 17.79 | 1.80 | 283.91 | 11.08 |

## Dispersion : médiane [min – max] sur 5 répétitions (chauffe écartée)

| Éléments | Mode | Simulation (s) | Image (s) |
|---|---|---|---|
| 200³ | sans | 7.560 [7.514 – 7.591] | 0.000 [0.000 – 0.000] |
| 200³ | avec | 266.125 [265.541 – 266.800] | 17.788 [17.730 – 17.835] |
| 200³ | slices | 9.279 [9.234 – 9.325] | 1.802 [1.797 – 1.806] |
