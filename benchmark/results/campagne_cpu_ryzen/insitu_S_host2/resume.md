# Resume des mesures

- machine : DESKTOP-0AFKAGB (AMD Ryzen 7 5700U with Radeon Graphics, 16 threads logiques, OMP_NUM_THREADS=16)
- GPU : inconnu
- systeme de fichiers : `/dev/sdd       ext4 1055762868 2720180 999339216   1% /`
- commit : `78018814d19f4133fde06f3a5b84bf7bbde8b63c` (modifications non commitees : False)
- repetitions : 5 ; mediane [min ; max]

## S (50^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| insitu_host | 5 | 99.410 [83.984 ; 105.978] | 97.013 [81.433 ; 103.597] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.239 [0.185 ; 0.241] | 0.414 [0.330 ; 0.426] | 0.094 [0.086 ; 0.098] | 1.529 [1.477 ; 1.671] | - | 32.93 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
