//************************************************************************
//   proxy application v.0.0.1
//
//  semproxy.cpp: the main interface of  proxy application
//
//************************************************************************

#include "sem_proxy.h"

#include <cartesian_struct_builder.h>
#include <cartesian_unstruct_builder.h>
#include <sem_solver_acoustic.h>
#include <source_and_receiver_utils.h>

#include <algorithm>
#include <cxxopts.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <variant>

#include <filesystem>
#include <fstream>

#include <sys/resource.h>

using namespace SourceAndReceiverUtils;

SEMproxy::SEMproxy(const SemProxyOptions& opt)
{
  const int order = opt.order;
  nb_elements_[0] = opt.ex;
  nb_elements_[1] = opt.ey;
  nb_elements_[2] = opt.ez;
  nb_nodes_[0] = opt.ex * order + 1;
  nb_nodes_[1] = opt.ey * order + 1;
  nb_nodes_[2] = opt.ez * order + 1;

  const float spongex = opt.boundaries_size;
  const float spongey = opt.boundaries_size;
  const float spongez = opt.boundaries_size;
  const std::array<float, 3> sponge_size = {spongex, spongey, spongez};
  src_coord_[0] = opt.srcx;
  src_coord_[1] = opt.srcy;
  src_coord_[2] = opt.srcz;

  domain_size_[0] = opt.lx;
  domain_size_[1] = opt.ly;
  domain_size_[2] = opt.lz;

  seismo_dir_ = opt.seismo_dir;
  readReceivers(opt.receivers_file, opt);

  bool isModelOnNodes = opt.isModelOnNodes;
  opt_ = opt;

  // snapshots
  is_snapshots_ = opt.snapshots;
  snap_time_interval_ = opt.snap_interval;
  snap_folder_ = opt.snap_folder;
  if (is_snapshots_) std::filesystem::create_directories(snap_folder_);

  isElastic_ = opt.isElastic;
  cout << boolalpha;
  bool isElastic = isElastic_;

  const SolverFactory::methodType methodType = getMethod(opt.method);
  const SolverFactory::implemType implemType = getImplem(opt.implem);
  const SolverFactory::meshType meshType = getMesh(opt.mesh);
  const SolverFactory::modelLocationType modelLocation =
      isModelOnNodes ? SolverFactory::modelLocationType::OnNodes
                     : SolverFactory::modelLocationType::OnElements;
  const SolverFactory::physicType physicType =
      SolverFactory::physicType::Acoustic;

  float lx = domain_size_[0];
  float ly = domain_size_[1];
  float lz = domain_size_[2];
  int ex = nb_elements_[0];
  int ey = nb_elements_[1];
  int ez = nb_elements_[2];

  if (meshType == SolverFactory::Struct)
  {
    switch (order)
    {
      case 1: {
        model::CartesianStructBuilder<float, int, 1> builder(
            ex, lx, ey, ly, ez, lz, isModelOnNodes);
        m_mesh = builder.getModel();
        break;
      }
      case 2: {
        model::CartesianStructBuilder<float, int, 2> builder(
            ex, lx, ey, ly, ez, lz, isModelOnNodes);
        m_mesh = builder.getModel();
        break;
      }
      case 3: {
        model::CartesianStructBuilder<float, int, 3> builder(
            ex, lx, ey, ly, ez, lz, isModelOnNodes);
        m_mesh = builder.getModel();
        break;
      }
      default:
        throw std::runtime_error(
            "Order other than 1 2 3 is not supported (semproxy)");
    }
  }
  else if (meshType == SolverFactory::Unstruct)
  {
    model::CartesianParams<float, int> param(order, ex, ey, ez, lx, ly, lz,
                                             isModelOnNodes);
    model::CartesianUnstructBuilder<float, int> builder(param);
    m_mesh = builder.getModel();
  }
  else
  {
    throw std::runtime_error("Incorrect mesh type (SEMproxy ctor.)");
  }

  // time parameters
  if (opt.autodt)
  {
    float cfl_factor = (order == 2) ? 0.5 : 0.7;
    dt_ = find_cfl_dt(cfl_factor);
  }
  else
  {
    dt_ = opt.dt;
  }
  timemax_ = opt.timemax;
  num_sample_ = timemax_ / dt_;

  m_solver = SolverFactory::createSolver(methodType, implemType, meshType,
                                         modelLocation, physicType, order);
  m_solver->computeFEInit(*m_mesh, sponge_size, opt.surface_sponge,
                          opt.taper_delta);

  initFiniteElem();

  std::cout << "Number of node is " << m_mesh->getNumberOfNodes() << std::endl;
  std::cout << "Number of element is " << m_mesh->getNumberOfElements()
            << std::endl;
  std::cout << "Launching the Method " << opt.method << ", the implementation "
            << opt.implem << " and the mesh is " << opt.mesh << std::endl;
  std::cout << "Model is on " << (isModelOnNodes ? "nodes" : "elements")
            << std::endl;
  std::cout << "Physics type is " << (isElastic ? "elastic" : "acoustic")
            << std::endl;
  std::cout << "Order of approximation will be " << order << std::endl;
  std::cout << "Time step is " << dt_ << "s" << std::endl;
  std::cout << "Simulated time is " << timemax_ << "s" << std::endl;
}

void SEMproxy::run()
{
  time_point<system_clock> startComputeTime, startOutputTime, totalComputeTime,
      totalOutputTime;
  double snapshotWriteTime = 0.0;  
  int snapshotCount = 0;           
  std::size_t snapshotBytes = 0;  

    std::vector<InsituRecord> insituRecords; 
  double insituTime = 0.0;
  std::vector<int> histSteps;
  std::vector<std::vector<std::size_t>> histRows;
  const std::size_t velNodes =
      opt_.insitu_vel ? static_cast<std::size_t>(m_mesh->getNumberOfNodes()) : 0;
  std::vector<double> velMax(velNodes, 0.0); 
  std::vector<int> velStep(velNodes, 0);                   

  SEMsolverDataAcoustic solverData(i1, i2, myRHSTerm, pnGlobal, rhsElement,
                                   rhsWeights);

  for (int indexTimeSample = 0; indexTimeSample < num_sample_;
       indexTimeSample++)
  {
    startComputeTime = system_clock::now();
    m_solver->computeOneStep(dt_, indexTimeSample, solverData);
    totalComputeTime += system_clock::now() - startComputeTime;

    startOutputTime = system_clock::now();

    if (indexTimeSample % 50 == 0)
    {
      m_solver->outputSolutionValues(indexTimeSample, i1, rhsElement[0],
                                     pnGlobal, "pnGlobal");
    }

    // Save pressure at receivers
    const int order = m_mesh->getOrder();
    const int npe = order + 1;

    for (int r = 0; r < nb_receivers_; r++)
    {
      float val = 0.f;
      for (int i = 0; i < npe; i++)
        for (int j = 0; j < npe; j++)
          for (int k = 0; k < npe; k++)
          {
            int nodeIdx = m_mesh->globalNodeIndex(rhsElementRcv[r], i, j, k);
            int local = i + j * npe + k * npe * npe;
            val += solverData.m_pnGlobal(nodeIdx, i1) * rhsWeightsRcv(r, local);
          }
      pnAtReceiver(r, indexTimeSample) = val;
    }

  if (is_snapshots_ && indexTimeSample % snap_time_interval_ == 0)
  {
      auto startSnap = std::chrono::steady_clock::now();

      snapshotBytes += saveSnapshot(
          indexTimeSample, solverData.m_pnGlobal);

      snapshotWriteTime += std::chrono::duration<double>(
          std::chrono::steady_clock::now() - startSnap
      ).count();

      snapshotCount++;
  }
  
    if (opt_.insitu_vel && indexTimeSample % opt_.insitu_interval == 0)
    {
#ifdef USE_KOKKOS
      Kokkos::fence();
#endif
      for (std::size_t n = 0; n < velNodes; ++n)
      {
        double v = solverData.m_pnGlobal(static_cast<int>(n), i1);
        if (v < 0.0) v = -v;
        if (v > velMax[n])
        {
          velMax[n] = v;
          velStep[n] = indexTimeSample;
        }
      }
    }

    if (opt_.insitu_hist && indexTimeSample % opt_.insitu_interval == 0)
    {
#ifdef USE_KOKKOS
      Kokkos::fence();
#endif
      StreamHistogram h;
      h.init(opt_.insitu_hist_bound, opt_.insitu_hist_bins);
      for (int n = 0; n < m_mesh->getNumberOfNodes(); ++n)
      {
        h.add(solverData.m_pnGlobal(n, i1));
      }
      histSteps.push_back(indexTimeSample);
      histRows.push_back(h.counts);
    }

    if (opt_.insitu_stats && indexTimeSample % opt_.insitu_interval == 0)
    {
      const auto startInsitu = std::chrono::steady_clock::now();
            const RunningStats s =
          (opt_.insitu_mode == "host") ? computeStatsHost(solverData.m_pnGlobal)
                                       : computeStatsDevice(solverData.m_pnGlobal);
      const double sec = std::chrono::duration<double>(
                             std::chrono::steady_clock::now() - startInsitu)
                             .count();
      insituTime += sec;
      insituRecords.push_back(
          {indexTimeSample, static_cast<double>(indexTimeSample) * dt_, s, sec});
    }
    swap(i1, i2);

    auto tmp = solverData.m_i1;
    solverData.m_i1 = solverData.m_i2;
    solverData.m_i2 = tmp;

    totalOutputTime += system_clock::now() - startOutputTime;
  }
  
  if (opt_.insitu_vel)
  {
    std::ofstream vf(opt_.insitu_vel_file);
    if (!vf) throw std::runtime_error("Cannot open " + opt_.insitu_vel_file);
    vf << "x,y,z,max_abs,step_pic,t_pic\n";
    for (std::size_t n = 0; n < velNodes; ++n)
    {
      const int ni = static_cast<int>(n);
      vf << m_mesh->nodeCoord(ni, 0) << "," << m_mesh->nodeCoord(ni, 1) << ","
         << m_mesh->nodeCoord(ni, 2) << "," << velMax[n] << "," << velStep[n]
         << "," << static_cast<double>(velStep[n]) * dt_ << "\n";
    }
    std::cout << "---- In-situ peaks written to " << opt_.insitu_vel_file << " ("
              << velNodes << " nodes)." << std::endl;
  }

  if (opt_.insitu_hist)
  {
    std::ofstream hf(opt_.insitu_hist_file);
    if (!hf) throw std::runtime_error("Cannot open " + opt_.insitu_hist_file);
    hf << "step,t,borne,nb_bins,sous,sur";
    for (int k = 0; k < opt_.insitu_hist_bins; ++k) hf << ",count_" << k;
    hf << "\n";
    for (std::size_t r = 0; r < histRows.size(); ++r)
    {
      const auto& c = histRows[r];
      hf << histSteps[r] << "," << static_cast<double>(histSteps[r]) * dt_
         << "," << opt_.insitu_hist_bound << "," << opt_.insitu_hist_bins
         << "," << c[0] << "," << c[opt_.insitu_hist_bins + 1];
      for (int k = 1; k <= opt_.insitu_hist_bins; ++k) hf << "," << c[k];
      hf << "\n";
    }
    std::cout << "---- In-situ histogram written to " << opt_.insitu_hist_file
              << " (" << histRows.size() << " histograms)." << std::endl;
  }

  if (opt_.insitu_stats)
  {
    writeInsituStats(insituRecords);
    std::cout << "---- In-situ analysis time : " << insituTime << " seconds ("
              << insituRecords.size() << " analyses, mode " << opt_.insitu_mode
              << ")." << std::endl;
    const std::size_t bytesPerAnalysis =
        (opt_.insitu_mode == "host")
            ? static_cast<std::size_t>(m_mesh->getNumberOfNodes()) * sizeof(float)
            : sizeof(RunningStats);
    std::cout << "---- Data moved to host    : " << bytesPerAnalysis
              << " bytes per analysis." << std::endl;
    }

  const auto startSeismo = std::chrono::steady_clock::now();
  saveSeismos();
  const double seismoWriteTime =
      std::chrono::duration<double>(std::chrono::steady_clock::now() -
                                    startSeismo)
          .count();
  const std::size_t seismoBytes =
      std::filesystem::file_size(seismo_dir_ + "/seismos.csv");
  std::cout << "---- Seismo write time   : " << seismoWriteTime
            << " seconds." << std::endl;

  float kerneltime_ms = time_point_cast<microseconds>(totalComputeTime)
                            .time_since_epoch()
                            .count();
  float outputtime_ms =
      time_point_cast<microseconds>(totalOutputTime).time_since_epoch().count();

  cout << "------------------------------------------------ " << endl;
  cout << "\n---- Elapsed Kernel Time : " << kerneltime_ms / 1E6 << " seconds."
       << endl;
  cout << "---- Elapsed Output Time : " << outputtime_ms / 1E6 << " seconds."
       << endl;
  cout << "------------------------------------------------ " << endl;
  writeMetrics(
      std::chrono::duration<double>(totalComputeTime.time_since_epoch())
          .count(),
      snapshotWriteTime, snapshotCount, snapshotBytes, seismoWriteTime,
      seismoBytes);
}

// Écrit un snapshot : un fichier CSV avec la pression de tous les noeuds
std::size_t SEMproxy::saveSnapshot(int timestep, const arrayReal& field)
{
  std::ostringstream name;
  name << snap_folder_ << "/snapshot_" << std::setw(6) << std::setfill('0')
       << timestep << ".csv";

  std::ofstream file(name.str());
  if (!file) throw std::runtime_error("Cannot open " + name.str());

  file << "x,y,z,pressure\n";
  const int nbNodes = m_mesh->getNumberOfNodes();
  for (int n = 0; n < nbNodes; n++)
  {
    file << m_mesh->nodeCoord(n, 0) << ',' << m_mesh->nodeCoord(n, 1) << ','
         << m_mesh->nodeCoord(n, 2) << ',' << field(n, i1) << '\n';
  }
  return static_cast<std::size_t>(file.tellp());  // octets écrits
}

// Statistiques en flux du champ de pression, calculees sur l'hote (CPU).
RunningStats SEMproxy::computeStatsHost(const arrayReal& field) const
{
#ifdef USE_KOKKOS
  Kokkos::fence();  // attendre la fin des calculs avant de lire sur l'hote
#endif
  RunningStats stats;
  const int nbNodes = m_mesh->getNumberOfNodes();
  for (int n = 0; n < nbNodes; n++)
  {
    stats.add(field(n, i1));
  }

  return stats;
}

RunningStats SEMproxy::computeStatsDevice(const arrayReal& field) const
{
#ifdef USE_KOKKOS
  RunningStats result;
  Kokkos::parallel_reduce("insitu_stats", m_mesh->getNumberOfNodes(),
                          RunningStatsReducer<arrayReal>{field, i1}, result);
  return result;
#else
  return computeStatsHost(field); 
#endif
}

void SEMproxy::writeInsituStats(const std::vector<InsituRecord>& records) const
{
  std::ofstream file(opt_.insitu_file);
  if (!file) throw std::runtime_error("Cannot open " + opt_.insitu_file);
  file << std::setprecision(10);
  file << "step,t,min,max,mean,var,max_abs,energie,insitu_s\n";
  for (const auto& r : records)
  {
    file << r.step << ',' << r.time << ',' << r.stats.min << ','
         << r.stats.max << ',' << r.stats.mean << ',' << r.stats.variance()
         << ',' << r.stats.max_abs << ',' << r.stats.energy << ',' << r.seconds
         << '\n';
  }
}

void SEMproxy::writeMetrics(double computeTime, double snapshotWriteTime,
                            int snapshotCount, std::size_t snapshotBytes,
                            double seismoWriteTime,
                            std::size_t seismoBytes) const
{
  if (opt_.metrics_file.empty()) return;

  struct rusage usage;
  getrusage(RUSAGE_SELF, &usage);

  int threads = 1;
#ifdef USE_KOKKOS
  threads = Kokkos::DefaultExecutionSpace().concurrency();
#endif

  const bool newFile = !std::filesystem::exists(opt_.metrics_file) ||
                       std::filesystem::file_size(opt_.metrics_file) == 0;
  std::ofstream file(opt_.metrics_file, std::ios::app);
  if (!file) throw std::runtime_error("Cannot open " + opt_.metrics_file);

  if (newFile)
  {
    file << "ex,ey,ez,order,nb_nodes,nb_elements,dt,timemax,nb_steps,threads,"
            "snapshots,snap_interval,compute_time_s,snapshot_write_time_s,"
            "snapshot_count,snapshot_bytes,max_rss_kb,nb_receivers,"
            "seismo_write_time_s,seismo_bytes\n";
  }
  file << std::setprecision(9) << opt_.ex << ',' << opt_.ey << ',' << opt_.ez
       << ',' << opt_.order << ',' << m_mesh->getNumberOfNodes() << ','
       << m_mesh->getNumberOfElements() << ',' << dt_ << ',' << timemax_ << ','
       << num_sample_ << ',' << threads << ',' << (is_snapshots_ ? 1 : 0)
       << ',' << snap_time_interval_ << ',' << computeTime << ','
       << snapshotWriteTime << ',' << snapshotCount << ',' << snapshotBytes
       << ',' << usage.ru_maxrss << ',' << nb_receivers_ << ','
       << seismoWriteTime << ',' << seismoBytes << '\n';
}

// Initialize arrays
void SEMproxy::init_arrays()
{
  cout << "Allocate host memory for source and pressure values ..." << endl;

  rhsElement = allocateVector<vectorInt>(myNumberOfRHS, "rhsElement");
  rhsWeights = allocateArray2D<arrayReal>(
      myNumberOfRHS, m_mesh->getNumberOfPointsPerElement(), "RHSWeight");
  myRHSTerm = allocateArray2D<arrayReal>(myNumberOfRHS, num_sample_, "RHSTerm");
  pnGlobal =
      allocateArray2D<arrayReal>(m_mesh->getNumberOfNodes(), 2, "pnGlobal");
  pnAtReceiver =
      allocateArray2D<arrayReal>(nb_receivers_, num_sample_, "pnAtReceiver");
  // Receiver
  rhsElementRcv = allocateVector<vectorInt>(nb_receivers_, "rhsElementRcv");
  rhsWeightsRcv = allocateArray2D<arrayReal>(
      nb_receivers_, m_mesh->getNumberOfPointsPerElement(), "RHSWeightRcv");
}

// Initialize sources
void SEMproxy::init_source()
{
  arrayReal myRHSLocation = allocateArray2D<arrayReal>(1, 3, "RHSLocation");
  // std::cout << "All source are currently are coded on element 50." <<
  // std::endl;
  std::cout << "All source are currently are coded on middle element."
            << std::endl;
  int ex = nb_elements_[0];
  int ey = nb_elements_[1];
  int ez = nb_elements_[2];

  int lx = domain_size_[0];
  int ly = domain_size_[1];
  int lz = domain_size_[2];

  // Get source element index

  int source_index = floor((src_coord_[0] * ex) / lx) +
                     floor((src_coord_[1] * ey) / ly) * ex +
                     floor((src_coord_[2] * ez) / lz) * ey * ex;

  for (int i = 0; i < 1; i++)
  {
    rhsElement[i] = source_index;
  }

  // Get coordinates of the corners of the sourc element
  float cornerCoords[8][3];
  int I = 0;
  int nodes_corner[2] = {0, m_mesh->getOrder()};
  for (int k : nodes_corner)
  {
    for (int j : nodes_corner)
    {
      for (int i : nodes_corner)
      {
        int nodeIdx = m_mesh->globalNodeIndex(rhsElement[0], i, j, k);
        cornerCoords[I][0] = m_mesh->nodeCoord(nodeIdx, 0);
        cornerCoords[I][2] = m_mesh->nodeCoord(nodeIdx, 2);
        cornerCoords[I][1] = m_mesh->nodeCoord(nodeIdx, 1);
        I++;
      }
    }
  }

  // initialize source term
  vector<float> sourceTerm =
      myUtils.computeSourceTerm(num_sample_, dt_, f0, sourceOrder);
  for (int j = 0; j < num_sample_; j++)
  {
    myRHSTerm(0, j) = sourceTerm[j];
    if (j % 100 == 0)
      cout << "Sample " << j << "\t: sourceTerm = " << sourceTerm[j] << endl;
  }

  // get element number of source term
  myElementSource = rhsElement[0];
  cout << "Element number for the source location: " << myElementSource << endl
       << endl;

  int order = m_mesh->getOrder();

  switch (order)
  {
    case 1:
      SourceAndReceiverUtils::ComputeRHSWeights<1>(cornerCoords, src_coord_,
                                                   rhsWeights);
      break;
    case 2:
      SourceAndReceiverUtils::ComputeRHSWeights<2>(cornerCoords, src_coord_,
                                                   rhsWeights);
      break;
    case 3:
      SourceAndReceiverUtils::ComputeRHSWeights<3>(cornerCoords, src_coord_,
                                                   rhsWeights);
      break;
    default:
      throw std::runtime_error("Unsupported order: " + std::to_string(order));
  }

  // Receivers computation
  for (int r = 0; r < nb_receivers_; r++)
  {
    const std::array<float, 3>& rc = rcv_coords_[r];

    int receiver_index = floor((rc[0] * ex) / lx) +
                         floor((rc[1] * ey) / ly) * ex +
                         floor((rc[2] * ez) / lz) * ey * ex;
    rhsElementRcv[r] = receiver_index;

    float cornerCoordsRcv[8][3];
    int Ir = 0;
    for (int k : nodes_corner)
      for (int j : nodes_corner)
        for (int i : nodes_corner)
        {
          int nodeIdx = m_mesh->globalNodeIndex(rhsElementRcv[r], i, j, k);
          cornerCoordsRcv[Ir][0] = m_mesh->nodeCoord(nodeIdx, 0);
          cornerCoordsRcv[Ir][1] = m_mesh->nodeCoord(nodeIdx, 1);
          cornerCoordsRcv[Ir][2] = m_mesh->nodeCoord(nodeIdx, 2);
          Ir++;
        }

    switch (order)
    {
      case 1:
        SourceAndReceiverUtils::ComputeRHSWeights<1>(cornerCoordsRcv, rc,
                                                     rhsWeightsRcv, r);
        break;
      case 2:
        SourceAndReceiverUtils::ComputeRHSWeights<2>(cornerCoordsRcv, rc,
                                                     rhsWeightsRcv, r);
        break;
      case 3:
        SourceAndReceiverUtils::ComputeRHSWeights<3>(cornerCoordsRcv, rc,
                                                     rhsWeightsRcv, r);
        break;
      default:
        throw std::runtime_error("Unsupported order: " + std::to_string(order));
    }
  }
}

void SEMproxy::saveSeismos()
{
  std::filesystem::create_directories(seismo_dir_);

  // positions des recepteurs (utile pour la visualisation)
  std::ofstream pos(seismo_dir_ + "/receivers.csv");
  pos << "id,x,y,z\n";
  for (int r = 0; r < nb_receivers_; r++)
    pos << r << "," << rcv_coords_[r][0] << "," << rcv_coords_[r][1] << ","
        << rcv_coords_[r][2] << "\n";

  // sismos : une colonne par recepteur
  std::ofstream out(seismo_dir_ + "/seismos.csv");
  out << std::setprecision(9);
  out << "time";
  for (int r = 0; r < nb_receivers_; r++) out << ",rcv" << r;
  out << "\n";
  for (int t = 0; t < num_sample_; t++)
  {
    out << t * dt_;
    for (int r = 0; r < nb_receivers_; r++) out << "," << pnAtReceiver(r, t);
    out << "\n";
  }
}

void SEMproxy::readReceivers(const std::string& filename,
                             const SemProxyOptions& opt)
{
  rcv_coords_.clear();

  if (filename.empty())  // comportement historique : 1 recepteur
  {
    rcv_coords_.push_back({opt.rcvx, opt.rcvy, opt.rcvz});
  }
  else
  {
    std::ifstream in(filename);
    if (!in)
      throw std::runtime_error("Cannot open receivers file: " + filename);

    std::string line;
    while (std::getline(in, line))
    {
      if (line.empty() || line[0] == '#') continue;
      std::replace(line.begin(), line.end(), ',', ' ');
      std::istringstream ss(line);
      std::array<float, 3> c;
      if (ss >> c[0] >> c[1] >> c[2])  // l'en-tete x,y,z echoue ici : ignore
        rcv_coords_.push_back(c);
    }
    if (rcv_coords_.empty())
      throw std::runtime_error("No receiver found in " + filename);
  }

  const float L[3] = {opt.lx, opt.ly, opt.lz};
  for (size_t r = 0; r < rcv_coords_.size(); r++)
    for (int d = 0; d < 3; d++)
      if (rcv_coords_[r][d] < 0 || rcv_coords_[r][d] > L[d])
        throw std::runtime_error("Receiver " + std::to_string(r) +
                                 " is outside the domain");

  nb_receivers_ = rcv_coords_.size();
  std::cout << "Receivers loaded: " << nb_receivers_ << std::endl;
}

SolverFactory::implemType SEMproxy::getImplem(string implemArg)
{
  if (implemArg == "makutu") return SolverFactory::MAKUTU;
  if (implemArg == "shiva") return SolverFactory::SHIVA;

  throw std::invalid_argument(
      "Implentation type does not follow any valid type.");
}

SolverFactory::meshType SEMproxy::getMesh(string meshArg)
{
  if (meshArg == "cartesian") return SolverFactory::Struct;
  if (meshArg == "ucartesian") return SolverFactory::Unstruct;

  std::cout << "Mesh type found is " << meshArg << std::endl;
  throw std::invalid_argument("Mesh type does not follow any valid type.");
}

SolverFactory::methodType SEMproxy::getMethod(string methodArg)
{
  if (methodArg == "sem") return SolverFactory::SEM;
  if (methodArg == "dg") return SolverFactory::DG;

  throw std::invalid_argument("Method type does not follow any valid type.");
}

float SEMproxy::find_cfl_dt(float cfl_factor)
{
  float sqrtDim3 = 1.73;  // to change for 2d
  float min_spacing = m_mesh->getMinSpacing();
  float v_max = m_mesh->getMaxSpeed();

  float dt = cfl_factor * min_spacing / (sqrtDim3 * v_max);

  return dt;
}
