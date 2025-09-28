"""Database helpers for the School app (SQLite).

This tiny module wraps SQLite calls and exposes a few convenience helpers
to run statements and fetch rows. It also owns the **schema** creation.

"""

# part4_db.py
# super tiny db helper... db go brrrrr

import sqlite3
import os
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), "school.db")


def _connect():
    """Open a new SQLite connection with foreign-keys enabled.

    Returns
    -------
    sqlite3.Connection
        Fresh connection with ``row_factory=sqlite3.Row`` and FKs enforced.
    """
    # make a new connection each time (simple life)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # so we can do dict(row)
    # yes bro, enforce FK or chaos will happen
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run(query, params=(), commit=False):
    """Execute a write or read query, optionally committing.

    Parameters
    ----------
    query : str
        SQL text to execute.
    params : tuple, optional
        Query parameters, by default ``()``.
    commit : bool, optional
        If ``True``, commits the transaction, by default ``False``.

    Returns
    -------
    sqlite3.Cursor or None
        Cursor on success, otherwise ``None``.
    """
    # i do not overthink this. execute and maybe commit
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        if commit:
            conn.commit()
        return cur
    except Exception as e:
        print("db run error:", e)
        try:
            conn.rollback()
        except:
            pass
        return None
    finally:
        conn.close()


def fetch_one(query, params=()):
    """Fetch a single row.

    Parameters
    ----------
    query : str
        SQL text to execute.
    params : tuple, optional
        Query parameters, by default ``()``.

    Returns
    -------
    sqlite3.Row or None
        One row or ``None`` if nothing / error.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        return row
    except Exception as e:
        print("db fetch_one error:", e)
        return None
    finally:
        conn.close()


def fetch_all(query, params=()):
    """Fetch all rows.

    Parameters
    ----------
    query : str
        SQL text to execute.
    params : tuple, optional
        Query parameters, by default ``()``.

    Returns
    -------
    list[sqlite3.Row]
        Result rows (empty list on error).
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print("db fetch_all error:", e)
        return []
    finally:
        conn.close()


def init_db():
    """Create the schema if not present (idempotent)."""
    # schema time. hold my juice.
    # silly note: if you change IDs we cry, but FK is still here for safety.
    create_students = """
    CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL CHECK(age >= 0),
        email TEXT NOT NULL UNIQUE
    );
    """
    create_instructors = """
    CREATE TABLE IF NOT EXISTS instructors(
        instructor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL CHECK(age >= 0),
        email TEXT NOT NULL UNIQUE
    );
    """
    create_courses = """
    CREATE TABLE IF NOT EXISTS courses(
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        instructor_id TEXT NULL,
        FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
            ON UPDATE CASCADE ON DELETE SET NULL
    );
    """
    create_regs = """
    CREATE TABLE IF NOT EXISTS registrations(
        student_id TEXT NOT NULL,
        course_id  TEXT NOT NULL,
        PRIMARY KEY(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY(course_id)  REFERENCES courses(course_id)
            ON UPDATE CASCADE ON DELETE CASCADE
    );
    """
    # create all
    for q in (create_students, create_instructors, create_courses, create_regs):
        ok = run(q, commit=True)
        if ok is None:
            print("schema creation failed for some table... yikes")


def backup_db(dest_path):
    """Copy ``school.db`` to ``dest_path``.

    Ensures the DB exists (creates empty schema if needed) before copying.

    Parameters
    ----------
    dest_path : str
        Destination file path for the backup.

    Returns
    -------
    bool
        ``True`` on success, ``False`` on failure.
    """
    # copy school.db to user path. yes captain.
    try:
        # make sure file exists
        if not os.path.exists(DB_PATH):
            # force-create empty schema so at least we have a file
            init_db()
        shutil.copyfile(DB_PATH, dest_path)
        return True
    except Exception as e:
        print("backup error:", e)
        return False


# create tables on import. boom.
try:
    init_db()
except Exception as e:
    print("init_db exploded:", e)
