#pragma once

#include <cxxopts.hpp>
#include <stdexcept>
#include <string>

class SemProxyOptions
{
 public:
  // Defaults
  int order = 2;
  int ex = 50, ey = 50, ez = 50;
  float lx = 2000.f, ly = 2000.f, lz = 2000.f;
  float srcx = 1010.f, srcy = 1010.f, srcz = 1010.f;
  float rcvx = 1410.f, rcvy = 1010.f, rcvz = 1010.f;
  std::string implem = "makutu"; 
  std::string method = "sem";    
  std::string mesh = "cartesian";
  float dt = 0.001;
  float timemax = 1.5;
  bool autodt = false;
  
  float boundaries_size = 0;
  bool surface_sponge = false;
  float taper_delta = 0.015;
  
  bool isModelOnNodes = false;
  bool isElastic = false;

  std::string receivers_file = "";
  std::string seismo_dir = "seismos";

  // snapshots
  bool snapshots = false;                 
  int snap_interval = 20;                 
  std::string snap_folder = "snapshots";     

  // slices
  bool slices = false;                    // faut-il sauvegarder des slices?
  std::string slice_axis = "z";                  // dans quelle diretion on coupe
  float slice_pos = 1000.f;               // à quelle hauteur on coupe (en mètres)
  std::string slice_folder = "slices";    // dossier où on range les fichiers
  
  std::string metrics_file = "";

  bool insitu_stats = false;                      
  int insitu_interval = 1;                        
  std::string insitu_file = "insitu_stats.csv";
  std::string insitu_mode = "device";
  bool insitu_hist = false;
  int insitu_hist_bins = 50;
  double insitu_hist_bound = 1.0;
  std::string insitu_hist_file = "insitu_hist.csv";
  bool insitu_vel = false;
  std::string insitu_vel_file = "insitu_vel.csv";
  bool insitu_sismos = false;                          // stats des sismos en flux ?
  std::string insitu_sismos_file = "insitu_sismos.csv"; // fichier de sortie
  

  void validate() const
  {
    if (order < 1) throw std::runtime_error("order must be >= 1");
    if (ex <= 0 || ey <= 0 || ez <= 0)
      throw std::runtime_error("ex/ey/ez must be > 0");
    if (lx <= 0 || ly <= 0 || lz <= 0)
      throw std::runtime_error("lx/ly/lz must be > 0");
    if (snap_interval <= 0)
      throw std::runtime_error("snap-interval must be > 0");
    if (insitu_interval <= 0)                                          
      throw std::runtime_error("insitu-interval must be > 0"); 
        if (insitu_mode != "device" && insitu_mode != "host")
      throw std::runtime_error("insitu-mode must be device or host");
    if (insitu_hist_bins <= 0)
      throw std::runtime_error("insitu-hist-bins must be > 0");
    if (insitu_hist_bound <= 0.0)
      throw std::runtime_error("insitu-hist-bound must be > 0");
    if (slice_axis != "x" && slice_axis != "y" && slice_axis != "z")
      throw std::runtime_error("slice-axis must be x, y or z");
  }

  static void bind_cli(cxxopts::Options& opts, SemProxyOptions& o)
  {
    opts.add_options()("o,order", "Order of approximation",
                       cxxopts::value<int>(o.order))(
        "ex", "Number of elements on X (Cartesian mesh)",
        cxxopts::value<int>(o.ex))("ey",
                                   "Number of elements on Y (Cartesian mesh)",
                                   cxxopts::value<int>(o.ey))(
        "ez", "Number of elements on Z (Cartesian mesh)",
        cxxopts::value<int>(o.ez))("lx", "Domain size X (Cartesian)",
                                   cxxopts::value<float>(o.lx))(
        "ly", "Domain size Y (Cartesian)", cxxopts::value<float>(o.ly))(
        "lz", "Domain size Z (Cartesian)", cxxopts::value<float>(o.lz))(
        "implem", "Implementation: makutu|shiva",
        cxxopts::value<std::string>(o.implem))(
        "method", "Method: sem|dg", cxxopts::value<std::string>(o.method))(
        "mesh", "Mesh: cartesian|ucartesian",
        cxxopts::value<std::string>(o.mesh))(
        "dt", "Time step selection in s (default = 0.001s)",
        cxxopts::value<float>(o.dt))(
        "timemax", "Duration of the simulation in s (default = 1.5s)",
        cxxopts::value<float>(o.timemax))(
        "auto-dt", "Select automatique dt via CFL equation.",
        cxxopts::value<bool>(o.autodt))(
        "boundaries-size", "Size of absorbing boundaries (meters)",
        cxxopts::value<float>(o.boundaries_size))(
        "sponge-surface", "Considere the surface's nodes as non sponge nodes",
        cxxopts::value<bool>(o.surface_sponge))(
        "taper-delta", "Taper delta for sponge boundaries value",
        cxxopts::value<float>(o.taper_delta))(
        "is-model-on-nodes",
        "Boolean to tell if the model is charged on nodes (true) or on element "
        "(false)",
        cxxopts::value<bool>(o.isModelOnNodes))(
        "is-elastic", "Elastic simulation", cxxopts::value<bool>(o.isElastic))(
        "receivers-file", "CSV file of receivers (x,y,z per line)",
        cxxopts::value<std::string>(o.receivers_file))(
        "seismo-dir", "Output directory for seismograms",
        cxxopts::value<std::string>(o.seismo_dir))(
        "snapshots", "Save snapshots of the wave field (CSV)",
        cxxopts::value<bool>(o.snapshots))(
        "snap-interval", "Number of time steps between two snapshots",
        cxxopts::value<int>(o.snap_interval))(
        "snap-folder", "Folder where snapshots are written",
        // cxxopts::value<std::string>(o.snap_folder));
        cxxopts::value<std::string>(o.snap_folder))(
        "slices", "Save a 2D slice of the wave field (CSV)",
        cxxopts::value<bool>(o.slices))(
        "slice-axis", "Axis perpendicular to the slice: x|y|z",
        cxxopts::value<std::string>(o.slice_axis))(
        "slice-pos", "Position of the slice plane (meters)",
        cxxopts::value<float>(o.slice_pos))(
        "slice-folder", "Folder where slices are written",
        cxxopts::value<std::string>(o.slice_folder))(
        "metrics-file", "CSV file where run metrics are appended",
        cxxopts::value<std::string>(o.metrics_file))(
        "insitu-stats", "Compute statistics in-situ (during the run)",
        cxxopts::value<bool>(o.insitu_stats))(
        "insitu-interval", "Number of time steps between two in-situ analyses",
        cxxopts::value<int>(o.insitu_interval))(
        "insitu-file", "CSV file where in-situ statistics are written",
        cxxopts::value<std::string>(o.insitu_file))(
        "insitu-mode", "Where to compute in-situ stats: device|host",
        cxxopts::value<std::string>(o.insitu_mode))(
        "insitu-hist", "Compute a streaming histogram in-situ",
        cxxopts::value<bool>(o.insitu_hist))(
        "insitu-hist-bins", "Number of histogram bins",
        cxxopts::value<int>(o.insitu_hist_bins))(
        "insitu-hist-bound", "Histogram covers [-bound, +bound]",
        cxxopts::value<double>(o.insitu_hist_bound))(
        "insitu-hist-file", "CSV file where the histogram is written",
        cxxopts::value<std::string>(o.insitu_hist_file))(
        "insitu-vel", "Track per-node peak |p| and its time in-situ",
        cxxopts::value<bool>(o.insitu_vel))(
        "insitu-vel-file", "CSV file where per-node peaks are written",
        cxxopts::value<std::string>(o.insitu_vel_file))(
        "insitu-sismos", "Compute seismogram statistics in-situ (streaming)",
        cxxopts::value<bool>(o.insitu_sismos))(
        "insitu-sismos-file", "CSV file where in-situ seismogram stats are written",
        cxxopts::value<std::string>(o.insitu_sismos_file));
      }
};
