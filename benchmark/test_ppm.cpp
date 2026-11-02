// Test autonome de ppm_image.h (hors simulation).
// Compilation : g++ -std=c++17 -O2 -o test_ppm test_ppm.cpp
// Produit :
//   gradient_P3.ppm / gradient_P6.ppm : degrade de -1 a +1 (verifie la palette)
//   onde_P3.ppm     / onde_P6.ppm     : fausse onde circulaire signee (verifie l'image 2D)

#include <chrono>
#include <cmath>
#include <iostream>

#include "ppm_image.h"

int main()
{
  // 1. Degrade horizontal : la valeur va de -1 (gauche) a +1 (droite)
  const int gw = 512, gh = 64;
  std::vector<ppm::RGB> grad(static_cast<std::size_t>(gw) * gh);
  for (int y = 0; y < gh; y++)
    for (int x = 0; x < gw; x++)
      grad[static_cast<std::size_t>(y) * gw + x] =
          ppm::coolwarm(-1.f + 2.f * x / (gw - 1));
  ppm::write_ppm("gradient_P3.ppm", grad, gw, gh, false);
  ppm::write_ppm("gradient_P6.ppm", grad, gw, gh, true);

  // 2. Fausse onde : anneau signe qui s'attenue avec la distance au centre
  const int w = 401, h = 401;  // comme une slice 200x200 elements a l'ordre 2
  std::vector<float> field(static_cast<std::size_t>(w) * h);
  float maxAbs = 0.f;
  for (int y = 0; y < h; y++)
    for (int x = 0; x < w; x++)
    {
      const float dx = x - w / 2.f, dy = y - h / 2.f;
      const float r = std::sqrt(dx * dx + dy * dy);
      const float p = std::sin(r / 6.f) * std::exp(-r / 120.f);
      field[static_cast<std::size_t>(y) * w + x] = p;
      maxAbs = std::max(maxAbs, std::abs(p));
    }

  std::vector<ppm::RGB> img(field.size());
  for (std::size_t i = 0; i < field.size(); i++)
    img[i] = ppm::coolwarm(ppm::normalize_symmetric(field[i], maxAbs));

  // Comparaison P3 / P6 : taille et temps d'ecriture
  for (bool binary : {false, true})
  {
    const char* name = binary ? "onde_P6.ppm" : "onde_P3.ppm";
    const auto t0 = std::chrono::steady_clock::now();
    const std::size_t bytes = ppm::write_ppm(name, img, w, h, binary);
    const double dt = std::chrono::duration<double>(
                          std::chrono::steady_clock::now() - t0).count();
    std::cout << name << " : " << bytes << " octets, " << dt * 1e3 << " ms\n";
  }
  return 0;
}
