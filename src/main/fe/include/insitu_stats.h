#pragma once
#include <cstddef>

#ifdef USE_KOKKOS
#include <Kokkos_Core.hpp>
#define INSITU_FN KOKKOS_INLINE_FUNCTION
#else
#define INSITU_FN inline
#endif

struct RunningStats
{
  std::size_t count = 0;   
  double mean = 0.0;       
  double m2 = 0.0;         
  double min = 1.0e300;   
  double max = -1.0e300;   
  double max_abs = 0.0;    
  double energy = 0.0;     

  INSITU_FN void add(double x)
  {
    ++count;
    const double delta = x - mean;
    mean += delta / static_cast<double>(count);
    m2 += delta * (x - mean);
    if (x < min) min = x;
    if (x > max) max = x;
    const double ax = x < 0.0 ? -x : x;
    if (ax > max_abs) max_abs = ax;
    energy += x * x;
  }

  INSITU_FN void merge(const RunningStats& o)
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
    if (o.min < min) min = o.min;
    if (o.max > max) max = o.max;
    if (o.max_abs > max_abs) max_abs = o.max_abs;
    energy += o.energy;
  }

  INSITU_FN double variance() const
  {
    return count > 0 ? m2 / static_cast<double>(count) : 0.0;
  }
};

#ifdef USE_KOKKOS

template <class FieldView>
struct RunningStatsReducer
{
  using value_type = RunningStats;
  FieldView field;  
  int column;       

  KOKKOS_INLINE_FUNCTION void operator()(const int n, value_type& update) const
  {
    update.add(field(n, column));
  }
  KOKKOS_INLINE_FUNCTION void init(value_type& v) const { v = RunningStats(); }
  KOKKOS_INLINE_FUNCTION void join(value_type& dst, const value_type& src) const
  {
    dst.merge(src);
  }
};
#endif
