# Lab4-MayssaHajjHassan_AhmadAbbas

This project focuses on developing user interfaces using both **tkinter** and **PyQt** frameworks. The repository demonstrates two desktop applications that manage a simple School Management System backed by SQLite.

## Technologies Used
- **tkinter** – Python's built-in GUI toolkit for creating desktop applications  
- **PyQt** – Python bindings for the Qt application framework  
- **SQLite** – Lightweight embedded database (`sqlite3` stdlib)

## Project Structure
The project includes implementations of GUI applications using both frameworks, showcasing different approaches to desktop application development in Python.

**Top-level files**
- **PyQt app**
  - `PyQt.py` — main PyQt GUI
  - `database_pyqt.py` — DB helpers for the PyQt app
  - `classes.py` — helper module for the PyQt part 
- **Tkinter app**
  - `tkinter-ui.py` — main Tkinter GUI
  - `utils.py` — repository/service layer (validation, CRUD, import/export)
  - `database.py` — SQLite helpers + schema creation
- **Data**
  - `school.db` — SQLite database (auto-created on first run)

---

## Getting Started

### Prerequisites
- Python 3.x installed on your system
- macOS, Linux, or Windows operating system

### Installation and Setup

Follow these step-by-step commands to set up and run the **PyQt** School Management System:
Use this one-liner:

```bash
git clone https://github.com/<your-username>/Lab4-MayssaHajjHassan_AhmadAbbas.git && cd Lab4-MayssaHajjHassan_AhmadAbbas
```

1. **Navigate to the project directory:**
   ```bash
   cd /path/to/Lab4-MayssaHajjHassan_AhmadAbbas
```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**

   ```bash
   # macOS/Linux
   source venv/bin/activate
   # Windows (PowerShell)
   # .\venv\Scripts\Activate.ps1
   ```

4. **Install required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the PyQt School Management System:**

   ```bash
   python PyQt.py
   ```

**What you'll see (PyQt):**

* **Students Tab** — add, edit, delete, search students
* **Instructors Tab** — add, edit, delete, search instructors
* **Courses Tab** — manage courses, enroll students, assign instructors
* **Menu/File** — save/load data, export to CSV

---

### Tkinter App — School Management System

A small desktop GUI (Tkinter) that manages **Students**, **Instructors**, and **Courses** with an SQLite database.

**Files (repo root):**

* `tkinter-ui.py` — GUI (tabs, forms, tables, buttons).
* `utils.py` — repository/service layer (validation, CRUD, import/export).
* `database.py` — SQLite helpers + schema creation.

**Features:**

* Create / update / delete students, instructors, courses
* Assign instructors to courses
* Register students in courses
* **Export JSON**, **Load JSON**, **Export CSV**, **Backup DB**
* Live search in each tab

**Data storage:**

* Uses `school.db` (auto-created next to the files).
* On first run, if `school_data.json` exists, it’s imported automatically.

**Run (Tkinter)**

```bash
python3 tkinter-ui.py
```

**Buttons (top bar):**

* **Save JSON** → exports all data to `school_data.json`
* **Export CSV** → exports all tables into one CSV with section headers
* **Load JSON** → imports from a JSON file (upsert)
* **Backup DB** → saves a copy of `school.db`

**Requirements for Tkinter runtime (OS packages):**

* Ubuntu/Debian: `sudo apt install -y python3-tk sqlite3`
* Fedora: `sudo dnf install -y python3-tkinter sqlite`
* macOS (Homebrew): `brew install python tcl-tk sqlite`
* Windows: install Python from python.org (ensure **tcl/tk** is selected)

> No extra pip packages are required for the Tkinter app.

---

### Deactivating the Virtual Environment

```bash
deactivate
```

