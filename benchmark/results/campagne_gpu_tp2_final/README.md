# Campagne GPU finale du TP2 (2–4 novembre 2026)

Machine, GPU et build : voir `BUILD_GPU.md` (RTX 5050 Laptop, CUDA 13.4, Kokkos dev, C++20).
Réglages communs (annexe) : ordre 2, dt = 0.001 s, timemax 1.5 s, intervalle 50,
5 répétitions + 1 chauffe, médiane [min ; max], S/M/L = 50/100/200 éléments par côté.
Lectures « à chaud » (vider le cache demande `sudo`). Référence `sans` : `--no-seismos --quiet`.

## Dossiers

| Dossier | Contenu | Commit |
|---|---|---|
| `S/`, `M/`, `L/` | nuit du 2→3 nov : `sans`, `adhoc`, `adhoc_fsync`, `insitu_host` (L : `sans`, `adhoc`, `adhoc_fsync`) | `64b893c` |
| `S_insitu/`, `M_insitu/`, `L_insitu/` | reprise du 3 nov : `insitu`, `insitu_fsync` (L : + `insitu_host`) | `7777beb` |
| `L_python/` | L, ad-hoc avec les 3 scripts Python, 1 run (42 Go de snapshots) | `7777beb` |
| `vitesse_insitu_L.txt` | vitesse du front depuis les pics in-situ, L | `7777beb` |
| `precision_M/` | précision in-situ vs ad-hoc sur le **même** run (M) | `7777beb` |
| `run_benchmark/` | snapshots vs slices vs sans, S/M/L | `7777beb` |
| `logs/` | logs complets des deux campagnes | |

Le code mesuré par `sans`, `adhoc*` et `insitu_host` est identique entre `64b893c` et `7777beb`
(seul le chemin GPU de l'histogramme in-situ a changé), d'où la fusion des deux campagnes.

## Lignes `insitu` / `insitu_fsync` de `S/` et `M/` : à NE PAS utiliser comme mesures

Elles ont été faites avec la première version de l'histogramme GPU (`64b893c`) :
un `atomic_add` par nœud sur une seule case (presque tous les nœuds sont dans la classe
centrale) → contention extrême : histogramme 114 s (S) et 910 s (M), contre 0,06 s (M)
après correction (histogramme local par équipe en mémoire partagée, `7777beb`).
Elles sont gardées comme illustration du piège, les vraies mesures sont dans `*_insitu/`.

## Non poussé (trop gros)

Les fichiers de pics par nœud `insitu_vel.csv` (≈ 33 Mo en S, 260 Mo en M, 2 Go en L,
seule sortie in-situ qui croît en N³) et les snapshots (42 Go en L) restent en local.
