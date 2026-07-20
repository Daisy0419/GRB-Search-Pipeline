cmake_minimum_required(VERSION 3.11)
project(op LANGUAGES CXX)

# ---------- C++17 ----------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(
        CMAKE_BUILD_TYPE "Release"
        CACHE STRING "Choose the type of build."
        FORCE
    )
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# ---------- OpenMP and threads ----------
find_package(OpenMP REQUIRED)
find_package(Threads REQUIRED)

# ---------- HDF5 (user-local) ----------
if(DEFINED ENV{HDF5_ROOT} AND NOT "$ENV{HDF5_ROOT}" STREQUAL "")
    set(HDF5_ROOT "$ENV{HDF5_ROOT}")
else()
    set(HDF5_ROOT "$ENV{HOME}/hdf5")
endif()

set(HDF5_INCLUDE_DIR "${HDF5_ROOT}/include")

find_library(
    HDF5_C_LIB
    NAMES hdf5
    PATHS
        "${HDF5_ROOT}/lib"
        "${HDF5_ROOT}/lib64"
    NO_DEFAULT_PATH
    REQUIRED
)

# Optional HDF5 libraries
find_library(
    HDF5_HL_LIB
    NAMES hdf5_hl
    PATHS
        "${HDF5_ROOT}/lib"
        "${HDF5_ROOT}/lib64"
    NO_DEFAULT_PATH
)

find_library(
    HDF5_CPP_LIB
    NAMES hdf5_cpp
    PATHS
        "${HDF5_ROOT}/lib"
        "${HDF5_ROOT}/lib64"
    NO_DEFAULT_PATH
)

if(NOT EXISTS "${HDF5_INCLUDE_DIR}/hdf5.h")
    message(
        FATAL_ERROR
        "HDF5 header not found at ${HDF5_INCLUDE_DIR}/hdf5.h"
    )
endif()

message(STATUS "HDF5 root: ${HDF5_ROOT}")
message(STATUS "HDF5 include: ${HDF5_INCLUDE_DIR}")
message(STATUS "HDF5 C library: ${HDF5_C_LIB}")

# ---------- HighFive (header-only) ----------
if(DEFINED ENV{HIGHFIVE_ROOT} AND NOT "$ENV{HIGHFIVE_ROOT}" STREQUAL "")
    set(HIGHFIVE_ROOT "$ENV{HIGHFIVE_ROOT}")
else()
    set(HIGHFIVE_ROOT "$ENV{HOME}/HighFive")
endif()

set(HIGHFIVE_INCLUDE_DIR "${HIGHFIVE_ROOT}/include")

if(NOT EXISTS "${HIGHFIVE_INCLUDE_DIR}/highfive/H5File.hpp")
    message(
        FATAL_ERROR
        "HighFive header not found at "
        "${HIGHFIVE_INCLUDE_DIR}/highfive/H5File.hpp"
    )
endif()

message(STATUS "HighFive include: ${HIGHFIVE_INCLUDE_DIR}")

# ---------- LEMON ----------
if(DEFINED ENV{LEMON_SOURCE_DIR}
   AND NOT "$ENV{LEMON_SOURCE_DIR}" STREQUAL "")
    set(LEMON_SOURCE_DIR "$ENV{LEMON_SOURCE_DIR}")
else()
    set(LEMON_SOURCE_DIR "$ENV{HOME}/lemon-1.3.1")
endif()

if(DEFINED ENV{LEMON_BUILD_DIR}
   AND NOT "$ENV{LEMON_BUILD_DIR}" STREQUAL "")
    set(LEMON_BUILD_DIR "$ENV{LEMON_BUILD_DIR}")
else()
    set(LEMON_BUILD_DIR "${LEMON_SOURCE_DIR}/build")
endif()

if(NOT IS_DIRECTORY "${LEMON_SOURCE_DIR}")
    message(
        FATAL_ERROR
        "LEMON source directory not found at ${LEMON_SOURCE_DIR}"
    )
endif()

if(NOT IS_DIRECTORY "${LEMON_BUILD_DIR}")
    message(
        FATAL_ERROR
        "LEMON build directory not found at ${LEMON_BUILD_DIR}"
    )
endif()

message(STATUS "LEMON source: ${LEMON_SOURCE_DIR}")
message(STATUS "LEMON build: ${LEMON_BUILD_DIR}")

# ---------- Source files ----------
file(
    GLOB_RECURSE ALL_SOURCES
    "${CMAKE_SOURCE_DIR}/src/*.cpp"
)

# main.cpp contains:
#   main_train()
#   main_verify()
# and the conditional main() dispatcher.
set(MAIN_SOURCE "${CMAKE_SOURCE_DIR}/src/main.cpp")

if(NOT EXISTS "${MAIN_SOURCE}")
    message(
        FATAL_ERROR
        "Expected entry-point source at ${MAIN_SOURCE}"
    )
endif()

# Remove every possible main source from the shared source list.
# This prevents duplicate main() definitions if old wrapper files remain.
set(CORE_SOURCES ${ALL_SOURCES})

list(
    REMOVE_ITEM CORE_SOURCES
    "${MAIN_SOURCE}"
    "${CMAKE_SOURCE_DIR}/src/main_train.cpp"
    "${CMAKE_SOURCE_DIR}/src/main_verify.cpp"
)

# ---------- Common include directories ----------
set(
    PROJECT_INCLUDES
    "${CMAKE_SOURCE_DIR}/include"
    "${LEMON_SOURCE_DIR}"
    "${LEMON_BUILD_DIR}"
    "${HIGHFIVE_INCLUDE_DIR}"
    "${HDF5_INCLUDE_DIR}"
)

# ---------- Common libraries ----------
set(
    PROJECT_LIBS
    OpenMP::OpenMP_CXX
    Threads::Threads
    "${HDF5_C_LIB}"
    "${CMAKE_DL_LIBS}"
    m
)

# Link the optional HDF5 libraries when available.
if(HDF5_HL_LIB)
    list(APPEND PROJECT_LIBS "${HDF5_HL_LIB}")
endif()

if(HDF5_CPP_LIB)
    list(APPEND PROJECT_LIBS "${HDF5_CPP_LIB}")
endif()

# Older GCC versions may require a separate filesystem library.
if(
    CMAKE_CXX_COMPILER_ID STREQUAL "GNU"
    AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS 9
)
    list(APPEND PROJECT_LIBS stdc++fs)
endif()

# ---------- Training executable ----------
add_executable(
    sp_train
    "${MAIN_SOURCE}"
    ${CORE_SOURCES}
)

# Select main_train() as the entry point.
target_compile_definitions(
    sp_train
    PRIVATE
    BUILD_SP_TRAIN
)

target_include_directories(
    sp_train
    PRIVATE
    ${PROJECT_INCLUDES}
)

target_link_libraries(
    sp_train
    PRIVATE
    ${PROJECT_LIBS}
)

# ---------- Verification executable ----------
add_executable(
    sp_verify
    "${MAIN_SOURCE}"
    ${CORE_SOURCES}
)

# Select main_verify() as the entry point.
target_compile_definitions(
    sp_verify
    PRIVATE
    BUILD_SP_VERIFY
)

target_include_directories(
    sp_verify
    PRIVATE
    ${PROJECT_INCLUDES}
)

target_link_libraries(
    sp_verify
    PRIVATE
    ${PROJECT_LIBS}
)

message(STATUS "Configured executable: sp_train")
message(STATUS "Configured executable: sp_verify")