"""Repository layer between GUI and DB.

This module exposes higher-level operations that the GUIs call.

Highlights
----------
- Validation helpers: :func:`valid_email`, :func:`valid_age`
- CRUD for students, instructors, courses
- Assign / Register operations
- Dropdown helpers (IDs)
"""

# part4_repo.py
# i am the middle guy between GUI and DB. i translate human vibes to SQL vibes.

import csv
import json
import re

# Robust import so it works both as a package (lab3_files.lab3_repo)
# and as a local script (lab3_repo.py next to lab3_db.py).

from database import run, fetch_one, fetch_all, init_db, backup_db as _backup_db, DB_PATH as _DB_PATH

# make sure DB exists (in case someone forgets to import part4_db first)
init_db()

import sqlite3

DB_PATH = _DB_PATH


def connect(path=DB_PATH):
    """Open a SQLite connection with foreign-keys enabled.

    Parameters
    ----------
    path : str, optional
        Database file path, by default ``"school.db"``.

    Returns
    -------
    sqlite3.Connection
    """
    # open db plz. we also turn on foreign keys because... safety vibes
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
    except:
        pass
    return conn


def list_students(conn):
    """(CSV helper) Return raw student tuples using an existing connection.

    Parameters
    ----------
    conn : sqlite3.Connection

    Returns
    -------
    list[tuple]
        Rows: ``(student_id, name, age, email)``.
    """
    cur = conn.cursor()
    # if  column names differ, tweak this SELECT (no shame)
    cur.execute("SELECT student_id, name, age, email FROM students ORDER BY student_id")
    return cur.fetchall()


def list_instructors(conn):
    """(CSV helper) Return raw instructor tuples using an existing connection.

    Parameters
    ----------
    conn : sqlite3.Connection

    Returns
    -------
    list[tuple]
        Rows: ``(instructor_id, name, age, email)``.
    """
    cur = conn.cursor()
    cur.execute("SELECT instructor_id, name, age, email FROM instructors ORDER BY instructor_id")
    return cur.fetchall()


def list_courses(conn):
    """(CSV helper) Return raw course tuples using an existing connection.

    Parameters
    ----------
    conn : sqlite3.Connection

    Returns
    -------
    list[tuple]
        Rows: ``(course_id, course_name, instructor_id)``.
    """
    cur = conn.cursor()
    cur.execute("SELECT course_id, course_name, instructor_id FROM courses ORDER BY course_id")
    return cur.fetchall()


def list_registrations(conn):
    """(CSV helper) Return raw registration tuples using an existing connection.

    Parameters
    ----------
    conn : sqlite3.Connection

    Returns
    -------
    list[tuple]
        Rows: ``(student_id, course_id)``.
    """
    cur = conn.cursor()
    cur.execute("SELECT student_id, course_id FROM registrations ORDER BY student_id, course_id")
    return cur.fetchall()


# validators (keep same vibes as earlier parts)
def valid_email(x):
    """Lightweight email validation: ``something@something.tld``."""
    try:
        x = (x or "").strip()
        # not too strict. just "a@b.something"
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", x))
    except:
        return False


def valid_age(x):
    """Return True iff ``x`` parses as an int â‰¥ 0."""
    try:
        a = int(x)
        return a >= 0
    except:
        return False


def _row_to_dict(row):
    """Convert a ``sqlite3.Row`` to a plain ``dict``."""
    try:
        return dict(row)
    except:
        return None


def student_email_exists(email, exclude_id=None):
    """Check uniqueness of student email.

    Parameters
    ----------
    email : str
    exclude_id : str, optional
        Skip this student id (when editing).

    Returns
    -------
    bool
    """
    if exclude_id:
        row = fetch_one("SELECT 1 FROM students WHERE lower(email)=lower(?) AND student_id<>?", (email, exclude_id))
    else:
        row = fetch_one("SELECT 1 FROM students WHERE lower(email)=lower(?)", (email,))
    return row is not None


def add_student(name, age, email, student_id):
    """Insert a student."""
    try:
        age = int(age)
    except:
        age = 0
    try:
        q = """INSERT INTO students(student_id, name, age, email)
               VALUES(?,?,?,?)"""
        ok = run(q, (student_id, name, age, email), commit=True)
        return ok is not None
    except Exception as e:
        print("add_student error:", e)
        return False


def update_student(student_id, name, age, email):
    """Update a student row by id."""
    try:
        age = int(age)
    except:
        age = 0
    try:
        q = "UPDATE students SET name=?, age=?, email=? WHERE student_id=?"
        ok = run(q, (name, age, email, student_id), commit=True)
        return ok is not None
    except Exception as e:
        print("update_student error:", e)
        return False


def delete_student(student_id):
    """Delete a student by id."""
    try:
        q = "DELETE FROM students WHERE student_id=?"
        ok = run(q, (student_id,), commit=True)
        return ok is not None
    except Exception as e:
        print("delete_student error:", e)
        return False


def get_student(student_id):
    """Get a student row as dict (or None)."""
    row = fetch_one("SELECT * FROM students WHERE student_id=?", (student_id,))
    return _row_to_dict(row) if row else None


# alias to match old core naming
def get_student_by_id(student_id):
    """Alias for :func:`get_student`."""
    return get_student(student_id)


def student_courses(student_id):
    """Return a list of course_ids a student is registered in."""
    rows = fetch_all("SELECT course_id FROM registrations WHERE student_id=? ORDER BY course_id", (student_id,))
    return [r["course_id"] for r in rows]


def list_students(search_text=""):
    """Dual-mode students list.

    If ``search_text`` is a :class:`sqlite3.Connection`, return raw tuples
    for CSV export. Otherwise, return a list of dicts for the UI. When a
    string is given, it is used as a case-insensitive filter on id/name/email.

    Parameters
    ----------
    search_text : str | sqlite3.Connection, optional

    Returns
    -------
    list[tuple] | list[dict]
    """
    # dual-mode: if someone passes a sqlite connection (export CSV), return raw tuples
    try:
        if isinstance(search_text, sqlite3.Connection):
            cur = search_text.cursor()
            cur.execute("SELECT student_id, name, age, email FROM students ORDER BY student_id")
            return cur.fetchall()
    except:
        pass
    search_text = (search_text or "").strip().lower()
    if not search_text:
        rows = fetch_all("SELECT * FROM students ORDER BY student_id")
    else:
        # filter like old UI: by id/name/email
        like = f"%{search_text}%"
        rows = fetch_all("""
            SELECT * FROM students
            WHERE lower(student_id) LIKE lower(?)
               OR lower(name) LIKE lower(?)
               OR lower(email) LIKE lower(?)
            ORDER BY student_id
        """, (like, like, like))
    res = []
    for r in rows:
        d = _row_to_dict(r)
        d["registered_course_ids"] = student_courses(d["student_id"])
        res.append(d)
    return res


# ---------- INSTRUCTORS ----------
def instructor_email_exists(email, exclude_id=None):
    """Check uniqueness of instructor email."""
    if exclude_id:
        row = fetch_one("SELECT 1 FROM instructors WHERE lower(email)=lower(?) AND instructor_id<>?", (email, exclude_id))
    else:
        row = fetch_one("SELECT 1 FROM instructors WHERE lower(email)=lower(?)", (email,))
    return row is not None


def add_instructor(name, age, email, instructor_id):
    """Insert an instructor."""
    try:
        age = int(age)
    except:
        age = 0
    try:
        q = """INSERT INTO instructors(instructor_id, name, age, email)
               VALUES(?,?,?,?)"""
        ok = run(q, (instructor_id, name, age, email), commit=True)
        return ok is not None
    except Exception as e:
        print("add_instructor error:", e)
        return False


def update_instructor(instructor_id, name, age, email):
    """Update an instructor row by id."""
    try:
        age = int(age)
    except:
        age = 0
    try:
        q = "UPDATE instructors SET name=?, age=?, email=? WHERE instructor_id=?"
        ok = run(q, (name, age, email, instructor_id), commit=True)
        return ok is not None
    except Exception as e:
        print("update_instructor error:", e)
        return False


def delete_instructor(instructor_id):
    """Delete an instructor by id."""
    try:
        q = "DELETE FROM instructors WHERE instructor_id=?"
        ok = run(q, (instructor_id,), commit=True)
        return ok is not None
    except Exception as e:
        print("delete_instructor error:", e)
        return False


def get_instructor(instructor_id):
    """Get an instructor row as dict (or None)."""
    row = fetch_one("SELECT * FROM instructors WHERE instructor_id=?", (instructor_id,))
    return _row_to_dict(row) if row else None


# alias to match old core naming
def get_instructor_by_id(instructor_id):
    """Alias for :func:`get_instructor`."""
    return get_instructor(instructor_id)


def list_instructors(search_text=""):
    """Dual-mode instructors list.

    If given a :class:`sqlite3.Connection`, returns raw tuples. Otherwise returns
    a list of dicts; an optional string filters id/name/email (case-insensitive).
    """
    # dual-mode: connection -> raw tuples; string -> UI dicts
    try:
        if isinstance(search_text, sqlite3.Connection):
            cur = search_text.cursor()
            cur.execute("SELECT instructor_id, name, age, email FROM instructors ORDER BY instructor_id")
            return cur.fetchall()
    except:
        pass
    search_text = (search_text or "").strip().lower()
    if not search_text:
        rows = fetch_all("SELECT * FROM instructors ORDER BY instructor_id")
    else:
        like = f"%{search_text}%"
        rows = fetch_all("""
            SELECT * FROM instructors
            WHERE lower(instructor_id) LIKE lower(?)
               OR lower(name) LIKE lower(?)
               OR lower(email) LIKE lower(?)
            ORDER BY instructor_id
        """, (like, like, like))
    res = []
    for r in rows:
        d = _row_to_dict(r)
        # we could also precompute assigned courses here if we want
        res.append(d)
    return res


def instructor_courses(instructor_id):
    """Return list of course_ids taught by an instructor."""
    rows = fetch_all("SELECT course_id FROM courses WHERE instructor_id=? ORDER BY course_id", (instructor_id,))
    return [r["course_id"] for r in rows]


# ---------- COURSES ----------
def add_course(course_id, course_name, instructor_id_or_none):
    """Insert a course."""
    try:
        q = "INSERT INTO courses(course_id, course_name, instructor_id) VALUES(?,?,?)"
        ok = run(q, (course_id, course_name, instructor_id_or_none), commit=True)
        return ok is not None
    except Exception as e:
        print("add_course error:", e)
        return False


def update_course(course_id, course_name, instructor_id_or_none):
    """Update a course by id."""
    try:
        q = "UPDATE courses SET course_name=?, instructor_id=? WHERE course_id=?"
        ok = run(q, (course_name, instructor_id_or_none, course_id), commit=True)
        return ok is not None
    except Exception as e:
        print("update_course error:", e)
        return False


def delete_course(course_id):
    """Delete a course by id."""
    try:
        q = "DELETE FROM courses WHERE course_id=?"
        ok = run(q, (course_id,), commit=True)
        return ok is not None
    except Exception as e:
        print("delete_course error:", e)
        return False


def get_course(course_id):
    """Get a course row as dict (or None)."""
    row = fetch_one("SELECT * FROM courses WHERE course_id=?", (course_id,))
    return _row_to_dict(row) if row else None


# alias to match old core naming
def get_course_by_id(course_id):
    """Alias for :func:`get_course`."""
    return get_course(course_id)


def list_courses(search_text=""):
    """Dual-mode courses list.

    If given a :class:`sqlite3.Connection`, returns raw tuples. Otherwise returns
    a list of dicts (with ``student_count``) and supports a case-insensitive
    string filter on id/name/instructor_id.
    """
    # dual-mode: connection -> raw tuples; string -> UI dicts with counts
    try:
        if isinstance(search_text, sqlite3.Connection):
            cur = search_text.cursor()
            cur.execute("SELECT course_id, course_name, instructor_id FROM courses ORDER BY course_id")
            return cur.fetchall()
    except:
        pass
    search_text = (search_text or "").strip().lower()
    base = """
        SELECT
          c.course_id,
          c.course_name,
          c.instructor_id,
          (SELECT COUNT(*) FROM registrations r WHERE r.course_id = c.course_id) AS student_count
        FROM courses c
    """
    order = " ORDER BY c.course_id"
    if not search_text:
        rows = fetch_all(base + order)
    else:
        like = f"%{search_text}%"
        rows = fetch_all(base + """
            WHERE lower(c.course_id) LIKE lower(?)
               OR lower(c.course_name) LIKE lower(?)
               OR lower(IFNULL(c.instructor_id,'')) LIKE lower(?)
        """ + order, (like, like, like))
    res = []
    for r in rows:
        d = _row_to_dict(r)
        res.append(d)
    return res


def course_students(course_id):
    """Return list of students (dicts) registered in a course."""
    rows = fetch_all("""
        SELECT s.student_id, s.name
        FROM registrations r
        JOIN students s ON s.student_id = r.student_id
        WHERE r.course_id=?
        ORDER BY s.student_id
    """, (course_id,))
    return [dict(r) for r in rows]


# ---------- REGISTRATIONS / ASSIGNMENTS ----------
def register_student_to_course(student_id, course_id):
    """Register a student in a course (idempotent via INSERT OR IGNORE)."""
    try:
        q = "INSERT OR IGNORE INTO registrations(student_id, course_id) VALUES(?,?)"
        ok = run(q, (student_id, course_id), commit=True)
        return ok is not None
    except Exception as e:
        print("register_student_to_course error:", e)
        return False


def unregister_student_from_course(student_id, course_id):
    """Remove a student from a course."""
    try:
        q = "DELETE FROM registrations WHERE student_id=? AND course_id=?"
        ok = run(q, (student_id, course_id), commit=True)
        return ok is not None
    except Exception as e:
        print("unregister_student_from_course error:", e)
        return False


def assign_instructor_to_course(instructor_id, course_id):
    """Assign an instructor to a course."""
    try:
        q = "UPDATE courses SET instructor_id=? WHERE course_id=?"
        ok = run(q, (instructor_id, course_id), commit=True)
        return ok is not None
    except Exception as e:
        print("assign_instructor_to_course error:", e)
        return False


# ---------- dropdown helpers ----------
def list_course_ids():
    """Return list of all course_ids (strings)."""
    rows = fetch_all("SELECT course_id FROM courses ORDER BY course_id")
    return [r["course_id"] for r in rows]


def list_instructor_ids():
    """Return list of all instructor_ids (strings)."""
    rows = fetch_all("SELECT instructor_id FROM instructors ORDER BY instructor_id")
    return [r["instructor_id"] for r in rows]


def list_student_ids():
    """Return list of all student_ids (strings)."""
    rows = fetch_all("SELECT student_id FROM students ORDER BY student_id")
    return [r["student_id"] for r in rows]



# ---------- CSV export ----------
def export_to_csv(path):
    """Export core tables to a CSV file with section headers."""
    tables = [
        ('students', ('student_id', 'name', 'age', 'email'), list_students),
        ('instructors', ('instructor_id', 'name', 'age', 'email'), list_instructors),
        ('courses', ('course_id', 'course_name', 'instructor_id'), list_courses),
        ('registrations', ('student_id', 'course_id'), list_registrations)
    ]
    conn = None
    try:
        conn = connect()
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            for label, headers, fetcher in tables:
                writer.writerow([label])
                writer.writerow(headers)
                for row in fetcher(conn):
                    writer.writerow(row)
                writer.writerow([])
        return True
    except Exception as e:
        print('export_to_csv error:', e)
        return False
    finally:
        if conn is not None:
            conn.close()

# ---------- JSON import/export (same shape as Part 1) ----------
def export_to_json(path):
    """Dump the whole DB into a JSON file compatible with Part 1â€™s schema.

    Parameters
    ----------
    path : str
        Destination file path.

    Returns
    -------
    bool
    """
    try:
        data = {
            "students": [],
            "instructors": [],
            "courses": []
        }
        # students
        for s in list_students():
            data["students"].append({
                "student_id": s["student_id"],
                "name": s["name"],
                "age": s["age"],
                "email": s["email"],
                "registered_course_ids": s.get("registered_course_ids", [])
            })
        # instructors
        for i in list_instructors():
            data["instructors"].append({
                "instructor_id": i["instructor_id"],
                "name": i["name"],
                "age": i["age"],
                "email": i["email"],
                "assigned_course_ids": instructor_courses(i["instructor_id"])
            })
        # courses
        for c in list_courses():
            data["courses"].append({
                "course_id": c["course_id"],
                "course_name": c["course_name"],
                "instructor_id": c.get("instructor_id"),
                "student_ids": [cs["student_id"] for cs in course_students(c["course_id"])]
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print("export_to_json error:", e)
        return False


def import_from_json(path):
    """Load entities from a JSON file (upsert semantics)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("import json read error:", e)
        return False

    # insert/replace (upsert). sqlite supports ON CONFLICT..DO UPDATE
    # keep it simple: try insert; if fail, do update.
    try:
        # instructors first (so courses FK can point to them)
        for i in data.get("instructors", []):
            ok = add_instructor(i.get("name"), i.get("age"), i.get("email"), i.get("instructor_id"))
            if not ok:
                update_instructor(i.get("instructor_id"), i.get("name"), i.get("age"), i.get("email"))

        # students
        for s in data.get("students", []):
            ok = add_student(s.get("name"), s.get("age"), s.get("email"), s.get("student_id"))
            if not ok:
                update_student(s.get("student_id"), s.get("name"), s.get("age"), s.get("email"))

        # courses
        for c in data.get("courses", []):
            ok = add_course(c.get("course_id"), c.get("course_name"), c.get("instructor_id"))
            if not ok:
                update_course(c.get("course_id"), c.get("course_name"), c.get("instructor_id"))

        # registrations from students list
        for s in data.get("students", []):
            sid = s.get("student_id")
            for cid in s.get("registered_course_ids", []):
                register_student_to_course(sid, cid)

        # registrations also from courses list (double-sources but INSERT OR IGNORE makes it chill)
        for c in data.get("courses", []):
            cid = c.get("course_id")
            for sid in c.get("student_ids", []):
                register_student_to_course(sid, cid)

        return True
    except Exception as e:
        print("import_from_json error:", e)
        return False


def backup_db(dest_path):
    """Public wrapper around :func:`lab3_db.backup_db`."""
    # yoink the DB file to another place
    return _backup_db(dest_path)
