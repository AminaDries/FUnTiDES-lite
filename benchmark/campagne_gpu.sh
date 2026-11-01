#!/bin/bash
# =============================================================================
# Campagne de mesures du groupe sur GPU (TP2) : compilation + benchmarks.
#
# A lancer depuis la racine du depot, sur la machine avec GPU :
#     bash benchmark/campagne_gpu.sh
#
# Etapes :
#   1. verifications (branche, GPU, secteur, build CUDA, place disque)
#   2. recompilation de build-release sur le code actuel
#   3. informations machine (annexe, sections 4 et 8)
#   4. chauffe : un run par taille, non compte (annexe, section 5)
#   5. benchmarks du groupe, 5 repetitions, tailles S/M/L
#
# La campagne tourne sous systemd-inhibit : l'ordinateur ne se met pas en
# veille pendant les mesures. Ne rien utiliser d'autre pendant ce temps.
#
# Pour ajouter un benchmark : ajouter une ligne dans la section 5, sur le
# modele des autres (toujours --exe "$EXE" et une sortie dans "$OUT/...").
# =============================================================================
set -euo pipefail

BUILD=build-release              # dossier de build CUDA (configure une fois a la main)
EXE="$BUILD/bin/semproxy"
SIZES="${SIZES:-50 100 200}"     # S, M, L (les memes qu'au TP1) ; SIZES="10" pour un essai rapide
REPEATS="${REPEATS:-5}"          # annexe, section 5 : au moins 5
OUT="benchmark/results/campagne_gpu_$(date +%Y%m%d_%H%M)"

# noms des configurations pour bench_adhoc_insitu.py : "S=50 M=100 L=200"
NOMS=(S M L)
CONFIGS=""
i=0
for N in $SIZES; do
  CONFIGS="$CONFIGS ${NOMS[$i]:-C$i}=$N"
  i=$((i + 1))
done

echo "=== 1. Verifications ==="

# racine du depot ?
[ -f CMakeLists.txt ] && [ -d benchmark ] || { echo "Lance ce script depuis la racine du depot."; exit 1; }

# GPU visible ?
nvidia-smi > /dev/null || { echo "nvidia-smi ne repond pas : pas de GPU visible."; exit 1; }

# build CUDA deja configure ? (configuration locale : Kokkos mis a jour pour Blackwell)
[ -f "$BUILD/CMakeCache.txt" ] || { echo "$BUILD n'est pas configure."; exit 1; }
grep -q "^ENABLE_CUDA:BOOL=ON" "$BUILD/CMakeCache.txt" || { echo "$BUILD n'est pas compile pour CUDA."; exit 1; }

# portable sur secteur ? (sur batterie, le GPU est bride)
if ls /sys/class/power_supply/A*/online > /dev/null 2>&1; then
  if ! grep -q 1 /sys/class/power_supply/A*/online; then
    echo "Le portable est sur batterie : branche-le sur secteur avant de lancer."; exit 1
  fi
fi

# place disque (les snapshots en L font environ 2 Go par run, effaces au fur et a mesure)
LIBRE_GO=$(df -BG --output=avail . | tail -1 | tr -dc '0-9')
[ "$LIBRE_GO" -ge 20 ] || { echo "Moins de 20 Go libres : libere de la place."; exit 1; }

# fichiers modifies non commites : seuls les reglages locaux CUDA sont attendus
AUTRES=$(git status --porcelain --untracked-files=no | grep -v -e "cmake/CompilerConfig.cmake" -e "external/kokkos" || true)
if [ -n "$AUTRES" ]; then
  echo "Fichiers modifies non commites (le hash du commit ne decrirait pas le code mesure) :"
  echo "$AUTRES"; exit 1
fi

echo "Branche : $(git branch --show-current), commit : $(git rev-parse --short HEAD)"

echo "=== 2. Compilation ==="
cmake --build "$BUILD" -j

mkdir -p "$OUT"

echo "=== 3. Informations machine ==="
{
  echo "date : $(date '+%Y-%m-%d %H:%M')"
  echo "commit : $(git rev-parse HEAD) (branche $(git branch --show-current))"
  echo "reglages locaux non commites : CompilerConfig.cmake + sous-module Kokkos"
  if [ -e external/kokkos/.git ]; then
    echo "kokkos : $(git -C external/kokkos describe --tags 2>/dev/null || git -C external/kokkos rev-parse --short HEAD)"
  fi
  echo "CPU : $(LC_ALL=C lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
  echo "GPU : $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader)"
  echo "CUDA : $(nvcc --version 2>/dev/null | grep release | sed 's/.*release //' || echo 'nvcc absent du PATH')"
  echo "RAM : $(LC_ALL=C free -h | grep Mem | awk '{print $2}')"
  echo "OS : $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')"
  echo "systeme de fichiers : $(df -T . | tail -1 | awk '{print $1, $2}')"
  echo "compilation :"
  grep -E "^(CMAKE_BUILD_TYPE|ENABLE_CUDA|USE_KOKKOS|Kokkos_ENABLE_CUDA_UVM|Kokkos_ARCH_[A-Z0-9_]+):" "$BUILD/CMakeCache.txt" | grep "=ON\|BUILD_TYPE" | sed 's/^/  /'
  echo "tailles : $SIZES, repetitions : $REPEATS (+ 1 chauffe par taille, non comptee)"
} | tee "$OUT/machine.txt"

# Tout ce qui suit tourne sans mise en veille possible (si systemd-inhibit marche)
if systemd-inhibit --what=sleep:idle --why=test true 2> /dev/null; then
  SANS_VEILLE=(systemd-inhibit --what=sleep:idle --why="Campagne de mesures TP2")
else
  echo "ATTENTION : impossible de bloquer la veille, desactive-la dans les parametres."
  SANS_VEILLE=()
fi
"${SANS_VEILLE[@]}" bash -c "
set -euo pipefail

echo '=== 4. Chauffe (non comptee) ==='
for N in $SIZES; do
  ./$EXE --ex \$N --ey \$N --ez \$N --timemax 0.1 --seismo-dir /tmp/chauffe > /dev/null
  echo \"chauffe \${N}³ faite\"
done
rm -rf /tmp/chauffe

echo '=== 5. Benchmarks ==='

# 5a. Snapshots vs slices (sans / avec snapshots / slices) : script de la partie slices
python3 benchmark/run_benchmark.py --exe $EXE --sizes $SIZES --repeats $REPEATS --out $OUT/snapshots_slices

# 5b. Sismos : ad-hoc vs in-situ (chauffe incluse dans le script)
python3 benchmark/bench_sismos.py --exe $EXE --sizes $SIZES --repeats $REPEATS --out $OUT/sismos

# 5c. Snapshots : ad-hoc vs in-situ, dont host vs device (comparaison obligatoire)
python3 analysis/bench_adhoc_insitu.py --exe $EXE --build-dir $BUILD --config $CONFIGS \
  --modes sans adhoc adhoc_fsync insitu insitu_fsync insitu_host \
  --repeats $REPEATS --out $OUT/snapshots_insitu
"

echo "=== Termine : resultats dans $OUT ==="
