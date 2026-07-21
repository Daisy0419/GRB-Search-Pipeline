#!/usr/bin/env python3
"""Run GCP validation for all configured scenarios, policies, and FoVs."""

from __future__ import annotations

import csv
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path



# Configuration -- edit only this section

REPO_ROOT = Path.home() / "GRB-Search-Pipeline"
SEARCH_ROOT = REPO_ROOT / "search-planning"

# scenarios, policies, and FoVs 
SCENARIOS = ["short", "longlow"]
POLICIES = ["utility", "nodeadline"]
FOVS = ["2.5x2.5", "5.36x4.5"]

DEADLINES = {
    "short": [10, 15, 20, 25, 30, 35, 40, 45, 50],
    "longlow": [30, 40, 50, 60, 70, 80, 90, 100, 110],
}

# Utility-guided maps are FoV-specific. The {fov} field is replaced by the
# current entry in FOVS.
UTILITY_ROOTS = {
    "short": "/shared/valid_tests/{fov}",
    "longlow": "/shared/valid_tests/{fov}_longlow",
}

# The nodeadline and gt maps are independent of FoV and reused for both FoVs.
BASELINE_ROOTS = {
    "short": Path("/shared/valid_tests/no-fov"),
    "longlow": Path("/shared/valid_tests/no-fov_longlow"),
}

EXECUTABLE = SEARCH_ROOT / "build" / "sp_verify"
TILING_DIR = SEARCH_ROOT / "tilings" / "tiling_files"
SOURCE_TILE_DIR = SEARCH_ROOT / "tilings" / "source_tile_validation"
RESULTS_DIR = REPO_ROOT / "results" / "validation"

W_MAX = 10.0
W_ACC = 10.0
IS_DEEPSLOW = False

# sp_verify must append its output rows to this filename in its working
# directory. The script moves the completed file to its final name.
RAW_RESULT_NAME = "out.csv"

# Set to an integer for a short test, for example MAX_MAPS = 5.
MAX_MAPS: int | None = None

# Retain the nearest-position fallback used by the original script.
ALLOW_FUZZY_MAP_MATCH = True

# Set to True to replace existing result files.
OVERWRITE = False

# =============================================================================


MAP_PATTERN = re.compile(
    r".*_p(\d+)-(\d+)_a(\d+)-(\d+)_(\d+)_map\.h5$"
)


@dataclass(frozen=True)
class TimingRecord:
    wait_time: float
    mapping_time: float


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{description} not found: {path}")


def require_directory(path: Path, description: str) -> None:
    if not path.is_dir():
        raise NotADirectoryError(f"{description} not found: {path}")


def parse_map_filename(filename: str) -> tuple[float, float, int] | None:
    match = MAP_PATTERN.fullmatch(filename)
    if match is None:
        return None

    p_int, p_frac, a_int, a_frac, transient_id = match.groups()
    polar = float(f"{p_int}.{p_frac}")
    azimuth = float(f"{a_int}.{a_frac}")
    altitude = 90.0 - polar
    return altitude, azimuth, int(transient_id)


def position_key(altitude: float, azimuth: float, transient_id: int):
    return round(altitude, 1), round(azimuth, 1), transient_id


def build_map_index(map_dir: Path) -> dict[tuple[float, float, int], Path]:
    index: dict[tuple[float, float, int], Path] = {}

    for map_file in sorted(map_dir.glob("*_map.h5")):
        parsed = parse_map_filename(map_file.name)
        if parsed is None:
            print(f"WARNING: unrecognized map filename: {map_file.name}")
            continue

        key = position_key(*parsed)
        if key in index:
            raise ValueError(
                f"Maps {index[key].name!r} and {map_file.name!r} have "
                f"the same matching key {key}."
            )
        index[key] = map_file

    if not index:
        raise FileNotFoundError(f"No recognized *_map.h5 files found in {map_dir}")
    return index


def find_nearest_map(
    index: dict[tuple[float, float, int], Path],
    altitude: float,
    azimuth: float,
    transient_id: int,
) -> Path | None:
    candidates = [item for item in index.items() if item[0][2] == transient_id]
    if not candidates:
        return None

    _, map_file = min(
        candidates,
        key=lambda item: (
            (item[0][0] - altitude) ** 2 + (item[0][1] - azimuth) ** 2
        ),
    )
    return map_file


def load_timing_records(stats_file: Path, map_dir: Path) -> dict[str, TimingRecord]:
    require_file(stats_file, "Mapping-statistics file")
    map_index = build_map_index(map_dir)
    records: dict[str, TimingRecord] = {}

    with stats_file.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required_columns = {
            "alt",
            "az",
            "transient_id",
            "wait_time",
            "mapping_time",
        }
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{stats_file} must contain columns: "
                f"{', '.join(sorted(required_columns))}"
            )

        for row in reader:
            altitude = float(row["alt"])
            azimuth = float(row["az"])
            transient_id = int(row["transient_id"])
            map_file = map_index.get(position_key(altitude, azimuth, transient_id))

            if map_file is None and ALLOW_FUZZY_MAP_MATCH:
                map_file = find_nearest_map(
                    map_index, altitude, azimuth, transient_id
                )
                if map_file is not None:
                    print(
                        "WARNING: fuzzy matched stats row "
                        f"(alt={altitude}, az={azimuth}, id={transient_id}) "
                        f"to {map_file.name}"
                    )

            if map_file is None:
                print(
                    "WARNING: no map for stats row "
                    f"(alt={altitude}, az={azimuth}, id={transient_id})"
                )
                continue

            if map_file.stem in records:
                raise ValueError(
                    f"Multiple statistics rows matched {map_file.name} in {stats_file}"
                )

            records[map_file.stem] = TimingRecord(
                wait_time=float(row["wait_time"]),
                mapping_time=float(row["mapping_time"]),
            )

    return records


def load_source_tiles(csv_path: Path) -> dict[str, int]:
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


def experiment_paths(
    scenario: str,
    policy: str,
    fov: str,
    deadline: int,
) -> tuple[Path, Path]:
    if policy == "utility":
        root = Path(UTILITY_ROOTS[scenario].format(fov=fov))
        return (
            root / f"emsoft_maps_{deadline}",
            root / f"emsoft_stats_{deadline}.csv",
        )

    root = BASELINE_ROOTS[scenario]
    return (
        root / f"emsoft_maps_{policy}",
        root / f"emsoft_stats_{policy}.csv",
    )


def prepare_output(raw_result: Path, final_result: Path) -> None:
    for path in (raw_result, final_result):
        if path.exists():
            if not OVERWRITE:
                raise FileExistsError(
                    f"Output already exists: {path}. Set OVERWRITE = True to replace it."
                )
            path.unlink()


def run_sp_verify(
    map_file: Path,
    tiling_file: Path,
    source_tile: int,
    remaining_time: float,
    log_stream,
) -> None:
    command = [
        str(EXECUTABLE),
        str(map_file),
        str(tiling_file),
        str(source_tile),
        str(W_MAX),
        str(W_ACC),
        str(remaining_time),
        "1" if IS_DEEPSLOW else "0",
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


def run_experiment(scenario: str, policy: str, fov: str, deadline: int) -> None:
    map_dir, stats_file = experiment_paths(scenario, policy, fov, deadline)
    require_directory(map_dir, "Validation-map directory")
    require_file(stats_file, "Mapping-statistics file")

    tiling_file = TILING_DIR / f"{fov}_tiling.csv"
    source_tile_file = SOURCE_TILE_DIR / f"source_tiles_{fov}_{scenario}.csv"
    require_file(tiling_file, "Tiling file")
    source_tiles = load_source_tiles(source_tile_file)

    maps = sorted(map_dir.glob("*_map.h5"))
    if MAX_MAPS is not None:
        if MAX_MAPS <= 0:
            raise ValueError("MAX_MAPS must be positive or None.")
        maps = maps[:MAX_MAPS]
    if not maps:
        raise FileNotFoundError(f"No *_map.h5 files found in {map_dir}")

    timing_records = load_timing_records(stats_file, map_dir)
    raw_result = RESULTS_DIR / RAW_RESULT_NAME
    result_stem = f"{scenario}_{fov}_tiling_{policy}_{deadline}"
    final_result = RESULTS_DIR / f"{result_stem}.csv"
    log_file = RESULTS_DIR / "logs" / f"{result_stem}.log"
    prepare_output(raw_result, final_result)

    print(
        f"\nScenario={scenario}, policy={policy}, FoV={fov}, "
        f"deadline={deadline}, maps={len(maps)}"
    )

    completed = 0
    with log_file.open("w", encoding="utf-8") as log_stream:
        for map_file in maps:
            timing = timing_records.get(map_file.stem)
            if timing is None:
                print(f"WARNING: no timing record for {map_file.name}; skipping")
                continue

            try:
                source_tile = source_tiles[map_file.name]
            except KeyError as error:
                raise KeyError(
                    f"No source tile for {map_file.name!r} in {source_tile_file}"
                ) from error

            remaining_time = deadline - timing.wait_time - timing.mapping_time
            run_sp_verify(
                map_file,
                tiling_file,
                source_tile,
                remaining_time,
                log_stream,
            )

            completed += 1
            if completed == 1 or completed % 100 == 0:
                print(f"  completed {completed}/{len(maps)} maps", flush=True)

    if completed == 0:
        raise RuntimeError(f"No maps were evaluated for {result_stem}")
    print(f"  completed {completed}/{len(maps)} maps", flush=True)

    if not raw_result.is_file():
        raise FileNotFoundError(
            f"sp_verify did not create {raw_result}. Set the C++ out_file "
            f"to {RAW_RESULT_NAME!r}."
        )

    shutil.move(str(raw_result), str(final_result))


def main() -> int:
    require_file(EXECUTABLE, "sp_verify executable")
    require_directory(TILING_DIR, "Tiling directory")
    require_directory(SOURCE_TILE_DIR, "Validation source-tile directory")

    for scenario in SCENARIOS:
        if scenario not in DEADLINES:
            raise KeyError(f"No deadline list configured for {scenario!r}")
        if scenario not in UTILITY_ROOTS:
            raise KeyError(f"No utility root configured for {scenario!r}")
        if scenario not in BASELINE_ROOTS:
            raise KeyError(f"No baseline root configured for {scenario!r}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "logs").mkdir(parents=True, exist_ok=True)

    print(f"Scenarios: {', '.join(SCENARIOS)}")
    print(f"Policies: {', '.join(POLICIES)}")
    print(f"FoVs: {', '.join(FOVS)}")
    print(f"Results: {RESULTS_DIR}")

    for scenario in SCENARIOS:
        for policy in POLICIES:
            if policy not in {"utility", "nodeadline", "gt"}:
                raise ValueError(f"Unsupported policy: {policy!r}")
            for fov in FOVS:
                for deadline in DEADLINES[scenario]:
                    run_experiment(scenario, policy, fov, deadline)

    print("\nAll validation runs completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
