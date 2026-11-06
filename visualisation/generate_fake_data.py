"""Génère des données FICTIVES pour tester les scripts de visualisation.

Formats produits (copiés sur le code C++ des branches feature/snapshots et feature/sismos) :
  output_fake/snapshots/snapshot_XXXXXX.csv -> x,y,z,pressure   (un fichier par instant)
  output_fake/seismos.csv                   -> time,rcv0,rcv1,...
  output_fake/receivers.csv                 -> id,x,y,z
"""
import os

import numpy as np

out = "output_fake"
snap_dir = os.path.join(out, "snapshots")
os.makedirs(snap_dir, exist_ok=True)  # crée les dossiers de sortie s'ils n'existent pas

# ---------------------------------------------------------------
# 1) Le maillage : une grille 3D de 21 x 21 x 21 nœuds dans un cube de 1000 m
# ---------------------------------------------------------------
n = 21
L = 1000.0
g = np.linspace(0, L, n)
X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
x, y, z = X.ravel(), Y.ravel(), Z.ravel()      # 1 valeur par nœud

# ---------------------------------------------------------------
# 2) Une onde fictive (ondelette de Ricker) qui part du centre
# ---------------------------------------------------------------
c, f0 = 1500.0, 10.0          # vitesse de l'onde (m/s), fréquence (Hz)
src = np.array([L / 2, L / 2, L / 2])


def ricker(t):
    a = (np.pi * f0 * (t - 1.0 / f0)) ** 2
    return (1 - 2 * a) * np.exp(-a)


def pressure(px, py, pz, t):
    r = np.sqrt((px - src[0]) ** 2 + (py - src[1]) ** 2 + (pz - src[2]) ** 2)
    return ricker(t - r / c) / (r / 100 + 1)   # retard r/c, et affaiblissement


# ---------------------------------------------------------------
# 3) Snapshots : une "photo" de tout le volume tous les 50 pas de temps.
#    Comme dans le C++ : chaque fichier contient x,y,z ET la pression de chaque nœud.
# ---------------------------------------------------------------
dt, nsteps, interval = 0.002, 400, 50
for step in range(0, nsteps, interval):
    p = pressure(x, y, z, step * dt)
    with open(os.path.join(snap_dir, f"snapshot_{step:06d}.csv"), "w") as f:
        f.write("x,y,z,pressure\n")
        for i in range(len(x)):
            f.write(f"{x[i]:g},{y[i]:g},{z[i]:g},{p[i]:.6g}\n")

# ---------------------------------------------------------------
# 4) Sismos : même format que saveSeismos() du code C++
# ---------------------------------------------------------------
rcv = [(200, 500, 500), (500, 800, 500), (800, 800, 800)]

with open(os.path.join(out, "receivers.csv"), "w") as f:
    f.write("id,x,y,z\n")
    for r, (rx, ry, rz) in enumerate(rcv):
        f.write(f"{r},{rx},{ry},{rz}\n")

t = np.arange(nsteps) * dt
cols = [pressure(*r, t) for r in rcv]
with open(os.path.join(out, "seismos.csv"), "w") as f:
    f.write("time," + ",".join(f"rcv{i}" for i in range(len(rcv))) + "\n")
    for k in range(nsteps):
        f.write(f"{t[k]:.9g}," + ",".join(f"{c_[k]:.9g}" for c_ in cols) + "\n")

print("Données écrites dans", out)