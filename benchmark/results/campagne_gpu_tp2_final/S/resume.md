# Resume des mesures

- machine : benachour-souhila-LOQ-15IRX10 (inconnu, 20 threads logiques, OMP_NUM_THREADS=20)
- GPU : NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, 595.99.02
- systeme de fichiers : `/dev/mapper/ubuntu--vg-ubuntu--lv ext4   980211368 236033996  694311644  26% /`
- commit : `64b893c34a0f38f190539c7bede926ccb75e56a5` (modifications non commitees : True)
- repetitions : 5 ; mediane [min ; max]

## S (50^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | copie GPU->hote snapshots (s) | copie GPU->hote in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sans | 5 | 0.834 [0.810 ; 0.873] | 0.545 [0.543 ; 0.549] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 0.00 Mo |
| adhoc | 5, lectures chaud | 18.455 [17.159 ; 18.469] | 0.546 [0.534 ; 0.551] | 16.307 [16.302 ; 16.349] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.066 [0.065 ; 0.066] | 0.000 [0.000 ; 0.000] | 18.296 [18.270 ; 18.552] | 716.37 Mo |
| adhoc_fsync | 5, lectures chaud | 18.715 [18.701 ; 18.853] | 0.542 [0.537 ; 0.556] | 16.563 [16.552 ; 16.700] | 0.258 [0.245 ; 0.393] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.069 [0.066 ; 0.070] | 0.000 [0.000 ; 0.000] | 18.293 [18.215 ; 18.386] | 716.37 Mo |
| insitu | 5 | 116.184 [116.134 ; 117.537] | 0.499 [0.499 ; 0.500] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.010 [0.010 ; 0.010] | 114.681 [114.641 ; 114.871] | 0.002 [0.002 ; 0.002] | 0.721 [0.719 ; 0.728] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 32.93 Mo |
| insitu_fsync | 5 | 116.215 [116.023 ; 116.281] | 0.499 [0.498 ; 0.500] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.010 [0.010 ; 0.010] | 114.701 [114.505 ; 114.761] | 0.002 [0.002 ; 0.002] | 0.747 [0.746 ; 0.749] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 32.93 Mo |
| insitu_host | 5 | 1.820 [1.812 ; 1.829] | 0.563 [0.556 ; 0.565] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.125 [0.125 ; 0.125] | 0.061 [0.061 ; 0.063] | 0.025 [0.025 ; 0.027] | 0.715 [0.715 ; 0.721] | 0.000 [0.000 ; 0.000] | 0.064 [0.064 ; 0.068] | - | 32.93 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
