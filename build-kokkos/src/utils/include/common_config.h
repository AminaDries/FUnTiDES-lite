#ifndef COMMON_CONFIG_HPP
#define COMMON_CONFIG_HPP

// Enable use of Vector (CMake option)
/* #undef USE_VECTOR */

// Enables use of KOKOS (CMake option)
#define USE_KOKKOS

// Enables use of ENABLE_HIP (CMake option)
/* #undef ENABLE_HIP */

// Enables use of ENABLE_CUDA (CMake option)
/* #undef ENABLE_CUDA */

// Enables python wrapping code
/* #undef ENABLE_PYWRAP */

// Enable save snapshots of wavefields in FD-proxy (for debugging)
/* #undef FD_SAVE_SNAPSHOTS */

// Enable printout memory allocation info for arrays
/* #undef PRINT_ALLOC_INFO */

// Enable hierarchical parallelism in Kokkos
/* #undef USE_KOKKOS_TEAMS */

/* #undef USE_DOUBLE */

/* #undef USE_SIMPLE_MESH */
#endif
