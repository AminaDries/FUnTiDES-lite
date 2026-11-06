# Resume des mesures

- machine : DESKTOP-0AFKAGB (AMD Ryzen 7 5700U with Radeon Graphics, 16 threads logiques, OMP_NUM_THREADS=16)
- GPU : inconnu
- systeme de fichiers : `/dev/sdd       ext4 1055762868 2619276 999440120   1% /`
- commit : `78018814d19f4133fde06f3a5b84bf7bbde8b63c` (modifications non commitees : False)
- repetitions : 5 ; mediane [min ; max]

## S (50^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sans | 5 | 98.770 [97.161 ; 99.520] | 98.566 [97.042 ; 99.379] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 0.00 Mo |
| adhoc | 5, lectures chaud | 151.133 [148.036 ; 157.530] | 104.287 [101.985 ; 110.101] | 46.583 [45.885 ; 47.282] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 46.631 [44.941 ; 48.808] | 718.58 Mo |
| adhoc_fsync | 5, lectures chaud | 152.665 [148.910 ; 154.168] | 105.597 [102.388 ; 106.785] | 46.992 [46.346 ; 47.430] | 0.820 [0.788 ; 0.860] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 44.623 [44.220 ; 47.523] | 718.58 Mo |
| insitu | 5 | 101.238 [100.229 ; 103.611] | 98.669 [97.621 ; 100.883] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.035 [0.031 ; 0.039] | 0.354 [0.351 ; 0.356] | 0.087 [0.086 ; 0.089] | 1.975 [1.933 ; 2.095] | - | 32.93 Mo |
| insitu_fsync | 5 | 100.927 [99.713 ; 102.117] | 98.201 [97.087 ; 99.501] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.032 [0.030 ; 0.035] | 0.354 [0.351 ; 0.366] | 0.086 [0.084 ; 0.092] | 1.982 [1.955 ; 2.128] | - | 32.93 Mo |
| insitu_host | 5 | 107.380 [100.071 ; 190.878] | 104.582 [97.349 ; 183.948] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.201 [0.195 ; 0.454] | 0.366 [0.365 ; 0.778] | 0.091 [0.087 ; 0.132] | 2.024 [1.908 ; 5.267] | - | 32.93 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
