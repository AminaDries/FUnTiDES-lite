# Resume des mesures

- machine : benachour-souhila-LOQ-15IRX10 (inconnu, 20 threads logiques, OMP_NUM_THREADS=20)
- GPU : NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, 595.99.02
- systeme de fichiers : `/dev/mapper/ubuntu--vg-ubuntu--lv ext4   980211368 233102468  697243172  26% /`
- commit : `4b4d19bb37b0789cc5d706735cea9fb58445ab9d` (modifications non commitees : True)
- repetitions : 5 ; mediane [min ; max]

## L (200^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sans | 5 | 52.770 [52.607 ; 52.790] | 51.511 [51.341 ; 51.534] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 0.00 Mo |
| adhoc | 5, lectures chaud | 1066.641 [1063.661 ; 1073.668] | 49.410 [49.336 ; 50.170] | 1014.530 [1012.900 ; 1021.514] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 41823.39 Mo |
| adhoc_fsync | 5, lectures chaud | 1071.528 [1068.937 ; 1085.251] | 49.268 [49.207 ; 49.815] | 1019.571 [1016.364 ; 1033.168] | 2.024 [1.676 ; 4.119] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 41823.39 Mo |
| insitu | 5 | 102.469 [102.362 ; 103.916] | 49.140 [49.024 ; 49.226] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.684 [0.680 ; 0.685] | 3.788 [3.786 ; 3.835] | 2.338 [2.336 ; 2.357] | 44.737 [44.625 ; 44.845] | - | 2060.22 Mo |
| insitu_fsync | 5 | 102.511 [102.494 ; 102.765] | 49.176 [49.135 ; 49.261] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.683 [0.680 ; 0.685] | 3.790 [3.788 ; 3.801] | 2.343 [2.339 ; 2.347] | 44.841 [44.786 ; 44.965] | - | 2060.22 Mo |
| insitu_host | 5 | 109.055 [108.762 ; 109.177] | 48.639 [48.404 ; 48.699] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 7.806 [7.800 ; 7.811] | 3.787 [3.782 ; 3.816] | 2.335 [2.333 ; 2.373] | 44.711 [44.651 ; 44.818] | - | 2060.22 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
