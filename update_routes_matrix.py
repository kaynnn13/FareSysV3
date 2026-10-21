"""
Updates fare_matrix.json and fare_system.db to exactly match the official
CTPRB & MCXMTODA Fare Matrix document (MTPFRB Blg. 2024-02).
"""

import json
import sqlite3
import os
from bayesian_model import calculate_bayesian_likelihood

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fare_system.db")
JSON_PATH = os.path.join(BASE_DIR, "fare_matrix.json")

OFFICIAL_ROUTES = [
    {
        "id": 1,
        "name": "Xentro Mall → San Jose / San Felipe / Felisicima",
        "distance_km": 1.0,
        "official_fare": 15.00,
        "special_fare": 30.00,
        "discounted_fare": 12.00,
        "active": 1,
        "zone": "1.0 KM Zone (Minimum Fare)"
    },
    {
        "id": 2,
        "name": "Xentro Mall → Sumapang Mtda. / Guinhawa Crossing / Sumapa Mtda. Kanto / Guinhawa Loob / Golden Grains",
        "distance_km": 1.5,
        "official_fare": 17.50,
        "special_fare": 35.00,
        "discounted_fare": 14.00,
        "active": 1,
        "zone": "1.5 KM Zone"
    },
    {
        "id": 3,
        "name": "Xentro Mall → Catmon / Liang / Capitol View Park / Alido Subd. / Bulihan",
        "distance_km": 2.0,
        "official_fare": 20.00,
        "special_fare": 40.00,
        "discounted_fare": 16.00,
        "active": 1,
        "zone": "2.0 KM Zone"
    },
    {
        "id": 4,
        "name": "Xentro Mall → Diversion / Alido / Bulihan / Maunlad Kanto / Sumapang Mtda. Gitna / San Gabriel",
        "distance_km": 2.5,
        "official_fare": 22.50,
        "special_fare": 45.00,
        "discounted_fare": 18.00,
        "active": 1,
        "zone": "2.5 KM Zone"
    },
    {
        "id": 5,
        "name": "Xentro Mall → Robinsons / Bayan (Malolos Proper) / New City Hall / South Supermarket / CEU",
        "distance_km": 3.0,
        "official_fare": 25.00,
        "special_fare": 50.00,
        "discounted_fare": 20.00,
        "active": 1,
        "zone": "3.0 KM Zone"
    },
    {
        "id": 6,
        "name": "Xentro Mall → Pinagbakahan / Menzyville / Menzyland Loob / Maunlad 7/11 / Sumapang Bata Bungad",
        "distance_km": 3.5,
        "official_fare": 27.50,
        "special_fare": 55.00,
        "discounted_fare": 22.00,
        "active": 1,
        "zone": "3.5 KM Zone"
    },
    {
        "id": 7,
        "name": "Xentro Mall → Sumapang Bata Gitna / Dakila Loob / Bungahan Bungad / Lugam Kanto / Grand Town Phase 1",
        "distance_km": 4.0,
        "official_fare": 30.00,
        "special_fare": 60.00,
        "discounted_fare": 24.00,
        "active": 1,
        "zone": "4.0 KM Zone"
    },
    {
        "id": 8,
        "name": "Xentro Mall → Ligas",
        "distance_km": 4.5,
        "official_fare": 32.50,
        "special_fare": 65.00,
        "discounted_fare": 26.00,
        "active": 1,
        "zone": "4.5 KM Zone"
    }
]

def apply_official_matrix():
    # 1. Update fare_matrix.json
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(OFFICIAL_ROUTES, f, indent=2, ensure_ascii=False)
    print(f"Updated {JSON_PATH} with official MCXMTODA tariff data.")

    # 2. Update SQLite database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # Ensure table has all columns
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(routes)").fetchall()}
    if "distance_km" not in cols:
        conn.execute("ALTER TABLE routes ADD COLUMN distance_km REAL NOT NULL DEFAULT 1.0")
    if "special_fare" not in cols:
        conn.execute("ALTER TABLE routes ADD COLUMN special_fare REAL NOT NULL DEFAULT 0.0")
    if "discounted_fare" not in cols:
        conn.execute("ALTER TABLE routes ADD COLUMN discounted_fare REAL NOT NULL DEFAULT 0.0")

    # Clear and repopulate routes cleanly
    conn.execute("DELETE FROM fare_reports;")
    conn.execute("DELETE FROM routes;")

    for item in OFFICIAL_ROUTES:
        conn.execute("""
            INSERT INTO routes (id, name, distance_km, official_fare, special_fare, discounted_fare, active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            item["id"],
            item["name"],
            item["distance_km"],
            item["official_fare"],
            item["special_fare"],
            item["discounted_fare"]
        ))

    # Re-seed sample reports strictly mapped to these official routes
    sample_reports = [
        # 1. Commuter #17 - Bayan / Malolos Proper (Official ₱25.00, Paid ₱30.00, Diff +₱5.00, 72.4%)
        {
            "user_id": 17,
            "route_id": 5, # Robinsons / Bayan (Malolos Proper)
            "reported_fare": 30.00,
            "distance_km": 3.0,
            "travel_time_min": 14,
            "body_number": "TM-0418",
            "photo_filename": "evidence_sample_1.png",
            "verification_status": "Verified",
            "created_at": "2026-10-03 08:24:00"
        },
        # 2. Commuter #24 - San Jose / San Felipe (Official ₱15.00, Paid ₱15.00, Diff ₱0.00, 5.2%)
        {
            "user_id": 24,
            "route_id": 1, # San Jose / San Felipe / Felisicima
            "reported_fare": 15.00,
            "distance_km": 1.0,
            "travel_time_min": 6,
            "body_number": "TC-1102",
            "photo_filename": "evidence_sample_2.png",
            "verification_status": "Verified",
            "created_at": "2026-10-03 07:12:00"
        },
        # 3. Commuter #31 - Catmon / Bulihan (Official ₱20.00, Paid ₱30.00, Diff +₱10.00, 91.3%)
        {
            "user_id": 31,
            "route_id": 3, # Catmon / Liang / Bulihan
            "reported_fare": 30.00,
            "distance_km": 2.0,
            "travel_time_min": 12,
            "body_number": "TB-0749",
            "photo_filename": "evidence_sample_3.png",
            "verification_status": "Verified",
            "created_at": "2026-10-03 09:45:00"
        },
        # 4. Commuter #08 - Bayan / Malolos Proper (Official ₱25.00, Paid ₱25.00, Diff ₱0.00, 5.2%)
        {
            "user_id": 8,
            "route_id": 5, # Robinsons / Bayan
            "reported_fare": 25.00,
            "distance_km": 3.0,
            "travel_time_min": 15,
            "body_number": "TC-0883",
            "photo_filename": "evidence_sample_4.png",
            "verification_status": "Verified",
            "created_at": "2026-10-02 16:30:00"
        },
        # 5. Commuter #17 - Guinhawa Crossing (Official ₱17.50, Paid ₱25.00, Diff +₱7.50, ~85%)
        {
            "user_id": 17,
            "route_id": 2, # Guinhawa Crossing
            "reported_fare": 25.00,
            "distance_km": 1.5,
            "travel_time_min": 8,
            "body_number": "TT-0194",
            "photo_filename": None,
            "verification_status": "Pending",
            "created_at": "2026-10-04 09:15:00"
        },
        # 6. Commuter #45 - Ligas (Official ₱32.50, Paid ₱40.00, Diff +₱7.50, ~81%)
        {
            "user_id": 45,
            "route_id": 8, # Ligas
            "reported_fare": 40.00,
            "distance_km": 4.5,
            "travel_time_min": 22,
            "body_number": "TG-0521",
            "photo_filename": None,
            "verification_status": "Pending",
            "created_at": "2026-10-04 11:02:00"
        }
    ]

    for rep in sample_reports:
        route = conn.execute("SELECT official_fare FROM routes WHERE id = ?", (rep["route_id"],)).fetchone()
        official = float(route["official_fare"])
        diff = round(rep["reported_fare"] - official, 2)
        calc = calculate_bayesian_likelihood(rep["reported_fare"], official, has_photo=bool(rep["photo_filename"]))
        
        conn.execute("""
            INSERT INTO fare_reports (
                user_id, route_id, reported_fare, fare_difference, distance_km,
                travel_time_min, body_number, photo_filename, verification_status,
                posterior_probability, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rep["user_id"], rep["route_id"], rep["reported_fare"], diff,
            rep["distance_km"], rep["travel_time_min"], rep["body_number"], rep["photo_filename"],
            rep["verification_status"], calc["posterior"], rep["created_at"]
        ))

    conn.commit()
    conn.close()
    print("Database routes and reports updated successfully.")

if __name__ == "__main__":
    apply_official_matrix()
