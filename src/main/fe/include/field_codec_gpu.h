#pragma once
#ifdef USE_KOKKOS
#include <Kokkos_Core.hpp>
#include <cstdint>

#include "field_codec.h"

namespace field_codec
{

template <class FieldView, class OutView>
struct QuantizeKernel
{
  FieldView field;
  int column;
  OutView out;
  float vmin;
  float scale;
  std::uint32_t levels;

  KOKKOS_INLINE_FUNCTION void operator()(const int n) const
  {
    out(n) = static_cast<typename OutView::value_type>(
        quantize(field(n, column), vmin, scale, levels));
  }
};

template <class FieldView, class OutView>
struct HalfKernel
{
  FieldView field;
  int column;
  OutView out;

  KOKKOS_INLINE_FUNCTION void operator()(const int n) const
  {
    out(n) = float_to_half(field(n, column));
  }
};

}
#endif
