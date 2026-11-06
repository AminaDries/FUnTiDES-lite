# Resume des mesures

- machine : benachour-souhila-LOQ-15IRX10 (inconnu, 20 threads logiques, OMP_NUM_THREADS=20)
- GPU : NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, 595.99.02
- systeme de fichiers : `/dev/mapper/ubuntu--vg-ubuntu--lv ext4   980211368 246925248  683420392  27% /`
- commit : `7777beb9716bb7198a6ca802e5ce7be4892374c1` (modifications non commitees : True)
- repetitions : 1 ; mediane [min ; max]

## L (200^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | copie GPU->hote snapshots (s) | copie GPU->hote in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adhoc | 1, lectures chaud | 1061.416 [1061.416 ; 1061.416] | 48.978 [48.978 ; 48.978] | 1011.385 [1011.385 ; 1011.385] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 3.963 [3.963 ; 3.963] | 0.000 [0.000 ; 0.000] | 1030.806 [1030.806 ; 1030.806] | 41823.41 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
