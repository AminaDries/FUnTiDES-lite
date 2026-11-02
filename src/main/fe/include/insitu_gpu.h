#pragma once
// Analyses in-situ des snapshots executees la ou vit le champ (GPU avec Kokkos).
// Version "device" de l'histogramme et des pics par noeud : le champ n'est
// jamais lu par l'hote ; seuls les resultats reduits sont rapatries
// (les classes de l'histogramme a chaque analyse, les pics une fois a la fin).
// Des foncteurs (et non des lambdas) pour rester compatibles CUDA, comme
// RunningStatsReducer dans insitu_stats.h.

#ifdef USE_KOKKOS
#include <Kokkos_Core.hpp>

// Pic de |p| par noeud et pas ou il est atteint (mise a jour en flux)
template <class FieldView, class ValueView, class StepView>
struct PeakPerNode
{
  FieldView field;  // pnGlobal
  int column;       // i1 : colonne du champ courant
  ValueView peak;   // max |p| vu jusqu'ici, par noeud
  StepView step;    // pas de temps de ce max, par noeud
  int timestep;     // pas courant

  KOKKOS_INLINE_FUNCTION void operator()(const int n) const
  {
    double v = field(n, column);
    if (v < 0.0) v = -v;
    if (v > peak(n))
    {
      peak(n) = v;
      step(n) = timestep;
    }
  }
};

// Histogramme a bornes fixees [-bound, +bound], meme decoupage que
// StreamHistogram::add : classe 0 = sous la borne, nbins+1 = au-dessus.
template <class FieldView, class CountView>
struct HistogramFill
{
  FieldView field;
  int column;
  double bound;
  int nbins;
  CountView counts;  // nbins + 2 cases, remises a 0 avant chaque analyse

  KOKKOS_INLINE_FUNCTION void operator()(const int n) const
  {
    const double x = field(n, column);
    int k;
    if (x < -bound)
      k = 0;
    else if (x > bound)
      k = nbins + 1;
    else
    {
      int b = static_cast<int>((x + bound) / (2.0 * bound) * nbins);
      if (b >= nbins) b = nbins - 1;  // cas x == +bound
      k = b + 1;
    }
    Kokkos::atomic_add(&counts(k), 1ULL);
  }
};
#endif
