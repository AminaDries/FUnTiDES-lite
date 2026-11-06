## Coût du workflow ad-hoc

| Éléments | Threads | Sans snapshots (s) | Avec snapshots (s) | Écriture snapshots (s) | Surcoût (%) | Snapshots total (Mo) | Moyenne/snapshot (Mo) | Débit écriture (Mo/s) | RAM max (Mo) | Visualisation (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 50³ = 125000 | 24 | 0.61 | 4.06 | 3.456 | 569.4 | 31.76 | 15.88 | 9.2 | 45 | 3.38 |
| 100³ = 1000000 | 24 | 4.51 | 31.86 | 27.306 | 606.1 | 249.26 | 124.63 | 9.1 | 161 | 7.95 |
| 200³ = 8000000 | 24 | 35.97 | 262.79 | 226.360 | 630.5 | 1978.28 | 989.14 | 8.7 | 1236 | 44.33 |

## Snapshots vs slices

| Éléments | Threads | Snapshots (Mo) | Slices (Mo) | Rapport taille | Écriture snap. (s) | Écriture slices (s) | Rapport écriture | Image snap. (s) | Image slice (s) | Workflow snap. (s) | Workflow slice (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 50³ | 24 | 31.76 | 0.334 | ×95 | 3.456 | 0.0667 | ×52 | 1.99 | 1.35 | 6.05 | 2.03 |
| 100³ | 24 | 249.26 | 1.290 | ×193 | 27.306 | 0.3788 | ×72 | 6.58 | 1.95 | 38.44 | 6.85 |
| 200³ | 24 | 1978.28 | 5.118 | ×387 | 226.360 | 2.4869 | ×91 | 42.97 | 4.60 | 305.75 | 43.01 |
