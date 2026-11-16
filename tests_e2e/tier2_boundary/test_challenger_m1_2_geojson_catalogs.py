"""Empirical Challenge Test Suite: GeoJSON Spatial Integrity and Catalogs Concordance.

Assigned to: challenger_m1_2
Objective: Empirically verify:
1. RFC 7946 Section 3.1.6 polygon ring orientation (exterior rings MUST be counterclockwise, CCW).
2. RFC 7946 Section 3.1.1 coordinate ordering [longitude, latitude].
3. Geographic bounding box strictly within Maturín / Monagas limits (Lon [-64.0, -62.5], Lat [9.0, 10.2]).
4. Linear ring closure (coords[0] == coords[-1]) and minimum 4 points.
5. Absence of self-intersections (simple polygons).
6. 100% 1-to-1 parish matching between GeoJSON, catalogs/parroquias.json, and PROJECT.md.
7. Semantic consistency of catalogs (modos_transporte, motivos_viaje) across schema, catalogs, and contracts.
"""

import json
from pathlib import Path
import unittest
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "shared" / "geojson" / "maturin_parroquias.geojson"
CATALOG_PARROQUIAS_PATH = PROJECT_ROOT / "shared" / "catalogs" / "parroquias.json"
CATALOG_MODOS_PATH = PROJECT_ROOT / "shared" / "catalogs" / "modos_transporte.json"
CATALOG_MOTIVOS_PATH = PROJECT_ROOT / "shared" / "catalogs" / "motivos_viaje.json"
SCHEMA_PATH = PROJECT_ROOT / "shared" / "schemas" / "pdul_origen_destino.json"

OFFICIAL_PARROQUIAS_11 = [
    "alto_de_los_godos",
    "boqueron",
    "las_cocuizas",
    "la_cruz",
    "san_simon",
    "santa_cruz",
    "el_corozo",
    "el_furrial",
    "jusepin",
    "la_pica",
    "san_vicente",
]


def signed_polygon_area(ring: List[List[float]]) -> float:
    """Computes signed area of a 2D planar polygon ring using the shoelace formula.
    
    Positive area (> 0) indicates Counter-Clockwise (CCW) winding.
    Negative area (< 0) indicates Clockwise (CW) winding.
    RFC 7946 Section 3.1.6 requires exterior rings to be CCW (signed_area > 0).
    """
    area = 0.0
    n = len(ring)
    for i in range(n - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        area += (x1 * y2 - x2 * y1)
    return area / 2.0


def _ccw_triplet(a: List[float], b: List[float], c: List[float]) -> bool:
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    p1: List[float], p2: List[float], p3: List[float], p4: List[float]
) -> bool:
    """Returns True if line segment p1-p2 intersects p3-p4 (excluding shared endpoints)."""
    return (
        _ccw_triplet(p1, p3, p4) != _ccw_triplet(p2, p3, p4)
        and _ccw_triplet(p1, p2, p3) != _ccw_triplet(p1, p2, p4)
    )


class TestGeoJsonSpatialIntegrityEmpirical(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assertTrue(GEOJSON_PATH.exists(), f"GeoJSON missing at {GEOJSON_PATH}")
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            cls.geojson = json.load(f)

        cls.assertTrue(CATALOG_PARROQUIAS_PATH.exists(), f"Catalog missing at {CATALOG_PARROQUIAS_PATH}")
        with open(CATALOG_PARROQUIAS_PATH, "r", encoding="utf-8") as f:
            cls.catalog_parroquias = json.load(f)

    def test_geojson_01_feature_count_and_types(self) -> None:
        """Verifies GeoJSON is FeatureCollection with exactly 11 Polygon features."""
        self.assertEqual(self.geojson.get("type"), "FeatureCollection")
        features = self.geojson.get("features", [])
        self.assertEqual(len(features), 11, f"Expected 11 features, got {len(features)}")
        for i, feat in enumerate(features):
            self.assertEqual(feat.get("type"), "Feature")
            geom = feat.get("geometry", {})
            self.assertEqual(geom.get("type"), "Polygon", f"Feature {i} is not Polygon")

    def test_geojson_02_coordinate_order_rfc7946_lon_lat(self) -> None:
        """Verifies coordinate ordering is strictly [longitude, latitude] in decimal degrees.
        
        Maturín longitude is around -63.5 to -62.9 (negative East-West).
        Maturín latitude is around 9.5 to 9.85 (positive North-South).
        """
        for feat in self.geojson["features"]:
            code = feat["properties"]["codigo_parroquia"]
            for ring in feat["geometry"]["coordinates"]:
                for pt in ring:
                    self.assertEqual(len(pt), 2, f"Point {pt} in {code} does not have length 2")
                    lon, lat = pt[0], pt[1]
                    self.assertLess(lon, 0.0, f"Longitude must be negative in Monagas/Venezuela: {lon} in {code}")
                    self.assertGreater(lat, 0.0, f"Latitude must be positive in Monagas/Venezuela: {lat} in {code}")
                    self.assertGreaterEqual(lon, -64.5, f"Longitude {lon} too far west")
                    self.assertLessEqual(lon, -62.0, f"Longitude {lon} too far east")
                    self.assertGreaterEqual(lat, 8.5, f"Latitude {lat} too far south")
                    self.assertLessEqual(lat, 11.0, f"Latitude {lat} too far north")

    def test_geojson_03_coordinate_bounds_within_maturin(self) -> None:
        """Verifies all polygon vertices are strictly bounded within Maturín limits.
        
        Expected bounding box: Lon [-64.0, -62.5], Lat [9.0, 10.2].
        """
        min_lon, max_lon = float("inf"), float("-inf")
        min_lat, max_lat = float("inf"), float("-inf")

        for feat in self.geojson["features"]:
            for ring in feat["geometry"]["coordinates"]:
                for pt in ring:
                    min_lon = min(min_lon, pt[0])
                    max_lon = max(max_lon, pt[0])
                    min_lat = min(min_lat, pt[1])
                    max_lat = max(max_lat, pt[1])

        self.assertGreaterEqual(min_lon, -64.0)
        self.assertLessEqual(max_lon, -62.5)
        self.assertGreaterEqual(min_lat, 9.0)
        self.assertLessEqual(max_lat, 10.2)

    def test_geojson_04_ring_closure_and_minimum_points(self) -> None:
        """Verifies each ring is closed (ring[0] == ring[-1]) and has >= 4 points."""
        for feat in self.geojson["features"]:
            code = feat["properties"]["codigo_parroquia"]
            for ring_idx, ring in enumerate(feat["geometry"]["coordinates"]):
                self.assertGreaterEqual(
                    len(ring), 4, f"Ring {ring_idx} in {code} has fewer than 4 points"
                )
                self.assertEqual(
                    ring[0], ring[-1], f"Ring {ring_idx} in {code} is not closed: {ring[0]} != {ring[-1]}"
                )

    def test_geojson_05_no_self_intersections(self) -> None:
        """Verifies polygon rings are simple and do not self-intersect."""
        for feat in self.geojson["features"]:
            code = feat["properties"]["codigo_parroquia"]
            for ring in feat["geometry"]["coordinates"]:
                n = len(ring) - 1
                for i in range(n):
                    for j in range(i + 2, n):
                        if i == 0 and j == n - 1:
                            continue
                        p1, p2 = ring[i], ring[i + 1]
                        p3, p4 = ring[j], ring[j + 1]
                        self.assertFalse(
                            segments_intersect(p1, p2, p3, p4),
                            f"Self-intersection detected in {code} between segment {i} and {j}",
                        )

    def test_geojson_06_parish_1_to_1_crossmatch(self) -> None:
        """Verifies 100% 1-to-1 matching across GeoJSON, catalog, and PROJECT.md."""
        geojson_codes = [f["properties"].get("codigo_parroquia") for f in self.geojson["features"]]
        catalog_codes = [p.get("codigo") for p in self.catalog_parroquias]

        self.assertEqual(len(geojson_codes), 11)
        self.assertEqual(len(set(geojson_codes)), 11)
        self.assertEqual(set(geojson_codes), set(OFFICIAL_PARROQUIAS_11))
        self.assertEqual(set(catalog_codes), set(OFFICIAL_PARROQUIAS_11))

    def test_geojson_07_rfc7946_right_hand_rule_ring_orientation(self) -> None:
        """CRITICAL CHALLENGE: Verifies exterior rings follow RFC 7946 right-hand rule.
        
        RFC 7946 Section 3.1.6:
        "A linear ring MUST follow the right-hand rule with respect to the area it bounds,
        i.e., exterior rings are counterclockwise, and holes are clockwise."
        
        Exterior ring signed area must be strictly POSITIVE (> 0).
        """
        violations = []
        for feat in self.geojson["features"]:
            code = feat["properties"].get("codigo_parroquia")
            coords = feat["geometry"]["coordinates"]
            exterior_ring = coords[0]
            s_area = signed_polygon_area(exterior_ring)
            if s_area <= 0:
                violations.append((code, s_area))

        self.assertEqual(
            len(violations),
            0,
            f"RFC 7946 Right-Hand Rule VIOLATION: {len(violations)} of {len(self.geojson['features'])} "
            f"exterior rings are wound CLOCKWISE (negative signed area) instead of COUNTER-CLOCKWISE: {violations}",
        )


class TestCatalogsConcordanceEmpirical(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(CATALOG_MODOS_PATH, "r", encoding="utf-8") as f:
            cls.modos = json.load(f)
        with open(CATALOG_MOTIVOS_PATH, "r", encoding="utf-8") as f:
            cls.motivos = json.load(f)
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)

    def test_catalog_01_modos_transporte_8_items(self) -> None:
        """Verifies catalog has 8 transport modes with codes '1' through '8'."""
        self.assertEqual(len(self.modos), 8)
        codes = {m["codigo"] for m in self.modos}
        self.assertEqual(codes, {str(i) for i in range(1, 9)})

    def test_catalog_02_modos_transporte_matches_survey_schema(self) -> None:
        """Verifies catalog matches options defined in schema's modo_principal."""
        # Find modo_principal in schema
        def find_comp(node, key):
            if isinstance(node, dict):
                if node.get("key") == key:
                    return node
                for v in node.values():
                    r = find_comp(v, key)
                    if r: return r
            elif isinstance(node, list):
                for item in node:
                    r = find_comp(item, key)
                    if r: return r
            return None

        comp = find_comp(self.schema, "modo_principal")
        self.assertIsNotNone(comp, "modo_principal not found in schema")
        schema_values = comp.get("data", {}).get("values", [])
        self.assertEqual(len(schema_values), 8)

        for cat_item, schema_item in zip(self.modos, schema_values):
            self.assertEqual(str(cat_item["codigo"]), str(schema_item["value"]))
            self.assertEqual(cat_item["label"], schema_item["label"])

    def test_catalog_03_motivos_viaje_matches_survey_schema(self) -> None:
        """Verifies motivos_viaje catalog matches options in schema's motivo_viaje."""
        def find_comp(node, key):
            if isinstance(node, dict):
                if node.get("key") == key:
                    return node
                for v in node.values():
                    r = find_comp(v, key)
                    if r: return r
            elif isinstance(node, list):
                for item in node:
                    r = find_comp(item, key)
                    if r: return r
            return None

        comp = find_comp(self.schema, "motivo_viaje")
        self.assertIsNotNone(comp, "motivo_viaje not found in schema")
        schema_values = comp.get("data", {}).get("values", [])
        self.assertEqual(len(schema_values), 8)

        for cat_item, schema_item in zip(self.motivos, schema_values):
            self.assertEqual(str(cat_item["codigo"]), str(schema_item["value"]))
            self.assertEqual(cat_item["label"], schema_item["label"])

    def test_catalog_04_modos_transporte_concordance_with_project_contract(self) -> None:
        """Verifies catalog concordance against PROJECT.md Interface Contract line 151.
        
        PROJECT.md line 151 states:
        'Claves numéricas "1" (A pie), "2" (Bicicleta), "3" (Motocicleta), "4" (Automóvil particular),
        "5" (Taxi), "6" (Transporte público - bus/buseta), "7" (Transporte informal - por puesto/mototaxi), "8" (Otro).'
        And shared/catalogs/modos_transporte.json defines the same official municipal survey mode codes.
        """
        project_contract_modes = {
            "1": "A pie",
            "2": "Bicicleta",
            "3": "Motocicleta",
            "4": "Automóvil Particular",
            "5": "Taxi",
            "6": "Transporte público",
            "7": "Transporte informal",
            "8": "Otro",
        }
        catalog_dict = {m["codigo"]: m["nombre"] for m in self.modos}
        mismatches = []
        for code, expected_name in project_contract_modes.items():
            actual_name = catalog_dict.get(code, "")
            # Check semantic match
            if expected_name.lower() not in actual_name.lower() and actual_name.lower() not in expected_name.lower():
                mismatches.append(f"Code '{code}': PROJECT.md expects '{expected_name}', catalog has '{actual_name}'")

        self.assertEqual(
            len(mismatches),
            0,
            f"INTERFACE CONTRACT CONFLICT: shared/catalogs/modos_transporte.json contradicts PROJECT.md line 151: {mismatches}",
        )



if __name__ == "__main__":
    unittest.main()
