// Test hors simulation : rejoue seismos.csv pas a pas dans SeismoStream
// et affiche les memes statistiques que analysis/sismos_adhoc.py.
// Usage : ./test_insitu_sismos DOSSIER
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "insitu_sismos.h"

int main(int argc, char** argv)
{
  if (argc < 2) { std::cerr << "Usage : " << argv[0] << " DOSSIER\n"; return 1; }
  std::ifstream in(std::string(argv[1]) + "/seismos.csv");
  if (!in) { std::cerr << "seismos.csv introuvable\n"; return 1; }

  std::string ligne;
  std::getline(in, ligne);  // en-tete : time,rcv0,rcv1,...
  std::vector<SeismoStream> rcv;
  double t_prec = 0.0, dt = 0.0;
  int nb_lignes = 0;

  while (std::getline(in, ligne))
  {
    std::stringstream ss(ligne);
    std::string champ;
    std::getline(ss, champ, ',');
    const double t = std::stod(champ);
    if (nb_lignes == 1) dt = t - t_prec;
    t_prec = t;
    int r = 0;
    while (std::getline(ss, champ, ','))
    {
      if ((int)rcv.size() <= r) rcv.emplace_back();
      rcv[r].add(std::stod(champ), t);  // une mise a jour par pas, comme dans la boucle
      r++;
    }
    nb_lignes++;
  }

  std::cout << "receiver,min,max,mean,var,energy,t_peak\n" << std::setprecision(9);
  for (std::size_t r = 0; r < rcv.size(); r++)
  {
    const RunningStats& s = rcv[r].stats;
    std::cout << r << ',' << s.min << ',' << s.max << ',' << s.mean << ','
              << s.variance() << ',' << s.energy * dt << ',' << rcv[r].t_peak << '\n';
  }
}
