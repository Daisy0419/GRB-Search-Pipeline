#!/usr/bin/env python3
"""Run GCP on all configured training maps."""

from __future__ import annotations

import csv
import shlex
import subprocess
import sys
from pathlib import Path


# =============================================================================
# Configuration -- edit only this section
# =============================================================================

REPO_ROOT = Path.home() / "GRB-Search-Pipeline"
SEARCH_ROOT = REPO_ROOT / "search-planning"

# Only these telescope fields of view are processed.
FOVS = ["2.5x2.5", "5.36x4.5"]

# Training-map directories for each transient scenario.
# Change these paths if your generated maps are stored elsewhere.
TRAINING_MAP_DIRS = {
    "short": REPO_ROOT / "results" / "training" / "maps" / "short",
    "longlow": REPO_ROOT / "results" / "training" / "maps" / "longlow",
}

EXECUTABLE = SEARCH_ROOT / "build" / "sp_train"
TILING_DIR = SEARCH_ROOT / "tilings" / "tiling_files"
SOURCE_TILE_DIR = SEARCH_ROOT / "tilings" / "source_tile_train"
RESULTS_DIR = REPO_ROOT / "results" / "training"

W_MAX = 10.0
W_ACC = 10.0
DWELL_TIME = 5.0
IS_DEEPSLOW = False

# Set to an integer for a short test, for example MAX_MAPS = 5.
MAX_MAPS: int | None = None

# Set to True to replace existing result files.
OVERWRITE = False

# =============================================================================


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{description} not found: {path}")


def require_directory(path: Path, description: str) -> None:
    if not path.is_dir():
        raise NotADirectoryError(f"{description} not found: {path}")


def load_source_tiles(csv_path: Path) -> dict[str, int]:
    """Return a map-filename to source-tile lookup."""
    require_file(csv_path, "Source-tile lookup")

    lookup: dict[str, int] = {}
    with csv_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required_columns = {"map", "RightTile"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{csv_path} must contain columns: "
                f"{', '.join(sorted(required_columns))}"
            )

        for row in reader:
            map_name = row["map"].strip()
            if map_name in lookup:
                raise ValueError(f"Duplicate map {map_name!r} in {csv_path}")
            lookup[map_name] = int(float(row["RightTile"]))

    return lookup


def prepare_output(result_file: Path) -> None:
    if result_file.exists():
        if not OVERWRITE:
            raise FileExistsError(
                f"Output already exists: {result_file}. "
                "Set OVERWRITE = True to replace it."
            )
        result_file.unlink()


def run_sp_train(
    map_file: Path,
    tiling_file: Path,
    source_tile: int,
    result_file: Path,
    log_stream,
) -> None:
    command = [
        str(EXECUTABLE),
        str(map_file),
        str(tiling_file),
        str(source_tile),
        str(W_MAX),
        str(W_ACC),
        str(DWELL_TIME),
        "1" if IS_DEEPSLOW else "0",
        str(result_file),
    ]

    log_stream.write(f"\n$ {shlex.join(command)}\n")
    log_stream.flush()
    subprocess.run(
        command,
        cwd=RESULTS_DIR,
        text=True,
        stdout=log_stream,
        stderr=subprocess.STDOUT,
        check=True,
    )


def run_training_scenario(scenario: str, map_dir: Path) -> None:
    require_directory(map_dir, f"Training-map directory for {scenario}")

    maps = sorted(map_dir.glob("*.h5"))
    if MAX_MAPS is not None:
        if MAX_MAPS <= 0:
            raise ValueError("MAX_MAPS must be positive or None.")
        maps = maps[:MAX_MAPS]
    if not maps:
        raise FileNotFoundError(f"No .h5 maps found in {map_dir}")

    print(f"\nScenario: {scenario}")
    print(f"Maps: {len(maps)} from {map_dir}")

    for fov in FOVS:
        tiling_file = TILING_DIR / f"{fov}_tiling.csv"
        source_tile_file = SOURCE_TILE_DIR / f"source_tiles_{fov}_{scenario}.csv"
        require_file(tiling_file, "Tiling file")
        source_tiles = load_source_tiles(source_tile_file)

        result_stem = f"{scenario}_searching_{fov}_tiling"
        final_result = RESULTS_DIR / f"{result_stem}.csv"
        log_file = RESULTS_DIR / "logs" / f"{result_stem}.log"
        prepare_output(final_result)

        print(f"FoV: {fov} -> {final_result}")
        with log_file.open("w", encoding="utf-8") as log_stream:
            for index, map_file in enumerate(maps, start=1):
                try:
                    source_tile = source_tiles[map_file.name]
                except KeyError as error:
                    raise KeyError(
                        f"No source tile for {map_file.name!r} in {source_tile_file}"
                    ) from error

                run_sp_train(
                    map_file,
                    tiling_file,
                    source_tile,
                    final_result,
                    log_stream,
                )

                if index == 1 or index % 100 == 0 or index == len(maps):
                    print(f"  completed {index}/{len(maps)} maps", flush=True)

        if not final_result.is_file():
            raise FileNotFoundError(
                f"sp_train did not create the requested output file: {final_result}"
            )


def main() -> int:
    require_file(EXECUTABLE, "sp_train executable")
    require_directory(TILING_DIR, "Tiling directory")
    require_directory(SOURCE_TILE_DIR, "Training source-tile directory")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "logs").mkdir(parents=True, exist_ok=True)

    print(f"FoVs: {', '.join(FOVS)}")
    print(f"Results: {RESULTS_DIR}")

    for scenario, map_dir in TRAINING_MAP_DIRS.items():
        run_training_scenario(scenario, map_dir.expanduser().resolve())

    print("\nAll training runs completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)