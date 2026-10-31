#pragma once
// Statistiques "en flux" : on met a jour un petit nombre de variables a chaque
// valeur recue, sans jamais garder les valeurs en memoire.
// La variance utilise l'algorithme de Welford (stable numeriquement).

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

struct RunningStats
{
  std::size_t count = 0;   // nombre de valeurs vues
  double mean = 0.0;       // moyenne courante
  double m2 = 0.0;         // somme des (x - moyenne)^2 (pour la variance)
  double min = std::numeric_limits<double>::infinity();
  double max = -std::numeric_limits<double>::infinity();
  double max_abs = 0.0;    // plus grande valeur absolue
  double energy = 0.0;     // somme des x^2 (indicateur d'energie)

  // Ajoute une valeur
  void add(double x)
  {
    ++count;
    const double delta = x - mean;
    mean += delta / static_cast<double>(count);
    m2 += delta * (x - mean);
    min = std::min(min, x);
    max = std::max(max, x);
    max_abs = std::max(max_abs, std::abs(x));
    energy += x * x;
  }

  // Fusionne avec un autre RunningStats (formule de Chan et al.).
  // Sert a combiner des morceaux calcules en parallele (threads, GPU, processus MPI).
  void merge(const RunningStats& o)
  {
    if (o.count == 0) return;
    if (count == 0) { *this = o; return; }
    const double na = static_cast<double>(count);
    const double nb = static_cast<double>(o.count);
    const double n = na + nb;
    const double delta = o.mean - mean;
    m2 += o.m2 + delta * delta * na * nb / n;
    mean += delta * nb / n;
    count += o.count;
    min = std::min(min, o.min);
    max = std::max(max, o.max);
    max_abs = std::max(max_abs, o.max_abs);
    energy += o.energy;
  }

  // Variance (meme definition que numpy.var : on divise par N)
  double variance() const
  {
    return count > 0 ? m2 / static_cast<double>(count) : 0.0;
  }
};