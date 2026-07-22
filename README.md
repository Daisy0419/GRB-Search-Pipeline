# Artifact for EMSOFT 2026: Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination

This repository contains the source code, processed datasets, and analysis tools supporting the EMSOFT 2026 paper, *"Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination."*

Repository: https://github.com/Daisy0419/GRB-Search-Pipeline.git

## Table of Contents

- [System Requirements](#system-requirements)
- [Overview](#overview)
  - [Proposed On-Board Workflow](#proposed-on-board-workflow)
  - [Artifact Experiment Workflow](#artifact-experiment-workflow)
  - [Directory Structure](#directory-structure)
- [1 Environment Setup and Data Download](#1-environment-setup-and-data-download)
  - [1.1 Local Installation](#11-local-installation)
  - [1.2 Download the Experiment Data](#12-download-the-experiment-data)
- [2 Reproducing Paper Figures](#2-reproducing-paper-figures)
- [3 Running Full Experiments](#3-running-full-experiments)
  - [3.1 Phase A: Generate the Offline Training Data](#31-phase-a-generate-the-offline-training-data)
    - [Step 1: Configure Paths](#step-1-configure-paths)
    - [Step 2: Generate the Short-Transient Training Maps](#step-2-generate-the-short-transient-training-maps)
    - [Step 3: Generate the Long-Transient Training Maps](#step-3-generate-the-long-transient-training-maps)
    - [Step 4: Run GCP on the Training Maps](#step-4-run-gcp-on-the-training-maps)
  - [3.2 Phase B: Evaluate the Policies](#32-phase-b-evaluate-the-policies)
    - [Step 5: Configure the Evaluation Inputs](#step-5-configure-the-evaluation-inputs)
    - [Step 6: Generate Utility-Guided Test Maps](#step-6-generate-utility-guided-test-maps)
    - [Step 7: Generate Deadline-Oblivious and Ground-Truth Test Maps](#step-7-generate-deadline-oblivious-and-ground-truth-test-maps)
    - [Step 8: Run GCP and Simulate the Search](#step-8-run-gcp-and-simulate-the-search)
    - [Step 9: Aggregate and Visualize the Recomputed Results](#step-9-aggregate-and-visualize-the-recomputed-results)


## System Requirements

- OS: Linux
- Tested architecture: Linux ARM64 (`aarch64`)
- Required command-line tools: Git, CMake, Make, a C++17 compiler with OpenMP support, `wget`, `curl`, and `tar`
- Reference platform used in the paper: NVIDIA Jetson Orin NX
  - 8 ARM Cortex-A78AE v8.2 CPU cores
  - CPU frequency fixed at 1.5 GHz
  - 16 GB DRAM
  - GPU not used
- Required storage after extraction: **at least 65 GB**, plus temporary space for the downloaded archive
  - Repository: 200 MB
  - Miniconda: 800 MB
  - Conda environment: 2.8 GB
  - LEMON: 70 MB
  - Transients and models: approximately 30 GB
  - Generated maps: approximately 30 GB

The provided `cosipy-312-deps.yaml` contains architecture-specific package builds from the ARM64 reference platform. Exact environment reproduction therefore requires Linux ARM64. An architecture-compatible environment file is required when running on Linux x86-64.


The paper's timing results are **platform-sensitive**. Functional results may be reproduced on another Linux machine with a compatible environment, but direct comparisons with Figures 4-11 should use the reference Jetson configuration.


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

1. **Generate training maps.** Use all 52,800 simulated training transients in each of the short- and long-transient scenarios. The long-transient scenario is named `longlow` in directory and result filenames. Generate each map using the true transient length and record the source-event count, background-event count, and map-generation time.

2. **Run search planning.** For each training map and telescope FoV, run GCP with different search budgets. Record the planning time and the minimum modeled slew-and-dwell time required to reach a tile containing the true source.

The utility query engine will use these measurements to estimate mapping time, planning time, and detection probability as functions of the observed event counts and remaining deadline. The paper uses `20 x 20` source/background bins and confidence level `q = 0.95`.

#### Phase B: Evaluation

Evaluation uses 10,000 test transients from each scenario. Use `-s 10000 -r 1957` in every map-generation run so that all policies use the same test transients.

1. **Generate utility-guided test maps.** Generate maps for both telescope FoVs at every evaluated deadline because the utility policy depends on the FoV-specific training table:

   - short: `10, 15, 20, 25, 30, 35, 40, 45, 50` seconds;
   - longlow: `30, 40, 50, 60, 70, 80, 90, 100, 110` seconds; and
   - FoVs: `2.5 x 2.5` and `5.36 x 4.5`.

   Save both the generated maps and the mapping-statistics CSV for every scenario, FoV, and deadline.

2. **Generate deadline-oblivious test maps.** Run the `nodeadline` mapping policy once for the short scenario and once for the longlow scenario. These maps do not depend on the FoV or deadline and can therefore be reused in all corresponding GCP evaluation runs.

   The `nodeadline` policy ignores the deadline when choosing when to begin mapping. It is still evaluated under each finite end-to-end deadline in the next step.

3. **Run GCP and simulate the search.** For both scenarios and both FoVs, run `sp_verify` at every evaluated deadline:

   - use the matching FoV- and deadline-specific maps for the utility policy; and
   - reuse the same `nodeadline` maps at every deadline.

   The evaluation accounts for the event-gathering time, map-generation time, GCP planning time, and modeled telescope slew-and-dwell time. It records whether the simulated search reaches a tile containing the true source before the overall deadline.

4. **Aggregate the results.** Calculate the mapping error, processing times, and detection probability for each combination of scenario, FoV, policy, and deadline.


### Directory Structure

The artifact uses the source repository and downloaded transient-data directory shown below. Generated and precomputed results are stored inside the source repository.

```text
~/
|-- GRB-Search-Pipeline/             # Source code and experiment results
|   |-- cosipy/                      # Python likelihood-map generation
|   |   |-- pyproject.toml
|   |   `-- cosipy/
|   |       `-- ts_map/              # Map-generation and utility code
|   |-- search-planning/             # C++ GCP search-planning code
|   |   |-- include/                 # C++ header files
|   |   |-- src/                     # C++ source files
|   |   |-- tilings/                 # FoV tilings and source-tile tables
|   |   |-- build/                   # sp_train and sp_verify executables
|   |   |-- run_training.py          # Runs GCP on training maps
|   |   `-- run_validation.py        # Evaluates generated test maps
|   |-- results/                     # Newly generated outputs and figures
|   |-- precomputed_results/         # Distributed training tables and paper results
|   |-- cosipy-312-deps.yaml         # Python environment configuration
|   `-- README.md                    # Artifact instructions
`-- transients/                      # Downloaded models and transient datasets
    |-- models/
    |-- emsoft_training_short/
    |-- emsoft_training_longlow/
    |-- emsoft_test_short/
    `-- emsoft_test_longlow/
```

The large transient datasets under `~/transients/` are downloaded separately and are not stored in the Git repository. Newly generated files are written under `~/GRB-Search-Pipeline/results/`, while the distributed files under `~/GRB-Search-Pipeline/precomputed_results/` should remain unchanged.

## 1 Environment Setup and Data Download

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
Download and install the Miniconda installer for the current Linux architecture (change `~/conda` to your preferred location):

```bash
export CONDA_DIR=~/conda

case "$(uname -m)" in
    x86_64)         export MINICONDA_ARCH=x86_64 ;;
    aarch64|arm64)  export MINICONDA_ARCH=aarch64 ;;
    *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

wget -q \
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${MINICONDA_ARCH}.sh" \
    -O miniconda.sh
bash miniconda.sh -b -p "${CONDA_DIR}"
rm miniconda.sh
```

Make conda available in your shell
```bash
. "${CONDA_DIR}/etc/profile.d/conda.sh"
conda config --system --set channel_priority flexible
```
Once Conda is available, create the Python environment using the provided YAML file:

```bash
cd ~/GRB-Search-Pipeline
conda env create -f cosipy-312-deps.yaml
```

The provided YAML contains ARM64-specific package builds. On x86-64, use an architecture-compatible environment file containing the same Python dependencies.

Activate **`cosipy-312`** for map generation and the other Python scripts:
```bash
conda activate cosipy-312
```

```bash
cd ~/GRB-Search-Pipeline/cosipy
git switch tsmap-artifact

python -m pip install "poetry-core>=2,<3"
python -m pip install --no-deps -e .
python -m pip install notebook
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

### 1.2 Download the Experiment Data

The detector models and simulated transient datasets are distributed separately from the source-code repository because the complete extracted dataset is approximately 25-30 GB.

The data archive is available from Zenodo:

- **Zenodo record:** [TODO: Zenodo record](TODO_ZENODO_RECORD_URL)
- **Archive:** `transients.tar.gz`
- **Download size:** TODO
- **SHA-256:** `TODO_SHA256`

The archive contains the complete `transients/` directory and should be extracted directly under the home directory.

#### 1.2.1 Download the Archive

Download the archive using a browser from the Zenodo record above, or run:

```bash
export TRANSIENTS_URL="TODO_TRANSIENTS_ARCHIVE_URL"
export TRANSIENTS_ARCHIVE="${HOME}/transients.tar.gz"

curl \
    --location \
    --fail \
    --continue-at - \
    --output "${TRANSIENTS_ARCHIVE}" \
    "${TRANSIENTS_URL}"
```

The `--continue-at -` option allows an interrupted download to resume when supported by the server.

Alternatively, use `wget`:

```bash
wget -c \
    "TODO_TRANSIENTS_ARCHIVE_URL" \
    -O "${HOME}/transients.tar.gz"
```

#### 1.2.2 Verify the Download

Verify the archive checksum before extracting it:

```bash
cd "${HOME}"

echo "TODO_SHA256  transients.tar.gz" | sha256sum --check
```

The expected output is:

```text
transients.tar.gz: OK
```

If the checksum does not match, remove the incomplete archive and download it again.

#### 1.2.3 Extract the Dataset

Extract the archive under the home directory:

```bash
tar -xzf "${HOME}/transients.tar.gz" -C "${HOME}"
```

This should create:

```text
~/transients/
├── models/
│   ├── adapt_response_w_area.h5
│   └── adapt_bkg_model.h5
├── emsoft_training_short/
├── emsoft_training_longlow/
├── emsoft_test_short/
└── emsoft_test_longlow/
```

--- 

## 2 Reproducing Paper Figures

You can visualize the results via Jupyter notebook.

```bash
conda activate cosipy-312
cd ~/GRB-Search-Pipeline/results
jupyter notebook visualize_results.ipynb
```

The visualization notebook should read the distributed results from `~/GRB-Search-Pipeline/precomputed_results/` and save newly generated figures under `~/GRB-Search-Pipeline/results/figures/`. Do not modify the distributed precomputed results.

The notebook should reproduce Figures 4-11 from the paper's results section. Figures 1-3 are explanatory diagrams rather than outputs of the experiment workflow.


## 3 Running Full Experiments

The full experiment has two phases:

1. **Training:** generate training maps, measure mapping and planning times, and collect the data used by the utility estimator.
2. **Evaluation:** generate maps for 10,000 test transients, run search planning, simulate the optical search, and calculate the success probability.

The full experiment is computationally expensive. To reproduce only the paper figures using the distributed results, skip this section and follow [Section 2](#2-reproducing-paper-figures).

To rerun evaluation using the distributed training tables, complete Step 1 to configure the common paths, skip Steps 2-4, and select the precomputed-training-data option in Step 5.


### 3.1 Phase A: Generate the Offline Training Data

The paper uses 52,800 training transients for each transient scenario. The training command processes every transient in the specified directory.

#### Step 1: Configure Paths

Activate the Python environment:

```bash
conda activate cosipy-312
```

Configure the repository, input-data, model, and output paths:

```bash
export REPO_ROOT="${HOME}/GRB-Search-Pipeline"
export DATA_ROOT="${HOME}/transients"

export MAP_SCRIPT="${REPO_ROOT}/cosipy/cosipy/ts_map/map_adapt_transients.py"

export RESPONSE_MODEL="${DATA_ROOT}/models/adapt_response_w_area.h5"
export BACKGROUND_MODEL="${DATA_ROOT}/models/adapt_bkg_model.h5"

export SHORT_TRAINING_TRANSIENTS="${DATA_ROOT}/emsoft_training_short"
export LONGLOW_TRAINING_TRANSIENTS="${DATA_ROOT}/emsoft_training_longlow"

export SHORT_TEST_TRANSIENTS="${DATA_ROOT}/emsoft_test_short"
export LONGLOW_TEST_TRANSIENTS="${DATA_ROOT}/emsoft_test_longlow"

export TRAINING_ROOT="${REPO_ROOT}/results/training"
export TRAINING_MAP_ROOT="${TRAINING_ROOT}/maps"
export TRAINING_LOG_ROOT="${TRAINING_ROOT}/logs"

mkdir -p \
    "${TRAINING_MAP_ROOT}/short" \
    "${TRAINING_MAP_ROOT}/longlow" \
    "${TRAINING_LOG_ROOT}"
```

Verify the required inputs:

```bash
ls "${MAP_SCRIPT}"
ls "${RESPONSE_MODEL}"
ls "${BACKGROUND_MODEL}"
ls "${SHORT_TRAINING_TRANSIENTS}"
ls "${LONGLOW_TRAINING_TRANSIENTS}"
ls "${SHORT_TEST_TRANSIENTS}"
ls "${LONGLOW_TEST_TRANSIENTS}"
```

#### Step 2: Generate the Short-Transient Training Maps

Run:

```bash
env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    "${SHORT_TRAINING_TRANSIENTS}" \
    gt \
    -m \
    -o "${TRAINING_MAP_ROOT}/short" \
    > "${TRAINING_ROOT}/short_mapping_time_stats.csv" \
    2> "${TRAINING_LOG_ROOT}/short_mapping.log"
```

The command processes all 52,800 short training transients. Do not use `-s 10000` during training.

The options specify:

- `-t 8`: use eight map-generation threads;
- `-n 64`: generate maps with HEALPix `nside = 64`;
- `gt`: use the true transient duration as the event-gathering endpoint;
- `-m`: write each generated map to disk; and
- `-o`: select the map output directory.

The generated mapping statistics are written to:

```text
~/GRB-Search-Pipeline/results/training/short_mapping_time_stats.csv
```

#### Step 3: Generate the Long-Transient Training Maps

Run:

```bash
env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
python "${MAP_SCRIPT}" \
    --response "${RESPONSE_MODEL}" \
    --bkg-model "${BACKGROUND_MODEL}" \
    -t 8 \
    -n 64 \
    "${LONGLOW_TRAINING_TRANSIENTS}" \
    gt \
    -m \
    -o "${TRAINING_MAP_ROOT}/longlow" \
    > "${TRAINING_ROOT}/longlow_mapping_time_stats.csv" \
    2> "${TRAINING_LOG_ROOT}/longlow_mapping.log"
```

The likelihood maps are independent of the optical telescope FoV. Therefore, each training transient is mapped only once.

#### Step 4: Run GCP on the Training Maps

Run GCP on every generated training map for the following four scenario/FoV combinations:

- short transients with the `2.5 x 2.5` FoV;
- short transients with the `5.36 x 4.5` FoV;
- longlow transients with the `2.5 x 2.5` FoV; and
- longlow transients with the `5.36 x 4.5` FoV.

The required tiling and true-source lookup files are pre-generated:

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

Open `run_training.py` and configure:

```python
FOVS = ["2.5x2.5", "5.36x4.5"]

TRAINING_MAP_DIRS = {
    "short": REPO_ROOT / "results" / "training" / "maps" / "short",
    "longlow": REPO_ROOT / "results" / "training" / "maps" / "longlow",
}

EXECUTABLE = SEARCH_ROOT / "build" / "sp_train"
RESULTS_DIR = REPO_ROOT / "results" / "training"
```

The generated maps use the Bitshuffle HDF5 compression filter. Before running the C++ program, make the corresponding plugin available to HDF5:

```bash
conda activate cosipy-312

export HDF5_PLUGIN_PATH="$(
    python -c "import hdf5plugin; print(hdf5plugin.PLUGIN_PATH)"
)"
export LD_LIBRARY_PATH="${HOME}/hdf5/lib:${LD_LIBRARY_PATH:-}"
```

From the directory containing `run_training.py`, run:

```bash
python run_training.py
```

The script invokes `sp_train` on every training map for each configured FoV. For each map, GCP records the planning runtime and the minimum search budget needed to reach the tile containing the true source.

The four output files are:

```text
~/GRB-Search-Pipeline/results/training/
├── short_2.5x2.5_tiling.csv
├── short_5.36x4.5_tiling.csv
├── longlow_2.5x2.5_tiling.csv
└── longlow_5.36x4.5_tiling.csv
```

The mapping statistics and GCP outcomes have different roles:

- `short_mapping_time_stats.csv` contains measurements used to predict map-generation time.
- `short_5.36x4.5_tiling.csv` contains outcomes used to estimate the probability of reaching the source within a given search budget.

The corresponding longlow and `2.5x2.5` files serve the same purposes.

### 3.2 Phase B: Evaluate the Policies

The evaluation uses 10,000 test transients from each scenario. The fixed random seed `1957` selects the same test transients for every policy and deadline.

#### Step 5: Configure the Evaluation Inputs

Configure the evaluation output directories:

```bash
export VALIDATION_ROOT="${REPO_ROOT}/results/validation"
export GENERATED_TEST_ROOT="${VALIDATION_ROOT}/generated"

mkdir -p "${GENERATED_TEST_ROOT}"
```

Choose one of the following training-data sources.

To use the training data generated in Phase A:

```bash
export SHORT_MAPPING_TIMES="${TRAINING_ROOT}/short_mapping_time_stats.csv"
export LONGLOW_MAPPING_TIMES="${TRAINING_ROOT}/longlow_mapping_time_stats.csv"
export TRAINING_OUTCOMES_ROOT="${TRAINING_ROOT}"
```

To skip Phase A and use the distributed training data:

```bash
export PRECOMPUTED_TRAINING_ROOT="${REPO_ROOT}/precomputed_results/training"

export SHORT_MAPPING_TIMES="${PRECOMPUTED_TRAINING_ROOT}/short-stats.csv"
export LONGLOW_MAPPING_TIMES="${PRECOMPUTED_TRAINING_ROOT}/TODO_LONGLOW_MAPPING_TIME_STATS.csv"
export TRAINING_OUTCOMES_ROOT="${PRECOMPUTED_TRAINING_ROOT}"
```

Replace `TODO_LONGLOW_MAPPING_TIME_STATS.csv` with the distributed longlow mapping-time filename after that filename has been finalized.

Verify the selected files before continuing:

```bash
ls "${SHORT_MAPPING_TIMES}"
ls "${LONGLOW_MAPPING_TIMES}"

ls "${TRAINING_OUTCOMES_ROOT}/short_2.5x2.5_tiling.csv"
ls "${TRAINING_OUTCOMES_ROOT}/short_5.36x4.5_tiling.csv"
ls "${TRAINING_OUTCOMES_ROOT}/longlow_2.5x2.5_tiling.csv"
ls "${TRAINING_OUTCOMES_ROOT}/longlow_5.36x4.5_tiling.csv"
```

#### Step 6: Generate Utility-Guided Test Maps

Utility-guided mapping depends on the telescope FoV because each FoV uses a different GCP training-outcome table. Generate a separate set of test maps for every FoV and deadline.

For short transients, run:

```bash
for FOV in 2.5x2.5 5.36x4.5; do
    for DEADLINE in 10 15 20 25 30 35 40 45 50; do
        EXPERIMENT_ROOT="${GENERATED_TEST_ROOT}/short/${FOV}"
        mkdir -p "${EXPERIMENT_ROOT}"

        echo "Running short: FoV=${FOV}, deadline=${DEADLINE}"

        env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
        python "${MAP_SCRIPT}" \
            --response "${RESPONSE_MODEL}" \
            --bkg-model "${BACKGROUND_MODEL}" \
            -t 8 \
            -n 64 \
            -s 10000 \
            -r 1957 \
            --training-times "${SHORT_MAPPING_TIMES}" \
            --training-outcomes \
                "${TRAINING_OUTCOMES_ROOT}/short_${FOV}_tiling.csv" \
            "${SHORT_TEST_TRANSIENTS}" \
            "${DEADLINE}" \
            -m \
            -o "${EXPERIMENT_ROOT}/emsoft_maps_${DEADLINE}" \
            > "${EXPERIMENT_ROOT}/emsoft_stats_${DEADLINE}.csv" \
            2> "${EXPERIMENT_ROOT}/emsoft_maps_${DEADLINE}.log"
    done
done
```

For longlow transients, run:

```bash
for FOV in 2.5x2.5 5.36x4.5; do
    for DEADLINE in 30 40 50 60 70 80 90 100 110; do
        EXPERIMENT_ROOT="${GENERATED_TEST_ROOT}/longlow/${FOV}"
        mkdir -p "${EXPERIMENT_ROOT}"

        echo "Running longlow: FoV=${FOV}, deadline=${DEADLINE}"

        env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
        python "${MAP_SCRIPT}" \
            --response "${RESPONSE_MODEL}" \
            --bkg-model "${BACKGROUND_MODEL}" \
            -t 8 \
            -n 64 \
            -s 10000 \
            -r 1957 \
            --training-times "${LONGLOW_MAPPING_TIMES}" \
            --training-outcomes \
                "${TRAINING_OUTCOMES_ROOT}/longlow_${FOV}_tiling.csv" \
            "${LONGLOW_TEST_TRANSIENTS}" \
            "${DEADLINE}" \
            -m \
            -o "${EXPERIMENT_ROOT}/emsoft_maps_${DEADLINE}" \
            > "${EXPERIMENT_ROOT}/emsoft_stats_${DEADLINE}.csv" \
            2> "${EXPERIMENT_ROOT}/emsoft_maps_${DEADLINE}.log"
    done
done
```

The `-s 10000` option selects 10,000 test transients. The explicit `-r 1957` option ensures that every run uses the same test subset.

#### Step 7: Generate Deadline-Oblivious and Ground-Truth Test Maps

The `nodeadline` and `gt` endpoint modes do not use the utility training tables and do not depend on FoV. Generate each once per transient scenario.

For short transients, run:

```bash
BASELINE_ROOT="${GENERATED_TEST_ROOT}/short/baselines"
mkdir -p "${BASELINE_ROOT}"

for MODE in nodeadline gt; do
    env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
    python "${MAP_SCRIPT}" \
        --response "${RESPONSE_MODEL}" \
        --bkg-model "${BACKGROUND_MODEL}" \
        -t 8 \
        -n 64 \
        -s 10000 \
        -r 1957 \
        "${SHORT_TEST_TRANSIENTS}" \
        "${MODE}" \
        -m \
        -o "${BASELINE_ROOT}/emsoft_maps_${MODE}" \
        > "${BASELINE_ROOT}/emsoft_stats_${MODE}.csv" \
        2> "${BASELINE_ROOT}/emsoft_maps_${MODE}.log"
done
```

For longlow transients, run:

```bash
BASELINE_ROOT="${GENERATED_TEST_ROOT}/longlow/baselines"
mkdir -p "${BASELINE_ROOT}"

for MODE in nodeadline gt; do
    env -u LD_LIBRARY_PATH -u HDF5_PLUGIN_PATH \
    python "${MAP_SCRIPT}" \
        --response "${RESPONSE_MODEL}" \
        --bkg-model "${BACKGROUND_MODEL}" \
        -t 8 \
        -n 64 \
        -s 10000 \
        -r 1957 \
        "${LONGLOW_TEST_TRANSIENTS}" \
        "${MODE}" \
        -m \
        -o "${BASELINE_ROOT}/emsoft_maps_${MODE}" \
        > "${BASELINE_ROOT}/emsoft_stats_${MODE}.csv" \
        2> "${BASELINE_ROOT}/emsoft_maps_${MODE}.log"
done
```

The `gt` mode uses the true transient duration and is included only as a ground-truth reference. It is not an implementable runtime policy.

#### Step 8: Run GCP and Simulate the Search

The `run_validation.py` script evaluates the generated test maps using the `sp_verify` executable.

The validation source-tile lookup files must be stored under:

```text
search-planning/tilings/source_tile_validation/
├── source_tiles_2.5x2.5_short.csv
├── source_tiles_5.36x4.5_short.csv
├── source_tiles_2.5x2.5_longlow.csv
└── source_tiles_5.36x4.5_longlow.csv
```

Open `run_validation.py` and configure:

```python
SCENARIOS = ["short", "longlow"]
POLICIES = ["utility", "nodeadline", "gt"]
FOVS = ["2.5x2.5", "5.36x4.5"]

DEADLINES = {
    "short": [10, 15, 20, 25, 30, 35, 40, 45, 50],
    "longlow": [30, 40, 50, 60, 70, 80, 90, 100, 110],
}

UTILITY_ROOTS = {
    "short": str(
        REPO_ROOT
        / "results"
        / "validation"
        / "generated"
        / "short"
        / "{fov}"
    ),
    "longlow": str(
        REPO_ROOT
        / "results"
        / "validation"
        / "generated"
        / "longlow"
        / "{fov}"
    ),
}

BASELINE_ROOTS = {
    "short": (
        REPO_ROOT
        / "results"
        / "validation"
        / "generated"
        / "short"
        / "baselines"
    ),
    "longlow": (
        REPO_ROOT
        / "results"
        / "validation"
        / "generated"
        / "longlow"
        / "baselines"
    ),
}

EXECUTABLE = SEARCH_ROOT / "build" / "sp_verify"
RESULTS_DIR = REPO_ROOT / "results" / "validation"
```

Make the HDF5 library and Bitshuffle reader plugin available to the C++ executable:

```bash
conda activate cosipy-312

export HDF5_PLUGIN_PATH="$(
    python -c "import hdf5plugin; print(hdf5plugin.PLUGIN_PATH)"
)"
export LD_LIBRARY_PATH="${HOME}/hdf5/lib:${LD_LIBRARY_PATH:-}"
```

From the directory containing `run_validation.py`, run:

```bash
python run_validation.py
```

For each test map, the script:

1. reads the gathering and mapping times from the corresponding statistics CSV;
2. subtracts those times from the overall deadline;
3. runs GCP and measures its planning time;
4. accounts for the remaining optical-search budget;
5. simulates following the planned path using the telescope timing model; and
6. records whether the path reaches the true source tile before the deadline.

The result files are stored under:

```text
~/GRB-Search-Pipeline/results/validation/
```

Each result filename has the following form:

```text
<scenario>_<fov>_tiling_<policy>_<deadline>.csv
```

Examples include:

```text
short_2.5x2.5_tiling_utility_10.csv
short_5.36x4.5_tiling_nodeadline_30.csv
longlow_2.5x2.5_tiling_gt_60.csv
longlow_5.36x4.5_tiling_utility_110.csv
```

#### Step 9: Visualize the Recomputed Results

