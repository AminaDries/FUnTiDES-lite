#pragma once
#include <cstdint>
#include <cstring>

#ifdef KOKKOS_INLINE_FUNCTION
#define FC_INLINE KOKKOS_INLINE_FUNCTION
#else
#define FC_INLINE inline
#endif

namespace field_codec
{

enum Codec : std::uint32_t
{
  RAW_F32 = 0,
  F16 = 1,
  QUANT = 2,
};

struct Header
{
  char magic[4];
  std::uint32_t version;
  std::uint32_t nb_values;
  std::uint32_t timestep;
  std::uint32_t codec;
  std::uint32_t nbits;
  float vmin;
  float vmax;
};
static_assert(sizeof(Header) == 32, "l'en-tete doit faire 32 octets");

inline Header make_header(std::uint32_t nb_values, std::uint32_t timestep,
                          Codec codec, std::uint32_t nbits, float vmin,
                          float vmax)
{
  Header h;
  std::memcpy(h.magic, "FTD1", 4);
  h.version = 1;
  h.nb_values = nb_values;
  h.timestep = timestep;
  h.codec = codec;
  h.nbits = nbits;
  h.vmin = vmin;
  h.vmax = vmax;
  return h;
}

FC_INLINE std::uint16_t float_to_half(float f)
{
  union
  {
    float f;
    std::uint32_t u;
  } in;
  in.f = f;
  const std::uint32_t x = in.u;
  const std::uint32_t sign = (x >> 16) & 0x8000u;
  const std::uint32_t e = (x >> 23) & 0xFFu;
  std::uint32_t m = x & 0x7FFFFFu;

  if (e == 0xFFu)
    return static_cast<std::uint16_t>(sign | 0x7C00u | (m ? 0x200u : 0u));

  const int he = static_cast<int>(e) - 127 + 15;
  if (he >= 0x1F) return static_cast<std::uint16_t>(sign | 0x7C00u);

  if (he <= 0)
  {
    if (he < -10) return static_cast<std::uint16_t>(sign);
    m |= 0x800000u;
    const int shift = 14 - he;
    std::uint32_t half = m >> shift;
    const std::uint32_t rem = m & ((1u << shift) - 1u);
    const std::uint32_t halfway = 1u << (shift - 1);
    if (rem > halfway || (rem == halfway && (half & 1u))) half++;
    return static_cast<std::uint16_t>(sign | half);
  }

  std::uint32_t half = (static_cast<std::uint32_t>(he) << 10) | (m >> 13);
  const std::uint32_t rem = m & 0x1FFFu;
  if (rem > 0x1000u || (rem == 0x1000u && (half & 1u))) half++;
  return static_cast<std::uint16_t>(sign | half);
}

FC_INLINE float half_to_float(std::uint16_t h)
{
  const std::uint32_t sign = static_cast<std::uint32_t>(h & 0x8000u) << 16;
  const std::uint32_t e = (h >> 10) & 0x1Fu;
  std::uint32_t m = h & 0x3FFu;
  union
  {
    std::uint32_t u;
    float f;
  } out;

  if (e == 0)
  {
    if (m == 0)
      out.u = sign;
    else
    {
      int shift = 0;
      while (!(m & 0x400u))
      {
        m <<= 1;
        shift++;
      }
      m &= 0x3FFu;
      out.u = sign | (static_cast<std::uint32_t>(127 - 15 - shift + 1) << 23) | (m << 13);
    }
  }
  else if (e == 0x1F)
    out.u = sign | 0x7F800000u | (m << 13);
  else
    out.u = sign | ((e + 127 - 15) << 23) | (m << 13);
  return out.f;
}

FC_INLINE std::uint32_t quant_levels(std::uint32_t nbits)
{
  return (1u << nbits) - 1u;
}

FC_INLINE float quant_scale(float vmin, float vmax, std::uint32_t nbits)
{
  const float range = vmax - vmin;
  return range > 0.f ? static_cast<float>(quant_levels(nbits)) / range : 0.f;
}

FC_INLINE std::uint32_t quantize(float p, float vmin, float scale,
                                 std::uint32_t levels)
{
  float q = (p - vmin) * scale + 0.5f;
  if (q < 0.f) q = 0.f;
  if (q > static_cast<float>(levels)) q = static_cast<float>(levels);
  return static_cast<std::uint32_t>(q);
}

FC_INLINE float dequantize(std::uint32_t q, float vmin, float vmax,
                           std::uint32_t levels)
{
  return levels ? vmin + static_cast<float>(q) *
                             ((vmax - vmin) / static_cast<float>(levels))
                : vmin;
}

}
