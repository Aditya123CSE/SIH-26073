"""
Automated Verification & Test Suite for VAYU-GUARD (SIH 26073)
Validates all 4 quality tiers, disambiguation logic, self-healing imputation, and REST endpoints.
"""

import sys
import unittest
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi.testclient import TestClient

import ml_engine
import data_generator
import backend_server
from backend_server import app, qc_pipeline


class TestVayuGuardSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 60)
        print("RUNNING VAYU-GUARD AUTOMATED VERIFICATION SUITE")
        print("=" * 60)
        backend_server.initialize_system(force_live=False)

    def test_01_tier1_physical_boundary_check(self):
        """Test physical and thermodynamic range enforcement with ISA elevation-awareness."""
        checker = ml_engine.PhysicalConstraintChecker()

        # 1. Extreme temperature impossible spike
        viol, reasons = checker.check({"temperature": 68.0, "humidity": 45.0})
        self.assertTrue(viol)
        self.assertTrue(any("temperature" in r for r in reasons))

        # 2. High-Altitude Himalayan AWS (Leh Ladakh, elevation 3524m, typical P = 683.6 hPa)
        # Should NOT trigger false physical alarm under elevation-aware ISA model
        viol_leh, reasons_leh = checker.check({"pressure": 683.6, "elevation_m": 3524, "temperature": 12.0, "humidity": 30.0})
        self.assertFalse(viol_leh)

        # 3. Impossible nocturnal solar radiation
        viol, reasons = checker.check({"solar_radiation": 450.0, "hour": 23})
        self.assertTrue(viol)
        self.assertTrue(any("solar" in r.lower() for r in reasons))

        # 4. Heavy rain with severe arid humidity
        viol, reasons = checker.check({"precipitation": 25.0, "humidity": 14.0})
        self.assertTrue(viol)
        self.assertTrue(any("rain" in r.lower() for r in reasons))

        # 5. Valid normal observation
        viol, reasons = checker.check({"temperature": 32.0, "humidity": 55.0, "pressure": 1005.0, "solar_radiation": 600.0, "hour": 12})
        self.assertFalse(viol)
        print("  ✓ Tier-1 Physical & Elevation-Aware ISA Rules: PASSED")

    def test_02_tier2_temporal_flatline_and_jump(self):
        """Test temporal flatline and step-jump detection."""
        detector = ml_engine.TemporalAnomalyDetector()

        # Flatline test (constant sensor value)
        frozen_vals = [28.4, 28.4, 28.4, 28.4, 28.4, 28.4]
        self.assertTrue(detector.detect_flatline(frozen_vals))

        # Dynamic series test (not flatline)
        varying_vals = [28.1, 28.3, 28.6, 28.9, 29.2, 29.5]
        self.assertFalse(detector.detect_flatline(varying_vals))

        # Sudden unphysical step jump
        jump_detected, delta = detector.detect_step_jump(current_val=38.0, prev_val=27.0, sensor="temperature")
        self.assertTrue(jump_detected)
        self.assertEqual(delta, 11.0)
        print("  ✓ Tier-2 Temporal Flatline & Rate-of-Change: PASSED")

    def test_03_tier3_multivariate_ml_ensemble(self):
        """Test Isolation Forest and Mahalanobis distance on correlation breakdown."""
        normal_pkt = {
            "temperature": 32.0,
            "humidity": 55.0,
            "pressure": 985.0,
            "wind_speed": 4.0,
            "solar_radiation": 650.0
        }
        is_anom, iforest_score, mahalanobis_dist, devs = qc_pipeline.tier3_ml.score_sample(normal_pkt)
        self.assertFalse(is_anom)

        # Corrupted multivariate pattern (impossible joint distribution: 48°C + 98% RH + 1030 hPa + 0 solar at noon)
        corrupted_pkt = {
            "temperature": 48.0,
            "humidity": 98.0,
            "pressure": 1030.0,
            "wind_speed": 0.1,
            "solar_radiation": 5.0
        }
        is_anom, iforest_score, mahalanobis_dist, devs = qc_pipeline.tier3_ml.score_sample(corrupted_pkt)
        self.assertTrue(is_anom)
        self.assertGreater(mahalanobis_dist, 3.0)
        print("  ✓ Tier-3 Multivariate ML & Isolation Forest: PASSED")

    def test_04_tier4_spatial_consistency(self):
        """Test spatial neighbor consensus cross-validation."""
        validator = ml_engine.SpatialNeighborValidator()

        target = {"station_id": "DEL01", "latitude": 28.584, "longitude": 77.206, "temperature": 44.5}
        neighbors = [
            {"station_id": "DEL02", "latitude": 28.566, "longitude": 77.098, "temperature": 32.0},
            {"station_id": "DEL03", "latitude": 28.472, "longitude": 77.127, "temperature": 31.8},
            {"station_id": "DEL04", "latitude": 28.591, "longitude": 77.228, "temperature": 32.2}
        ]
        is_anom, dev, reasons = validator.validate_station(target, neighbors, sensor="temperature")
        self.assertTrue(is_anom)
        self.assertGreater(dev, 10.0)
        print("  ✓ Tier-4 Spatial Neighbor Cross-Validation: PASSED")

    def test_05_severe_weather_disambiguation(self):
        """Test distinction between genuine atmospheric storm and sensor failure."""
        disambiguator = ml_engine.SevereWeatherDisambiguator()

        prev_rec = {"temperature": 34.0, "pressure": 988.0, "wind_speed": 3.0, "precipitation": 0.0}
        curr_squall = {"temperature": 27.5, "pressure": 985.8, "wind_speed": 18.5, "precipitation": 12.0}
        neighbors = [{"wind_speed": 15.0, "precipitation": 8.0}]

        is_legit, note = disambiguator.evaluate(curr_squall, prev_rec, neighbors)
        self.assertTrue(is_legit)
        self.assertIn("severe", note.lower())
        print("  ✓ Severe Weather vs. Sensor Failure Disambiguator: PASSED")

    def test_06_self_healing_imputation(self):
        """Test that corrupted sensor values are reconstructed within realistic physical bounds."""
        record = {"temperature": 75.0, "humidity": 60.0, "pressure": 985.0, "wind_speed": 4.0, "solar_radiation": 700.0}
        imputed_temp = qc_pipeline.imputer.impute_sensor("temperature", record, neighbor_stations=[])
        self.assertGreaterEqual(imputed_temp, -15.0)
        self.assertLessEqual(imputed_temp, 55.0)
        print(f"  ✓ Self-Healing ML Imputer (Reconstructed {record['temperature']}°C -> {imputed_temp:.1f}°C): PASSED")

    def test_07_rest_api_endpoints(self):
        """Test full REST API integration, healthz, and jury evaluation aliases via TestClient."""
        with TestClient(app) as client:
            # 1. Standard Kubernetes / jury healthz probe
            res = client.get("/healthz")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "healthy")

            # 2. Stats health alias
            res = client.get("/api/stats/health")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "healthy")

            # 3. Summary
            res = client.get("/api/network/summary")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("network_trust_index", data)

            # 4. Stations list
            res = client.get("/api/stations")
            self.assertEqual(res.status_code, 200)
            stations = res.json()
            self.assertGreaterEqual(len(stations), 8)

            # 5. Telemetry time series
            res = client.get("/api/telemetry/DEL01")
            self.assertEqual(res.status_code, 200)
            tel_data = res.json()
            self.assertIn("telemetry", tel_data)

            # 6. Simulation fault injection alias (/api/simulate/fault)
            res = client.post("/api/simulate/fault", json={
                "station_id": "DEL01",
                "fault_type": "drift",
                "parameter": "air_temperature_c",
                "magnitude": 5.0
            })
            self.assertEqual(res.status_code, 200)
            inj_data = res.json()
            self.assertEqual(inj_data["status"], "success")

            # 7. Simulation reset
            res = client.post("/api/simulate/reset", json={"station_id": "DEL01"})
            self.assertEqual(res.status_code, 200)
            print("  ✓ REST API Integration, Healthz & Fault Simulation Aliases: PASSED")


if __name__ == "__main__":
    unittest.main(verbosity=1)
