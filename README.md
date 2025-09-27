# FaceAttend-System (QR + Face Recognition) — Full Documentation

A desktop attendance app built with **Python**, **CustomTkinter**, **OpenCV**, **face_recognition**, **MySQL**, and **QR codes**.
It supports:

* ✅ QR-code–based check-in
* ✅ Face-recognition check-in
* ✅ CSV log + MySQL persistence
* ✅ Student registration & login
* ✅ Searchable student directory
* ✅ Full-screen kiosk-style UI

---

## Table of Contents

* [Demo & Screenshots](#demo--screenshots)
* [Features](#features)
* [Architecture](#architecture)
* [Tech Stack](#tech-stack)
* [Folder Structure](#folder-structure)
* [Database Schema](#database-schema)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the App](#running-the-app)
* [Usage Guide](#usage-guide)
* [CSV Log Format](#csv-log-format)
* [How Face Recognition Works](#how-face-recognition-works)
* [QR Workflow](#qr-workflow)
* [Security & Privacy Notes](#security--privacy-notes)
* [Troubleshooting](#troubleshooting)
* [Known Limitations](#known-limitations)
* [Performance Tips](#performance-tips)
* [Extending the App](#extending-the-app)
* [License](#license)

---

## Demo & Screenshots

> Add screenshots of:
>
> 1. **StartWindow** (Staff vs Student)
> 2. **Main Screen** (QR / Face / Search)
> 3. **QR Scanner** overlay
> 4. **Face Recognition** overlay
> 5. **Student Detail** page

```
/docs/images/start.png
/docs/images/main.png
/docs/images/qr.png
/docs/images/face.png
/docs/images/detail.png
```

---

## Features

* **Two attendance modes**

  * **QR** scanner using `cv2.QRCodeDetector`
  * **Face recognition** using `face_recognition` (dlib)
* **Persistence**

  * **Attendance.csv** (quick export & audit)
  * **MySQL** `attendance` table (query/report at scale)
* **User flows**

  * **Staff** login → choose QR / Face / Search
  * **Student** register & login → see personal details + last status
* **Search**

  * Type-ahead **student search** + full list view
* **Kiosk-ready UI**

  * Full-screen **CustomTkinter** with background imagery
* **Auto QR generation**

  * Generates QR images for each person in `AttendanceList/`

---

## Architecture

```
UI (CustomTkinter)
 ├─ StartWindow(): Role picker (Staff / Student)
 ├─ StaffloginScreen() → mainScreen()
 │   ├─ takeQRAttendance() → showAttendanceDetailsQR()
 │   ├─ takeFaceRecognitionAttendance() → showAttendanceDetailsFaceRecognition()
 │   └─ open_search_window() → student detail modal
 └─ studentMenu() → studentRegisterPage() / studentLoginPage()

Core
 ├─ AttendanceList/        # source images for known faces
 ├─ findEncodings()        # build encodings for known faces
 ├─ markAttendance(name)   # CSV + MySQL write
 ├─ QR generator           # build QR for each name in AttendanceList/
 └─ Attendance.csv         # append-only log

Storage
 ├─ MySQL: registration (students), attendance (events)
 └─ CSV: local audit trail
```

---

## Tech Stack

* **Python 3.10+**
* **GUI**: `customtkinter`, `Pillow`
* **Vision**: `opencv-python`, `face_recognition` (requires `dlib`)
* **Data**: `mysql-connector-python`, CSV
* **QR**: `qrcode[pil]`

---

## Folder Structure

```
.
├─ AttendanceList/          # input face images (jpg/png, filename = person's name)
├─ AttendanceListQR/        # auto-generated QR images (one per person)
├─ assets/
│  ├─ Background_Image2.jpg
│  ├─ passshow.png
│  └─ close2.png
├─ Attendance.csv           # created on first write
├─ app.py                   # your main script (this repo's code)
├─ requirements.txt
└─ docs/
   └─ images/               # screenshots for README
```

> **Important**: The code uses `"Background_Image2.jpg"`, `"passshow.png"`, and `"close2.png"` in the working directory.

---

## Database Schema

Create the database and tables:

```sql
CREATE DATABASE IF NOT EXISTS testdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE testdb;

-- Student master
CREATE TABLE IF NOT EXISTS registration (
  Name         VARCHAR(100) NOT NULL,
  ClassSection VARCHAR(50)  NOT NULL,
  DOB          VARCHAR(20)  NOT NULL,  -- Consider DATE type in future
  Gender       VARCHAR(20)  NOT NULL,
  Nationality  VARCHAR(50)  NOT NULL,
  Email        VARCHAR(100) NOT NULL,
  PhoneNo      VARCHAR(30)  NOT NULL,
  AdmissionNo  VARCHAR(50)  NOT NULL PRIMARY KEY,
  Password     VARCHAR(255) NOT NULL   -- Hash in production
);

-- Attendance events
CREATE TABLE IF NOT EXISTS attendance (
  id    INT AUTO_INCREMENT PRIMARY KEY,
  Name  VARCHAR(100) NOT NULL,
  Date  VARCHAR(20)  NOT NULL,  -- Consider DATE type in future
  Time  VARCHAR(20)  NOT NULL,  -- Consider TIME type in future
  Status VARCHAR(20) NOT NULL
);

-- Helpful index if querying by name
CREATE INDEX idx_attendance_name ON attendance (Name);
```

---

## Installation

1. **System prerequisites**

* Windows: Install **Visual Studio Build Tools** (C++), and **CMake** (for `dlib` if needed).
* macOS: `xcode-select --install`
* Linux: `sudo apt install build-essential cmake`

2. **Python & virtual environment**

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

3. **Dependencies**

`requirements.txt`:

```
customtkinter
opencv-python
numpy
face-recognition
qrcode[pil]
Pillow
mysql-connector-python
```

Install:

```bash
pip install -r requirements.txt
```

> If `face-recognition` fails due to `dlib`, try `pip install dlib==19.24.4` or install a prebuilt wheel for your platform.

---

## Configuration

### 1) MySQL credentials

The code currently uses **hardcoded credentials**:

```py
mysql.connector.connect(host="localhost", user="root", passwd="OIS@12345", database="testdb")
```

**Recommended**: move secrets to environment variables.

Create a `.env` (and load with `python-dotenv` if you like):

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=OIS@12345
DB_NAME=testdb
```

Update connection calls to read from `os.getenv`.

### 2) Folders

* Ensure **AttendanceList/** exists and contains **one face image per person**.
  The **filename (without extension) = person’s name** (e.g., `Ayaan.jpg`).

* Ensure **AttendanceListQR/** exists (for generated QR codes).

* Place UI assets (`Background_Image2.jpg`, `passshow.png`, `close2.png`) in the working dir.

---

## Running the App

```bash
python app.py
```

* **Esc** toggles full-screen in most windows.
* Start → choose **STAFF** or **STUDENT**.

---

## Usage Guide

### Staff Flow

1. **Login**

   * Username: `12F`
   * Password: `OIS@12345`

   > Change these in `StaffloginScreen()` for production.

2. **Main Screen**

   * **Face Recognition Attendance**

     * Uses the webcam.
     * Detects known faces from `AttendanceList/`, draws boxes & names, marks attendance.
   * **QR Code Attendance**

     * Uses the webcam to read QR values (the person’s name).
     * On scan, draws bounding box, writes to CSV + DB.
   * **Student Search**

     * Type to filter / view all, click a name to open details.

3. **Details Screens**

   * After marking attendance, a summary shows the **most recent record**.
   * Buttons to **Open Records** (CSV), **Take Next Attendance**, **Switch Mode**, or **Logout**.

### Student Flow

* **Register**

  * Fill the form; persists to `registration` table.
* **Login**

  * Admission No + Password → view personal profile and last status.

---

## CSV Log Format

**File**: `Attendance.csv`
Each new unique name (per session run) appends:

```
<Name>,<Date as %m/%d/%y>,<Time as %H:%M:%S>,"PRESENT"
```

> The code uses `%D` in places which formats as **mm/dd/yy** (US). Consider using ISO dates (`%Y-%m-%d`).

---

## How Face Recognition Works

1. **Known encodings** are built at startup from images in `AttendanceList/`.
2. For each webcam frame:

   * Downscale 0.25× for speed.
   * Detect face locations & compute encodings.
   * Compare to known encodings via `compare_faces` & `face_distance`.
   * If matched, show the **name** (from filename) and **mark attendance**.

**Tips:**

* One clear, front-facing image per person works best.
* Good lighting and camera quality improve accuracy.
* You can add multiple samples per person and average/aggregate encodings (future enhancement).

---

## QR Workflow

1. On startup, the app:

   * Reads filenames from `AttendanceList/`
   * Generates a QR **per person name** into `AttendanceListQR/`.
2. During scanning:

   * Detects QR, decodes **string value = name**
   * Calls `markAttendance(name)`

---

## Security & Privacy Notes

* **Passwords** (student login) are stored **in plaintext** in DB and shown in code.
  → **Use hashing** (e.g., `bcrypt`) and never log/store raw passwords.
* **DB credentials** are hardcoded.
  → Move to environment variables / secrets manager.
* **Faces are biometric data**.
  → Obtain consent, provide a privacy notice, and comply with local laws (e.g., UAE PDPL/GDPR equivalents).
* **CSV** is append-only and unencrypted.
  → Restrict file permissions and rotate/export securely.

---

## Troubleshooting

* **`face_recognition` / `dlib` build errors**

  * Install a prebuilt wheel compatible with your Python/OS.
  * Ensure CMake & C++ Build Tools are installed (Windows).

* **Webcam not opening**

  * Check `cv2.VideoCapture(0)` index; try `1` or `2`.
  * Close other apps using the camera.

* **No faces detected**

  * Ensure `AttendanceList/` images exist, are readable, and contain clear faces.
  * Lighting & camera positioning matter.

* **QR not detected**

  * Increase QR size/print quality. Maintain steady frame.
  * Ensure high contrast (black on white).

* **MySQL errors**

  * Confirm DB is running, credentials are correct, tables exist.

---

## Known Limitations

* **Hardcoded credentials** (`root`/`OIS@12345`) in code.
* **Date/time strings** stored as text in DB; not proper `DATE/TIME`.
* **CSV append**: no header and no rotation/limit.
* **Duplicate attendance control**: Only blocks duplicates per **CSV session** based on simple name check (no per-day uniqueness).
* **Error handling** is minimal; UI assumes happy paths.
* **Blocking UI**: capture loops run on the main thread; no background threads.

---

## Performance Tips

* In `takeFaceRecognitionAttendance()` a **frame skip** is used:

  ```py
  frame_skip = 10
  for _ in range(frame_skip): cap.grab()
  ```

  Adjust `frame_skip` to balance CPU vs responsiveness.

* Downscaling to 0.25× is already applied—keep it for speed.

* Precompute encodings once at startup (already done). If you add students at runtime, rebuild encodings or cache per person.

---

## Extending the App

* ✅ **Env config**: Switch all DB creds to `.env` + `python-dotenv`.
* ✅ **Password hashing**: Store `bcrypt` hashes; add password reset flow.
* ✅ **Per-day attendance rule**: Only allow one “PRESENT” per person per date.
* ✅ **Admin dashboard**: Export daily/monthly reports; charts by class/section.
* ✅ **Threading**: Run camera capture in a background thread; keep UI responsive.
* ✅ **API layer**: Expose a REST API (FastAPI) for attendance queries and future mobile apps.
* ✅ **Better dates**: Use `DATE` and `TIME` (or `DATETIME`) columns in MySQL.
* ✅ **Packaging**: Build an executable with `pyinstaller` for deployment.

---

## Notes on the Current Code (Quick Review)

* `time = datetime.now()` shadows the imported `time` module.
  → Rename the variable to avoid breaking `time.perf_counter()` usage.
* QR generation block does:

  ```py
  path2 = "AttendanceListQR"
  files = os.listdir(path)  # reads from AttendanceList
  ```

  That’s fine; just ensure `AttendanceListQR/` **exists** before saving.
* `Attendance.csv` is assumed to exist; if not, open in `a+` and write a header once.
* Repeated MySQL connections: consider a helper function or context manager.
* String dates use `%D` (US format). Prefer `%Y-%m-%d`.

---

### Quick Start (TL;DR)

```bash
# 1) Create DB/tables (see schema above)
# 2) Put face images into AttendanceList/ (filename = Name.jpg)
mkdir -p AttendanceList AttendanceListQR

# 3) Install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4) Run
python app.py
```
