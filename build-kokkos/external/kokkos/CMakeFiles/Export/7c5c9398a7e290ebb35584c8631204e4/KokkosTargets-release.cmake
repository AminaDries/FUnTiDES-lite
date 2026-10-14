#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Kokkos::kokkoscore" for configuration "Release"
set_property(TARGET Kokkos::kokkoscore APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Kokkos::kokkoscore PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libkokkoscore.so.4.1.00"
  IMPORTED_SONAME_RELEASE "libkokkoscore.so.4.1"
  )

list(APPEND _cmake_import_check_targets Kokkos::kokkoscore )
list(APPEND _cmake_import_check_files_for_Kokkos::kokkoscore "${_IMPORT_PREFIX}/lib/libkokkoscore.so.4.1.00" )

# Import target "Kokkos::kokkoscontainers" for configuration "Release"
set_property(TARGET Kokkos::kokkoscontainers APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Kokkos::kokkoscontainers PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libkokkoscontainers.so.4.1.00"
  IMPORTED_SONAME_RELEASE "libkokkoscontainers.so.4.1"
  )

list(APPEND _cmake_import_check_targets Kokkos::kokkoscontainers )
list(APPEND _cmake_import_check_files_for_Kokkos::kokkoscontainers "${_IMPORT_PREFIX}/lib/libkokkoscontainers.so.4.1.00" )

# Import target "Kokkos::kokkossimd" for configuration "Release"
set_property(TARGET Kokkos::kokkossimd APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Kokkos::kokkossimd PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libkokkossimd.so.4.1.00"
  IMPORTED_SONAME_RELEASE "libkokkossimd.so.4.1"
  )

list(APPEND _cmake_import_check_targets Kokkos::kokkossimd )
list(APPEND _cmake_import_check_files_for_Kokkos::kokkossimd "${_IMPORT_PREFIX}/lib/libkokkossimd.so.4.1.00" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
