#pragma once
// Analyses in-situ des sismogrammes, mises a jour a chaque pas de temps
// (memoire constante par recepteur). Reutilise RunningStats (Welford)
// de insitu_stats.h pour avoir exactement les memes formules que les snapshots.

#include <array>
#include <cmath>
#include <complex>
#include <vector>

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

// ---------------------------------------------------------------------------
// Analyses de fin de simulation : elles ont besoin de tout le signal
// (ou du maximum final), donc on les fait une fois apres la boucle, a partir
// du signal deja en memoire (pnAtReceiver). Memes reglages que sismos_adhoc.py.

constexpr double SEUIL_ARRIVEE = 0.1;  // premiere arrivee : |p| > 10 % du max
constexpr int NFFT = 8192;             // grille de frequences : k / (NFFT * dt)
constexpr double FMAX_DFT = 50.0;      // on ne calcule le spectre que jusqu'a 50 Hz
constexpr double FENETRE = 0.2;        // demi-largeur (s) autour du pic (onde directe)

struct SeismoFinal
{
  double t_first = 0.0;       // premier depassement de SEUIL_ARRIVEE * max
  double f_dom = 0.0;         // frequence dominante du signal entier
  double f_dom_direct = 0.0;  // frequence dominante de l'onde directe seule
};

// Frequence ou |DFT| est maximal. DFT directe sur la grille k / (NFFT * dt),
// la meme que np.fft.rfft(p, n=NFFT), mais limitee a FMAX_DFT : la source
// (Ricker a 5 Hz) n'a pratiquement plus d'energie au-dela.
inline double frequenceDominante(const std::vector<double>& p, double dt)
{
  const int kmax = static_cast<int>(FMAX_DFT * NFFT * dt);
  double best = -1.0, f_best = 0.0;
  for (int k = 0; k <= kmax; k++)
  {
    const double w = -2.0 * M_PI * k / NFFT;  // pulsation par echantillon
    std::complex<double> X(0.0, 0.0);
    for (std::size_t n = 0; n < p.size(); n++)
      X += p[n] * std::polar(1.0, w * static_cast<double>(n));
    if (std::abs(X) > best)
    {
      best = std::abs(X);
      f_best = k / (NFFT * dt);
    }
  }
  return f_best;
}

// p : signal du recepteur, t : instants, s : son accumulateur en flux
inline SeismoFinal analyseFinale(const std::vector<double>& p,
                                 const std::vector<double>& t, double dt,
                                 const SeismoStream& s)
{
  SeismoFinal res;

  // premiere arrivee : le seuil depend du max FINAL, d'ou le calcul apres coup
  for (std::size_t n = 0; n < p.size(); n++)
    if (std::fabs(p[n]) > SEUIL_ARRIVEE * s.peak)
    {
      res.t_first = t[n];
      break;
    }

  // spectre du signal entier
  res.f_dom = frequenceDominante(p, dt);

  // spectre de l'onde directe : on garde +/- FENETRE autour du pic, le reste a 0
  std::vector<double> direct(p.size(), 0.0);
  for (std::size_t n = 0; n < p.size(); n++)
    if (std::fabs(t[n] - s.t_peak) < FENETRE) direct[n] = p[n];
  res.f_dom_direct = frequenceDominante(direct, dt);

  return res;
}

// Regression lineaire t = t0 + d / v (moindres carres). Renvoie {v, t0}.
inline std::array<double, 2> regressionVitesse(const std::vector<double>& d,
                                               const std::vector<double>& t)
{
  const double n = static_cast<double>(d.size());
  double sd = 0, st = 0, sdd = 0, sdt = 0;
  for (std::size_t i = 0; i < d.size(); i++)
  {
    sd += d[i];
    st += t[i];
    sdd += d[i] * d[i];
    sdt += d[i] * t[i];
  }
  const double pente = (n * sdt - sd * st) / (n * sdd - sd * sd);
  const double t0 = (st - pente * sd) / n;
  return {1.0 / pente, t0};
}
