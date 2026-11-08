#!/bin/bash
set -euo pipefail

EXE="${EXE:-build-release/bin/semproxy}"
SIZES="${SIZES:-50 100 200}"
REPEATS="${REPEATS:-5}"
TIMEMAX="${TIMEMAX:-1.5}"
INTERVAL="${INTERVAL:-50}"
OUT="benchmark/results/compression_gpu_$(date +%Y%m%d_%H%M)"
TMP="${TMP:-$OUT/tmp}"

[ -x "$EXE" ] || { echo "Executable introuvable : $EXE"; exit 1; }
mkdir -p "$OUT" "$TMP"

NOMS=(S M L)
MODES=(
  "bin|--snap-format bin"
  "q8|--snap-format q8"
  "q8_rle|--snap-format q8 --snap-rle"
  "q16_rle|--snap-format q16 --snap-rle"
  "q8_rle_host|--snap-format q8 --snap-rle --quant-where host"
)

{
  echo "date : $(date '+%Y-%m-%d %H:%M')"
  echo "commit : $(git rev-parse HEAD) ($(git branch --show-current))"
  echo "GPU : $(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo aucun)"
  echo "tailles : $SIZES, repetitions : $REPEATS, timemax : $TIMEMAX, intervalle : $INTERVAL"
} | tee "$OUT/machine.txt"

lancer() {
  local n=$1 args=$2 dossier=$3
  rm -rf "$dossier"; mkdir -p "$dossier"
  local debut=$(date +%s.%N)
  "$EXE" --ex "$n" --ey "$n" --ez "$n" --timemax "$TIMEMAX" --no-seismos --quiet \
    --snapshots --snap-interval "$INTERVAL" --snap-folder "$dossier/snap" \
    --metrics-file "$dossier/metrics.csv" $args > "$dossier/log.txt"
  DUREE=$(echo "$(date +%s.%N) - $debut" | bc)
  OCTETS=$(du -sb "$dossier/snap" | cut -f1)
}

i=0
for N in $SIZES; do
  NOM=${NOMS[$i]:-C$i}
  i=$((i + 1))
  echo "=== $NOM ($N^3) : chauffe ==="
  lancer "$N" "--snap-format bin" "$TMP/chauffe"
  for m in "${MODES[@]}"; do
    MODE=${m%%|*}; ARGS=${m#*|}
    for r in $(seq 1 "$REPEATS"); do
      echo "$NOM $MODE run $r/$REPEATS"
      lancer "$N" "$ARGS" "$TMP/run"
      if [ ! -f "$OUT/resultats.csv" ]; then
        echo "taille,n,mode,run,wall_s,octets_snapshots,$(head -1 "$TMP/run/metrics.csv")" > "$OUT/resultats.csv"
      fi
      echo "$NOM,$N,$MODE,$r,$DUREE,$OCTETS,$(tail -1 "$TMP/run/metrics.csv")" >> "$OUT/resultats.csv"
    done
  done
done

rm -rf "$TMP"
echo "Termine : $OUT/resultats.csv"
