#include <cmath>
#include <cstdio>
#include <random>
#include <vector>

#include "field_codec.h"

using namespace field_codec;

static int echecs = 0;
#define VERIFIE(cond, msg)                      \
  do                                            \
  {                                             \
    if (!(cond))                                \
    {                                           \
      std::printf("ECHEC : %s\n", msg);         \
      echecs++;                                 \
    }                                           \
  } while (0)

int main()
{
  VERIFIE(float_to_half(0.f) == 0x0000, "0 -> 0x0000");
  VERIFIE(float_to_half(-0.f) == 0x8000, "-0 -> 0x8000");
  VERIFIE(float_to_half(1.f) == 0x3C00, "1 -> 0x3C00");
  VERIFIE(float_to_half(-2.f) == 0xC000, "-2 -> 0xC000");
  VERIFIE(float_to_half(65504.f) == 0x7BFF, "65504 (plus grand) -> 0x7BFF");
  VERIFIE(float_to_half(65520.f) == 0x7C00, "65520 -> infini");
  VERIFIE(float_to_half(1e10f) == 0x7C00, "1e10 -> infini");
  VERIFIE(float_to_half(6.103515625e-05f) == 0x0400, "plus petit normal");
  VERIFIE(float_to_half(5.9604645e-08f) == 0x0001, "plus petit sous-normal");
  VERIFIE(float_to_half(1e-9f) == 0x0000, "trop petit -> 0");
  VERIFIE(half_to_float(0x3C00) == 1.f, "0x3C00 -> 1");
  VERIFIE(half_to_float(0xC000) == -2.f, "0xC000 -> -2");
  VERIFIE(half_to_float(0x0001) == 5.9604645e-08f, "0x0001 -> plus petit sous-normal");

  int mauvais = 0;
  for (std::uint32_t h = 0; h < 0x10000u; h++)
  {
    const std::uint32_t e = (h >> 10) & 0x1Fu, m = h & 0x3FFu;
    if (e == 0x1Fu && m != 0) continue;
    if (float_to_half(half_to_float(static_cast<std::uint16_t>(h))) != h) mauvais++;
  }
  VERIFIE(mauvais == 0, "aller-retour half -> float -> half");

  std::mt19937 gen(1);
  std::uniform_real_distribution<float> ud(-2.2f, 2.2f);
  double pire_rel = 0;
  for (int i = 0; i < 1000000; i++)
  {
    const float p = ud(gen);
    if (std::fabs(p) < 6.2e-5f) continue;
    const float r = half_to_float(float_to_half(p));
    const double rel = std::fabs(double(r) - p) / std::fabs(p);
    if (rel > pire_rel) pire_rel = rel;
  }
  VERIFIE(pire_rel <= 4.89e-4, "erreur relative float16 <= 2^-11");
  std::printf("float16 : erreur relative maximale mesuree %.3e (theorie 4.88e-04)\n", pire_rel);

  for (std::uint32_t nbits : {8u, 16u})
  {
    const float vmin = -2.0f, vmax = 2.2f;
    const std::uint32_t L = quant_levels(nbits);
    const float s = quant_scale(vmin, vmax, nbits);
    const double demi_marche = double(vmax - vmin) / L / 2.0;
    double pire = 0;
    std::uniform_real_distribution<float> u(vmin, vmax);
    for (int i = 0; i < 1000000; i++)
    {
      const float p = u(gen);
      const std::uint32_t q = quantize(p, vmin, s, L);
      if (q > L) VERIFIE(false, "q hors de [0, 2^N - 1]");
      const double e = std::fabs(double(dequantize(q, vmin, vmax, L)) - p);
      if (e > pire) pire = e;
    }
    const double ulp = 1.2e-7 * 2.2;
    VERIFIE(pire <= demi_marche + 4 * ulp, "erreur <= une demi-marche + arrondi float32");
    std::printf("%2u bits : erreur max mesuree %.3e, demi-marche %.3e\n", nbits, pire, demi_marche);

    VERIFIE(quantize(vmin, vmin, s, L) == 0, "vmin -> 0");
    VERIFIE(quantize(vmax, vmin, s, L) == L, "vmax -> 2^N - 1");
    VERIFIE(quantize(vmin - 5.f, vmin, s, L) == 0, "sous vmin : borne a 0");
    VERIFIE(quantize(vmax + 5.f, vmin, s, L) == L, "au-dessus de vmax : borne a 2^N - 1");
  }

  {
    const std::uint32_t L = quant_levels(8);
    const float s = quant_scale(0.f, 0.f, 8);
    VERIFIE(s == 0.f, "champ constant : echelle nulle");
    VERIFIE(quantize(0.f, 0.f, s, L) == 0, "champ constant : q = 0");
    VERIFIE(dequantize(0, 0.f, 0.f, L) == 0.f, "champ constant : reconstruit = vmin");
  }

  for (std::size_t w : {1u, 2u, 4u})
  {
    std::vector<std::uint8_t> data;
    std::uniform_int_distribution<int> val(0, 255), len(1, 5000);
    while (data.size() < 100000 * w)
    {
      const int run = len(gen);
      std::uint8_t v[4] = {static_cast<std::uint8_t>(val(gen)), static_cast<std::uint8_t>(val(gen)),
                           static_cast<std::uint8_t>(val(gen)), static_cast<std::uint8_t>(val(gen))};
      for (int r = 0; r < run && data.size() < 100000 * w; r++)
        data.insert(data.end(), v, v + w);
    }
    const std::size_t n = data.size() / w;
    std::vector<std::uint8_t> enc, dec(data.size());
    rle_encode(data.data(), n, w, enc);
    const std::size_t k = rle_decode(enc.data(), enc.size(), w, dec.data(), n);
    VERIFIE(k == n && dec == data, "RLE : aller-retour exact");
    std::printf("RLE largeur %zu : %zu octets -> %zu octets\n", w, data.size(), enc.size());
  }
  {
    std::vector<std::uint8_t> zeros(100000, 0), enc, dec(100000);
    rle_encode(zeros.data(), zeros.size(), 1, enc);
    VERIFIE(enc.size() == 4, "RLE : 100000 zeros -> 4 octets");
    VERIFIE(rle_decode(enc.data(), enc.size(), 1, dec.data(), dec.size()) == dec.size() && dec == zeros,
            "RLE : zeros restitues");
    std::vector<std::uint8_t> alt(1000), enc2;
    for (std::size_t i = 0; i < alt.size(); i++) alt[i] = static_cast<std::uint8_t>(i % 2);
    rle_encode(alt.data(), alt.size(), 1, enc2);
    VERIFIE(enc2.size() == 2 * alt.size(), "RLE : sans repetition, taille doublee");
    std::vector<std::uint8_t> un(1, 7), enc3, dec3(1);
    rle_encode(un.data(), 1, 1, enc3);
    VERIFIE(rle_decode(enc3.data(), enc3.size(), 1, dec3.data(), 1) == 1 && dec3 == un, "RLE : une valeur");
    VERIFIE(rle_decode(enc.data(), enc.size() - 1, 1, dec.data(), dec.size()) < dec.size(),
            "RLE : flux tronque detecte");
  }

  std::printf(echecs ? "\n%d ECHEC(S)\n" : "\nTous les tests passent.\n", echecs);
  return echecs ? 1 : 0;
}
