#!/bin/bash
# TP3 partie 1 : mesures des images de slices, host (CPU) contre device (GPU).
# A lancer depuis la racine du depot, sur la machine GPU.
set -e
BIN=${BIN:-./build-cuda/bin/semproxy}   # binaire compile avec CUDA
OUT=${OUT:-results_images}               # dossier des resultats
REPS=6                                   # 1 chauffe + 5 mesures

# informations demandees par l'annexe (section 8)
mkdir -p "$OUT"
git rev-parse --short HEAD > "$OUT/commit.txt"
git status --porcelain --untracked-files=no > "$OUT/modifs_non_commitees.txt"
nvidia-smi > "$OUT/gpu.txt" 2>&1 || true
df -T "$OUT" > "$OUT/filesystem.txt"

for size in S:50 M:100 L:200; do
  name=${size%%:*}; n=${size##*:}
  for cfg in host:p6 device:p6 device:p3; do
    mode=${cfg%%:*}; fmt=${cfg##*:}
    for rep in $(seq 0 $((REPS-1))); do
      dir="$OUT/$name/${mode}_${fmt}/rep$rep"
      mkdir -p "$dir"
      echo ">>> $name  $mode  $fmt  run $rep"
      "$BIN" --ex $n --ey $n --ez $n --timemax 1.5 \
        --slice-image --snap-interval 50 --image-mode $mode --image-format $fmt \
        --image-norm local --image-folder "$dir/images" \
        --no-seismos --quiet --metrics-file "$dir/metrics.csv" > "$dir/log.txt" 2>&1
    done
  done
done
echo "Fini. Resultats dans $OUT"