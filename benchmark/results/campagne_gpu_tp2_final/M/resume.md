# Resume des mesures

- machine : benachour-souhila-LOQ-15IRX10 (inconnu, 20 threads logiques, OMP_NUM_THREADS=20)
- GPU : NVIDIA GeForce RTX 5050 Laptop GPU, 8151 MiB, 595.99.02
- systeme de fichiers : `/dev/mapper/ubuntu--vg-ubuntu--lv ext4   980211368 236124244  694221396  26% /`
- commit : `64b893c34a0f38f190539c7bede926ccb75e56a5` (modifications non commitees : True)
- repetitions : 5 ; mediane [min ; max]

## M (100^3 elements)

| mode | runs | total (s) | calcul (s) | ecriture snapshots (s) | dont fsync (s) | in-situ stats (s) | in-situ hist (s) | in-situ vitesse (s) | ecriture in-situ (s) | copie GPU->hote snapshots (s) | copie GPU->hote in-situ (s) | Python ad-hoc (s) | volume ecrit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sans | 5 | 6.696 [6.671 ; 6.771] | 6.353 [6.317 ; 6.361] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 0.00 Mo |
| adhoc | 5, lectures chaud | 133.435 [133.423 ; 136.660] | 5.265 [5.241 ; 5.280] | 126.484 [126.454 ; 130.150] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.512 [0.505 ; 0.522] | 0.000 [0.000 ; 0.000] | 127.735 [127.569 ; 127.939] | 5405.56 Mo |
| adhoc_fsync | 5, lectures chaud | 134.724 [134.588 ; 134.755] | 5.247 [5.234 ; 5.258] | 127.782 [127.635 ; 127.813] | 1.612 [1.551 ; 1.620] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.514 [0.507 ; 0.518] | 0.000 [0.000 ; 0.000] | 127.557 [127.239 ; 127.848] | 5405.55 Mo |
| insitu | 5 | 921.858 [920.844 ; 923.514] | 5.331 [5.320 ; 5.351] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.057 [0.057 ; 0.057] | 910.427 [909.412 ; 910.752] | 0.013 [0.013 ; 0.013] | 5.632 [5.627 ; 5.660] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 259.52 Mo |
| insitu_fsync | 5 | 922.860 [921.011 ; 923.684] | 5.333 [5.327 ; 5.340] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.057 [0.057 ; 0.057] | 911.344 [909.530 ; 912.196] | 0.013 [0.013 ; 0.013] | 5.692 [5.691 ; 5.714] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | - | 259.52 Mo |
| insitu_host | 5 | 13.800 [13.767 ; 13.817] | 5.630 [5.604 ; 5.653] | 0.000 [0.000 ; 0.000] | 0.000 [0.000 ; 0.000] | 0.986 [0.984 ; 0.986] | 0.477 [0.476 ; 0.481] | 0.202 [0.202 ; 0.207] | 5.603 [5.599 ; 5.608] | 0.000 [0.000 ; 0.000] | 0.501 [0.500 ; 0.503] | - | 259.52 Mo |

Notes : 'total' = duree de la simulation vue de l'exterieur (sans les scripts Python). Le cout d'un workflow ad-hoc = total + Python ad-hoc. Sans `fsync`, le temps d'ecriture est celui vu par l'application (copie dans le cache du systeme) ; avec `fsync` c'est le temps de persistance.
