# Visualisation des résultats de la simulation

Scripts Python qui lisent les fichiers CSV écrits par le solveur (`sem_proxy`) et produisent
des images. Ils sont indépendants du code C++ : le solveur écrit des fichiers, ces scripts
les lisent.

## Installation

Python 3 et trois bibliothèques :

```
pip install numpy matplotlib pillow
```

(`pillow` sert uniquement à créer l'animation GIF.)

## Format des données lues

| Fichier | Contenu | Colonnes |
|---|---|---|
| `snapshots/snapshot_XXXXXX.csv` | pression de tous les nœuds à un pas de temps (`XXXXXX` = numéro du pas) | `x,y,z,pressure` |
| `seismos.csv` | pression à chaque récepteur, à chaque pas de temps | `time,rcv0,rcv1,...` |
| `receivers.csv` | position des récepteurs | `id,x,y,z` |

## Les scripts

### `plot_snapshot.py` : coupe 2D du champ de pression

```
python visualisation/plot_snapshot.py DOSSIER_SNAPSHOTS [options]
```

| Option | Effet |
|---|---|
| `--step N` | numéro du pas de temps à afficher (défaut : le snapshot du milieu) |
| `--axis x\|y\|z` | axe perpendiculaire à la coupe (défaut : `z`) |
| `--pos VALEUR` | position de la coupe sur cet axe (défaut : milieu du domaine) |
| `--receivers FICHIER` | affiche les récepteurs (`receivers.csv`) sur la carte |
| `--out FICHIER` | image de sortie (défaut : `DOSSIER/coupe_stepN.png`) |
| `--anim FICHIER.gif` | crée une animation avec tous les snapshots, au lieu d'une image |

L'échelle de couleurs est symétrique autour de 0 (rouge = surpression, bleu = dépression).
Dans l'animation, elle est commune à toutes les images.

### `plot_sismos.py` : sismogrammes

```
python visualisation/plot_sismos.py DOSSIER [SORTIE.png]
```

`DOSSIER` contient `seismos.csv` (et `receivers.csv`, facultatif, pour afficher la position
de chaque récepteur). Une courbe pression/temps est tracée par récepteur.

### `generate_fake_data.py` : données fictives

Crée un dossier `output_fake/` avec des fichiers au même format que le solveur
(onde sphérique partant du centre d'un cube de 1000 m, 3 récepteurs). Il permet de tester
les scripts sans lancer la simulation.

```
python visualisation/generate_fake_data.py
```

## Exemple complet

```
python visualisation/generate_fake_data.py
python visualisation/plot_snapshot.py output_fake/snapshots --step 100 --receivers output_fake/receivers.csv
python visualisation/plot_snapshot.py output_fake/snapshots --anim output_fake/onde.gif
python visualisation/plot_sismos.py output_fake
```

Sous Windows (PowerShell), remplacer `/` par `\` dans les chemins.

## Sur les vraies données

Donner le dossier écrit par le solveur à la place de `output_fake` :

```
python visualisation/plot_snapshot.py CHEMIN/snapshots --step 100
python visualisation/plot_sismos.py CHEMIN_DU_DOSSIER_DES_SISMOS
```

## Remarques

- Le dossier `output_fake/` est ignoré par Git (`.gitignore`).
- Le `.gitignore` du projet contient la règle `*snapshot*` : un nouveau fichier dont le nom
  contient « snapshot » doit être ajouté avec `git add -f`.
- Le script lit les coordonnées dans chaque snapshot. Si le format du solveur change
  (autres colonnes, autre séparateur), adapter `lire_snapshot()` dans `plot_snapshot.py`.
