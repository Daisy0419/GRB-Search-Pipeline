#!/usr/bin/env python3
import os
import re
import csv
import h5py
import numpy as np
import pandas as pd

from astropy import units as u
from astropy.coordinates import SkyCoord, ICRS
from astropy_healpix import HEALPix


# Tiling lookup (tile_of_radec)
def load_tiling_csv_as_pix2tile(tiling_csv: str) -> dict[int, int]:
    """Read disjoint tiling.csv (ID, RA, DEC, HEALPixels) -> dict[ipix]=tile_id."""
    pix2tile: dict[int, int] = {}
    with open(tiling_csv, "r", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            tid = int(row["ID"])
            hp_str = (row.get("HEALPixels") or "").strip()
            if not hp_str:
                continue
            for x in hp_str.split():
                ip = int(x)
                prev = pix2tile.get(ip, None)
                if prev is not None and prev != tid:
                    raise ValueError(f"CSV not disjoint: ipix {ip} in tiles {prev} and {tid}")
                pix2tile[ip] = tid
    return pix2tile

class TilingIndex:
    def __init__(self, tiling_csv: str, nside: int, order: str = "nested"):
        self.nside = nside
        self.order = order.lower()
        self.frame = ICRS()
        self.hpx = HEALPix(nside=nside, order=self.order, frame=self.frame)
        self.pix2tile = load_tiling_csv_as_pix2tile(tiling_csv)

    def tile_of_radec(self, ra_deg: float, dec_deg: float) -> tuple[int, int]:
        c = SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg, frame=self.frame)
        ipix = int(self.hpx.skycoord_to_healpix(c))
        tid = int(self.pix2tile[ipix])  # assumes complete disjoint mapping
        return tid, ipix



# H5 "source" -> (ra, dec) in ICRS
def read_source_radec_from_h5(h5_path: str) -> tuple[float, float]:
    """
    Based on your inference: file stores (latitude, longitude) in ICRS.
    attribute 'source' is [lat, lon] = [dec, ra].
    """
    with h5py.File(h5_path, "r") as f:
        src = np.array(f.attrs["source"], dtype=float).ravel()
        dec_deg = float(src[0])
        ra_deg  = float(src[1])
    return ra_deg, dec_deg



def get_source_tile(
    tiling_csv: str,
    nside: int,
    maps_dir: str = "",
    order: str = "nested",
    datasets: list[str] | None = None,
):
    tiling = TilingIndex(tiling_csv, nside=nside, order=order)

    # If no explicit list, glob the maps directory
    if datasets is None:
        datasets = sorted(
            f for f in os.listdir(maps_dir) if f.endswith(".h5")
        )

    rows = []
    for ds in datasets:
        h5_path = os.path.join(maps_dir, ds) if maps_dir else ds
        ra, dec = read_source_radec_from_h5(h5_path)
        tile, ipix = tiling.tile_of_radec(ra, dec)
        rows.append({
            "map": ds,
            "RightTile": tile,
            "RightIpix": ipix,
            "RightRA": ra,
            "RightDec": dec,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    tiling = "5.36x4.5_tiling"
    # tiling = "1.34x0.9_tiling"
    # tiling = "2.5x2.5_tiling"
    # tiling = "10x6_tiling"
    tiling_csv = f"../tilings/{tiling}.csv"
    maps_prefix = "/shared/valid_tests/res_test/emsoft_maps_30"
    nside = 64

    src_res = [10, 20, 30, 40, 50]
    bkg_res = [10, 20, 30, 40, 50]
    src_res = [10]
    bkg_res = [10]

    for src_bins in src_res:
        for bkg_bins in bkg_res:
            maps_dir = f"{maps_prefix}_{src_bins}_{bkg_bins}"

            df = get_source_tile(
                tiling_csv=tiling_csv,
                nside=nside,
                maps_dir=maps_dir,
            )

            # df.to_csv(f"source_tiles_emsoft_maps_30_{src_bins}_{bkg_bins}.csv", index=False)
            df.to_csv(f"source_tiles_{tiling}_tiling.csv", index=False)
            print(df.head(10))
            # print(df.iloc[20000:20005])
            print(df.shape)

