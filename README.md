# Lab4-MayssaHajjHassan_AhmadAbbas

This project focuses on developing user interfaces using both tkinter and PyQt frameworks. The project demonstrates the implementation of GUI applications using Python's two main GUI libraries.

## Technologies Used
- **tkinter**: Python's built-in GUI toolkit for creating desktop applications
- **PyQt**: A comprehensive set of Python bindings for the Qt application framework

## Project Structure
The project includes implementations of GUI applications using both frameworks, showcasing different approaches to desktop application development in Python.

## Getting Started

### Prerequisites
- Python 3.x installed on your system
- macOS, Linux, or Windows operating system

### Installation and Setup

Follow these step-by-step commands to set up and run the PyQt School Management System:

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
   source venv/bin/activate
   ```
   *Note: On Windows, use `venv\Scripts\activate` instead*

4. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the PyQt School Management System:**
   ```bash
   python PyQt.py
   ```

### What You'll See
The application will open with a graphical interface featuring:
- **Students Tab**: Manage student records (add, edit, delete, search)
- **Instructors Tab**: Manage instructor records (add, edit, delete, search)
- **Courses Tab**: Manage courses, enroll students, and assign instructors
- **Menu Bar**: File operations (Save/Load data, Export to CSV)

### Deactivating the Virtual Environment
When you're done, deactivate the virtual environment:
```bash
deactivate
```
=======
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

**Run**

```bash
python3 tkinter-ui.py
```

**Buttons (top bar):**

* **Save JSON** → exports all data to `school_data.json`
* **Export CSV** → exports all tables into one CSV with section headers
* **Load JSON** → imports from a JSON file (upsert)
* **Backup DB** → saves a copy of `school.db`

**Requirements:**

* Python 3.9+ with `tkinter` and `sqlite3` available.

  * Ubuntu/Debian: `sudo apt install -y python3-tk sqlite3`
  * Fedora: `sudo dnf install -y python3-tkinter sqlite`
  * macOS (Homebrew): `brew install python tcl-tk sqlite`
  * Windows: install Python from python.org (ensure **tcl/tk** component is selected).

> No pip packages are required for this Tkinter app.


