"""
Realistic IMD Indian Automatic Weather Station (AWS) Network Telemetry Generator
Covers 35 official stations across every meteorological subdivision of India:
Himalayan, Indo-Gangetic, Thar Desert, Deccan Plateau, Coastal, Northeast, and Islands.
"""

import math
import random
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any

# Complete Indian AWS National Network (35 Stations)
AWS_STATIONS = [
    # --- NORTH & HIMALAYAN SUBDIVISIONS ---
    {
        "station_id": "DEL01", "wmo_id": "42182", "icao": "VIDD", "station_name": "New Delhi (Safdarjung)", "state": "Delhi",
        "city": "New Delhi", "latitude": 28.584, "longitude": 77.206, "elevation_m": 216, "zone": "North Plains",
        "sensor_hardware": "PT100 4-Wire RTD, Vaisala PTB210 Barometer, Young 05103 Wind Monitor",
        "base_temp": 32.0, "base_rh": 55.0, "base_pres": 985.0
    },
    {
        "station_id": "DEL02", "wmo_id": "42181", "icao": "VIDP", "station_name": "New Delhi (Palam Airport)", "state": "Delhi",
        "city": "New Delhi", "latitude": 28.566, "longitude": 77.098, "elevation_m": 237, "zone": "North Plains",
        "sensor_hardware": "PT100 RTD, Setra 278 Barometer, Gill Ultrasonic Anemometer",
        "base_temp": 32.5, "base_rh": 53.0, "base_pres": 983.0
    },
    {
        "station_id": "RTK01", "wmo_id": "42180", "icao": None, "station_name": "Rohtak Meteorological Center", "state": "Haryana",
        "city": "Rohtak", "latitude": 28.895, "longitude": 76.606, "elevation_m": 220, "zone": "North Plains",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Vaisala PTB210 Barometer",
        "base_temp": 33.0, "base_rh": 52.0, "base_pres": 984.0
    },
    {
        "station_id": "SXR01", "wmo_id": "42027", "icao": "VISR", "station_name": "Srinagar Observatory", "state": "Jammu & Kashmir",
        "city": "Srinagar", "latitude": 34.083, "longitude": 74.797, "elevation_m": 1587, "zone": "Western Himalayas",
        "sensor_hardware": "Heated PT100 RTD, Campbell CS215, Young Wind Monitor",
        "base_temp": 18.0, "base_rh": 65.0, "base_pres": 845.0
    },
    {
        "station_id": "IXL01", "wmo_id": "42012", "icao": "VILH", "station_name": "Leh High-Altitude AWS", "state": "Ladakh",
        "city": "Leh", "latitude": 34.152, "longitude": 77.577, "elevation_m": 3524, "zone": "Trans-Himalayas",
        "sensor_hardware": "Arctic-spec Heated PT100, Vaisala PTB330, Ultrasonic Wind",
        "base_temp": 12.0, "base_rh": 35.0, "base_pres": 670.0
    },
    {
        "station_id": "SLV01", "wmo_id": "42083", "icao": None, "station_name": "Shimla Ridge Observatory", "state": "Himachal Pradesh",
        "city": "Shimla", "latitude": 31.104, "longitude": 77.173, "elevation_m": 2205, "zone": "Western Himalayas",
        "sensor_hardware": "Heated PT100 RTD, Vaisala HMP155, Young Wind Monitor",
        "base_temp": 16.0, "base_rh": 70.0, "base_pres": 790.0
    },
    {
        "station_id": "DED01", "wmo_id": "42111", "icao": "VIDN", "station_name": "Dehradun Meteorological Center", "state": "Uttarakhand",
        "city": "Dehradun", "latitude": 30.316, "longitude": 78.032, "elevation_m": 682, "zone": "Himalayan Foothills",
        "sensor_hardware": "PT100 RTD, Setra 278 Barometer, Texas TR-525 Rain Gauge",
        "base_temp": 28.0, "base_rh": 68.0, "base_pres": 935.0
    },
    {
        "station_id": "IXC01", "wmo_id": "42131", "icao": "VICG", "station_name": "Chandigarh Observatory", "state": "Chandigarh",
        "city": "Chandigarh", "latitude": 30.733, "longitude": 76.779, "elevation_m": 321, "zone": "North Plains",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210, Rotronic HC2A Temp/RH",
        "base_temp": 31.0, "base_rh": 58.0, "base_pres": 975.0
    },
    {
        "station_id": "JAI01", "wmo_id": "42348", "icao": "VIJP", "station_name": "Jaipur Observatory (Sanganer)", "state": "Rajasthan",
        "city": "Jaipur", "latitude": 26.824, "longitude": 75.812, "elevation_m": 390, "zone": "Northwest Semi-Arid",
        "sensor_hardware": "PT100 RTD, Kipp & Zonen Pyranometer, Vaisala HMP155",
        "base_temp": 35.0, "base_rh": 40.0, "base_pres": 968.0
    },
    {
        "station_id": "TNK01", "wmo_id": "42352", "icao": None, "station_name": "Tonk Meteorological Center", "state": "Rajasthan",
        "city": "Tonk", "latitude": 26.166, "longitude": 75.789, "elevation_m": 289, "zone": "Northwest Semi-Arid",
        "sensor_hardware": "PT100 RTD, Vaisala HMP155, Texas TR-525 Rain Gauge",
        "base_temp": 34.5, "base_rh": 42.0, "base_pres": 974.0
    },
    {
        "station_id": "ALW01", "wmo_id": "42255", "icao": None, "station_name": "Alwar Meteorological Center", "state": "Rajasthan",
        "city": "Alwar", "latitude": 27.564, "longitude": 76.606, "elevation_m": 270, "zone": "Northwest Semi-Arid",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Setra 278 Barometer",
        "base_temp": 34.0, "base_rh": 45.0, "base_pres": 976.0
    },
    {
        "station_id": "AJM01", "wmo_id": "42339", "icao": None, "station_name": "Ajmer Observatory", "state": "Rajasthan",
        "city": "Ajmer", "latitude": 26.450, "longitude": 74.640, "elevation_m": 486, "zone": "Northwest Semi-Arid",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210 Barometer, Young 05103 Wind Monitor",
        "base_temp": 33.5, "base_rh": 42.0, "base_pres": 952.0
    },
    {
        "station_id": "JSA01", "wmo_id": "42205", "icao": "VIJR", "station_name": "Jaisalmer Desert AWS", "state": "Rajasthan",
        "city": "Jaisalmer", "latitude": 26.915, "longitude": 70.908, "elevation_m": 224, "zone": "Thar Desert",
        "sensor_hardware": "Dust-shielded PT100 RTD, Kipp & Zonen CMP11, Vaisala HMP155",
        "base_temp": 41.0, "base_rh": 22.0, "base_pres": 984.0
    },
    {
        "station_id": "LKO01", "wmo_id": "42369", "icao": "VILK", "station_name": "Lucknow (Amausi Airport)", "state": "Uttar Pradesh",
        "city": "Lucknow", "latitude": 26.760, "longitude": 80.880, "elevation_m": 128, "zone": "Central Gangetic Plains",
        "sensor_hardware": "PT100 RTD, Setra 278, Young Wind Monitor",
        "base_temp": 33.0, "base_rh": 62.0, "base_pres": 995.0
    },
    {
        "station_id": "VNS01", "wmo_id": "42475", "icao": "VIBN", "station_name": "Varanasi (Babatpur)", "state": "Uttar Pradesh",
        "city": "Varanasi", "latitude": 25.450, "longitude": 82.859, "elevation_m": 81, "zone": "East Gangetic Plains",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Texas TR-525 Rain Gauge",
        "base_temp": 33.5, "base_rh": 65.0, "base_pres": 1000.0
    },
    {
        "station_id": "PAT01", "wmo_id": "42492", "icao": "VEPT", "station_name": "Patna Meteorological Office", "state": "Bihar",
        "city": "Patna", "latitude": 25.594, "longitude": 85.137, "elevation_m": 53, "zone": "East Gangetic Plains",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210, Texas TR-525 Rain Gauge",
        "base_temp": 32.5, "base_rh": 70.0, "base_pres": 1003.0
    },

    # --- WEST & CENTRAL SUBDIVISIONS ---
    {
        "station_id": "BOM01", "wmo_id": "43003", "icao": "VABB", "station_name": "Mumbai (Santacruz Coastal)", "state": "Maharashtra",
        "city": "Mumbai", "latitude": 19.089, "longitude": 72.854, "elevation_m": 8, "zone": "West Coast",
        "sensor_hardware": "Marine-grade PT100 RTD, Vaisala PTB330, Young 05103 Wind Monitor",
        "base_temp": 30.5, "base_rh": 82.0, "base_pres": 1008.0
    },
    {
        "station_id": "BOM02", "wmo_id": "43057", "icao": None, "station_name": "Mumbai (Colaba Marine Met)", "state": "Maharashtra",
        "city": "Mumbai", "latitude": 18.906, "longitude": 72.814, "elevation_m": 11, "zone": "West Coast",
        "sensor_hardware": "Marine PT100 RTD, Ultrasonic Anemometer, Vaisala Barometer",
        "base_temp": 30.2, "base_rh": 84.0, "base_pres": 1008.0
    },
    {
        "station_id": "PUN01", "wmo_id": "43063", "icao": "VAPO", "station_name": "Pune (Shivajinagar)", "state": "Maharashtra",
        "city": "Pune", "latitude": 18.520, "longitude": 73.856, "elevation_m": 560, "zone": "Madhya Maharashtra",
        "sensor_hardware": "PT100 RTD, Vaisala HMP155, Campbell CS106",
        "base_temp": 28.5, "base_rh": 65.0, "base_pres": 950.0
    },
    {
        "station_id": "NAG01", "wmo_id": "42867", "icao": "VANP", "station_name": "Nagpur Regional Met Center", "state": "Maharashtra",
        "city": "Nagpur", "latitude": 21.145, "longitude": 79.088, "elevation_m": 310, "zone": "Vidarbha",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210, Kipp & Zonen Pyranometer",
        "base_temp": 34.0, "base_rh": 50.0, "base_pres": 976.0
    },
    {
        "station_id": "AMD01", "wmo_id": "42647", "icao": "VAAH", "station_name": "Ahmedabad Airport AWS", "state": "Gujarat",
        "city": "Ahmedabad", "latitude": 23.073, "longitude": 72.634, "elevation_m": 55, "zone": "Gujarat Plains",
        "sensor_hardware": "PT100 RTD, Setra 278 Barometer, Rotronic HC2A",
        "base_temp": 36.0, "base_rh": 45.0, "base_pres": 1002.0
    },
    {
        "station_id": "BHO01", "wmo_id": "42675", "icao": "VABP", "station_name": "Bhopal (Bairagarh Met)", "state": "Madhya Pradesh",
        "city": "Bhopal", "latitude": 23.287, "longitude": 77.350, "elevation_m": 523, "zone": "West MP Plateau",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Vaisala PTB210",
        "base_temp": 32.0, "base_rh": 55.0, "base_pres": 955.0
    },
    {
        "station_id": "RPR01", "wmo_id": "43041", "icao": "VARP", "station_name": "Raipur Meteorological Center", "state": "Chhattisgarh",
        "city": "Raipur", "latitude": 21.251, "longitude": 81.629, "elevation_m": 298, "zone": "Chhattisgarh Basin",
        "sensor_hardware": "PT100 RTD, Texas TR-525 Rain Gauge, Young Wind",
        "base_temp": 33.0, "base_rh": 60.0, "base_pres": 978.0
    },
    {
        "station_id": "GOI01", "wmo_id": "43192", "icao": "VOGO", "station_name": "Goa (Panaji Observatory)", "state": "Goa",
        "city": "Panaji", "latitude": 15.498, "longitude": 73.827, "elevation_m": 60, "zone": "Konkan & Goa",
        "sensor_hardware": "Marine PT100 RTD, Optical Rain Sensor, Vaisala PTB330",
        "base_temp": 29.5, "base_rh": 86.0, "base_pres": 1002.0
    },

    # --- SOUTH & PENINSULAR SUBDIVISIONS ---
    {
        "station_id": "BLR01", "wmo_id": "43295", "icao": "VOBL", "station_name": "Bengaluru (HAL Airport)", "state": "Karnataka",
        "city": "Bengaluru", "latitude": 12.955, "longitude": 77.668, "elevation_m": 920, "zone": "South Interior Karnataka",
        "sensor_hardware": "PT100 RTD, Gill WindSonic Ultrasonic Anemometer, Campbell CS106",
        "base_temp": 26.5, "base_rh": 65.0, "base_pres": 915.0
    },
    {
        "station_id": "MAA01", "wmo_id": "43279", "icao": "VOMM", "station_name": "Chennai (Meenambakkam)", "state": "Tamil Nadu",
        "city": "Chennai", "latitude": 12.994, "longitude": 80.180, "elevation_m": 16, "zone": "North Coastal Tamil Nadu",
        "sensor_hardware": "PT100 RTD, Campbell CS215 Temp/RH, Texas TR-525 Rain Gauge",
        "base_temp": 33.0, "base_rh": 74.0, "base_pres": 1007.0
    },
    {
        "station_id": "HYD01", "wmo_id": "43128", "icao": "VOHS", "station_name": "Hyderabad (Begumpet Airport)", "state": "Telangana",
        "city": "Hyderabad", "latitude": 17.453, "longitude": 78.467, "elevation_m": 531, "zone": "Telangana Plateau",
        "sensor_hardware": "PT100 RTD, Vaisala HMP155, Young Wind Monitor",
        "base_temp": 31.5, "base_rh": 58.0, "base_pres": 954.0
    },
    {
        "station_id": "VTZ01", "wmo_id": "43149", "icao": "VOVZ", "station_name": "Visakhapatnam Cyclone Warning Center", "state": "Andhra Pradesh",
        "city": "Visakhapatnam", "latitude": 17.704, "longitude": 83.297, "elevation_m": 5, "zone": "Coastal Andhra",
        "sensor_hardware": "Heavy-Duty Marine Ultrasonic Wind, PT100 RTD, Vaisala Barometer",
        "base_temp": 31.0, "base_rh": 78.0, "base_pres": 1008.0
    },
    {
        "station_id": "TRV01", "wmo_id": "43371", "icao": "VOTV", "station_name": "Thiruvananthapuram Observatory", "state": "Kerala",
        "city": "Thiruvananthapuram", "latitude": 8.507, "longitude": 76.955, "elevation_m": 64, "zone": "Kerala Coast",
        "sensor_hardware": "PT100 RTD, Dual Tipping Bucket, Vaisala PTB330",
        "base_temp": 29.0, "base_rh": 85.0, "base_pres": 1002.0
    },
    {
        "station_id": "COK01", "wmo_id": "43353", "icao": "VOCI", "station_name": "Kochi (Willingdon Island Naval AWS)", "state": "Kerala",
        "city": "Kochi", "latitude": 9.931, "longitude": 76.267, "elevation_m": 3, "zone": "Kerala Coast",
        "sensor_hardware": "Marine PT100, Young Wind Monitor, Texas TR-525 Rain Gauge",
        "base_temp": 29.2, "base_rh": 88.0, "base_pres": 1009.0
    },

    # --- EAST, NORTHEAST & ISLANDS SUBDIVISIONS ---
    {
        "station_id": "CCU01", "wmo_id": "42809", "icao": "VECC", "station_name": "Kolkata (Alipore Regional Met)", "state": "West Bengal",
        "city": "Kolkata", "latitude": 22.527, "longitude": 88.326, "elevation_m": 6, "zone": "Gangetic West Bengal",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210 Barometer, Hukseflux SR05 Pyranometer",
        "base_temp": 31.0, "base_rh": 78.0, "base_pres": 1009.0
    },
    {
        "station_id": "BBI01", "wmo_id": "42971", "icao": "VEBS", "station_name": "Bhubaneswar Airport AWS", "state": "Odisha",
        "city": "Bhubaneswar", "latitude": 20.252, "longitude": 85.817, "elevation_m": 45, "zone": "Odisha Coastal Plains",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Texas TR-525 Rain Gauge",
        "base_temp": 32.0, "base_rh": 76.0, "base_pres": 1004.0
    },
    {
        "station_id": "IXR01", "wmo_id": "42701", "icao": "VERC", "station_name": "Ranchi (Birsa Munda Airport)", "state": "Jharkhand",
        "city": "Ranchi", "latitude": 23.314, "longitude": 85.321, "elevation_m": 652, "zone": "Chhota Nagpur Plateau",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210, Rotronic HC2A",
        "base_temp": 28.0, "base_rh": 65.0, "base_pres": 941.0
    },
    {
        "station_id": "GAU01", "wmo_id": "42410", "icao": "VEGT", "station_name": "Guwahati Regional Met Center", "state": "Assam",
        "city": "Guwahati", "latitude": 26.106, "longitude": 91.585, "elevation_m": 54, "zone": "Brahmaputra Valley",
        "sensor_hardware": "PT100 RTD, Dual Tipping Bucket, Vaisala HMP155",
        "base_temp": 28.5, "base_rh": 82.0, "base_pres": 1003.0
    },
    {
        "station_id": "SHL01", "wmo_id": "42515", "icao": None, "station_name": "Cherrapunji (Sohra Plateau)", "state": "Meghalaya",
        "city": "Cherrapunji", "latitude": 25.298, "longitude": 91.733, "elevation_m": 1313, "zone": "Northeastern Hills",
        "sensor_hardware": "High-capacity Dual Tipping Bucket, Optical Disdrometer, PT100 RTD",
        "base_temp": 21.0, "base_rh": 92.0, "base_pres": 875.0
    },
    {
        "station_id": "IXA01", "wmo_id": "42724", "icao": "VEAT", "station_name": "Agartala Airport AWS", "state": "Tripura",
        "city": "Agartala", "latitude": 23.886, "longitude": 91.240, "elevation_m": 15, "zone": "Northeast Plains",
        "sensor_hardware": "PT100 RTD, Vaisala Barometer, Texas TR-525 Rain Gauge",
        "base_temp": 29.5, "base_rh": 80.0, "base_pres": 1008.0
    },
    {
        "station_id": "IXZ01", "wmo_id": "43333", "icao": "VOPB", "station_name": "Port Blair (Andaman Marine Met)", "state": "Andaman & Nicobar",
        "city": "Port Blair", "latitude": 11.641, "longitude": 92.729, "elevation_m": 16, "zone": "Bay of Bengal Islands",
        "sensor_hardware": "Marine-proof Ultrasonic Wind, PT100 RTD, Vaisala Barometer",
        "base_temp": 29.0, "base_rh": 86.0, "base_pres": 1008.0
    },
    {
        "station_id": "KAV01", "wmo_id": "43311", "icao": None, "station_name": "Kavaratti Island Marine AWS", "state": "Lakshadweep",
        "city": "Kavaratti", "latitude": 10.567, "longitude": 72.642, "elevation_m": 2, "zone": "Arabian Sea Islands",
        "sensor_hardware": "Marine Corrosion-Proof PT100, Ultrasonic Anemometer, Vaisala Barometer",
        "base_temp": 30.0, "base_rh": 82.0, "base_pres": 1010.0
    },
    {
        "station_id": "ASR01", "wmo_id": "42071", "icao": "VIAR", "station_name": "Amritsar (Rajasansi Airport)", "state": "Punjab",
        "city": "Amritsar", "latitude": 31.710, "longitude": 74.797, "elevation_m": 230, "zone": "Northwest Plains",
        "sensor_hardware": "PT100 RTD, Campbell CS215, Young Wind Monitor",
        "base_temp": 32.0, "base_rh": 52.0, "base_pres": 984.0
    },
    {
        "station_id": "STV01", "wmo_id": "42824", "icao": "VASU", "station_name": "Surat Coastal Met Station", "state": "Gujarat",
        "city": "Surat", "latitude": 21.170, "longitude": 72.831, "elevation_m": 13, "zone": "Gujarat Coast",
        "sensor_hardware": "PT100 RTD, Vaisala PTB210, Texas TR-525 Rain Gauge",
        "base_temp": 33.0, "base_rh": 75.0, "base_pres": 1006.0
    },
    {
        "station_id": "IDR01", "wmo_id": "42754", "icao": "VAID", "station_name": "Indore Meteorological Office", "state": "Madhya Pradesh",
        "city": "Indore", "latitude": 22.719, "longitude": 75.857, "elevation_m": 553, "zone": "Malwa Plateau",
        "sensor_hardware": "PT100 RTD, Kipp & Zonen CMP11, Rotronic Temp/RH",
        "base_temp": 31.0, "base_rh": 56.0, "base_pres": 952.0
    },
    {
        "station_id": "CJB01", "wmo_id": "43321", "icao": "VOCB", "station_name": "Coimbatore (Peelamedu)", "state": "Tamil Nadu",
        "city": "Coimbatore", "latitude": 11.016, "longitude": 76.955, "elevation_m": 411, "zone": "South Peninsular",
        "sensor_hardware": "PT100 RTD, Ultrasonic Anemometer, Campbell CS106",
        "base_temp": 30.0, "base_rh": 64.0, "base_pres": 968.0
    },
    {
        "station_id": "IXT01", "wmo_id": "42299", "icao": None, "station_name": "Gangtok Ridge Observatory", "state": "Sikkim",
        "city": "Gangtok", "latitude": 27.338, "longitude": 88.606, "elevation_m": 1650, "zone": "Eastern Himalayas",
        "sensor_hardware": "Heated PT100, Campbell CS215, Dual Rain Tipping Bucket",
        "base_temp": 17.0, "base_rh": 88.0, "base_pres": 835.0
    },
    {
        "station_id": "ITA01", "wmo_id": "42405", "icao": None, "station_name": "Itanagar AWS", "state": "Arunachal Pradesh",
        "city": "Itanagar", "latitude": 27.084, "longitude": 93.605, "elevation_m": 750, "zone": "Northeast Sub-Himalayan",
        "sensor_hardware": "PT100 RTD, Vaisala HMP155, Young Wind Monitor",
        "base_temp": 24.0, "base_rh": 85.0, "base_pres": 925.0
    }
]


def generate_single_reading(station: Dict[str, Any], dt: datetime.datetime) -> Dict[str, Any]:
    """Generates a thermodynamically consistent synthetic reading for an AWS station."""
    hour = dt.hour + dt.minute / 60.0

    # Diurnal solar radiation: peaks around 13:00 IST (~850-1000 W/m²)
    if 6.0 <= hour <= 18.0:
        solar_rad = max(0.0, 950.0 * math.sin((hour - 6.0) / 12.0 * math.pi) + random.uniform(-25, 25))
    else:
        solar_rad = 0.0

    # Diurnal temperature cycle: lowest at 05:30 IST, highest at 14:30 IST
    temp_diurnal = 6.0 * math.sin((hour - 8.5) / 24.0 * 2.0 * math.pi)
    temperature = station["base_temp"] + temp_diurnal + random.gauss(0, 0.35)

    # Relative humidity inverse diurnal cycle
    rh_diurnal = -18.0 * math.sin((hour - 8.5) / 24.0 * 2.0 * math.pi)
    humidity = np.clip(station["base_rh"] + rh_diurnal + random.gauss(0, 1.2), 12.0, 98.0)

    # Atmospheric tidal pressure oscillation (~1.5 hPa diurnal cycle)
    pres_tide = 1.2 * math.cos(hour / 12.0 * 2.0 * math.pi)
    pressure = station["base_pres"] + pres_tide + random.gauss(0, 0.15)

    # Wind speed & direction
    wind_speed = max(0.5, 3.2 + 2.0 * (solar_rad / 1000.0) + random.gauss(0, 0.6))
    wind_direction = (random.randint(180, 240) + random.gauss(0, 8)) % 360

    # Precipitation
    rain = 0.0
    if station["station_id"] == "SHL01" and random.random() < 0.35:
        rain = round(random.uniform(2.0, 18.0), 1)
    elif random.random() < 0.04:
        rain = round(random.uniform(0.5, 4.0), 1)

    # Battery voltage (solar charging profile: 13.8V day, 12.4V night)
    if 7.0 <= hour <= 17.0:
        battery = 13.8 + random.uniform(-0.1, 0.15)
    else:
        battery = 12.4 + random.uniform(-0.1, 0.1)

    return {
        "timestamp": dt.isoformat(),
        "hour": dt.hour,
        "station_id": station["station_id"],
        "wmo_id": station["wmo_id"],
        "station_name": station["station_name"],
        "state": station["state"],
        "city": station.get("city", station["state"]),
        "latitude": station["latitude"],
        "longitude": station["longitude"],
        "elevation_m": station["elevation_m"],
        "zone": station["zone"],
        "sensor_hardware": station["sensor_hardware"],
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 1),
        "pressure": round(pressure, 2),
        "wind_speed": round(wind_speed, 2),
        "wind_direction": round(wind_direction, 1),
        "precipitation": rain,
        "solar_radiation": round(solar_rad, 1),
        "battery_voltage": round(battery, 2),
        "ground_truth_anomaly": "None"
    }


def generate_baseline_dataset(hours: int = 48) -> pd.DataFrame:
    """Generates clean historical dataset across all stations to fit models."""
    start_dt = datetime.datetime.now() - datetime.timedelta(hours=hours)
    records = []
    for step in range(hours * 4):  # 15-minute intervals
        curr_dt = start_dt + datetime.timedelta(minutes=15 * step)
        for stn in AWS_STATIONS:
            rec = generate_single_reading(stn, curr_dt)
            records.append(rec)
    return pd.DataFrame(records)


def generate_station_time_series(station_id: str, steps: int = 48) -> List[Dict[str, Any]]:
    """
    Generates recent 48 intervals (12 hours) of telemetry for a station
    including realistic operational failure modes.
    """
    station = next((s for s in AWS_STATIONS if s["station_id"] == station_id), AWS_STATIONS[0])
    start_dt = datetime.datetime.now() - datetime.timedelta(minutes=15 * steps)
    readings = []

    for i in range(steps):
        dt = start_dt + datetime.timedelta(minutes=15 * i)
        r = generate_single_reading(station, dt)

        # Baseline realistic failure modes for initial inspection:
        # Case 1: DEL01 (Safdarjung) - RTD sensor thermal decalibration drift (+4.5°C)
        if station_id == "DEL01" and i >= steps - 10:
            drift_amount = (i - (steps - 10) + 1) * 0.45
            r["temperature"] = round(r["temperature"] + drift_amount, 2)
            r["ground_truth_anomaly"] = "RTD Sensor Decalibration Drift (+4.5°C offset)"

        # Case 2: BOM01 (Santacruz) - Humidity sensor ADC lockup / flatline
        elif station_id == "BOM01" and i >= steps - 8:
            r["humidity"] = 88.4
            r["ground_truth_anomaly"] = "Capacitive Sensor Lockup (Frozen at 88.4%)"

        # Case 3: CCU01 (Kolkata) - Impossible thermodynamic reading
        elif station_id == "CCU01" and i >= steps - 5:
            r["precipitation"] = 28.5
            r["humidity"] = 18.0
            r["ground_truth_anomaly"] = "Thermodynamic Inconsistency (28.5mm rain with 18% RH)"

        # Case 4: JSA01 (Jaisalmer) - Midnight pyranometer noise
        elif station_id == "JSA01" and i >= steps - 6:
            if dt.hour >= 20 or dt.hour <= 4:
                r["solar_radiation"] = 385.0
                r["ground_truth_anomaly"] = "Nocturnal Pyranometer Drift (385 W/m² at 01:00 AM)"

        # Case 5: DEL02 (Palam Airport) - Monsoon squall (tests natural storm disambiguation)
        elif station_id == "DEL02" and i >= steps - 4:
            r["temperature"] = round(r["temperature"] - 5.8, 2)
            r["pressure"] = round(r["pressure"] - 2.6, 2)
            r["wind_speed"] = round(22.0 + random.uniform(0, 3.5), 2)
            r["precipitation"] = 16.5
            r["ground_truth_anomaly"] = "Natural Severe Meteorological Event (Monsoon Squall)"

        readings.append(r)

    return readings
