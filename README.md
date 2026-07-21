# Artifact for EMSOFT 2026: Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination

This repository contains the source code, processed datasets, and analysis tools supporting the EMSOFT 2026 paper, *"Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination."*

[Repository:](https://github.com/Daisy0419/GRB-Search-Pipeline.git)

## Table of Contents

- [System Requirements](#system-requirements)
- [Overview](#overview)
  - [Included Components](#included-components)
  - [Directory Structure](#directory-structure)
- [1 Environment Setup](#1-environment-setup)
  - [1.1 Option A: Using the Provided Docker Container](#11-option-a-using-the-provided-docker-container)
  - [1.2 Option B: Local Installation](#12-option-b-local-installation)
- [2 Reproducing Paper Figures](#2-reproducing-paper-figures)
  - [2.1 Run the Visualization via Docker](#21-run-the-visualization-via-docker)
  - [2.2 Run the Visualization Locally](#22-run-the-visualization-locally)
  - [2.3 Reproducing Results and Figures](#23-reproducing-results-and-figures)
- [3 Running Full Experiments](#3-running-full-experiments)
  - [3.1 Set Up the Run Environment](#31-set-up-the-run-environment)
  - [3.2 Regenerate Pipeline Inputs](#32-regenerate-pipeline-inputs)
  - [3.3 Rerun the Experiments](#33-rerun-the-experiments)
  - [3.4 Visualizing Recomputed Results](#34-visualizing-recomputed-results)
- [4 Extensibility of Experiments](#4-extensibility-of-experiments)


## System Requirements
- OS: Linux
- Reference platform used in the paper: NVIDIA Jetson Orin NX
  - 8 ARM Cortex-A78AE v8.2 CPU cores
  - CPU frequency fixed at 1.5 GHz
  - 16 GB DRAM
  - GPU not used
- Required Storage: **Total: 35GB**
  - Repo: 200MB
  - Miniconda: 800MB
  - Conda environments: 2.8GB
  - LEMON: 70MB
  - Store Resulting maps: 30GB


The paper's timing results are **platform-sensitive**. Functional results may be reproduced on another Linux machine, but direct comparisons with Figures 4-6 should use the reference Jetson configuration.


## Overview

This artifact contains the software and data for offline experiments that simulate and evaluate the proposed on-board observation workflow. It does not acquire data from a live instrument or control a physical telescope.

### Proposed On-Board Workflow

During a real observation, the gamma-ray telescope would receive a mixture of source and background events without knowing which events came from the transient. The proposed workflow would:

1. **Gather events** after detecting a transient.
2. **Choose when to generate a map** using the observed events, estimated background rate, overall deadline, and pre-trained utility tables.
3. **Generate a likelihood map** representing the probable transient location.
4. **Plan the optical search** by converting the map into telescope-FoV tiles and running the GCP planning algorithm.
5. **Search for the transient** until it is detected or the deadline expires.

In the artifact, the event stream and optical search are simulated. The likelihood-mapping, utility-estimation, tiling, and GCP planning code is executed normally. Telescope movement and observation are simulated using the slew- and dwell-time models.

### Artifact Experiment Workflow

The artifact experiments consist of offline training followed by evaluation.

#### Phase A: Training

1. **Generate training maps.** Use all 52,800 simulated training transients in each of the short- and long-transient scenarios. Generate each map using the true transient length and record the source-event count, background-event count, and map-generation time.

2. **Run search planning.** For each training map and telescope FoV, run GCP with different search budgets. Record the planning time and the minimum modeled slew-and-dwell time required to reach a tile containing the true source.

3. **Build the utility tables.** Use these measurements to estimate mapping time, planning time, and detection probability as functions of the observed event counts and remaining deadline. The paper uses `20 x 20` source/background bins and confidence level `q = 0.95`.

The training process uses ground-truth information because the transient locations and lengths are known in the simulation.

#### Phase B: Evaluation

1. Select 10,000 independent test transients.
2. Generate maps using the deadline-oblivious policy (`nodeadline`) and the utility-guided policy for each tested deadline.
3. Run GCP on each generated map and simulate the resulting optical search.
4. Determine whether the search reaches a tile containing the true source before the deadline.
5. Aggregate the mapping errors, processing times, and detection probabilities across the test set.

The provided training tables reproduce the measurements obtained on the Jetson platform. To calibrate the utility estimator for different hardware, users should remeasure the platform-dependent mapping and planning times and rebuild the utility tables. The simulated transient datasets themselves do not need to be regenerated.


### Directory Structure

```text
.
|
|-- cosipy/                 # Python: likelihood mapping
|   |-- cosipy/    
|   |   |-- ts_map/         # key workdir      
|
|-- search_planning/                # Follow-up tiling and search planning
|   |-- include/                    # C++ header files, if used
|   |-- src/                        # C++ GCP implementation
|   |-- CMakeLists.txt              # C++ build configuration
|
|-- data/
|   |-- training/                   # Utility-model training data
|   |   |-- short/
|   |   `-- long/
|   |-- test/                       # End-to-end test data
|   |   |-- short/
|   |   `-- long/
|   |-- likelihood_maps/            # Generated or precomputed maps
|   `-- tilings/                    # Telescope-specific tile sets
|
|-- results/
|   |-- figures/                    # Figures reproduced 
|   |-- precomputed_results/        # Results distributed with the artifact
|   |   |-- mapping_performance/    # Figure 4
|   |   |-- timing/                 # Figures 5-6
|   |   |-- mapping_behavior/       # Figures 7-8
|   |   |-- utility_behavior/       # Figures 9-10
|   |   `-- end_to_end/             # Figure 11
|   |-- recomputed_results/         # Outputs from rerunning experiments
|   `-- [visualization code]        # TODO: add notebook script 
|
|-- cosipy-312-deps.yml             # python environment configuration file
`-- README.md
```

## 1 Environment Setup

### 1.1 Local Installation

#### 1.1.1 Clone Repository

Clone the repository to the path of your choice. All commands listed hereafter assume it is placed directly into your home directory.

Clone the main repository:
```bash
cd ~
git clone https://github.com/Daisy0419/GRB-Search-Pipeline.git
```

Clone the map generation code:
```bash
cd ~/GRB-Search-Pipeline
git clone -b tsmap-artifact https://github.com/McKelvey-Engineering-CSE/cosipy.git
```

#### 1.1.2 Python Environment Setup

We recommend setting up a [conda](https://docs.conda.io/en/latest/) environment for Python.

If you do not have conda installed locally:

```bash
cd ~/GRB-Search-Pipeline
```
Download and install Miniconda (change ~/conda to your preferred location)
```bash
export CONDA_DIR=~/conda
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p "${CONDA_DIR}"
rm miniconda.sh
```

Make conda available in your shell
```bash
. "${CONDA_DIR}/etc/profile.d/conda.sh"
conda config --system --set channel_priority flexible
```
Once conda is available, create the python environments using provided yaml files:
```bash
conda env create -f cosipy-312-deps.yml
```

Activate **cosipy-312** map generation all other scripts:
```bash
conda activate cosipy-312
```

---
#### 1.1.3 C++ Environment Setup

**(1) LEMON Graph Library (Required)**

The Lemon Graph Library is used to compute the minimum-weight perfect matching used in our Greedy Christofides Pathfinding algorithm. 

1. Download, extract, and build the LEMON Graph Library to the directory of your choice. All commands listed hereafter assume it is placed directly in your home directory.

```bash
wget http://lemon.cs.elte.hu/pub/sources/lemon-1.3.1.tar.gz
tar xvfz lemon-1.3.1.tar.gz
cd lemon-1.3.1
mkdir build && cd build
cmake ..
make -j
sudo make install
```

2. Set the necessary environment variables in your shell (change `~/lemon-1.3.1` to your preferred location).

```bash
export LEMON_SOURCE_DIR=~/lemon-1.3.1
export LEMON_BUILD_DIR=~/lemon-1.3.1/build
```

**(2) HDF5 Library (Required)**

The search-planning code reads likelihood maps stored in HDF5 files. Install [HDF5](https://github.com/HDFGroup/hdf5) under your home directory so that administrator privileges are not required.

Download, build, and install HDF5:

```bash
cd ~
git clone --depth 1 https://github.com/HDFGroup/hdf5.git hdf5-source

cmake -S ~/hdf5-source -B ~/hdf5-build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${HOME}/hdf5" \
    -DCMAKE_INSTALL_LIBDIR=lib \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DHDF5_BUILD_EXAMPLES=OFF \
    -DHDF5_BUILD_CPP_LIB=ON \
    -DHDF5_BUILD_HL_LIB=ON

cmake --build ~/hdf5-build -j
cmake --install ~/hdf5-build
```

Configure the HDF5 environment variables:

```bash
export HDF5_ROOT="${HOME}/hdf5"
export LD_LIBRARY_PATH="${HDF5_ROOT}/lib:${LD_LIBRARY_PATH:-}"
```

Verify the installation:

```bash
ls "${HDF5_ROOT}/include/hdf5.h"
ls "${HDF5_ROOT}"/lib/libhdf5*
```

---

**(3) HighFive Library (Required)**

[HighFive](https://github.com/highfive-devs/highfive) is a header-only C++ interface to HDF5. It does not need to be compiled, but its header files must be available when building the search-planning code.

Clone HighFive into your home directory:

```bash
cd ~
git clone --depth 1 --recursive \
    https://github.com/highfive-devs/highfive.git HighFive
```

Configure the HighFive path:

```bash
export HIGHFIVE_ROOT="${HOME}/HighFive"
```

Verify that the required headers are present:

```bash
ls "${HIGHFIVE_ROOT}/include/highfive/H5File.hpp"
```

HighFive is header-only, no separate build or installation step is required.

---

**(4) Build the C++ Executables**

Once all dependencies are installed, build the C++ project with:

```bash
cd ~/GRB-Search-Pipeline/search-planning

export HDF5_ROOT="${HOME}/hdf5"
export HIGHFIVE_ROOT="${HOME}/HighFive"
export LEMON_SOURCE_DIR="${HOME}/lemon-1.3.1"
export LEMON_BUILD_DIR="${LEMON_SOURCE_DIR}/build"
export LD_LIBRARY_PATH="${HDF5_ROOT}/lib:${LD_LIBRARY_PATH:-}"

cmake -S . -B build
cmake --build build -j
```

This produces two binaries in `build/`. Both are compiled from `src/main.cpp` and share the same search-planning implementation. CMake selects a different entry point for each binary:

- **`sp_train`** — compiled with `BUILD_SP_TRAIN` and dispatches to `main_train()`. It processes training maps and produces search-outcome training data.
- **`sp_verify`** — compiled with `BUILD_SP_VERIFY` and dispatches to `main_verify()`. It processes evaluation maps and records whether the simulated search reaches the source before the deadline.

Verify that both binaries were created:

```bash
ls build/sp_train build/sp_verify
```

--- 

## 2 Reproducing Paper Figures

You can visualize the results via Jupyter notebook.

### 2.2 Run Jupyter notebook 

```bash
conda activate cosipy-312
cd ~/GRB-Search-Pipeline/results
jupyter notebook visualize_results.ipynb
```

### 2.3 Reproducing Results and Figures in the Jupyter Notebook

The visualization should read from `results/precomputed_results/` and save newly generated figures to `results/figures/` or another clearly documented output directory.

It should reproduce:

- **Figure 4:** mapping runtime across the cosipy, JIT, external-memory, in-memory, and in-memory multiresolution implementations
- **Figure 5:** map-generation time distributions and their dependence on source-event count
- **Figure 6:** search-planning time distributions by transient scenario and FoV, and their dependence on source-event count
- **Figure 7:** cumulative distribution of mapping error for short and long transients
- **Figure 8:** mapping error as a function of source and background event counts
- **Figure 9:** utility-selected gathering time relative to the deadline-oblivious baseline
- **Figure 10:** change in mapping error caused by utility-selected gathering time
- **Figure 11:** end-to-end success probability versus deadline for two transient scenarios and two FoVs

Figures 1-3 are explanatory diagrams rather than outputs of the main experimental pipeline.


## 3 Running Full Experiments

The full experiment has two phases:

1. **Offline training:** generate training maps, measure mapping and planning times, and collect the training data used by the utility estimator.
2. **Evaluation:** generate maps for 10,000 test transients, run search planning, simulate the optical search, and calculate the success probability.

The full experiment is computationally expensive. To reproduce only the paper figures using the distributed results, skip this section and follow [Section 2](#2-reproducing-paper-figures).

### 3.1 Selecting an Experiment Workflow

There are two ways to run the experiments:

- To reproduce the complete training and evaluation process, follow both Phase A and Phase B.
- To evaluate the policies using the distributed training data, skip Phase A and begin with Phase B.

### 3.2 Phase A: Generate the Offline Training Data

The paper uses 52,800 training transients for each transient scenario. All training transients in the specified directory are processed.

#### Step 1: Configure Paths

Activate the Python environment:

```bash
conda activate cosipy-312
```

Configure the paths for the map-generation script, models, training transients, and output directories:

```bash
export MAP_SCRIPT=~/cosipy/cosipy/ts_map/map_adapt_transients.py

export RESPONSE_MODEL=/shared/models/adapt_response_with_area.h5
export BACKGROUND_MODEL=/shared/models/adapt_bkg_model.h5

export SHORT_TRAINING_TRANSIENTS="/path/to/short/training/transients"  # TODO
export LONG_TRAINING_TRANSIENTS="/path/to/long/training/transients"    # TODO

export OUTPUT_ROOT=~/GRB-Search-Pipeline/results/recomputed_results
export TRAINING_MAP_ROOT="${OUTPUT_ROOT}/training/maps"
export TRAINING_STATS_ROOT="${OUTPUT_ROOT}/training/mapping_stats"
export LOG_ROOT="${OUTPUT_ROOT}/logs"

mkdir -p "${TRAINING_STATS_ROOT}" "${LOG_ROOT}"
```

Here:

- `RESPONSE_MODEL` must point to `adapt_response_with_area.h5`.
- `BACKGROUND_MODEL` must point to `adapt_bkg_model.h5`.
- `SHORT_TRAINING_TRANSIENTS` and `LONG_TRAINING_TRANSIENTS` must point to the corresponding directories of simulated training transients.
- The map output directories are created automatically by `map_adapt_transients.py` if they do not already exist.

#### Step 2: Generate the Short-Transient Training Maps

Run:

```bash
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    "${SHORT_TRAINING_TRANSIENTS}" \
    gt \
    -m \
    -o "${TRAINING_MAP_ROOT}/short" \
    > "${TRAINING_STATS_ROOT}/short_mapping_time_stats.csv" \
    2> "${LOG_ROOT}/short_training_maps.log"
```

The options specify:

- `-t 8`: use eight map-generation threads;
- `-n 64`: generate maps with HEALPix `nside = 64`;
- `gt`: use the true transient duration as the event-gathering endpoint;
- `-m`: write the generated maps to disk; and
- `-o`: select the map output directory.

No `-s` option is supplied during training, so the script processes every transient in the training directory.

The script writes one row of statistics for each processed transient to standard output. Redirecting standard output creates `short_mapping_time_stats.csv`, which contains information including the source-event count, background-event count, gathering time, and measured map-generation time.

The `gt` endpoint uses known source information only because this is an offline simulation for constructing the training data.

#### Step 3: Generate the Long-Transient Training Maps

Run the same command using the long-transient training directory:

```bash
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    "${LONG_TRAINING_TRANSIENTS}" \
    gt \
    -m \
    -o "${TRAINING_MAP_ROOT}/long" \
    > "${TRAINING_STATS_ROOT}/long_mapping_time_stats.csv" \
    2> "${LOG_ROOT}/long_training_maps.log"
```

The likelihood maps are independent of the optical telescope FoV. Therefore, each training map needs to be generated only once, even though search planning is evaluated with multiple FoVs.

#### Step 4: Run GCP on the Training Maps

Run GCP on every generated training map for the following four scenario/FoV combinations:

- short transients with the `2.5 x 2.5` FoV;
- short transients with the `5.36 x 4.5` FoV;
- long transients with the `2.5 x 2.5` FoV; and
- long transients with the `5.36 x 4.5` FoV.

The required tiling and true-source lookup files are pre-generated and stored under:

```text
search-planning/tilings/
├── tiling_files/
│   ├── 2.5x2.5_tiling.csv
│   └── 5.36x4.5_tiling.csv
└── source_tile_train/
    ├── source_tiles_2.5x2.5_short.csv
    ├── source_tiles_5.36x4.5_short.csv
    ├── source_tiles_2.5x2.5_longlow.csv
    └── source_tiles_5.36x4.5_longlow.csv
```

Before running the experiment, open `run_training.py` and check the configuration section at the beginning of the file. In particular, verify:

```python
FOVS = ["2.5x2.5", "5.36x4.5"]

TRAINING_MAP_DIRS = {
    "short":  # path to the short-transient training maps
    "longlow":  # path to the long-transient training maps
}
```

Also verify that the training executable is:

```python
EXECUTABLE = SEARCH_ROOT / "build" / "sp_train"
```

From the directory containing the script, run:

```bash
python run_training.py
```

The script runs `sp_train` on every training map for each configured FoV. For each map, GCP determines the minimum search budget needed to reach the tile containing the true source and records the corresponding search-planning measurements.

The four output files are stored in `results/training/`:

```text
results/training/
├── short_2.5x2.5_tiling.csv
├── short_5.36x4.5_tiling.csv
├── longlow_2.5x2.5_tiling.csv
└── longlow_5.36x4.5_tiling.csv
```

Detailed execution logs are stored in:

```text
results/training/logs/
```

The mapping statistics and GCP training outcomes have different roles:

- `short_mapping_time_stats.csv` contains measurements used to predict map-generation time.
- `short_5.36x4.5_tiling.csv` contains GCP outcomes used to estimate the probability of reaching the source within a given search budget.

The corresponding files for the other scenario/FoV combinations serve the same purposes.


### 3.3 Phase B: Evaluate the Policies

The evaluation uses 10,000 test transients for each transient scenario. The script's default random seed selects the same test transients used in the paper.

#### Step 5: Configure the Evaluation Inputs

Set the test directory and select the training files for the transient scenario and FoV being evaluated:

```bash
export TEST_TRANSIENTS="/path/to/test/transients"                 # TODO
export TRAINING_TIMES_FILE="/path/to/mapping_time_stats.csv"      # TODO
export TRAINING_OUTCOMES_FILE="/path/to/search_outcomes.csv"      # TODO

export TEST_MAP_ROOT="${OUTPUT_ROOT}/test/maps"
export TEST_STATS_ROOT="${OUTPUT_ROOT}/test/mapping_stats"

mkdir -p "${TEST_STATS_ROOT}"
```

Here:

- `TRAINING_TIMES_FILE` is the mapping-statistics file generated during Phase A, such as `short_mapping_time_stats.csv`.
- `TRAINING_OUTCOMES_FILE` is the output of the GCP training experiments for the selected scenario and FoV, such as `short_5.36x4.5_tiling.csv`.

If the distributed training data are used, these variables should instead point to the corresponding files in:

```text
/shared/training/emsoft_data/
```

#### Step 6: Generate Utility-Guided Test Maps

Set the deadline, map output directory, and statistics output file:

```bash
export DEADLINE=10
export TEST_MAP_DIR="${TEST_MAP_ROOT}/short/5.36x4.5/${DEADLINE}"
export TEST_STATS_FILE="${TEST_STATS_ROOT}/short_5.36x4.5_${DEADLINE}.csv"
```

Generate the test maps:

```bash
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    -s 10000 \
    --training-times "${TRAINING_TIMES_FILE}" \
    --training-outcomes "${TRAINING_OUTCOMES_FILE}" \
    "${TEST_TRANSIENTS}" \
    "${DEADLINE}" \
    -m \
    -o "${TEST_MAP_DIR}" \
    > "${TEST_STATS_FILE}" \
    2> "${LOG_ROOT}/test_${DEADLINE}.log"
```

For the utility-guided policy, `DEADLINE` is the overall deadline in seconds. Repeat the command for every deadline and FoV evaluated in the paper.

The short-transient deadlines are:

```text
10, 15, 20, 25, 30, 35, 40, 45, and 50 seconds
```

The long-transient deadlines are:

```text
30, 40, 50, 60, 70, 80, 90, 100, and 110 seconds
```

The training-outcomes file is FoV-specific. Therefore, utility-guided maps must be generated separately for each FoV.

As in training, the script writes the test statistics to standard output. These statistics must be saved because they include the selected gathering time and measured map-generation time for each test transient.

#### Step 7: Generate Deadline-Oblivious Test Maps

Use `nodeadline` instead of an integer deadline to generate the deadline-oblivious baseline:

```bash
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    -s 10000 \
    "${TEST_TRANSIENTS}" \
    nodeadline \
    -m \
    -o "${TEST_MAP_ROOT}/short/nodeadline" \
    > "${TEST_STATS_ROOT}/short_nodeadline.csv" \
    2> "${LOG_ROOT}/short_nodeadline.log"
```

The deadline-oblivious policy does not use the utility training files. Its maps are also independent of the telescope FoV and therefore need to be generated only once per transient scenario.

Optionally, replace `nodeadline` with `gt` to generate ground-truth test maps for reference.

#### Step 8: Run GCP and Simulate the Search

The `run_validation.py` script evaluates the generated test maps using the `sp_verify` executable.

Before running it, open the configuration section at the beginning of the script and check:

```python
SCENARIOS = ["short", "longlow"]
POLICIES = ["utility", "nodeadline", "gt"]
FOVS = ["2.5x2.5", "5.36x4.5"]
```

Also verify the configured deadlines and test-map locations:

```python
DEADLINES = {
    "short": [10, 15, 20, 25, 30, 35, 40, 45, 50],
    "longlow": [30, 40, 50, 60, 70, 80, 90, 100, 110],
}
```

```python
UTILITY_ROOTS = {
    # Paths to the FoV-specific utility-guided maps and statistics
}

BASELINE_ROOTS = {
    # Paths to the FoV-independent nodeadline and gt maps and statistics
}
```

The validation source-tile lookup files must be stored under:

```text
search-planning/tilings/source_tile_validation/
├── source_tiles_2.5x2.5_short.csv
├── source_tiles_5.36x4.5_short.csv
├── source_tiles_2.5x2.5_longlow.csv
└── source_tiles_5.36x4.5_longlow.csv
```

From the directory containing the script, run:

```bash
python run_validation.py
```

For each configured test map, the script and `sp_verify` perform the following steps:

1. Read the gathering and map-generation times from the corresponding mapping-statistics CSV.
2. Subtract the gathering and map-generation times from the overall deadline.
3. Run GCP and measure the search-planning time.
4. Subtract the planning time from the remaining search budget.
5. Simulate following the resulting path using the telescope slew, settling, and dwell-time models.
6. Record whether the path reaches the true source tile before the deadline.

The script evaluates both transient scenarios, both FoVs, and every configured policy and deadline. Results are stored under:

```text
results/validation/
```

Each result filename has the following form:

```text
<scenario>_<fov>_tiling_<policy>_<deadline>.csv
```

For example:

```text
short_2.5x2.5_tiling_utility_10.csv
short_5.36x4.5_tiling_nodeadline_30.csv
longlow_2.5x2.5_tiling_gt_60.csv
longlow_5.36x4.5_tiling_utility_110.csv
```

Detailed execution logs are stored in:

```text
results/validation/logs/
```

These newly generated results do not overwrite the distributed results under:

```text
results/precomputed_results/
```