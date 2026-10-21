# MALOLOS FAREWATCH
### Bayesian Tricycle Fare Deviation Monitoring System
**College Thesis / Research Prototype Decision-Support System**  
**Research Setting:** Xentro Mall Terminal Hub / Malolos City Terminal Hub, Malolos City, Bulacan, Philippines

---

## 1. System Overview

**Malolos FareWatch** is a research decision-support prototype developed for the thesis entitled:
> *"A Bayesian Probability Model for Estimating Tricycle Fare Deviation Likelihood Using Crowd-Sourced Commuter Fare Reports and Current Fare Matrix Data."*

The system aggregates crowd-sourced commuter fare reports, benchmarks them against an officially configured terminal fare matrix, and applies Bayes' theorem to compute the posterior deviation likelihood $P(A|B)$.

### System Scope & Ethics
- **Decision-Support and Monitoring System**: Designed for commuters, terminal administrators, and local government unit (LGU) transport personnel.
- **Non-Accusatory Framework**: The system does **not** automatically accuse drivers, declare drivers legally guilty, impose fines or legal penalties, nor replace authorized LGU traffic enforcement.
- **Hardware-Free**: Does not rely on GPS tracking, IoT sensors, or electronic taximeters.
- **Privacy-Preserving**: Public community reports strictly display anonymized identifiers (e.g., `Commuter #17`, `Commuter #24`) and never expose usernames, phone numbers, or emails.

---

## 2. Project Directory Structure

```text
AntiGrav System/
│
├── static/
│   ├── uploads/                   # Secure storage for uploaded evidence photos
│   │   ├── evidence_sample_1.png  # Demo ticket evidence #1
│   │   ├── evidence_sample_2.png  # Demo ticket evidence #2
│   │   ├── evidence_sample_3.png  # Demo ticket evidence #3
│   │   └── evidence_sample_4.png  # Demo ticket evidence #4
│   ├── main.js                    # Client-side scripts (sidebar drawer, photo preview, modal)
│   ├── style.css                  # UI Design System & responsive styling
│   └── terminal_hub_logo.png      # Official Malolos City Terminal Hub / XentroMall emblem
│
├── templates/
│   ├── admin_dashboard.html       # Admin route monitoring summary & likelihood rankings
│   ├── admin_reports.html         # Admin report verification, rejection, and review
│   ├── admin_routes.html          # Admin route creation, fare modification, and toggling
│   ├── base.html                  # Shell layout (sidebar, header, breadcrumbs, watermark)
│   ├── dashboard.html             # Commuter dashboard with 4 KPI cards and recent reports
│   ├── fare_matrix.html           # Baseline official fare matrix with research notice
│   ├── fare_reports.html          # Community reports table with horizontal filters & lightbox
│   ├── index.html                 # Institutional landing page with hero and feature cards
│   ├── login.html                 # Login card with default account credentials helper
│   ├── my_reports.html            # Personal submission history and status tracking
│   ├── profile.html               # User profile metadata and secure password change form
│   ├── register.html              # Commuter registration form
│   └── report_details.html        # Comprehensive report view with step-by-step Bayesian math
│
├── app.py                         # Flask application controller and routes
├── bayesian_model.py              # Bayesian probability formulation and likelihood engine
├── database.py                    # SQLite database schema, seeding, and connection manager
├── fare_system.db                 # Relational SQLite database
├── requirements.txt               # Python package dependencies
├── test_system.py                 # Automated unit and integration test suite
└── README.md                      # Complete system documentation
```

---

## 3. Installation Requirements

- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14
- **Operating System**: Windows, macOS, or Linux
- **Web Browser**: Any modern browser (Google Chrome, Microsoft Edge, Mozilla Firefox, Opera)

---

## 4. Exact Installation Commands

Open PowerShell or Command Prompt in the project folder:

```powershell
# Navigate into the project folder
cd "d:\School\2026-2027 SY\THESIS\AntiGrav System"

# Install required dependencies
pip install -r requirements.txt
```

---

## 5. Database Initialization

The database schema and thesis seed data can be initialized or reset at any time using:

```powershell
python database.py
```

This will automatically create `fare_system.db` with all tables, initial routes, sample commuters, and realistic sample reports.

---

## 6. How to Start the Development Server

To launch the web application:

```powershell
python app.py
```

You will see output similar to:
```text
Malolos FareWatch application started at http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

## 7. Local URL

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 8. Default Login Credentials

### Administrator Account
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Administrator (Access to Monitoring Dashboard, Manage Routes, Manage Reports)

### Commuter Demo Accounts
- **Username:** `juandelacruz`
- **Password:** `commuter123`
- **Role:** Commuter (Commuter #17)

*(Additional demo commuters: `mariasantos`, `pedroreyes`, `claradelrosario`, `joserizal` with password `commuter123`)*

---

## 9. How to Change the Administrator Password

1. Log in with the `admin` account.
2. In the top navigation header or sidebar, click on **Profile**.
3. Under the **Security Credentials** card, enter:
   - Current password (`admin123`)
   - New password
   - Confirm new password
4. Click **Update Password**.
5. The password will be hashed using `werkzeug.security.generate_password_hash` and updated in the database.

---

## 10. How Uploaded Photos are Stored

- Uploaded fare evidence photos are saved to the directory:
  ```text
  static/uploads/
  ```
- **Security Protections:**
  - Files are renamed using a cryptographically random UUID (`uuid.uuid4().hex`) combined with a Unix timestamp and the sanitized file extension (e.g., `evidence_8a4f1c9...png`).
  - Original client-supplied filenames are never executed or stored directly.
  - Allowed image file types are strictly limited to `.png`, `.jpg`, `.jpeg`, and `.webp`.
  - Maximum upload size is enforced at **5 MB**.
  - Uploaded files are served through a controlled Flask route (`/uploads/<filename>`) using `werkzeug.utils.secure_filename` to prevent path traversal attacks.

---

## 11. How to Replace the Development Fare Matrix

### Via the Administrator User Interface (Recommended)
1. Log in as `admin`.
2. Navigate to **Manage Routes** in the sidebar.
3. To update an existing fare: Modify the numeric fare input beside any route and click **Update**.
4. To add a new LGU-approved route: Fill in the **Route Origin & Destination** and **Official Matrix Fare**, then click **Add Route**.
5. To disable a route without breaking historical reports: Click **Deactivate**.

### Directly in the Database Seeder
Edit the `default_routes` list in [`database.py`](file:///d:/School/2026-2027%20SY/THESIS/AntiGrav%20System/database.py#L71-L82):
```python
default_routes = [
    ("Xentro Mall → Malolos Proper", 20.00),
    ("Xentro Mall → Calumpit", 25.00),
    ("Xentro Mall → Bulihan", 20.00),
    # Add or update routes with actual LGU ordinance values
]
```
Then re-run `python database.py`.

---

## 12. How to Replace the Development Bayesian Parameters

Open [`bayesian_model.py`](file:///d:/School/2026-2027%20SY/THESIS/AntiGrav%20System/bayesian_model.py#L27-L32).

The baseline placeholder parameters are defined as constants:
```python
# Baseline development parameters as defined in thesis proposal specifications
DEFAULT_PRIOR = 0.50
DEFAULT_LIKELIHOOD_DEVIATION = 0.90
DEFAULT_LIKELIHOOD_NO_DEVIATION = 0.10
```

To update the parameters based on your empirical study data:
1. Update `DEFAULT_PRIOR` with the empirical route deviation frequency derived from your preliminary survey or terminal dispatch records.
2. In `calculate_bayesian_likelihood()`, calibrate `p_b_given_a` (likelihood of observing evidence given deviation exists) and `p_b_given_not_a` (likelihood of false report given compliance) using your research data.
3. Update the note in `bayesian_model.py` and `report_details.html` to cite your validated thesis survey parameters.

---

## 13. Running Automated Tests

A comprehensive integration test suite is included in `test_system.py`. To run the tests:

```powershell
python test_system.py
```

All 10 test cases verify landing page rendering, commuter authentication, admin RBAC, route management, fare reporting, Bayesian calculations, and status persistence.


### Privacy note
Commuter valid IDs are stored outside `static/` in `private_uploads/ids/` and are served only through an administrator-authenticated endpoint. They are never rendered on the public Fare Reports pages. Fare evidence supports both photos and videos.
