"""
Comprehensive Integration & Verification Test Suite for Malolos FareWatch
Tests all pages, authentication, RBAC, Bayesian model, and database actions.
"""

import os
import unittest
from app import app
from database import init_db, get_db

class MalolosFareWatchTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["DATABASE"] = "test_fare_system.db"
        self.client = app.test_client()
        init_db(app.config["DATABASE"])

    def tearDown(self):
        if os.path.exists("test_fare_system.db"):
            try:
                os.remove("test_fare_system.db")
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        from database import sync_routes_to_json, DB_FILE
        sync_routes_to_json(DB_FILE)


    def login(self, username, password):
        return self.client.post("/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_01_landing_page(self):
        """Test landing page loads without error."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"MALOLOS", resp.data)
        self.assertIn(b"FAREWATCH", resp.data)
        self.assertIn(b"See the fare. Understand the difference.", resp.data)

    def test_02_login_commuter(self):
        """Test commuter login."""
        resp = self.login("juandelacruz", "commuter123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Welcome back", resp.data)
        self.assertIn(b"Dashboard", resp.data)

    def test_03_login_admin(self):
        """Test administrator login."""
        resp = self.login("admin", "admin123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Administrator", resp.data)

    def test_04_role_based_access_control(self):
        """Test commuter cannot access admin dashboard."""
        self.login("juandelacruz", "commuter123")
        resp = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Access denied", resp.data)

    def test_05_fare_matrix_page(self):
        """Test fare matrix renders all active routes."""
        self.login("juandelacruz", "commuter123")
        resp = self.client.get("/fare-matrix")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Xentro Mall", resp.data)
        self.assertIn(b"MCXMTODA Approved Rates", resp.data)
        self.assertIn(b"MTPFRB BLG. 2024-02", resp.data)

    def test_06_fare_reports_page_and_filtering(self):
        """Test community fare reports and filtering."""
        self.login("juandelacruz", "commuter123")
        resp = self.client.get("/fare-reports")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Commuter #17", resp.data)
        self.assertIn(b"72.4%", resp.data)
        self.assertIn(b"5.2%", resp.data)
        self.assertIn(b"Showing", resp.data)

        # Test likelihood filter
        resp_high = self.client.get("/fare-reports?likelihood=high")
        self.assertEqual(resp_high.status_code, 200)
        self.assertIn(b"91.3%", resp_high.data)

    def test_07_submit_fare_report(self):
        """Test submitting a new fare report with Point A, Point B, and trip arrangement."""
        self.login("juandelacruz", "commuter123")
        from datetime import datetime, timedelta
        valid_trip_time = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")

        resp = self.client.post("/report", data={
            "origin_choice": "Xentro Mall Terminal Hub",
            "destination_choice": "San Jose",
            "route_id": "1",
            "trip_type": "regular",
            "passenger_count": "1",
            "reported_fare": "25.00",
            "distance_km": "1.0",
            "travel_time_min": "14",
            "body_number": "TM-9988",
            "occurred_at": valid_trip_time
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Bayesian Probability Model Breakdown", resp.data)
        self.assertIn(b"Report Overview", resp.data)
        self.assertIn(b"San Jose", resp.data)
        self.assertIn(b"TM-9988", resp.data)
        self.assertIn(b"Date &amp; Time Occurred", resp.data)
        self.assertIn(b"Date &amp; Time Reported", resp.data)

    def test_08_admin_manage_reports(self):
        """Test admin verifying and rejecting reports."""
        self.login("admin", "admin123")
        resp = self.client.get("/admin/reports")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Manage Fare Reports", resp.data)

        # Update report #5 status to Verified
        resp_update = self.client.post("/admin/reports/5/status", data={
            "status": "Verified"
        }, follow_redirects=True)
        self.assertEqual(resp_update.status_code, 200)
        self.assertIn(b"status updated to Verified", resp_update.data)

    def test_09_admin_manage_routes(self):
        """Test admin adding and updating routes."""
        self.login("admin", "admin123")
        resp_add = self.client.post("/admin/routes/add", data={
            "name": "Xentro Mall \u2192 Barasoain Church",
            "official_fare": "18.00"
        }, follow_redirects=True)
        self.assertEqual(resp_add.status_code, 200)
        self.assertIn(b"Barasoain Church", resp_add.data)

        # Update fare
        conn = get_db(app.config["DATABASE"])
        r = conn.execute("SELECT id FROM routes WHERE name LIKE '%Barasoain%'").fetchone()
        conn.close()

        resp_edit = self.client.post(f"/admin/routes/{r['id']}/edit", data={
            "name": "Xentro Mall \u2192 Barasoain Church",
            "official_fare": "20.00"
        }, follow_redirects=True)
        self.assertEqual(resp_edit.status_code, 200)
        self.assertIn(b"saved to fare_matrix.json", resp_edit.data)


    def test_10_profile_and_password_change(self):
        """Test user profile and changing password."""
        self.login("juandelacruz", "commuter123")
        resp = self.client.get("/profile")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Account Information", resp.data)

        resp_pw = self.client.post("/profile/change-password", data={
            "current_password": "commuter123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }, follow_redirects=True)
        self.assertEqual(resp_pw.status_code, 200)
        self.assertIn(b"Password updated successfully", resp_pw.data)

    def test_11_24_hour_timing_restriction(self):
        """Test strict enforcement that commuters can only report trips occurring within the last 24 hours."""
        self.login("juandelacruz", "commuter123")
        from datetime import datetime, timedelta

        # 1. Trip occurring 26 hours ago (Exceeds 24 hours limit) -> Must be rejected
        stale_time = (datetime.now() - timedelta(hours=26)).strftime("%Y-%m-%dT%H:%M")
        resp_stale = self.client.post("/report", data={
            "origin_choice": "Xentro Mall Terminal Hub",
            "destination_choice": "San Jose",
            "route_id": "1",
            "trip_type": "regular",
            "passenger_count": "1",
            "reported_fare": "20.00",
            "occurred_at": stale_time
        }, follow_redirects=True)
        self.assertEqual(resp_stale.status_code, 200)
        self.assertIn(b"Submission restricted: Reports can only be submitted for trips that occurred within the last 24 hours.", resp_stale.data)

        # 2. Trip occurring in the future (+2 hours) -> Must be rejected
        future_time = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        resp_future = self.client.post("/report", data={
            "origin_choice": "Xentro Mall Terminal Hub",
            "destination_choice": "San Jose",
            "route_id": "1",
            "trip_type": "regular",
            "passenger_count": "1",
            "reported_fare": "20.00",
            "occurred_at": future_time
        }, follow_redirects=True)
        self.assertEqual(resp_future.status_code, 200)
        self.assertIn(b"Invalid trip time: Trip occurrence date and time cannot be in the future.", resp_future.data)

        # 3. Missing occurred_at -> Must prompt user
        resp_missing = self.client.post("/report", data={
            "origin_choice": "Xentro Mall Terminal Hub",
            "destination_choice": "San Jose",
            "route_id": "1",
            "trip_type": "regular",
            "passenger_count": "1",
            "reported_fare": "20.00",
            "occurred_at": ""
        }, follow_redirects=True)
        self.assertEqual(resp_missing.status_code, 200)
        self.assertIn(b"Please provide a valid date and time when the trip occurred.", resp_missing.data)

        # 4. Valid trip occurring 3 hours ago -> Must succeed
        valid_time = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
        resp_valid = self.client.post("/report", data={
            "origin_choice": "Xentro Mall Terminal Hub",
            "destination_choice": "Catmon",
            "route_id": "2",
            "trip_type": "regular",
            "passenger_count": "1",
            "reported_fare": "25.00",
            "occurred_at": valid_time
        }, follow_redirects=True)
        self.assertEqual(resp_valid.status_code, 200)
        self.assertIn(b"Your fare report has been submitted successfully!", resp_valid.data)
        self.assertIn(b"Within 24h Window Verified", resp_valid.data)

if __name__ == "__main__":
    unittest.main()
