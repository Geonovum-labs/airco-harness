"""GeoJSON from an agent's map, matched to a vendored reference extract.

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


def feature_id(feature: dict) -> str:
    """The identificatie property, or the feature id when that property is absent."""
    return (feature.get("properties") or {}).get("identificatie") or feature["id"]


@dataclass(frozen=True)
class Reference:
    """Reference geometries by identificatie, in meters around `lat0`."""

    features: dict[str, BaseGeometry]
    lat0: float

    @classmethod
    @cache
    def load(cls, source: str, commit: str = "") -> Reference:
        """Load a GeoJSON file under sources/, as it was at `commit`, if given."""
        features = json.loads(sources.read(sources.path(source), commit))["features"]
        geometries = {feature_id(f): shape(f["geometry"]) for f in features}
        lat0 = sum(p.centroid.y for p in geometries.values()) / len(geometries)
        return cls({i: _metric(p, lat0) for i, p in geometries.items()}, lat0)

    def nearest(self, point: Point, tolerance_m: float) -> str | None:
        """The nearest reference geometry within tolerance_m, or None."""
        here = _metric(point, self.lat0)
        distance, identifier = min((p.distance(here), i) for i, p in self.features.items())
        return identifier if distance <= tolerance_m else None

    def assign_points(self, places: list[Point], tolerance_m: float, allowed: set[str]) -> list[str | None]:
        """Maximum one-to-one matching of places to allowed point features, with nearest candidates first."""
        candidates = []
        for place in places:
            here = _metric(place, self.lat0)
            candidates.append([i for d, i in sorted((p.distance(here), i) for i, p in self.features.items() if i in allowed)
                               if d <= tolerance_m])
        owners: dict[str, int] = {}

        def assign(index: int, seen: set[str]) -> bool:
            for identifier in candidates[index]:
                if identifier in seen:
                    continue
                seen.add(identifier)
                if identifier not in owners or assign(owners[identifier], seen):
                    owners[identifier] = index
                    return True
            return False

        for index in range(len(places)):
            assign(index, set())
        assigned = {index: identifier for identifier, index in owners.items()}
        return [assigned.get(index) or (choices[0] if choices else None) for index, choices in enumerate(candidates)]


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
