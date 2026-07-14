cmake_minimum_required(VERSION 3.11)
project(op)

# ---------- C++17 ----------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Choose the type of build." FORCE)
endif()
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# ---------- OpenMP ----------
find_package(OpenMP REQUIRED)

# ---------- HDF5 (user-local) ----------
set(HDF5_ROOT "$ENV{HOME}/hdf5")
set(HDF5_INCLUDE_DIR "${HDF5_ROOT}/include")
set(HDF5_LIBRARY_DIR "${HDF5_ROOT}/lib")

find_library(HDF5_C_LIB NAMES hdf5 PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH REQUIRED)
# Optional extras (only if you need them):
find_library(HDF5_HL_LIB  NAMES hdf5_hl  PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH)
find_library(HDF5_CPP_LIB NAMES hdf5_cpp PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH)

message(STATUS "HDF5 include: ${HDF5_INCLUDE_DIR}")
message(STATUS "HDF5 lib: ${HDF5_C_LIB}")


# ---------- HighFive (header-only) ----------
set(HIGHFIVE_INCLUDE_DIR "/home/daisy/HighFive/include")  

# ---------- Gurobi ----------
set(GUROBI_HOME "$ENV{GUROBI_HOME}")
if(NOT GUROBI_HOME)
  message(FATAL_ERROR "GUROBI_HOME is not set.")
endif()

set(GUROBI_INCLUDE_DIR "${GUROBI_HOME}/include")
set(GUROBI_LIBRARY_DIR "${GUROBI_HOME}/lib")

# Headers
find_path(GUROBI_INCLUDE_DIR_FOUND
  NAMES gurobi_c++.h
  HINTS "${GUROBI_INCLUDE_DIR}" "${GUROBI_HOME}"
  PATH_SUFFIXES include
  REQUIRED)

# C++ static archive
find_library(GUROBI_CXX_LIB
  NAMES gurobi_c++
  HINTS "${GUROBI_LIBRARY_DIR}" "${GUROBI_HOME}"
  PATH_SUFFIXES lib
  REQUIRED)

# Core shared library (versioned)
find_library(GUROBI_CORE_LIB
  NAMES gurobi120 gurobi
  HINTS "${GUROBI_LIBRARY_DIR}" "${GUROBI_HOME}"
  PATH_SUFFIXES lib
  REQUIRED)

message(STATUS "Gurobi include: ${GUROBI_INCLUDE_DIR}")
message(STATUS "Gurobi C++ lib: ${GUROBI_CXX_LIB}")
message(STATUS "Gurobi core lib: ${GUROBI_CORE_LIB}")

# Ensure runtime can find libgurobi120.so without setting LD_LIBRARY_PATH
set(CMAKE_INSTALL_RPATH "${GUROBI_LIBRARY_DIR}")
set(CMAKE_BUILD_RPATH   "${GUROBI_LIBRARY_DIR}")


# ---------- LEMON (adjust paths) ----------
set(LEMON_SOURCE_DIR "/home/daisy/lemon-1.3.1")
set(LEMON_BUILD_DIR  "/home/daisy/lemon-1.3.1/build")

# ---------- Sources ----------
# Grab all .cpp files
file(GLOB_RECURSE ALL_SOURCES "src/*.cpp")

# Explicitly identify the two mains
set(MAIN          "${CMAKE_SOURCE_DIR}/src/main.cpp")
# set(MAIN_CUSTOM   "${CMAKE_SOURCE_DIR}/src/main_custom.cpp")

# Guard against missing files
if(NOT EXISTS "${MAIN}")
    message(FATAL_ERROR "Expected main at ${MAIN} not found.")
endif()
# if(NOT EXISTS "${MAIN_CUSTOM}")
#     message(FATAL_ERROR "Expected main at ${MAIN_CUSTOM} not found.")
# endif()

# Core sources = all sources minus the two mains
set(CORE_SOURCES ${ALL_SOURCES})
list(REMOVE_ITEM CORE_SOURCES "${MAIN}" "${MAIN_CUSTOM}")

# ---------- Common include dirs ----------
set(PROJECT_INCLUDES
    ${CMAKE_SOURCE_DIR}/include
    ${GUROBI_INCLUDE_DIR}
    ${LEMON_SOURCE_DIR}
    ${LEMON_BUILD_DIR}
    ${HIGHFIVE_INCLUDE_DIR}
    ${HDF5_INCLUDE_DIRS}
)

# set(GRB_LINK_LIBS ${GUROBI_CXX_LIB} ${GUROBI_LIB})
set(GRB_LINK_LIBS ${GUROBI_CXX_LIB} ${GUROBI_CORE_LIB})

# ---------- Common libs ----------
set(PROJECT_LIBS
    OpenMP::OpenMP_CXX
    ${GRB_LINK_LIBS}
    ${HDF5_LIBRARIES}
    ${HDF5_CPP_LIB}
    pthread m dl
    stdc++fs 
)

# ---------- Executable: ts (main.cpp) ----------
add_executable(ts ${MAIN} ${CORE_SOURCES})
target_include_directories(ts PRIVATE ${PROJECT_INCLUDES} 
  ${HIGHFIVE_INCLUDE_DIR}
  ${HDF5_INCLUDE_DIR}
  ${HDF5_INCLUDE_DIR}/hdf5)
target_link_libraries(ts PRIVATE ${PROJECT_LIBS} ${HDF5_C_LIB})

# cmake_minimum_required(VERSION 3.11)
# project(op)

# set(CMAKE_CXX_STANDARD 17)
# set(CMAKE_CXX_STANDARD_REQUIRED ON)

# if(NOT CMAKE_BUILD_TYPE)
#     set(CMAKE_BUILD_TYPE "RelWithDebInfo" CACHE STRING "Choose the type of build." FORCE)
# endif()
# message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# find_package(OpenMP REQUIRED)

# # ---------- HDF5 (user-local) ----------
# set(HDF5_ROOT "$ENV{HOME}/hdf5")
# set(HDF5_INCLUDE_DIR "${HDF5_ROOT}/include")
# set(HDF5_LIBRARY_DIR "${HDF5_ROOT}/lib")

# find_library(HDF5_C_LIB NAMES hdf5 PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH REQUIRED)
# find_library(HDF5_HL_LIB  NAMES hdf5_hl  PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH)
# find_library(HDF5_CPP_LIB NAMES hdf5_cpp PATHS "${HDF5_LIBRARY_DIR}" NO_DEFAULT_PATH)

# message(STATUS "HDF5 include: ${HDF5_INCLUDE_DIR}")
# message(STATUS "HDF5 lib: ${HDF5_C_LIB}")

# # ---------- HighFive ----------
# set(HIGHFIVE_INCLUDE_DIR "/home/daisy/HighFive/include")

# # ---------- Gurobi ----------
# set(GUROBI_HOME "$ENV{GUROBI_HOME}")
# if(NOT GUROBI_HOME)
#   message(FATAL_ERROR "GUROBI_HOME is not set.")
# endif()

# set(GUROBI_INCLUDE_DIR "${GUROBI_HOME}/include")
# set(GUROBI_LIBRARY_DIR "${GUROBI_HOME}/lib")

# find_path(GUROBI_INCLUDE_DIR_FOUND
#   NAMES gurobi_c++.h
#   HINTS "${GUROBI_INCLUDE_DIR}" "${GUROBI_HOME}"
#   PATH_SUFFIXES include
#   REQUIRED)

# find_library(GUROBI_CXX_LIB
#   NAMES gurobi_c++
#   HINTS "${GUROBI_LIBRARY_DIR}" "${GUROBI_HOME}"
#   PATH_SUFFIXES lib
#   REQUIRED)

# find_library(GUROBI_CORE_LIB
#   NAMES gurobi120 gurobi
#   HINTS "${GUROBI_LIBRARY_DIR}" "${GUROBI_HOME}"
#   PATH_SUFFIXES lib
#   REQUIRED)

# message(STATUS "Gurobi include: ${GUROBI_INCLUDE_DIR}")
# message(STATUS "Gurobi C++ lib: ${GUROBI_CXX_LIB}")
# message(STATUS "Gurobi core lib: ${GUROBI_CORE_LIB}")

# set(CMAKE_INSTALL_RPATH "${GUROBI_LIBRARY_DIR}")
# set(CMAKE_BUILD_RPATH   "${GUROBI_LIBRARY_DIR}")

# # ---------- LEMON ----------
# set(LEMON_SOURCE_DIR "/home/daisy/lemon-1.3.1")
# set(LEMON_BUILD_DIR  "/home/daisy/lemon-1.3.1/build")

# # ---------- Sources ----------
# file(GLOB_RECURSE ALL_SOURCES "src/*.cpp")

# set(MAIN "${CMAKE_SOURCE_DIR}/src/main.cpp")

# if(NOT EXISTS "${MAIN}")
#     message(FATAL_ERROR "Expected main at ${MAIN} not found.")
# endif()

# set(CORE_SOURCES ${ALL_SOURCES})
# list(REMOVE_ITEM CORE_SOURCES "${MAIN}")

# # ---------- Includes ----------
# set(PROJECT_INCLUDES
#     ${CMAKE_SOURCE_DIR}/include
#     ${GUROBI_INCLUDE_DIR}
#     ${LEMON_SOURCE_DIR}
#     ${LEMON_BUILD_DIR}
#     ${HIGHFIVE_INCLUDE_DIR}
#     ${HDF5_INCLUDE_DIR}
# )

# set(GRB_LINK_LIBS ${GUROBI_CXX_LIB} ${GUROBI_CORE_LIB})

# set(PROJECT_LIBS
#     OpenMP::OpenMP_CXX
#     ${GRB_LINK_LIBS}
#     ${HDF5_CPP_LIB}
#     pthread m dl
#     stdc++fs
# )

# add_executable(ts ${MAIN} ${CORE_SOURCES})
# target_include_directories(ts PRIVATE
#   ${PROJECT_INCLUDES}
#   ${HDF5_INCLUDE_DIR}/hdf5
# )
# target_link_libraries(ts PRIVATE ${PROJECT_LIBS} ${HDF5_C_LIB})

# # ---------- gprof ----------
# option(ENABLE_GPROF "Enable gprof profiling" ON)

# if(ENABLE_GPROF)
#     target_compile_options(ts PRIVATE -pg -g)
#     target_link_options(ts PRIVATE -pg)
# endif()


# # cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_GPROF=ON ..
# # make -j
# # ./ts
# # gprof ./ts gmon.out > profile.txt