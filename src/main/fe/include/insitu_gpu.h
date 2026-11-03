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
// Histogramme par equipes : chaque equipe remplit un histogramme local en
// memoire partagee du GPU (scratch), puis l'ajoute a l'histogramme global.
// Pourquoi : avec HistogramFill, des millions de threads font atomic_add sur
// LA MEME case (presque tous les noeuds sont dans la classe centrale) ; sur le
// GPU ces atomiques se serialisent (mesure : 910 s a M contre 0,5 s sur l'hote).
// Ici il n'y a plus qu'une atomique globale par classe et par equipe.
template <class FieldView, class CountView>
struct HistogramTeam
{
  using member_type = Kokkos::TeamPolicy<>::member_type;
  using scratch_view =
      Kokkos::View<int*, Kokkos::DefaultExecutionSpace::scratch_memory_space,
                   Kokkos::MemoryTraits<Kokkos::Unmanaged>>;

  FieldView field;
  int column;
  double bound;
  int nbins;
  int nnodes;
  int chunk;          // noeuds traites par une equipe
  CountView counts;   // nbins + 2 cases, remises a 0 avant chaque analyse

  KOKKOS_INLINE_FUNCTION void operator()(const member_type& team) const
  {
    const int nk = nbins + 2;
    scratch_view local(team.team_scratch(0), nk);
    Kokkos::parallel_for(Kokkos::TeamThreadRange(team, nk),
                         [&](const int k) { local(k) = 0; });
    team.team_barrier();

    const int begin = team.league_rank() * chunk;
    const int end = (begin + chunk < nnodes) ? begin + chunk : nnodes;
    Kokkos::parallel_for(Kokkos::TeamThreadRange(team, begin, end), [&](const int n) {
      const double x = field(n, column);
      int k;
      if (x < -bound)
        k = 0;
      else if (x > bound)
        k = nbins + 1;
      else
      {
        int b = static_cast<int>((x + bound) / (2.0 * bound) * nbins);
        if (b >= nbins) b = nbins - 1;
        k = b + 1;
      }
      Kokkos::atomic_add(&local(k), 1);
    });
    team.team_barrier();

    Kokkos::parallel_for(Kokkos::TeamThreadRange(team, nk), [&](const int k) {
      if (local(k) != 0)
        Kokkos::atomic_add(&counts(k), static_cast<unsigned long long>(local(k)));
    });
  }
};
#endif
