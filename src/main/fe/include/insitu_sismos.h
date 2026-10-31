#pragma once
// Analyses in-situ des sismogrammes, mises a jour a chaque pas de temps
// (memoire constante par recepteur). Reutilise RunningStats (Welford)
// de insitu_stats.h pour avoir exactement les memes formules que les snapshots.

#include <cmath>

#include "insitu_stats.h"

struct SeismoStream
{
  RunningStats stats;   // min, max, moyenne, variance, somme des p^2
  double peak = 0.0;    // plus grande valeur de |p| vue jusqu'ici
  double t_peak = 0.0;  // instant ou ce maximum a ete vu

  // Ajoute la pression p mesuree au temps t
  void add(double p, double t)
  {
    stats.add(p);
    const double a = std::fabs(p);
    if (a > peak)  // ">" strict : on garde le premier maximum, comme np.argmax
    {
      peak = a;
      t_peak = t;
    }
  }
};
