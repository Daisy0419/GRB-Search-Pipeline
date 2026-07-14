# Artifact for EMSOFT 2026: Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination

This repository contains the source code, processed datasets, and analysis tools supporting the EMSOFT 2026 paper, *"Suborbital and Orbital Real-Time Localization of Gamma-Ray Bursts via Utility-Guided Coordination."*

Repository: **TODO**

Data: **TODO: add drive URL**

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
**TODO**
- OS: Linux (some instructions are Ubuntu-specific)
- CPU: Minimum 2 cores, **8+ cores preferred** (24 physical/48 logical cores used in paper)
- RAM: **8GB**
- Required Storage, Option A, Docker Container: **Total: 5.6GB**
  - Docker package install: 500MB
  - Docker container: 5.1GB
- Required Storage, Option B, Local Install: **Total: 4.1GB**
  - Repo: 200MB
  - Miniconda: 800MB
  - Conda environments: 2.8GB
  - LEMON: 70MB


## Overview

This artifact implements an on-board pipeline for localizing a gamma-ray transient and planning a follow-up optical search under an overall deadline.

The pipeline has the following stages:

1. gather source and background events;
2. evaluate the expected utility of beginning map generation;
3. generate a HEALPix likelihood map;
4. discretize the likelihood map into telescope-specific tiles;
5. construct a deadline-aware search path; and
6. evaluate whether the path images the true transient location before the deadline.

All code is written in Python except for the performance-critical search-planning algorithm, which is written in C++. Python code controls data processing, likelihood-map generation, utility estimation, experiment execution, result analysis, and plotting.

### Included Components

- Python likelihood-map generation code, including the optimized in-memory and multiresolution implementation evaluated in the paper
- Python utility-model training and runtime utility evaluation
- Python data preparation, experiment orchestration, and result analysis
- Python conversion of HEALPix likelihood maps into telescope FoV tiles
- C++ implementation of Greedy Christofides Pathfinding (GCP) for deadline-aware search planning
- Processed response and background models used by likelihood mapping
- Training data for utility and processing-time estimation
- Test data for the short- and long-transient scenarios
- Precomputed results for Figures 4-11
- A notebook or plotting entry point for reproducing the paper figures **TODO**

### Directory Structure

The intended high-level organization is shown below. Exact internal Python filenames should be added only after the repository layout is finalized.

```text
.
|
|-- map_generation/                 # Python: likelihood mapping
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
|-- configuration.yml           # TODO: add python configuration file
`-- README.md
```

## 1 Environment Setup

You can run the artifact via **Docker (recommended)** or a **Local Setup**. 

### 1.1 Option A: Using the Provided Docker Container

You may install Docker according to [these instructions](https://docs.docker.com/engine/install/). Here, we include the instructions for Ubuntu distributions:

#### 1.1.1 Install Docker

1. Set up Docker's `apt` repository:

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

2. Install the latest Docker packages.

```bash
sudo apt-get install docker-ce docker-ce-cli \
  containerd.io docker-buildx-plugin docker-compose-plugin
```

#### 1.1.2 Pull the Docker Image
<!-- ```bash
sudo docker pull ghcr.io/daisy0419/rtss25-op-solver:1.0
``` -->
**TODO: docker**
All dependencies are pre-installed, and project binaries are precompiled in the image. You can jump to Reproducing Paper Figures or Running Full Experiments.


### 1.2 (Option B) Local Installation

#### 1.2.1 Clone Repository

Clone the repository to the path of your choice. All commands listed hereafter assume it is placed directly into your home directory.

```bash
cd ~
git clone -b rtss2025_artifact https://github.com/Daisy0419/Telescope-Searching-Problem/
```

#### 1.2.2 Python Environment Setup

We recommend setting up a [conda](https://docs.conda.io/en/latest/) environment for Python.

If you do not have conda installed locally:

```bash
cd ~/Telescope-Search-Problem
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
conda env create -f rtss25-sky-tiling.yml
conda env create -f rtss25-telescope-search.yml
```

Activate **rtss25-sky-tiling** before running tiling scripts or **rtss25-telescope-search** before running all other scripts:
```bash
conda activate rtss25-sky-tiling
# or
conda activate rtss25-telescope-search
```

---
#### 1.2.3 C++ Environment Setup

**(1) Gurobi Optimizer (Required)**

The Gurobi Optimizer is used to solve our ILP approach to the orienteering problem.

1. Download and extract Gurobi to the directory of your choice. All commands listed hereafter assume it is placed directly in your home directory.

```bash
cd ~
wget https://packages.gurobi.com/12.0/gurobi12.0.3_linux64.tar.gz
tar xvfz gurobi12.0.3_linux64.tar.gz
```

2. Set the necessary environment variables in your shell (change `~/gurobi1203` to your preferred location).

```bash
export GUROBI_HOME=~/gurobi1203/linux64
export PATH="${GUROBI_HOME}/bin:$PATH"
export LD_LIBRARY_PATH="${GUROBI_HOME}/lib:$LD_LIBRARY_PATH"
```

**Note**: If you don't have Gurobi license and you do not plan to run experiments involving Gurobi, you still need to install Gurobi in order to compile the project code (due to build-time linking requirements).


#### (2) LEMON Graph Library (Required)

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

**(3) Build the C++ Executables**

Once all dependencies are installed, you can build the C++ project with:

```bash
cd ~/Telescope-Search-Problem
mkdir build && cd build
cmake ..
make -j
```

This produces two binaries in `build/`. The only difference between them is the `main` function:
- **ts** — built from `src/main.cpp`. Entry point for batch experiments used in the paper, invoked by the Python scripts in `results/`.
- **op** — built from `src/main_custom.cpp`. Entry point for single-case runs, one algorithm on one (skymap, budget, slewrate) instance.

--- 

## 2 Reproducing Paper Figures

You can visualize the results via Jupyter notebook either via **container** or **locally**.

### 2.1 Run Jupyter Notebook via Docker Container
```bash
sudo docker run --rm -it -p 8888:8888 \
  -v "$PWD:/workspace" \
  ghcr.io/daisy0419/rtss25-op-solver:1.0 \
  bash -lc 'conda run -n rtss25-telescope-search \
    jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
      --IdentityProvider.token="" \
      --ServerApp.root_dir=/workspace \
      --allow-root'
```

Then open http://localhost:8888 and navigate to **results/visualize_results.ipynb** in the sidebar.

### 2.2 Run Jupyter notebook Locally

```bash
conda activate rtss25-telescope-search
cd ~/Telescope-Searching-Problem/results
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

The full experiments are substantially more expensive than reproducing plots from precomputed result tables. The artifact should therefore provide both a small validation run and the complete experiment path.

### 3.1 Set Up the Run Environment

#### 3.1.1 Run Experiments in the Docker Container

**TODO**

#### 3.1.2 Run Experiments Locally

**TODO**

### 3.2 Regenerate Pipeline Inputs

#### 3.2.1 Obtain the Response and Background Models

**TODO** 

#### 3.2.2 Generate Likelihood Maps

**TODO** 

#### 3.2.3 Train the Utility Models

**TODO** 

#### 3.2.4 Generate Telescope Tilings

**TODO** 

### 3.3 Rerun the Experiments

#### Running Time

| Experiment path | Expected time |
| --- | ---: |
| Reproduce Figures 4-11 from precomputed tables | **TODO** |
| Small smoke test of the integrated pipeline | **TODO** |
| Utility-model training measurements | About one day on the reference Jetson; confirm final artifact time |
| Complete end-to-end test experiments | **TODO** |

If a single command reruns all experiments, provide it here:

```text
TODO: insert the actual command.
```

The complete workflow should not overwrite `results/precomputed_results/`. Newly generated results should be placed under `results/recomputed_results/`.

#### 3.3.1 Mapping-Implementation Benchmark (Figure 4)

#### 3.3.2 Mapping and Search-Planning Times (Figures 5-6)


#### 3.3.3 Likelihood-Mapping Behavior (Figures 7-8)


#### 3.3.4 Utility Decisions and Mapping Error (Figures 9-10)


#### 3.3.5 End-to-End Detection Success (Figure 11)


### 3.4 Visualizing Recomputed Results



## 4 Extensibility of Experiments

