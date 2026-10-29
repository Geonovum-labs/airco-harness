"""GeoJSON from an agent's map, matched to the panden of a vendored BAG extract.

Coordinates are WGS84 longitude, latitude, as GeoJSON requires, and the extract
is fetched in WGS84 too, so nothing is reprojected. Distances use a local
equirectangular projection around the extract, accurate to well under a meter
at city scale.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import cache

import shapely
from shapely.errors import ShapelyError
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from . import sources

NETHERLANDS = (3.2, 50.7, 7.3, 53.6)  # lon/lat bounding box, to recognize swapped coordinates
METERS_PER_DEGREE = 111_320


@dataclass(frozen=True)
class Reference:
    """Pand polygons by identificatie, in meters around `lat0`."""

    panden: dict[str, BaseGeometry]
    lat0: float

    @classmethod
    @cache
    def load(cls, source: str) -> Reference:
        """`source` is a GeoJSON file under sources/ with the identificatie of each pand in its properties."""
        features = json.loads(sources.path(source).read_text(encoding="utf-8"))["features"]
        polygons = {f["properties"]["identificatie"]: shape(f["geometry"]) for f in features}
        lat0 = sum(p.centroid.y for p in polygons.values()) / len(polygons)
        return cls({i: _metric(p, lat0) for i, p in polygons.items()}, lat0)

    def nearest(self, point: Point, tolerance_m: float) -> str | None:
        """The pand that contains the WGS84 point, else the nearest pand within tolerance_m, else None."""
        here = _metric(point, self.lat0)
        distance, pand = min((p.distance(here), i) for i, p in self.panden.items())
        return pand if distance <= tolerance_m else None


def _metric(geometry: BaseGeometry, lat0: float) -> BaseGeometry:
    scale = (METERS_PER_DEGREE * math.cos(math.radians(lat0)), METERS_PER_DEGREE)
    return shapely.transform(geometry, lambda lonlat: lonlat * scale)


def points(geojson: object) -> list[Point]:
    """One point per geometry part of a FeatureCollection, Feature or geometry: the point
    itself, or the representative point of a line or polygon. ValueError when it is none of these."""
    if not isinstance(geojson, dict):
        raise ValueError("GeoJSON must be an object")
    kind = geojson.get("type")
    if kind == "FeatureCollection":
        features = geojson.get("features")
        if not isinstance(features, list):
            raise ValueError("a FeatureCollection needs a list of features")
        return [p for f in features for p in points(f)]
    if kind == "Feature":
        return points(geojson["geometry"]) if geojson.get("geometry") else []
    try:
        geometry = shape(geojson)
    except (ShapelyError, ValueError, TypeError, KeyError, IndexError, AttributeError) as error:
        raise ValueError(f"not a GeoJSON geometry: {error}") from error
    parts = geometry.geoms if isinstance(geometry, BaseMultipartGeometry) else [geometry]
    return [p if isinstance(p, Point) else p.representative_point() for p in parts if not p.is_empty]


def swapped(point: Point) -> bool:
    """The point lies outside the Netherlands, but would lie inside with longitude and latitude swapped."""
    west, south, east, north = NETHERLANDS

    def inside(lon: float, lat: float) -> bool:
        return west <= lon <= east and south <= lat <= north

    return not inside(point.x, point.y) and inside(point.y, point.x)
