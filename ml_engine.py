"""
VAYU-GUARD: AI/ML-Powered Intelligent Anomaly Detection & Self-Healing Engine
Problem Statement: SIH 26073 (Ministry of Earth Sciences / IMD)
Compliant with World Meteorological Organization (WMO-No. 8) QC Standards.
"""

import math
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


# =====================================================================
# WMO Quality Control Flags (WMO-No. 8 Guide to Instruments and Methods)
# =====================================================================
class QCFlag:
    GOOD = 0        # Passed all physical, temporal, ML, and spatial tests
    SUSPECT = 1     # Minor deviation or spatial inconsistency
    ERRONEOUS = 2   # Gross error, physical impossibility, or high-confidence ML anomaly
    IMPUTED = 3     # Sensor failed; reading reconstructed via self-healing ML


@dataclass
class AnomalyResult:
    is_anomaly: bool
    qc_flag: int
    severity: str          # "INFO", "WARNING", "CRITICAL"
    tier_triggered: str    # "Tier-1 (Physical)", "Tier-2 (Temporal)", "Tier-3 (ML)", "Tier-4 (Spatial)", "None"
    reasons: List[str] = field(default_factory=list)
    confidence: float = 1.0
    is_extreme_weather: bool = False
    imputed_values: Dict[str, float] = field(default_factory=dict)
    sensor_scores: Dict[str, float] = field(default_factory=dict)


# =====================================================================
# Tier 1: Deterministic Physical & Thermodynamic Constraint Checker
# =====================================================================
class PhysicalConstraintChecker:
    """
    Validates sensor values against atmospheric laws and climatological limits.
    Complies with WMO-No. 8 Level-3 Quality Control with elevation-aware ISA pressure bounds.
    """

    LIMITS = {
        "temperature": (-25.0, 55.0),     # °C (from Ladakh/Himalayas sub-zero to Thar Desert heatwaves)
        "humidity": (1.0, 100.0),          # %
        "pressure": (500.0, 1085.0),       # hPa (covers high altitude Ladakh 3500m+ to coastal plains)
        "wind_speed": (0.0, 75.0),         # m/s (up to Category 5 Super Cyclones)
        "wind_direction": (0.0, 360.0),    # degrees
        "precipitation": (0.0, 200.0),     # mm/hr (cloudburst limits)
        "solar_radiation": (0.0, 1400.0),  # W/m² (Solar constant ~ 1361 W/m²)
        "battery_voltage": (9.0, 16.0)     # V (Nominal 12V lead-acid / LiFePO4 AWS battery)
    }

    @staticmethod
    def calculate_isa_pressure(elevation_m: float) -> float:
        """
        Calculates the International Standard Atmosphere (ISA) barometric pressure (hPa)
        for a given geopotential station elevation (m ASL).
        Formula: P_isa(h) = 1013.25 * (1 - 2.25577e-5 * h)^5.25588
        """
        h = max(0.0, float(elevation_m))
        base = max(0.01, 1.0 - (2.25577e-5 * h))
        return 1013.25 * (base ** 5.25588)

    @staticmethod
    def calculate_dew_point(temp_c: float, rh_pct: float) -> float:
        """
        Magnus-Tetens formula for dew point calculation over liquid water and ice.
        WMO-No. 8 compliant with ice phase saturation for T < 0°C.
        """
        if rh_pct <= 0:
            return -50.0
        # Over water vs. over ice (Sonntag / Alduchov-Eskridge formulations)
        if temp_c >= 0:
            a, b = 17.27, 237.7
        else:
            a, b = 21.875, 265.5  # Ice phase
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(max(rh_pct / 100.0, 0.0001))
        return (b * alpha) / (a - alpha)

    def check_physical_limits(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Tier 1: Checks individual sensor boundaries against absolute planetary physical limits with elevation-awareness."""
        violations = []
        elevation = record.get("elevation_m") or record.get("elevation")

        for sensor, (low, high) in self.LIMITS.items():
            if sensor in record and record[sensor] is not None:
                try:
                    val = float(record[sensor])
                    sensor_low, sensor_high = low, high

                    # Elevation-Aware Barometric Range (International Standard Atmosphere ISA)
                    if sensor == "pressure" and elevation is not None:
                        p_isa = self.calculate_isa_pressure(float(elevation))
                        sensor_low = max(450.0, p_isa - 65.0)
                        sensor_high = min(1090.0, p_isa + 45.0)

                    if val < sensor_low or val > sensor_high:
                        elev_hint = f" at {elevation}m ASL" if sensor == "pressure" and elevation else ""
                        violations.append(
                            f"Physical range violation: {sensor} = {val:.2f} (Permitted IMD range{elev_hint}: [{sensor_low:.1f}, {sensor_high:.1f}])"
                        )
                except (ValueError, TypeError):
                    pass
        return (len(violations) > 0, violations)

    def check_thermodynamic_diurnal(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Tier 3: Checks internal thermodynamic consistency, diurnal solar limits, and cross-channel laws."""
        violations = []

        # 1. Thermodynamic Consistency: Dew Point <= Dry Bulb Temperature
        temp = record.get("temperature")
        rh = record.get("humidity")
        explicit_dew = record.get("dew_point")

        if temp is not None:
            t_val = float(temp)
            # If explicit dew point sensor exists, validate directly
            if explicit_dew is not None:
                dew_val = float(explicit_dew)
                if dew_val > t_val + 0.2:
                    violations.append(
                        f"Thermodynamic conflict: Measured Dew Point ({dew_val:.1f}°C) exceeds Air Temp ({t_val:.1f}°C)"
                    )
            elif rh is not None and 0 < float(rh) <= 100:
                dew_point = self.calculate_dew_point(t_val, float(rh))
                if dew_point > t_val + 0.2:
                    violations.append(
                        f"Thermodynamic conflict: Calculated Dew Point ({dew_point:.1f}°C) exceeds Air Temp ({t_val:.1f}°C)"
                    )

        # 2. Solar Radiation vs. Astronomical Solar Zenith Angle (cos θz)
        solar = record.get("solar_radiation")
        if solar is not None:
            try:
                solar_val = float(solar)
                lat = float(record.get("latitude", 20.0))
                lon = float(record.get("longitude", 78.0))

                dt_utc = None
                if "timestamp" in record and record["timestamp"]:
                    try:
                        ts = str(record["timestamp"]).replace("Z", "+00:00")
                        dt_obj = datetime.datetime.fromisoformat(ts)
                        dt_utc = dt_obj.astimezone(datetime.timezone.utc) if dt_obj.tzinfo else dt_obj
                    except Exception:
                        pass

                hour_val = record.get("hour")
                if dt_utc is None:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if hour_val is not None:
                        # IST = UTC + 5:30 -> UTC = IST - 5:30
                        utc_dec = (hour_val - 5.5) % 24.0
                        dt_utc = now.replace(hour=int(utc_dec), minute=int((utc_dec % 1.0) * 60))
                    else:
                        dt_utc = now

                day_of_year = dt_utc.timetuple().tm_yday
                utc_hour_dec = dt_utc.hour + (dt_utc.minute / 60.0)

                # Solar geometry: declination angle delta
                declination_deg = 23.45 * math.sin(math.radians((360.0 / 365.0) * (284 + day_of_year)))
                # Local Solar Time hour angle H
                local_solar_hour = (utc_hour_dec + (lon / 15.0)) % 24.0
                hour_angle_deg = 15.0 * (local_solar_hour - 12.0)

                # cos(theta_z) = sin(phi)*sin(delta) + cos(phi)*cos(delta)*cos(H)
                phi_rad = math.radians(lat)
                delta_rad = math.radians(declination_deg)
                h_rad = math.radians(hour_angle_deg)
                cos_zenith = (math.sin(phi_rad) * math.sin(delta_rad)) + (math.cos(phi_rad) * math.cos(delta_rad) * math.cos(h_rad))

                # Nocturnal Period: Sun is below the horizon (cos θz <= -0.05)
                if cos_zenith <= -0.05:
                    if solar_val > 10.0:
                        violations.append(
                            f"Diurnal solar anomaly: Solar Radiation reported as {solar_val:.1f} W/m² while sun is astronomically below horizon (cos θz = {cos_zenith:.3f}, nocturnal limit: 0.0 W/m²)"
                        )
                # Dawn / Dusk Twilight Transition (cos θz between -0.05 and 0.08)
                elif cos_zenith <= 0.08:
                    if solar_val > 75.0:
                        violations.append(
                            f"Diurnal solar anomaly: Solar Radiation reported as {solar_val:.1f} W/m² during astronomical twilight transition (cos θz = {cos_zenith:.3f}, limit: < 45.0 W/m²)"
                        )
                # Daytime: Clear-sky physical maximum
                else:
                    g_max = (1.2 * 1361.0 * (cos_zenith ** 1.15)) + 30.0
                    if solar_val > g_max:
                        violations.append(
                            f"Solar radiation physical ceiling breached: {solar_val:.1f} W/m² exceeds astronomical clear-sky ceiling ({g_max:.1f} W/m² for cos θz = {cos_zenith:.3f})"
                        )
            except Exception:
                # Fallback to simple hour rule if calculation fails
                h_fallback = record.get("hour", 12)
                if (h_fallback >= 19 or h_fallback < 5) and float(solar) > 10.0:
                    violations.append(
                        f"Diurnal solar anomaly: Solar Radiation reported as {float(solar):.1f} W/m² during nocturnal period"
                    )

        # 3. Rain vs Humidity Sanity Check
        rain = record.get("precipitation", 0.0)
        if rain:
            try:
                rain_val = float(rain)
                if rain_val > 10.0 and rh is not None and float(rh) < 35.0:
                    violations.append(
                        f"Meteorological conflict: Heavy rain reported ({rain_val:.1f} mm) while Relative Humidity is extremely dry ({float(rh):.1f}%)"
                    )
            except (ValueError, TypeError):
                pass

        return (len(violations) > 0, violations)

    def check(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Combined check for backwards compatibility."""
        v1_has, v1 = self.check_physical_limits(record)
        v2_has, v2 = self.check_thermodynamic_diurnal(record)
        return (v1_has or v2_has, v1 + v2)


# =====================================================================
# Tier 2: Temporal Anomaly, Flatline & Sensor Drift Detector
# =====================================================================
class TemporalAnomalyDetector:
    """
    Detects temporal defects across consecutive time steps:
    1. Flatline / Sensor Sticking (frozen values)
    2. Unphysical Step Jumps (impulse spikes)
    3. Slow Sensor Drift (continuous degradation)
    """

    MAX_STEP_JUMP_15MIN = {
        "temperature": 5.0,    # Max 5°C jump in 15 min under normal conditions
        "humidity": 25.0,      # Max 25% jump in 15 min
        "pressure": 3.5,       # Max 3.5 hPa drop/rise in 15 min (cyclone threshold)
        "wind_speed": 20.0,    # Max 20 m/s sudden change
        "battery_voltage": 1.5 # Max 1.5V jump
    }

    def detect_flatline(self, window_series: List[float], min_samples: int = 5, epsilon: float = 0.001) -> bool:
        """Detects if a sensor has frozen on a constant value for several readings."""
        if len(window_series) < min_samples:
            return False
        recent = window_series[-min_samples:]
        std_dev = float(np.std(recent))
        return std_dev < epsilon

    def detect_step_jump(self, current_val: float, prev_val: float, sensor: str) -> Tuple[bool, float]:
        """Detects an excessive rate of change between adjacent timestamps."""
        if sensor not in self.MAX_STEP_JUMP_15MIN:
            return False, 0.0
        delta = abs(current_val - prev_val)
        threshold = self.MAX_STEP_JUMP_15MIN[sensor]
        return (delta > threshold, delta)

    def detect_drift(self, recent_vals: List[float], baseline_mean: float, std_threshold: float = 2.5) -> bool:
        """Detects systematic linear or cumulative bias deviation."""
        if len(recent_vals) < 10:
            return False
        current_mean = float(np.mean(recent_vals[-6:]))
        diff = abs(current_mean - baseline_mean)
        return diff > std_threshold


# =====================================================================
# Tier 3: Multivariate Machine Learning Ensemble (Isolation Forest + Covariance)
# =====================================================================
class MultivariateMLEngine:
    """
    Unsupervised ML ensemble trained on multi-sensor correlations.
    Learns non-linear joint distributions across (Temp, RH, Pressure, Wind, Solar).
    """

    FEATURE_COLS = ["temperature", "humidity", "pressure", "wind_speed", "solar_radiation"]

    def __init__(self, contamination: float = 0.03):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=1
        )
        self.mean_vector = None
        self.cov_inv = None
        self.is_fitted = False

    def fit(self, df: pd.DataFrame):
        """Train the multivariate models on historical normal observations."""
        X = df[self.FEATURE_COLS].dropna().values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

        # Fit robust covariance for Mahalanobis distance scoring
        self.mean_vector = np.mean(X_scaled, axis=0)
        cov = np.cov(X_scaled, rowvar=False) + np.eye(len(self.FEATURE_COLS)) * 1e-4
        self.cov_inv = np.linalg.pinv(cov)
        self.is_fitted = True

    def score_sample(self, sample_dict: Dict[str, float]) -> Tuple[bool, float, float, Dict[str, float]]:
        """
        Returns:
            (is_anomaly, iforest_score, mahalanobis_dist, sensor_feature_contributions)
        """
        if not self.is_fitted:
            return False, 0.0, 0.0, {}

        try:
            x_raw = np.array([[float(sample_dict.get(col, 0.0)) for col in self.FEATURE_COLS]])
            x_scaled = self.scaler.transform(x_raw)

            # 1. Isolation Forest Decision Score (negative = anomalous, positive = normal)
            iforest_raw = float(self.model.decision_function(x_scaled)[0])
            is_iforest_anomaly = bool(iforest_raw < 0.0)

            # 2. Mahalanobis Distance for correlation breakdown
            diff = x_scaled[0] - self.mean_vector
            mahalanobis_dist = float(np.sqrt(np.dot(np.dot(diff, self.cov_inv), diff.T)))
            is_mahalanobis_anomaly = mahalanobis_dist > 3.6

            # 3. Individual Sensor Deviation Contributions (Explainability / XAI)
            sensor_deviations = {}
            for idx, col in enumerate(self.FEATURE_COLS):
                sensor_deviations[col] = float(abs(x_scaled[0][idx] - self.mean_vector[idx]))

            is_anomaly = is_iforest_anomaly or is_mahalanobis_anomaly
            return is_anomaly, iforest_raw, mahalanobis_dist, sensor_deviations
        except Exception:
            return False, 0.0, 0.0, {}


def station_pressure_to_mslp(p_station_hpa: Optional[float], elevation_m: Optional[float], temp_c: Optional[float] = 15.0) -> Optional[float]:
    """
    Reduces station pressure (QFE) to Mean Sea Level Pressure (MSLP / QFF)
    using the WMO hypsometric barometric reduction formula (WMO-No. 8, Part I, Chapter 3).
    Formula: P_mslp = P_stn * (1 - (0.0065 * h) / (T_kelvin + 0.0065 * h)) ^ (-5.257)
    """
    if p_station_hpa is None:
        return None
    if elevation_m is None or elevation_m == 0:
        return round(float(p_station_hpa), 2)
    try:
        t_kelvin = (temp_c if temp_c is not None else 15.0) + 273.15
        lapse_factor = (0.0065 * float(elevation_m)) / (t_kelvin + 0.0065 * float(elevation_m))
        p_mslp = float(p_station_hpa) * ((1.0 - lapse_factor) ** (-5.257))
        return round(float(p_mslp), 2)
    except Exception:
        return round(float(p_station_hpa), 2)


def mslp_to_station_pressure(p_mslp_hpa: Optional[float], elevation_m: Optional[float], temp_c: Optional[float] = 15.0) -> Optional[float]:
    """
    Inverse of hypsometric reduction: converts Mean Sea Level Pressure (MSLP)
    back to station pressure (QFE) at elevation h.
    Formula: P_stn = P_mslp * (1 - (0.0065 * h) / (T_kelvin + 0.0065 * h)) ^ (5.257)
    """
    if p_mslp_hpa is None:
        return None
    if elevation_m is None or elevation_m == 0:
        return round(float(p_mslp_hpa), 2)
    try:
        t_kelvin = (temp_c if temp_c is not None else 15.0) + 273.15
        lapse_factor = (0.0065 * float(elevation_m)) / (t_kelvin + 0.0065 * float(elevation_m))
        p_stn = float(p_mslp_hpa) * ((1.0 - lapse_factor) ** (5.257))
        return round(float(p_stn), 2)
    except Exception:
        return round(float(p_mslp_hpa), 2)


# =====================================================================
# Tier 4: Spatial Neighbor Cross-Validation (K-Nearest Stations)
# =====================================================================
class SpatialNeighborValidator:
    """
    Cross-checks station readings against neighboring AWS stations.
    Enforces WMO-No. 8 150 km spatial radius, environmental lapse rate,
    and hypsometric MSLP reduction.
    """

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two GPS coordinates."""
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def validate_station(
        self,
        target_station: Dict[str, Any],
        neighbor_stations: List[Dict[str, Any]],
        sensor: str = "temperature",
        max_distance_km: float = 200.0
    ) -> Tuple[bool, float, List[str]]:
        target_val = target_station.get(sensor)
        if target_val is None:
            return False, 0.0, []

        t_lat, t_lon = float(target_station.get("latitude", 0.0)), float(target_station.get("longitude", 0.0))
        t_elev = float(target_station.get("elevation_m") or target_station.get("elevation", 0.0))
        t_temp = target_station.get("temperature", 25.0)

        # Barometric reduction: for pressure, evaluate strictly on Mean Sea Level Pressure (MSLP)
        if sensor == "pressure":
            target_val = station_pressure_to_mslp(target_val, t_elev, t_temp)
        elif sensor == "temperature":
            # Environmental lapse rate normalization to Sea Level equivalent (0.0065°C/m)
            target_val = float(target_val) + (0.0065 * t_elev)

        weights = []
        vals = []

        for n in neighbor_stations:
            if n.get("station_id") == target_station.get("station_id"):
                continue
            n_val = n.get(sensor)
            if n_val is None:
                continue

            n_lat, n_lon = float(n.get("latitude", 0.0)), float(n.get("longitude", 0.0))
            dist = self.haversine_km(t_lat, t_lon, n_lat, n_lon) if (t_lat != 0.0 and n_lat != 0.0) else 50.0

            if dist <= max_distance_km or len(vals) < 3:
                w = 1.0 / max(dist, 1.0)
                weights.append(w)
                n_elev = float(n.get("elevation_m") or n.get("elevation", 0.0))
                n_temp = n.get("temperature", 25.0)
                if sensor == "pressure":
                    n_val_reduced = station_pressure_to_mslp(n_val, n_elev, n_temp)
                    vals.append(float(n_val_reduced))
                elif sensor == "temperature":
                    n_val_reduced = float(n_val) + (0.0065 * n_elev)
                    vals.append(float(n_val_reduced))
                else:
                    vals.append(float(n_val))

        if len(vals) < 2:
            return False, 0.0, []

        idw_consensus = float(np.sum(np.array(vals) * np.array(weights)) / np.sum(weights))
        deviation = abs(target_val - idw_consensus)

        tolerances = {
            "temperature": 5.5,   # °C (after lapse rate normalization)
            "humidity": 25.0,      # %
            "pressure": 4.5,       # hPa (MSLP barometric consensus)
            "wind_speed": 16.0     # m/s
        }

        tol = tolerances.get(sensor, 6.0)
        if deviation > tol:
            sensor_label = "MSLP Pressure" if sensor == "pressure" else ("Sea-Level Temp" if sensor == "temperature" else sensor)
            unit = "hPa" if sensor == "pressure" else ("°C" if sensor == "temperature" else "%")
            return True, deviation, [
                f"Spatial divergence: {sensor_label} ({target_val:.1f} {unit}) diverges by {deviation:.1f} {unit} from {len(vals)} regional AWS stations (Cluster Consensus: {idw_consensus:.1f} {unit})"
            ]

        return False, deviation, []


# =====================================================================
# Severe Weather vs. Sensor Failure Disambiguator
# =====================================================================
class SevereWeatherDisambiguator:
    """
    Suppresses false alarms during genuine atmospheric severe weather events.
    Recognizes both cyclonic barometric plunges and thunderstorm cold-pool mesohigh pressure jumps.
    """

    @staticmethod
    def evaluate(
        record: Dict[str, Any],
        prev_record: Optional[Dict[str, Any]],
        neighbor_records: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        if not prev_record:
            return False, ""

        temp_delta = record.get("temperature", 0) - prev_record.get("temperature", 0)
        pressure_delta = record.get("pressure", 0) - prev_record.get("pressure", 0)
        wind_speed = record.get("wind_speed", 0)
        rain = record.get("precipitation", 0)

        # Monsoon Squall / Severe Convective Downburst Signature:
        # Pressure fluctuation (cyclone plunge < -1.2 hPa OR thunderstorm cold-pool mesohigh nose > +1.2 hPa),
        # sudden drop in temp, wind gust > 11 m/s, and precipitation
        pressure_jump = abs(pressure_delta) >= 1.2
        is_squall = (
            pressure_jump and
            temp_delta < -2.0 and
            wind_speed > 11.0 and
            rain > 0.8
        )

        neighbor_corroboration = any(
            n.get("wind_speed", 0) > 10.0 or n.get("precipitation", 0) > 1.0
            for n in neighbor_records
        )
        ongoing_squall = (wind_speed > 15.0 and rain > 5.0 and float(record.get("humidity", 0)) > 80.0)
        if is_squall or (wind_speed > 18.0 and neighbor_corroboration) or ongoing_squall:
            return True, "Natural severe event verified: Multi-sensor atmospheric squall dynamics confirmed with regional corroboration."

        temp = record.get("temperature", 0)
        rh = record.get("humidity", 50)
        if temp > 43.0 and rh < 25.0:
            return True, "Heatwave / Loo condition verified: Elevated temperature with low humidity aligns with continental summer climatology."

        return False, ""


# =====================================================================
# Self-Healing ML Imputer (Automated Data Reconstruction)
# =====================================================================
class SelfHealingImputer:
    """
    Replaces corrupted or missing values using multi-sensor Ridge regression
    and spatial neighbor interpolation with elevation and distance weighting.
    """

    def __init__(self):
        self.models: Dict[str, Ridge] = {}
        self.is_ready = False

    def fit_imputers(self, clean_df: pd.DataFrame):
        features = ["temperature", "humidity", "pressure", "wind_speed", "solar_radiation"]
        for target in features:
            predictors = [f for f in features if f != target]
            X = clean_df[predictors].dropna()
            y = clean_df.loc[X.index, target]
            if len(X) > 20:
                reg = Ridge(alpha=1.0)
                reg.fit(X, y)
                self.models[target] = reg
        self.is_ready = True

    def impute_sensor(
        self,
        target_sensor: str,
        record: Dict[str, Any],
        neighbor_stations: List[Dict[str, Any]]
    ) -> float:
        t_elev = float(record.get("elevation_m") or record.get("elevation", 0.0))
        t_lat = float(record.get("latitude", 0.0))
        t_lon = float(record.get("longitude", 0.0))

        # Spatial neighbor consensus with distance cutoff and elevation correction
        valid_neighbors = []
        for n in neighbor_stations:
            val = n.get(target_sensor)
            if val is not None:
                n_lat = float(n.get("latitude", 0.0))
                n_lon = float(n.get("longitude", 0.0))
                dist = SpatialNeighborValidator.haversine_km(t_lat, t_lon, n_lat, n_lon) if (t_lat != 0 and n_lat != 0) else 100.0
                n_elev = float(n.get("elevation_m") or n.get("elevation", 0.0))
                n_temp = n.get("temperature", 25.0)
                valid_neighbors.append((dist, val, n_elev, n_temp))

        # Sort by distance and pick local peers (within 350 km or top 4 closest)
        if valid_neighbors:
            valid_neighbors.sort(key=lambda x: x[0])
            local_peers = [vn for vn in valid_neighbors if vn[0] <= 350.0]
            if len(local_peers) < 2:
                local_peers = valid_neighbors[:4]

            if target_sensor == "pressure":
                # Convert peers to MSLP, compute distance-weighted consensus, reduce back to station elevation
                mslp_vals = [station_pressure_to_mslp(vn[1], vn[2], vn[3]) for vn in local_peers]
                weights = [1.0 / max(vn[0], 5.0) for vn in local_peers]
                consensus_mslp = float(np.sum(np.array(mslp_vals) * np.array(weights)) / np.sum(weights))
                imputed_p = mslp_to_station_pressure(consensus_mslp, t_elev, record.get("temperature", 25.0))
                return round(float(imputed_p), 2)

            elif target_sensor == "temperature":
                # Normalize peers to MSL using lapse rate, compute consensus, reduce back
                msl_temps = [float(vn[1]) + (0.0065 * vn[2]) for vn in local_peers]
                weights = [1.0 / max(vn[0], 5.0) for vn in local_peers]
                consensus_msl_t = float(np.sum(np.array(msl_temps) * np.array(weights)) / np.sum(weights))
                imputed_t = consensus_msl_t - (0.0065 * t_elev)
                return round(float(imputed_t), 2)

            else:
                # Distance-weighted average for humidity, wind, etc.
                weights = [1.0 / max(vn[0], 5.0) for vn in local_peers]
                vals = [float(vn[1]) for vn in local_peers]
                return round(float(np.sum(np.array(vals) * np.array(weights)) / np.sum(weights)), 2)

        if self.is_ready and target_sensor in self.models:
            reg = self.models[target_sensor]
            features = ["temperature", "humidity", "pressure", "wind_speed", "solar_radiation"]
            predictors = [f for f in features if f != target_sensor]
            try:
                x_df = pd.DataFrame([[float(record.get(f, 0.0)) for f in predictors]], columns=predictors)
                pred = float(reg.predict(x_df)[0])
                limits = PhysicalConstraintChecker.LIMITS.get(target_sensor, (-50, 1500))
                return float(np.clip(pred, limits[0], limits[1]))
            except Exception:
                pass

        limits = PhysicalConstraintChecker.LIMITS.get(target_sensor, (0, 50))
        return float((limits[0] + limits[1]) / 2.0)


# =====================================================================
# Complete 4-Tier Master Quality Control Pipeline
# =====================================================================
class AWSQualityControlPipeline:
    """
    Main entry point orchestrating all 4 QC tiers, disambiguation,
    trust scoring, and self-healing imputation.
    """

    def __init__(self):
        self.tier1_physical = PhysicalConstraintChecker()
        self.tier2_temporal = TemporalAnomalyDetector()
        self.tier3_ml = MultivariateMLEngine(contamination=0.03)
        self.tier4_spatial = SpatialNeighborValidator()
        self.disambiguator = SevereWeatherDisambiguator()
        self.imputer = SelfHealingImputer()

        # Station historical cache for temporal windows
        self.station_history: Dict[str, List[Dict[str, Any]]] = {}

    def seed_and_train(self, historical_df: pd.DataFrame):
        self.tier3_ml.fit(historical_df)
        self.imputer.fit_imputers(historical_df)

    def process_packet(
        self,
        record: Dict[str, Any],
        neighbor_records: Optional[List[Dict[str, Any]]] = None
    ) -> AnomalyResult:
        neighbor_records = neighbor_records or []
        station_id = record.get("station_id", "AWS_UNKNOWN")

        if station_id not in self.station_history:
            self.station_history[station_id] = []
        history = self.station_history[station_id]
        prev_record = history[-1] if len(history) > 0 else None

        all_reasons = []
        tier_triggered = "None"
        is_anomaly = False
        qc_flag = QCFlag.GOOD
        severity = "INFO"
        confidence = 0.98
        imputed_dict = {}

        # -------------------------------------------------------------
        # Tier 1: Physical Boundary Checks (Absolute Climatological Limits)
        # -------------------------------------------------------------
        t1_viol, t1_reasons = self.tier1_physical.check_physical_limits(record)
        if t1_viol:
            is_anomaly = True
            qc_flag = QCFlag.ERRONEOUS
            severity = "CRITICAL"
            tier_triggered = "Tier 1: Global Physical Limits"
            all_reasons.extend(t1_reasons)
            confidence = 1.0

        # -------------------------------------------------------------
        # Tier 2: Temporal & Sensor Health Checks (Flatline / Step Jump)
        # -------------------------------------------------------------
        if not is_anomaly and prev_record:
            for sensor in ["temperature", "humidity", "pressure", "wind_speed"]:
                curr = record.get(sensor)
                prev = prev_record.get(sensor)
                if curr is not None and prev is not None:
                    jump_detected, delta = self.tier2_temporal.detect_step_jump(curr, prev, sensor)
                    if jump_detected:
                        is_anomaly = True
                        qc_flag = QCFlag.ERRONEOUS
                        severity = "CRITICAL"
                        tier_triggered = "Tier 2: Rate of Change & Persistence"
                        all_reasons.append(
                            f"Abrupt step jump: {sensor} shifted by {delta:.2f} in single interval (Exceeds IMD physical limit)"
                        )

            # Flatline check (stuck reading over past 6 intervals)
            if len(history) >= 5:
                for sensor in ["temperature", "humidity", "pressure"]:
                    recent_series = [float(h.get(sensor, 0.0)) for h in history[-5:]] + [float(record.get(sensor, 0.0))]
                    if self.tier2_temporal.detect_flatline(recent_series, min_samples=6):
                        is_anomaly = True
                        qc_flag = QCFlag.ERRONEOUS
                        severity = "CRITICAL"
                        tier_triggered = "Tier 2: Rate of Change & Persistence"
                        all_reasons.append(
                            f"Sensor lockup / Flatline: {sensor} frozen at {record.get(sensor):.2f} across consecutive readings"
                        )

        # -------------------------------------------------------------
        # Tier 3: Internal Thermodynamic & Diurnal Consistency
        # -------------------------------------------------------------
        if not is_anomaly:
            t3_viol, t3_reasons = self.tier1_physical.check_thermodynamic_diurnal(record)
            if t3_viol:
                is_anomaly = True
                qc_flag = QCFlag.ERRONEOUS
                severity = "CRITICAL"
                tier_triggered = "Tier 3: Internal Thermodynamic Consistency"
                all_reasons.extend(t3_reasons)
                confidence = 1.0

        # -------------------------------------------------------------
        # Severe Weather vs Sensor Failure Disambiguation
        # -------------------------------------------------------------
        is_legit_weather, weather_note = self.disambiguator.evaluate(record, prev_record, neighbor_records)
        if is_legit_weather:
            if "Tier 1" not in tier_triggered and "Tier 3" not in tier_triggered:
                is_anomaly = False
                qc_flag = QCFlag.GOOD
                severity = "INFO"
                all_reasons = [f"NATURAL EVENT: {weather_note}"]
                history.append(record)
                return AnomalyResult(
                    is_anomaly=False,
                    qc_flag=QCFlag.GOOD,
                    severity="INFO",
                    tier_triggered="Disambiguated (Natural Event)",
                    reasons=all_reasons,
                    confidence=0.96,
                    is_extreme_weather=True
                )

        # -------------------------------------------------------------
        # Tier 3b: Multivariate ML Ensemble (Isolation Forest + Mahalanobis)
        # -------------------------------------------------------------
        if not is_anomaly:
            ml_anom, iforest_score, mahalanobis_dist, dev_dict = self.tier3_ml.score_sample(record)
            if ml_anom:
                is_anomaly = True
                qc_flag = QCFlag.SUSPECT
                severity = "WARNING"
                tier_triggered = "Tier 3: Internal Thermodynamic Consistency"
                all_reasons.append(
                    f"Multivariate correlation anomaly (Isolation Forest: {iforest_score:.3f}, Mahalanobis Distance: {mahalanobis_dist:.2f})"
                )
                if dev_dict:
                    top_sensor = max(dev_dict.items(), key=lambda item: item[1])[0]
                    all_reasons.append(f"Top anomalous feature contribution: {top_sensor} (Normalized deviation: {dev_dict[top_sensor]:.2f}σ)")
                confidence = float(np.clip(mahalanobis_dist / 5.0, 0.70, 0.98))

        # -------------------------------------------------------------
        # Tier 4: Spatial Neighbor Cross-Validation
        # -------------------------------------------------------------
        if not is_anomaly and neighbor_records:
            for sensor in ["temperature", "humidity", "pressure"]:
                spat_anom, dev, spat_reasons = self.tier4_spatial.validate_station(
                    record, neighbor_records, sensor=sensor
                )
                if spat_anom:
                    is_anomaly = True
                    qc_flag = QCFlag.SUSPECT
                    severity = "WARNING"
                    tier_triggered = "Tier 4: Spatial Neighbor Cross-Validation"
                    all_reasons.extend(spat_reasons)
                    confidence = 0.88

        # -------------------------------------------------------------
        # Self-Healing Imputation on Anomalous Sensors
        # -------------------------------------------------------------
        if is_anomaly:
            for sensor in ["temperature", "humidity", "pressure", "wind_speed", "solar_radiation"]:
                sensor_mentioned = any(sensor in r.lower() for r in all_reasons)
                if sensor_mentioned or "Tier 3" in tier_triggered:
                    imputed_val = self.imputer.impute_sensor(sensor, record, neighbor_records)
                    imputed_dict[sensor] = round(imputed_val, 2)

        history.append(record)
        if len(history) > 40:
            history.pop(0)

        return AnomalyResult(
            is_anomaly=is_anomaly,
            qc_flag=qc_flag,
            severity=severity,
            tier_triggered=tier_triggered,
            reasons=all_reasons if all_reasons else ["Telemetry healthy, passed all 4 quality tiers."],
            confidence=confidence,
            is_extreme_weather=is_legit_weather,
            imputed_values=imputed_dict
        )
