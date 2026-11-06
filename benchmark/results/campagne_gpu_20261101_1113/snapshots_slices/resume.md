## Coût du workflow ad-hoc

| Éléments | Threads | Sans snapshots (s) | Avec snapshots (s) | Écriture snapshots (s) | Surcoût (%) | Snapshots total (Mo) | Moyenne/snapshot (Mo) | Débit écriture (Mo/s) | RAM max (Mo) | Visualisation (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 50³ = 125000 | 30720 | 0.35 | 4.65 | 4.191 | 1226.4 | 142.50 | 17.81 | 34.0 | 219 | 1.24 |
| 100³ = 1000000 | 30720 | 1.13 | 33.29 | 32.160 | 2842.2 | 1033.85 | 129.23 | 32.1 | 246 | 3.16 |

## Snapshots vs slices

| Éléments | Threads | Snapshots (Mo) | Slices (Mo) | Rapport taille | Écriture snap. (s) | Extraction slices (s) | Écriture slices (s) | fsync slices (s) | Rapport écriture | Image snap. (s) | Image slice (s) | Workflow snap. (s) | Workflow slice (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50³ | 30720 | 142.50 | 1.664 | ×86 | 4.191 | 0.0308 | 0.0416 | 0.0146 | ×58 | 0.74 | 0.47 | 5.39 | 0.91 |
| 100³ | 30720 | 1033.85 | 5.747 | ×180 | 32.160 | 0.2324 | 0.1581 | 0.0284 | ×82 | 2.66 | 0.70 | 35.95 | 2.20 |

## Dispersion : médiane [min – max] sur 5 répétitions (chauffe écartée)

| Éléments | Mode | Simulation (s) | Image (s) |
|---|---|---|---|
| 50³ | sans | 0.351 [0.339 – 0.360] | 0.000 [0.000 – 0.000] |
| 50³ | avec | 4.652 [4.630 – 4.697] | 0.736 [0.735 – 0.741] |
| 50³ | slices | 0.438 [0.428 – 0.452] | 0.470 [0.469 – 0.505] |
| 100³ | sans | 1.132 [1.124 – 1.147] | 0.000 [0.000 – 0.000] |
| 100³ | avec | 33.292 [33.243 – 34.833] | 2.660 [2.652 – 2.686] |
| 100³ | slices | 1.507 [1.492 – 1.516] | 0.695 [0.691 – 0.700] |
