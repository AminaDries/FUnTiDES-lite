# Resume des mesures

- machine : benachour-souhila-LOQ-15IRX10 (inconnu, 20 threads logiques, OMP_NUM_THREADS=20)
- GPU : NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, 595.99.02
- systeme de fichiers : `/dev/mapper/ubuntu--vg-ubuntu--lv ext4   980211368 240319296  690026344  26% /`
- commit : `7777beb9716bb7198a6ca802e5ce7be4892374c1` (modifications non commitees : True)
- repetitions : 5 ; mediane [min ; max]

## S (50^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | copie GPU->hote snapshots (s) | copie GPU->hote in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| insitu | 5 | 1.565 [1.553 ; 1.590] | 0.543 [0.542 ; 0.575] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.011 [0.011 ; 0.012] | 0.007 [0.007 ; 0.007] | 0.002 [0.002 ; 0.002] | 0.730 [0.729 ; 0.737] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 32.93 Mo |
| insitu_fsync | 5 | 1.566 [1.556 ; 1.586] | 0.543 [0.542 ; 0.544] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.011 [0.011 ; 0.011] | 0.007 [0.007 ; 0.007] | 0.002 [0.002 ; 0.002] | 0.740 [0.738 ; 0.741] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 32.93 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
