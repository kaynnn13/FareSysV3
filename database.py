"""
Database Management Module for Malolos FareWatch
SQLite Relational Database Engine with JSON File Synchronization
Based on Official MCXMTODA & CTPRB Fare Matrix (MTPFRB Blg. 2024-02)
"""

import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_FILE = "fare_system.db"
JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fare_matrix.json")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('commuter', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    distance_km REAL NOT NULL DEFAULT 1.0,
    official_fare REAL NOT NULL CHECK(official_fare > 0),
    special_fare REAL NOT NULL DEFAULT 0.0,
    discounted_fare REAL NOT NULL DEFAULT 0.0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS fare_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    origin TEXT NOT NULL DEFAULT 'Xentro Mall Terminal Hub',
    destination TEXT NOT NULL DEFAULT '',
    trip_type TEXT NOT NULL DEFAULT 'regular'
        CHECK(trip_type IN ('regular', 'special', 'special_round_trip')),
    passenger_count INTEGER NOT NULL DEFAULT 1 CHECK(passenger_count >= 1),
    reported_fare REAL NOT NULL CHECK(reported_fare > 0),
    expected_fare REAL NOT NULL DEFAULT 0.0,
    fare_difference REAL NOT NULL,
    distance_km REAL,
    travel_time_min INTEGER,
    body_number TEXT,
    photo_filename TEXT,
    id_filename TEXT,
    verification_status TEXT NOT NULL DEFAULT 'Pending' 
        CHECK(verification_status IN ('Pending', 'Verified', 'Rejected')),
    posterior_probability REAL NOT NULL,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(route_id) REFERENCES routes(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS report_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(report_id) REFERENCES fare_reports(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

def get_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def sync_routes_to_json(db_path=DB_FILE):
    """
    Exports current routes from the database directly into fare_matrix.json.
    Ensures that any edit made via the Web UI updates the physical file as well.
    """
    try:
      conn = get_db(db_path)
      rows = conn.execute(
          "SELECT id, name, distance_km, official_fare, special_fare,"
          " discounted_fare, active FROM routes ORDER BY id ASC"
      ).fetchall()
      conn.close()

      matrix = [
          {
              "id": r["id"],
              "name": r["name"],
              "distance_km": float(r["distance_km"]),
              "official_fare": float(r["official_fare"]),
              "special_fare": float(r["special_fare"]),
              "discounted_fare": float(r["discounted_fare"]),
              "active": int(r["active"]),
          }
          for r in rows
      ]

      with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
      print(f"Synced {len(matrix)} routes to {JSON_FILE}")
    except Exception as e:
      print(f"Error syncing routes to JSON file: {e}")

def init_db(db_path=DB_FILE):
    """Initializes the database schema and loads official CTPRB / MCXMTODA routes."""
    conn = get_db(db_path)
    conn.executescript(SCHEMA)

    # Automatic schema migration for existing databases
    table_cols = [row[1] for row in conn.execute("PRAGMA table_info(fare_reports)").fetchall()]
    if "origin" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN origin TEXT NOT NULL DEFAULT 'Xentro Mall Terminal Hub'")
    if "destination" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN destination TEXT NOT NULL DEFAULT ''")
    if "trip_type" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN trip_type TEXT NOT NULL DEFAULT 'regular'")
    if "passenger_count" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN passenger_count INTEGER NOT NULL DEFAULT 1")
    if "expected_fare" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN expected_fare REAL NOT NULL DEFAULT 0.0")
    if "occurred_at" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN occurred_at TEXT NOT NULL DEFAULT ''")
    if "id_filename" not in table_cols:
        conn.execute("ALTER TABLE fare_reports ADD COLUMN id_filename TEXT DEFAULT NULL")

    # Backfill origin/destination, expected_fare, occurred_at, and sample ID for any records missing it
    conn.execute("""
        UPDATE fare_reports 
        SET origin = 'Xentro Mall Terminal Hub'
        WHERE origin = '' OR origin IS NULL
    """)
    conn.execute("""
        UPDATE fare_reports 
        SET destination = (SELECT name FROM routes WHERE routes.id = fare_reports.route_id)
        WHERE destination = '' OR destination IS NULL
    """)
    conn.execute("""
        UPDATE fare_reports 
        SET expected_fare = (SELECT official_fare FROM routes WHERE routes.id = fare_reports.route_id)
        WHERE expected_fare = 0.0 OR expected_fare IS NULL
    """)
    conn.execute("""
        UPDATE fare_reports 
        SET occurred_at = created_at
        WHERE occurred_at = '' OR occurred_at IS NULL
    """)
    conn.execute("""
        UPDATE fare_reports 
        SET id_filename = 'id_sample_commuter17.png'
        WHERE user_id = 17 AND (id_filename IS NULL OR id_filename = '')
    """)
    conn.commit()

    # 1. Seed Administrator and Commuter accounts
    admin = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, '2026-09-01 08:00:00')",
            ("admin", generate_password_hash("admin123"), "admin")
        )

    demo_users = [
        (8, "claradelrosario", "commuter123", "commuter", "2026-09-10 10:15:00"),
        (17, "juandelacruz", "commuter123", "commuter", "2026-09-12 11:20:00"),
        (24, "mariasantos", "commuter123", "commuter", "2026-09-15 14:05:00"),
        (31, "pedroreyes", "commuter123", "commuter", "2026-09-18 09:30:00"),
        (45, "joserizal", "commuter123", "commuter", "2026-09-22 16:45:00"),
    ]

    for uid, uname, pwd, role, created_at in demo_users:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (uname,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (uid, uname, generate_password_hash(pwd), role, created_at)
            )

    # 2. Seed Official CTPRB / MCXMTODA Routes (prefer fare_matrix.json if present)
    routes_to_seed = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                routes_to_seed = json.load(f)
        except Exception as e:
            print(f"Could not read {JSON_FILE}: {e}")

    if not routes_to_seed:
        # Fallback to official CTPRB & MCXMTODA matrix values
        routes_to_seed = [
            {"name": "Xentro Mall → San Jose / San Felipe / Felisicima", "distance_km": 1.0, "official_fare": 15.00, "special_fare": 30.00, "discounted_fare": 12.00, "active": 1},
            {"name": "Xentro Mall → Guinhawa Crossing / Guinhawa Loob / Sumapa Mtda. / Golden Grains", "distance_km": 1.5, "official_fare": 17.50, "special_fare": 35.00, "discounted_fare": 14.00, "active": 1},
            {"name": "Xentro Mall → Catmon / Liang / Capitol View Park / Alido Subd. / Bulihan", "distance_km": 2.0, "official_fare": 20.00, "special_fare": 40.00, "discounted_fare": 16.00, "active": 1},
            {"name": "Xentro Mall → Diversion / Alido / Bulihan / Maunlad Kanto / Sumapang Mtda. Gitna / San Gabriel", "distance_km": 2.5, "official_fare": 22.50, "special_fare": 45.00, "discounted_fare": 18.00, "active": 1},
            {"name": "Xentro Mall → Robinsons / Bayan (Malolos Proper) / New City Hall / South Supermarket / CEU", "distance_km": 3.0, "official_fare": 25.00, "special_fare": 50.00, "discounted_fare": 20.00, "active": 1},
            {"name": "Xentro Mall → Pinagbakahan / Menzyville / Menzyland Loob / Maunlad 7/11 / Sumapang Bata Bungad", "distance_km": 3.5, "official_fare": 27.50, "special_fare": 55.00, "discounted_fare": 22.00, "active": 1},
            {"name": "Xentro Mall → Sumapang Bata Gitna / Dakila Loob / Bungahan Bungad / Lugam Kanto / Grand Town Phase 1", "distance_km": 4.0, "official_fare": 30.00, "special_fare": 60.00, "discounted_fare": 24.00, "active": 1},
            {"name": "Xentro Mall → Ligas", "distance_km": 4.5, "official_fare": 32.50, "special_fare": 65.00, "discounted_fare": 26.00, "active": 1}
        ]

    for item in routes_to_seed:
        r = conn.execute("SELECT id FROM routes WHERE name = ?", (item["name"],)).fetchone()
        if not r:
            conn.execute("""
                INSERT INTO routes (name, distance_km, official_fare, special_fare, discounted_fare, active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item["name"],
                item.get("distance_km", 1.0),
                item["official_fare"],
                item.get("special_fare", item["official_fare"] * 2),
                item.get("discounted_fare", item["official_fare"] * 0.8),
                item.get("active", 1)
            ))

    # 3. Seed Realistic Sample Reports matching Thesis Requirements
    report_count = conn.execute("SELECT COUNT(*) AS count FROM fare_reports").fetchone()["count"]
    if report_count == 0:
        def get_rid(keyword):
            row = conn.execute("SELECT id FROM routes WHERE name LIKE ?", (f"%{keyword}%",)).fetchone()
            return row["id"] if row else 1

        sample_reports = [
            # 1. Oct 3, 2026 08:24 AM - Commuter #17 - Bayan (Regular, 1 pax: Official ₱25.00, Paid ₱30.00, Diff +₱5.00, 72.4%)
            {
                "user_id": 17,
                "route_id": get_rid("Bayan (Malolos Proper)"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "Bayan (Malolos Proper)",
                "trip_type": "regular",
                "passenger_count": 1,
                "reported_fare": 30.00,
                "expected_fare": 25.00,
                "fare_difference": 5.00,
                "distance_km": 3.0,
                "travel_time_min": 14,
                "body_number": "TM-0418",
                "photo_filename": "evidence_sample_1.png",
                "verification_status": "Verified",
                "posterior_probability": 0.724,
                "occurred_at": "2026-10-03 08:05:00",
                "created_at": "2026-10-03 08:24:00"
            },
            # 2. Oct 3, 2026 07:12 AM - Commuter #24 - San Jose (Regular, 1 pax: Official ₱15.00, Paid ₱15.00, Diff ₱0.00, 5.2%)
            {
                "user_id": 24,
                "route_id": get_rid("San Jose / San Felipe"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "San Jose",
                "trip_type": "regular",
                "passenger_count": 1,
                "reported_fare": 15.00,
                "expected_fare": 15.00,
                "fare_difference": 0.00,
                "distance_km": 1.0,
                "travel_time_min": 6,
                "body_number": "TC-1102",
                "photo_filename": "evidence_sample_2.png",
                "verification_status": "Verified",
                "posterior_probability": 0.052,
                "occurred_at": "2026-10-03 06:55:00",
                "created_at": "2026-10-03 07:12:00"
            },
            # 3. Oct 3, 2026 09:45 AM - Commuter #31 - Catmon (Regular, 1 pax: Official ₱20.00, Paid ₱30.00, Diff +₱10.00, 91.3%)
            {
                "user_id": 31,
                "route_id": get_rid("Catmon / Liang"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "Catmon",
                "trip_type": "regular",
                "passenger_count": 1,
                "reported_fare": 30.00,
                "expected_fare": 20.00,
                "fare_difference": 10.00,
                "distance_km": 2.0,
                "travel_time_min": 12,
                "body_number": "TB-0749",
                "photo_filename": "evidence_sample_3.png",
                "verification_status": "Verified",
                "posterior_probability": 0.913,
                "occurred_at": "2026-10-03 09:20:00",
                "created_at": "2026-10-03 09:45:00"
            },
            # 4. Oct 2, 2026 04:30 PM - Commuter #08 - Bayan (Special Solo Trip: Official Special ₱50.00, Paid ₱50.00, Diff ₱0.00, 5.2%)
            {
                "user_id": 8,
                "route_id": get_rid("Bayan (Malolos Proper)"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "Bayan (Malolos Proper)",
                "trip_type": "special",
                "passenger_count": 1,
                "reported_fare": 50.00,
                "expected_fare": 50.00,
                "fare_difference": 0.00,
                "distance_km": 3.0,
                "travel_time_min": 15,
                "body_number": "TC-0883",
                "photo_filename": "evidence_sample_4.png",
                "verification_status": "Verified",
                "posterior_probability": 0.052,
                "occurred_at": "2026-10-02 16:00:00",
                "created_at": "2026-10-02 16:30:00"
            },
            # 5. Oct 4, 2026 09:15 AM - Commuter #17 - Guinhawa Crossing (Special Round Trip: Official Special ₱35.00 × 2 = ₱70.00, Paid ₱80.00, Diff +₱10.00, 64.8%)
            {
                "user_id": 17,
                "route_id": get_rid("Guinhawa Crossing"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "Guinhawa Crossing",
                "trip_type": "special_round_trip",
                "passenger_count": 1,
                "reported_fare": 80.00,
                "expected_fare": 70.00,
                "fare_difference": 10.00,
                "distance_km": 1.5,
                "travel_time_min": 25,
                "body_number": "TT-0194",
                "photo_filename": None,
                "verification_status": "Pending",
                "posterior_probability": 0.648,
                "occurred_at": "2026-10-04 08:45:00",
                "created_at": "2026-10-04 09:15:00"
            },
            # 6. Oct 4, 2026 11:02 AM - Commuter #45 - Pinagbakahan (Regular, 2 pax: Official ₱27.50 × 2 = ₱55.00, Paid ₱60.00, Diff +₱5.00, 57.6%)
            {
                "user_id": 45,
                "route_id": get_rid("Pinagbakahan"),
                "origin": "Xentro Mall Terminal Hub",
                "destination": "Pinagbakahan",
                "trip_type": "regular",
                "passenger_count": 2,
                "reported_fare": 60.00,
                "expected_fare": 55.00,
                "fare_difference": 5.00,
                "distance_km": 3.5,
                "travel_time_min": 18,
                "body_number": "TG-0521",
                "photo_filename": None,
                "verification_status": "Pending",
                "posterior_probability": 0.576,
                "occurred_at": "2026-10-04 10:30:00",
                "created_at": "2026-10-04 11:02:00"
            }
        ]

        for rep in sample_reports:
            conn.execute("""
                INSERT INTO fare_reports (
                    user_id, route_id, origin, destination, trip_type, passenger_count,
                    reported_fare, expected_fare, fare_difference, distance_km,
                    travel_time_min, body_number, photo_filename, id_filename, verification_status,
                    posterior_probability, occurred_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rep["user_id"], rep["route_id"], rep["origin"], rep["destination"],
                rep["trip_type"], rep["passenger_count"], rep["reported_fare"],
                rep["expected_fare"], rep["fare_difference"], rep["distance_km"],
                rep["travel_time_min"], rep["body_number"], rep["photo_filename"],
                rep.get("id_filename", "id_sample_commuter17.png" if rep["user_id"] == 17 else None),
                rep["verification_status"], rep["posterior_probability"],
                rep.get("occurred_at", rep["created_at"]), rep["created_at"]
            ))

    # 4. Seed Sample Inquiries & Verification Messages between Admin and Reporter
    msg_count = conn.execute("SELECT COUNT(*) AS count FROM report_messages").fetchone()["count"]
    if msg_count == 0:
        first_rep = conn.execute("SELECT id, user_id FROM fare_reports WHERE user_id = 17 LIMIT 1").fetchone()
        if not first_rep:
            first_rep = conn.execute("SELECT id, user_id FROM fare_reports ORDER BY id ASC LIMIT 1").fetchone()

        admin_row = conn.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()

        if first_rep and admin_row:
            conn.execute("""
                INSERT INTO report_messages (report_id, user_id, message, created_at)
                VALUES (?, ?, ?, '2026-10-03 08:35:00')
            """, (
                first_rep["id"],
                admin_row["id"],
                "Good day Commuter #17. Could you please confirm if this was regular passenger queueing at the terminal or a private solo charter?"
            ))
            conn.execute("""
                INSERT INTO report_messages (report_id, user_id, message, created_at)
                VALUES (?, ?, ?, '2026-10-03 08:42:00')
            """, (
                first_rep["id"],
                first_rep["user_id"],
                "Hello Admin! Yes, it was regular queueing at the Xentro Mall terminal bay around 8:05 AM. The driver collected ₱30.00 instead of the standard ₱25.00 tariff."
            ))
            conn.execute("""
                INSERT INTO report_messages (report_id, user_id, message, created_at)
                VALUES (?, ?, ?, '2026-10-03 08:50:00')
            """, (
                first_rep["id"],
                admin_row["id"],
                "Thank you for clarifying. Your valid ID and attached evidence have been reviewed, and the report has been marked as Verified in the system."
            ))

    conn.commit()
    conn.close()

    # Ensure JSON file is created and synced
    sync_routes_to_json(db_path)

if __name__ == "__main__":
    init_db()
    print("Database initialized and synced with fare_matrix.json successfully.")
