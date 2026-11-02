#ifndef PPM_IMAGE_H_
#define PPM_IMAGE_H_

// Visualisation in-situ (TP3, partie 1) : outils pour produire des images PPM.
//
//  - normalize_symmetric : pression -> valeur dans [-1, 1] (bornes symetriques)
//  - coolwarm            : valeur dans [-1, 1] -> couleur (R, G, B)
//  - write_ppm           : ecrit une image RGB en PPM, mode P3 (texte) ou P6 (binaire)
//
// Aucune bibliotheque externe : seulement la bibliotheque standard C++.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace ppm
{

// Pixel RGB, une composante = un octet (0..255).
struct RGB
{
  std::uint8_t r, g, b;
};

// ---------------------------------------------------------------------------
// Normalisation
// ---------------------------------------------------------------------------
// Le champ de pression est signe. On utilise des bornes symetriques [-bound, bound] :
// 0 tombe toujours au milieu de la palette (blanc en coolwarm).
// Les valeurs hors bornes sont ecretees a -1 ou 1.
inline float normalize_symmetric(float p, float bound)
{
  if (bound <= 0.f) return 0.f;
  const float v = p / bound;
  return std::max(-1.f, std::min(1.f, v));
}

// ---------------------------------------------------------------------------
// Palette "coolwarm" (palette divergente de K. Moreland, 2009)
// ---------------------------------------------------------------------------
// v = -1 -> bleu, v = 0 -> gris tres clair, v = +1 -> rouge.
// Interpolation lineaire entre 9 couleurs de reference de la palette coolwarm.
// La luminosite est maximale en 0 et baisse de facon reguliere vers les deux
// extremites : pas de fausses bandes de contraste (contrairement a "jet").
inline RGB coolwarm(float v)
{
  static const float table[9][3] = {
      {59, 76, 192},    // -1.00
      {98, 130, 234},   // -0.75
      {141, 176, 254},  // -0.50
      {184, 208, 249},  // -0.25
      {221, 221, 221},  //  0.00
      {245, 196, 173},  // +0.25
      {244, 154, 123},  // +0.50
      {222, 96, 77},    // +0.75
      {180, 4, 38},     // +1.00
  };

  if (!(v == v)) v = 0.f;  // NaN -> milieu de la palette
  v = std::max(-1.f, std::min(1.f, v));

  const float pos = (v + 1.f) * 4.f;  // [-1, 1] -> [0, 8]
  int i = static_cast<int>(pos);
  if (i >= 8) i = 7;
  const float t = pos - static_cast<float>(i);

  RGB c;
  c.r = static_cast<std::uint8_t>(std::lround(table[i][0] + t * (table[i + 1][0] - table[i][0])));
  c.g = static_cast<std::uint8_t>(std::lround(table[i][1] + t * (table[i + 1][1] - table[i][1])));
  c.b = static_cast<std::uint8_t>(std::lround(table[i][2] + t * (table[i + 1][2] - table[i][2])));
  return c;
}

// ---------------------------------------------------------------------------
// Ecriture PPM
// ---------------------------------------------------------------------------
// pixels : width * height pixels, ligne par ligne, du haut vers le bas.
// binary = false -> P3 (valeurs RGB en texte)
// binary = true  -> P6 (octets bruts : 3 octets par pixel)
// Renvoie le nombre d'octets ecrits.
inline std::size_t write_ppm(const std::string& filename,
                             const std::vector<RGB>& pixels, int width,
                             int height, bool binary)
{
  if (width <= 0 || height <= 0 ||
      pixels.size() != static_cast<std::size_t>(width) * height)
    throw std::runtime_error("write_ppm : taille d'image incoherente");

  std::ofstream file(filename, std::ios::binary);
  if (!file) throw std::runtime_error("write_ppm : impossible d'ouvrir " + filename);

  // En-tete commun : format, largeur hauteur, valeur max
  file << (binary ? "P6" : "P3") << '\n' << width << ' ' << height << "\n255\n";

  if (binary)
  {
    // P6 : les pixels sont deja ranges R, G, B, R, G, B... en memoire
    file.write(reinterpret_cast<const char*>(pixels.data()),
               static_cast<std::streamsize>(pixels.size() * sizeof(RGB)));
  }
  else
  {
    // P3 : une ligne de texte par ligne de pixels
    std::string line;
    line.reserve(static_cast<std::size_t>(width) * 12);
    for (int y = 0; y < height; y++)
    {
      line.clear();
      for (int x = 0; x < width; x++)
      {
        const RGB& c = pixels[static_cast<std::size_t>(y) * width + x];
        line += std::to_string(c.r);
        line += ' ';
        line += std::to_string(c.g);
        line += ' ';
        line += std::to_string(c.b);
        line += (x + 1 < width) ? ' ' : '\n';
      }
      file << line;
    }
  }

  const std::size_t bytes = static_cast<std::size_t>(file.tellp());
  file.close();
  if (!file) throw std::runtime_error("write_ppm : erreur d'ecriture " + filename);
  return bytes;
}

}  // namespace ppm

#endif  // PPM_IMAGE_H_
