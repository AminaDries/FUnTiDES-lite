# Build GPU utilisé pour les mesures (TP1 à TP3)

Toutes les mesures GPU du groupe (`benchmark/results/campagne_gpu_*`) ont été faites
avec ce build. Il **diffère du dépôt** sur deux points, nécessaires pour la carte
utilisée (architecture Blackwell, que le Kokkos du dépôt ne connaît pas).
Ces deux modifications sont **locales** : elles ne sont pas commitées, pour ne pas
changer le build des autres membres du groupe.

## Machine

| | |
|---|---|
| CPU | 13th Gen Intel Core i7-13650HX (20 threads logiques) |
| GPU | NVIDIA GeForce RTX 5050 Laptop GPU, 8151 Mio, pilote 595.99.02 |
| CUDA | 13.4 (`nvcc` V13.4.92, `/usr/local/cuda/bin/nvcc`) |
| RAM | 31 Gio |
| OS | Ubuntu 24.04.5 LTS (natif, pas de WSL) |
| Système de fichiers des mesures | ext4, disque local (`/dev/mapper/ubuntu--vg-ubuntu--lv`) |
| Mode d'énergie | Performance, sur secteur |

## Différences avec le dépôt

### 1. Kokkos plus récent (sous-module `external/kokkos`)

| | Commit | Version |
|---|---|---|
| Attendu par le dépôt | `1a3ea28f6e97b4c9dd2c8ceed53ad58ed5f94dfe` | Kokkos 4.1.00 |
| **Utilisé** | `b8c48cc9c790ab5a7676497aa9a8657f4360f57d` (2026-10-16) | branche de développement (`git describe` : `post-formating-12062-gb8c48cc9c`) |

Pourquoi : Kokkos 4.1 ne connaît pas l'architecture Blackwell (`compute capability 12.0`),
et avec un repli sur une architecture plus ancienne (`AMPERE80`), la compilation échoue sur
une signature de `cudaMemPrefetchAsync` qui a changé avec CUDA 13.

### 2. `cmake/CompilerConfig.cmake` : C++20 au lieu de C++17

```diff
-set(CMAKE_CXX_STANDARD 17 CACHE STRING "" FORCE)
+set(CMAKE_CXX_STANDARD 20 CACHE STRING "" FORCE)
```

Pourquoi : la version de Kokkos utilisée exige C++20.

## Refaire ce build

```bash
# 1. passe le sous-module Kokkos sur le commit utilisé
git -C external/kokkos fetch origin
git -C external/kokkos checkout b8c48cc9c790ab5a7676497aa9a8657f4360f57d

# 2. passe le standard C++ à 20 (modification locale, à ne pas commiter)
sed -i 's/set(CMAKE_CXX_STANDARD 17/set(CMAKE_CXX_STANDARD 20/' cmake/CompilerConfig.cmake

# 3. configure avec Kokkos + CUDA (UVM et lambdas sont activés par cmake/KokkosConfig.cmake)
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release -DUSE_KOKKOS=ON -DENABLE_CUDA=ON \
      -DKokkos_ARCH_BLACKWELL120=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc

# 4. compile
cmake --build build-release -j
```

Options effectivement actives dans `build-release/CMakeCache.txt` :

```
CMAKE_BUILD_TYPE=Release
USE_KOKKOS=ON
ENABLE_CUDA=ON
Kokkos_ARCH_BLACKWELL120=ON
Kokkos_ENABLE_CUDA_UVM=ON        (mémoire unifiée, imposée par cmake/KokkosConfig.cmake)
Kokkos_ENABLE_CUDA_LAMBDA=ON
CMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -march=native -mtune=native
```

## Conséquence pour les résultats

Les fichiers de mesures indiquent « modifications non commitées : True »
(`meta.json` de `bench_adhoc_insitu.py`) ou
« reglages locaux non commites : CompilerConfig.cmake + sous-module Kokkos »
(`machine.txt` de `campagne_gpu.sh`). Ce sont uniquement ces deux modifications :
le code de l'application mesuré est exactement celui du commit indiqué.
