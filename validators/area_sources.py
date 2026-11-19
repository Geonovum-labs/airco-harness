"""A block of GeoTOP reduced to the CBS buurten of Amersfoort: per buurt, the clay probability of the upper voxels of each column."""

from __future__ import annotations

import json
import re

import shapely

GEOTOP_NODATA = -127
GEOTOP_CELL = 100
# The voxels kept per column, from the top down: 6 m, so a definition of the upper 5 m can be checked one voxel either way.
UPPER_VOXELS = 12


def geotop_clay_per_buurt(ascii_kans: str, buurten_geojson: bytes) -> dict:
    """Per buurt its name and, per column whose 100 m cell has its centre in the buurt, the clay probability in percent of the upper voxels.

    `ascii_kans` is an OPeNDAP ASCII response of kans_2, whose x and y label the lower left corner of a cell. A column is keyed by its centre in RD.
    """
    features = json.loads(buurten_geojson)["features"]
    shapes = [shapely.make_valid(shapely.geometry.shape(f["geometry"])) for f in features]
    tree = shapely.STRtree(shapes)
    columns: list[dict[str, list[int]]] = [{} for _ in features]
    for m in re.finditer(r"^kans_2\.kans_2\[kans_2\.x=(\d+)\]\[kans_2\.y=(\d+)\], (.*)$", ascii_kans, re.M):
        x, y = int(m.group(1)) + GEOTOP_CELL // 2, int(m.group(2)) + GEOTOP_CELL // 2
        hit = tree.query(shapely.Point(x, y), predicate="within")
        values = [int(v) for v in m.group(3).split(",") if int(v) != GEOTOP_NODATA]
        if len(hit) and values:
            columns[hit[0]][f"{x},{y}"] = values[::-1][:UPPER_VOXELS]
    return {f["id"]: {"naam": f["properties"]["naam"], "kolommen": dict(sorted(c.items()))} for f, c in zip(features, columns)}
