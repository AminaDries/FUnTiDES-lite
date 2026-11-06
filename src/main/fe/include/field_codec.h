#pragma once
#include <cstdint>
#include <cstring>

namespace field_codec
{

enum Codec : std::uint32_t
{
  RAW_F32 = 0,
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

}
