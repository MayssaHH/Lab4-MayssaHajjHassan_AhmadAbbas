"""School Management System (Tkinter GUI)

This module implements a simple school management GUI with **Students**, **Instructors**,
and **Courses** tabs. It uses an SQLite database (via :mod:`lab3_repo`) for persistence.

The UI supports:
    - Creating, updating, deleting students/instructors/courses
    - Assigning instructors to courses
    - Registering students in courses
    - Import/Export to JSON (DB-backed)
    - Database backup
"""

# part4_tk.py
# Tkinter GUI with tabs (Students / Instructors / Courses)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# was: import part1_oop as core
# Sphinx import (package path) or direct run (local import)
import utils as core  # pragma: no cover

# state
selected_student_id = None
selected_instructor_id = None
selected_course_id = None


def safe_int(x, d=0):
    """Convert value to int safely.

    Parameters
    ----------
    x : Any
        Value to convert.
    d : int, optional
        Default value if conversion fails, by default ``0``.

    Returns
    -------
    int
        Parsed integer or default.
    """
    try:
        return int(x)
    except:
        return d


def get_student_ids():
    """Get all student IDs from DB.

    Returns
    -------
    list[str]
        List of ``student_id`` strings.
    """
    # was reading from core.students
    return core.list_student_ids()


def get_instructor_ids():
    """Get all instructor IDs from DB.

    Returns
    -------
    list[str]
        List of ``instructor_id`` strings.
    """
    # was reading from core.instructors
    return core.list_instructor_ids()


def get_course_ids():
    """Get all course IDs from DB.

    Returns
    -------
    list[str]
        List of ``course_id`` strings.
    """
    # was reading from core.courses
    return core.list_course_ids()


def refresh_all_dropdowns():
    """Reload all dropdowns (comboboxes) from DB."""
    # students tab
    stu_course_dd["values"] = get_course_ids()
    # instructors tab
    ins_course_dd["values"] = get_course_ids()
    # courses tab
    crs_inst_dd["values"] = [""] + get_instructor_ids()


def refresh_students_table():
    """Fill the students table from DB, applying text search filter."""
    q = stu_search.get().strip().lower()
    stu_table.delete(*stu_table.get_children())
    # was: for s in core.students:
    for s in core.list_students():  # dicts now
        courses_txt = ",".join(s.get("registered_course_ids", []))
        row = [s["student_id"], s["name"], str(s["age"]), s["email"], courses_txt]
        if q and q not in (" ".join(row)).lower():
            continue
        stu_table.insert("", tk.END, iid=s["student_id"], values=row)


def refresh_instructors_table():
    """Fill the instructors table from DB, applying text search filter."""
    q = ins_search.get().strip().lower()
    ins_table.delete(*ins_table.get_children())
    # was: for i in core.instructors:
    for i in core.list_instructors():
        courses_txt = ",".join(core.instructor_courses(i["instructor_id"]))
        row = [i["instructor_id"], i["name"], str(i["age"]), i["email"], courses_txt]
        if q and q not in (" ".join(row)).lower():
            continue
        ins_table.insert("", tk.END, iid=i["instructor_id"], values=row)


def refresh_courses_table():
    """Fill the courses table from DB, applying text search filter."""
    q = crs_search.get().strip().lower()
    crs_table.delete(*crs_table.get_children())
    # was: for c in core.courses:
    for c in core.list_courses():
        inst_id = c.get("instructor_id") or ""
        row = [c["course_id"], c["course_name"], inst_id, str(c.get("student_count", 0))]
        if q and q not in (" ".join(row)).lower():
            continue
        crs_table.insert("", tk.END, iid=c["course_id"], values=row)


def clear_student_form():
    """Clear the student form and reset selection state."""
    global selected_student_id
    selected_student_id = None
    stu_name_e.delete(0, tk.END)
    stu_age_e.delete(0, tk.END)
    stu_email_e.delete(0, tk.END)
    stu_id_e.delete(0, tk.END)
    stu_course_dd.set("")
    stu_msg.config(text="")


def clear_instructor_form():
    """Clear the instructor form and reset selection state."""
    global selected_instructor_id
    selected_instructor_id = None
    ins_name_e.delete(0, tk.END)
    ins_age_e.delete(0, tk.END)
    ins_email_e.delete(0, tk.END)
    ins_id_e.delete(0, tk.END)
    ins_course_dd.set("")
    ins_msg.config(text="")


def clear_course_form():
    """Clear the course form and reset selection state."""
    global selected_course_id
    selected_course_id = None
    crs_id_e.delete(0, tk.END)
    crs_name_e.delete(0, tk.END)
    crs_inst_dd.set("")
    crs_msg.config(text="")


def students_on_select(e):
    """Selection handler for students table. Loads row into the form.

    Parameters
    ----------
    e : Any
        Unused Tk event object.
    """
    global selected_student_id
    sel = stu_table.selection()
    if not sel:
        selected_student_id = None
        return
    selected_student_id = sel[0]
    s = core.get_student_by_id(selected_student_id)  # dict now
    if not s:
        return
    stu_name_e.delete(0, tk.END); stu_name_e.insert(0, s["name"])
    stu_age_e.delete(0, tk.END); stu_age_e.insert(0, str(s["age"]))
    stu_email_e.delete(0, tk.END); stu_email_e.insert(0, s["email"])
    stu_id_e.delete(0, tk.END); stu_id_e.insert(0, s["student_id"])
    stu_msg.config(text="")


def instructors_on_select(e):
    """Selection handler for instructors table. Loads row into the form.

    Parameters
    ----------
    e : Any
        Unused Tk event object.
    """
    global selected_instructor_id
    sel = ins_table.selection()
    if not sel:
        selected_instructor_id = None
        return
    selected_instructor_id = sel[0]
    i = core.get_instructor_by_id(selected_instructor_id)
    if not i:
        return
    ins_name_e.delete(0, tk.END); ins_name_e.insert(0, i["name"])
    ins_age_e.delete(0, tk.END); ins_age_e.insert(0, str(i["age"]))
    ins_email_e.delete(0, tk.END); ins_email_e.insert(0, i["email"])
    ins_id_e.delete(0, tk.END); ins_id_e.insert(0, i["instructor_id"])
    ins_msg.config(text="")


def courses_on_select(e):
    """Selection handler for courses table. Loads row into the form.

    Parameters
    ----------
    e : Any
        Unused Tk event object.
    """
    global selected_course_id
    sel = crs_table.selection()
    if not sel:
        selected_course_id = None
        return
    selected_course_id = sel[0]
    c = core.get_course_by_id(selected_course_id)
    if not c:
        return
    crs_id_e.delete(0, tk.END); crs_id_e.insert(0, c["course_id"])
    crs_name_e.delete(0, tk.END); crs_name_e.insert(0, c["course_name"])
    crs_inst_dd.set(c.get("instructor_id") or "")
    crs_msg.config(text="")


# helpers for duplicate email within role
def email_taken_in_students(email, exclude_sid=None):
    """Check if a student email already exists.

    Parameters
    ----------
    email : str
        Email to check.
    exclude_sid : str, optional
        Student ID to exclude (for edits), by default ``None``.

    Returns
    -------
    bool
        True if email exists on another student.
    """
    # was: loop over core.students; now ask DB
    return core.student_email_exists(email, exclude_sid)


def email_taken_in_instructors(email, exclude_iid=None):
    """Check if an instructor email already exists.

    Parameters
    ----------
    email : str
        Email to check.
    exclude_iid : str, optional
        Instructor ID to exclude (for edits), by default ``None``.

    Returns
    -------
    bool
        True if email exists on another instructor.
    """
    # was: loop over core.instructors; now ask DB
    return core.instructor_email_exists(email, exclude_iid)


def add_or_save_student():
    """Create or update a student using form values.

    Validation
    ----------
    - Requires name and ``student_id``.
    - Validates age and email format.
    - Prevents duplicate emails within students.

    Side Effects
    ------------
    Updates the DB and refreshes tables/dropdowns.
    """
    name = stu_name_e.get().strip()
    age = stu_age_e.get().strip()
    email = stu_email_e.get().strip()
    sid = stu_id_e.get().strip()

    if not name or not sid:
        stu_msg.config(text="Brooo fill name and student id pls")
        return
    if not core.valid_age(age):
        stu_msg.config(text="Age looks sus. Non-negative integer pls")
        return
    if not core.valid_email(email):
        stu_msg.config(text="Brooo u should have a valid email")
        return

    if selected_student_id is None:
        if email_taken_in_students(email):
            stu_msg.config(text="Email already used by another student")
            return
        ok = core.add_student(name, age, email, sid)
        if not ok:
            stu_msg.config(text="Could not add student. maybe duplicate id?")
            return
    else:
        # do not allow changing ID in edit (keeps links sane)
        if sid != selected_student_id:
            stu_msg.config(text="ID change not allowed here")
            return
        if email_taken_in_students(email, exclude_sid=selected_student_id):
            stu_msg.config(text="Email already used by another student")
            return
        s = core.get_student_by_id(selected_student_id)
        if not s:
            stu_msg.config(text="Selected vanished lol try again")
            return
        ok = core.update_student(selected_student_id, name, age, email)
        if not ok:
            stu_msg.config(text="DB said nope while updating")
            return

    refresh_students_table()
    refresh_courses_table()
    refresh_all_dropdowns()
    clear_student_form()


def delete_student():
    """Delete the selected student (asks for confirmation).

    Side Effects
    ------------
    Removes the row from DB and refreshes UI.
    """
    global selected_student_id
    if not selected_student_id:
        stu_msg.config(text="Select someone to delete bro")
        return
    if not messagebox.askyesno("Confirm", "Delete this student?"):
        return
    ok = core.delete_student(selected_student_id)
    if not ok:
        stu_msg.config(text="DB said nope while deleting")
        return
    selected_student_id = None
    refresh_students_table()
    refresh_courses_table()
    refresh_all_dropdowns()
    clear_student_form()


def register_student_to_course():
    """Register the student (from form) to a selected course.

    Notes
    -----
    Uses ``INSERT OR IGNORE`` in DB layer to avoid duplicates.
    """
    sid = stu_id_e.get().strip()
    cid = stu_course_dd.get().strip()
    s = core.get_student_by_id(sid)
    c = core.get_course_by_id(cid)
    if not s or not c:
        stu_msg.config(text="Pick a real student and course first")
        return
    # was: if c in s.registered_courses:
    if cid in core.student_courses(sid):
        stu_msg.config(text="Already registered, chill")
        return
    core.register_student_to_course(sid, cid)
    refresh_students_table()
    refresh_courses_table()
    stu_msg.config(text="Registered âœ”")


def add_or_save_instructor():
    """Create or update an instructor using form values.

    Validation
    ----------
    - Requires name and ``instructor_id``.
    - Validates age and email format.
    - Prevents duplicate emails within instructors.

    Side Effects
    ------------
    Updates the DB and refreshes tables/dropdowns.
    """
    name = ins_name_e.get().strip()
    age = ins_age_e.get().strip()
    email = ins_email_e.get().strip()
    iid = ins_id_e.get().strip()

    if not name or not iid:
        ins_msg.config(text="Need name + instructor id, my friend")
        return
    if not core.valid_age(age):
        ins_msg.config(text="Age invalid. try 0 or more")
        return
    if not core.valid_email(email):
        ins_msg.config(text="Brooo u should have a valid email")
        return

    if selected_instructor_id is None:
        if email_taken_in_instructors(email):
            ins_msg.config(text="Email already used by another instructor")
            return
        ok = core.add_instructor(name, age, email, iid)
        if not ok:
            ins_msg.config(text="Could not add instructor (duplicate id?)")
            return
    else:
        if iid != selected_instructor_id:
            ins_msg.config(text="ID change not allowed here")
            return
        if email_taken_in_instructors(email, exclude_iid=selected_instructor_id):
            ins_msg.config(text="Email already used by another instructor")
            return
        i = core.get_instructor_by_id(selected_instructor_id)
        if not i:
            ins_msg.config(text="Selection lost in space")
            return
        ok = core.update_instructor(selected_instructor_id, name, age, email)
        if not ok:
            ins_msg.config(text="DB said nope while updating")
            return

    refresh_instructors_table()
    refresh_courses_table()
    refresh_all_dropdowns()
    clear_instructor_form()


def delete_instructor():
    """Delete the selected instructor (asks for confirmation)."""
    global selected_instructor_id
    if not selected_instructor_id:
        ins_msg.config(text="Select an instructor first")
        return
    if not messagebox.askyesno("Confirm", "Delete this instructor?"):
        return
    ok = core.delete_instructor(selected_instructor_id)
    if not ok:
        ins_msg.config(text="DB said nope while deleting")
        return
    selected_instructor_id = None
    refresh_instructors_table()
    refresh_courses_table()
    refresh_all_dropdowns()
    clear_instructor_form()


def assign_instructor_to_course():
    """Assign the instructor (from form) to the selected course.

    Notes
    -----
    If the course already has this instructor, a small message is shown and the DB isnâ€™t updated.
    """
    iid = ins_id_e.get().strip()
    cid = ins_course_dd.get().strip()
    i = core.get_instructor_by_id(iid)
    c = core.get_course_by_id(cid)
    if not i or not c:
        ins_msg.config(text="Pick a real instructor and course")
        return
    # was: check via object lists; now check course record
    if (c.get("instructor_id") or "") == iid:
        ins_msg.config(text="Already assigned, my dude")
        return
    core.assign_instructor_to_course(iid, cid)
    refresh_instructors_table()
    refresh_courses_table()
    ins_msg.config(text="Assigned âœ”")


def add_or_save_course():
    """Create or update a course using form values.

    Validation
    ----------
    - Requires course name and course id.
    - Does not allow changing course ID on edit.

    Side Effects
    ------------
    Updates the DB and refreshes tables/dropdowns.
    """
    name = crs_name_e.get().strip()
    cid = crs_id_e.get().strip()
    inst_id = crs_inst_dd.get().strip()
    inst = core.get_instructor_by_id(inst_id) if inst_id else None

    if not name or not cid:
        crs_msg.config(text="Need course name + id")
        return

    if selected_course_id is None:
        ok = core.add_course(cid, name, inst_id if inst else None)
        if not ok:
            crs_msg.config(text="Could not add course (duplicate id?)")
            return
    else:
        c = core.get_course_by_id(selected_course_id)
        if not c:
            crs_msg.config(text="Selection gone. reopen tab maybe")
            return
        # do not allow changing course ID in edit either
        if cid != selected_course_id:
            crs_msg.config(text="ID change not allowed here")
            return
        ok = core.update_course(selected_course_id, name, inst_id if inst else None)
        if not ok:
            crs_msg.config(text="DB said nope while updating")
            return

    refresh_courses_table()
    refresh_instructors_table()
    refresh_all_dropdowns()
    clear_course_form()


def delete_course():
    """Delete the selected course (asks for confirmation)."""
    global selected_course_id
    if not selected_course_id:
        crs_msg.config(text="Select a course first")
        return
    if not messagebox.askyesno("Confirm", "Delete this course?"):
        return
    ok = core.delete_course(selected_course_id)
    if not ok:
        crs_msg.config(text="DB said nope while deleting")
        return
    selected_course_id = None
    refresh_courses_table()
    refresh_instructors_table()
    refresh_students_table()
    refresh_all_dropdowns()
    clear_course_form()


def do_backup_db():
    """Prompt user to save a DB backup (``.db`` file).

    Opens a save dialog and uses :func:`lab3_repo.backup_db` to copy the SQLite file.
    """
    # new for Part 4: DB backup button
    p = filedialog.asksaveasfilename(defaultextension=".db", initialfile="school_backup.db")
    if not p:
        return
    ok = core.backup_db(p)
    if ok:
        messagebox.showinfo("Backup", "backup done yay")
    else:
        messagebox.showerror("Backup", "backup failed :(")



def export_csv():
    """Export the DB to a CSV file via utils.export_to_csv."""
    p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="school_data.csv")
    if not p:
        return
    ok = core.export_to_csv(p)
    if not ok:
        messagebox.showerror("Export CSV", "could not export")

def save_json():
    """Export the whole DB to a JSON file.

    Uses :func:`lab3_repo.export_to_json`.
    """
    p = filedialog.asksaveasfilename(defaultextension=".json", initialfile="school_data.json")
    if not p:
        return
    # was: core.save_to_json; now DB export
    ok = core.export_to_json(p)
    if not ok:
        messagebox.showerror("Save JSON", "could not export")


def load_json():
    """Import data from a JSON file into the DB, then refresh UI.

    Uses :func:`lab3_repo.import_from_json`.
    """
    p = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
    if not p:
        return
    # was: core.load_from_json; now DB import
    ok = core.import_from_json(p)
    if not ok:
        messagebox.showerror("Load JSON", "could not import")
        return
    refresh_students_table()
    refresh_instructors_table()
    refresh_courses_table()
    refresh_all_dropdowns()
    clear_student_form(); clear_instructor_form(); clear_course_form()


# --------------------------- GUI boot (guarded) ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("School Management System")
    root.geometry("1100x720")

    top = tk.Frame(root)
    top.pack(fill="x", padx=8, pady=6)

    tk.Button(top, text="Save JSON", command=save_json).pack(side="left")
    tk.Button(top, text="Export CSV", command=export_csv).pack(side="left")
    tk.Button(top, text="Load JSON", command=load_json).pack(side="left")
    # Part 4 required: backup db button (tiny addition)
    tk.Button(top, text="Backup DB", command=do_backup_db).pack(side="left")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=6)

    # Students tab
    stu_tab = tk.Frame(nb)
    nb.add(stu_tab, text="Students")

    left_s = tk.Frame(stu_tab); left_s.pack(side="left", fill="y", padx=6, pady=4)
    right_s = tk.Frame(stu_tab); right_s.pack(side="right", fill="both", expand=True, padx=6, pady=4)

    tk.Label(left_s, text="Name").grid(row=0, column=0, sticky="w"); stu_name_e = tk.Entry(left_s, width=28); stu_name_e.grid(row=0, column=1)
    tk.Label(left_s, text="Age").grid(row=1, column=0, sticky="w"); stu_age_e = tk.Entry(left_s, width=28); stu_age_e.grid(row=1, column=1)
    tk.Label(left_s, text="Email").grid(row=2, column=0, sticky="w"); stu_email_e = tk.Entry(left_s, width=28); stu_email_e.grid(row=2, column=1)
    tk.Label(left_s, text="Student ID").grid(row=3, column=0, sticky="w"); stu_id_e = tk.Entry(left_s, width=28); stu_id_e.grid(row=3, column=1)

    tk.Label(left_s, text="Register to Course").grid(row=4, column=0, sticky="w")
    stu_course_dd = ttk.Combobox(left_s, width=25, state="readonly"); stu_course_dd.grid(row=4, column=1)

    btn_s1 = tk.Frame(left_s); btn_s1.grid(row=5, column=0, columnspan=2, pady=4)
    tk.Button(btn_s1, text="Add / Save", command=add_or_save_student).pack(side="left")
    tk.Button(btn_s1, text="Register", command=register_student_to_course).pack(side="left")
    tk.Button(btn_s1, text="Delete", command=delete_student).pack(side="left")
    tk.Button(btn_s1, text="Clear", command=clear_student_form).pack(side="left")

    stu_msg = tk.Label(left_s, text="", fg="red"); stu_msg.grid(row=6, column=0, columnspan=2, sticky="w")

    sb_s = tk.Frame(right_s); sb_s.pack(fill="x")
    tk.Label(sb_s, text="Search").pack(side="left")
    stu_search = tk.Entry(sb_s, width=30); stu_search.pack(side="left")
    tk.Button(sb_s, text="Go", command=refresh_students_table).pack(side="left")

    stu_table = ttk.Treeview(right_s, columns=("student_id","name","age","email","courses"), show="headings")
    for c in ("student_id","name","age","email","courses"):
        stu_table.heading(c, text=c); stu_table.column(c, width=150)
    stu_table.pack(fill="both", expand=True, pady=4)
    stu_table.bind("<<TreeviewSelect>>", students_on_select)

    # Students: Enter-to-search + scrollbar
    stu_search.bind("<Return>", lambda e: refresh_students_table())
    stu_scroll = ttk.Scrollbar(right_s, orient="vertical", command=stu_table.yview)
    stu_table.configure(yscrollcommand=stu_scroll.set)
    stu_scroll.pack(side="right", fill="y")

    # Instructors tab
    ins_tab = tk.Frame(nb)
    nb.add(ins_tab, text="Instructors")

    left_i = tk.Frame(ins_tab); left_i.pack(side="left", fill="y", padx=6, pady=4)
    right_i = tk.Frame(ins_tab); right_i.pack(side="right", fill="both", expand=True, padx=6, pady=4)

    tk.Label(left_i, text="Name").grid(row=0, column=0, sticky="w"); ins_name_e = tk.Entry(left_i, width=28); ins_name_e.grid(row=0, column=1)
    tk.Label(left_i, text="Age").grid(row=1, column=0, sticky="w"); ins_age_e = tk.Entry(left_i, width=28); ins_age_e.grid(row=1, column=1)
    tk.Label(left_i, text="Email").grid(row=2, column=0, sticky="w"); ins_email_e = tk.Entry(left_i, width=28); ins_email_e.grid(row=2, column=1)
    tk.Label(left_i, text="Instructor ID").grid(row=3, column=0, sticky="w"); ins_id_e = tk.Entry(left_i, width=28); ins_id_e.grid(row=3, column=1)

    tk.Label(left_i, text="Assign to Course").grid(row=4, column=0, sticky="w")
    ins_course_dd = ttk.Combobox(left_i, width=25, state="readonly"); ins_course_dd.grid(row=4, column=1)

    btn_i1 = tk.Frame(left_i); btn_i1.grid(row=5, column=0, columnspan=2, pady=4)
    tk.Button(btn_i1, text="Add / Save", command=add_or_save_instructor).pack(side="left")
    tk.Button(btn_i1, text="Assign", command=assign_instructor_to_course).pack(side="left")
    tk.Button(btn_i1, text="Delete", command=delete_instructor).pack(side="left")
    tk.Button(btn_i1, text="Clear", command=clear_instructor_form).pack(side="left")

    ins_msg = tk.Label(left_i, text="", fg="red"); ins_msg.grid(row=6, column=0, columnspan=2, sticky="w")

    sb_i = tk.Frame(right_i); sb_i.pack(fill="x")
    tk.Label(sb_i, text="Search").pack(side="left")
    ins_search = tk.Entry(sb_i, width=30); ins_search.pack(side="left")
    tk.Button(sb_i, text="Go", command=refresh_instructors_table).pack(side="left")

    ins_table = ttk.Treeview(right_i, columns=("instructor_id","name","age","email","courses"), show="headings")
    for c in ("instructor_id","name","age","email","courses"):
        ins_table.heading(c, text=c); ins_table.column(c, width=150)
    ins_table.pack(fill="both", expand=True, pady=4)
    ins_table.bind("<<TreeviewSelect>>", instructors_on_select)

    # Instructors: Enter-to-search + scrollbar
    ins_search.bind("<Return>", lambda e: refresh_instructors_table())
    ins_scroll = ttk.Scrollbar(right_i, orient="vertical", command=ins_table.yview)
    ins_table.configure(yscrollcommand=ins_scroll.set)
    ins_scroll.pack(side="right", fill="y")

    # Courses tab
    crs_tab = tk.Frame(nb)
    nb.add(crs_tab, text="Courses")

    left_c = tk.Frame(crs_tab); left_c.pack(side="left", fill="y", padx=6, pady=4)
    right_c = tk.Frame(crs_tab); right_c.pack(side="right", fill="both", expand=True, padx=6, pady=4)

    tk.Label(left_c, text="Course ID").grid(row=0, column=0, sticky="w"); crs_id_e = tk.Entry(left_c, width=28); crs_id_e.grid(row=0, column=1)
    tk.Label(left_c, text="Course Name").grid(row=1, column=0, sticky="w"); crs_name_e = tk.Entry(left_c, width=28); crs_name_e.grid(row=1, column=1)
    tk.Label(left_c, text="Instructor").grid(row=2, column=0, sticky="w")
    crs_inst_dd = ttk.Combobox(left_c, width=25, state="readonly"); crs_inst_dd.grid(row=2, column=1)

    btn_c1 = tk.Frame(left_c); btn_c1.grid(row=3, column=0, columnspan=2, pady=4)
    tk.Button(btn_c1, text="Add / Save", command=add_or_save_course).pack(side="left")
    tk.Button(btn_c1, text="Delete", command=delete_course).pack(side="left")
    tk.Button(btn_c1, text="Clear", command=clear_course_form).pack(side="left")

    crs_msg = tk.Label(left_c, text="", fg="red"); crs_msg.grid(row=4, column=0, columnspan=2, sticky="w")

    sb_c = tk.Frame(right_c); sb_c.pack(fill="x")
    tk.Label(sb_c, text="Search").pack(side="left")
    crs_search = tk.Entry(sb_c, width=30); crs_search.pack(side="left")
    tk.Button(sb_c, text="Go", command=refresh_courses_table).pack(side="left")

    crs_table = ttk.Treeview(right_c, columns=("course_id","course_name","instructor_id","student_count"), show="headings")
    for c in ("course_id","course_name","instructor_id","student_count"):
        crs_table.heading(c, text=c); crs_table.column(c, width=160)
    crs_table.pack(fill="both", expand=True, pady=4)
    crs_table.bind("<<TreeviewSelect>>", courses_on_select)

    # Courses: Enter-to-search + scrollbar
    crs_search.bind("<Return>", lambda e: refresh_courses_table())
    crs_scroll = ttk.Scrollbar(right_c, orient="vertical", command=crs_table.yview)
    crs_table.configure(yscrollcommand=crs_scroll.set)
    crs_scroll.pack(side="right", fill="y")

    # boot
    try:
        # was: core.load_from_json("school_data.json")
        # now: if present, import json into DB, otherwise just continue (empty tables ok)
        core.import_from_json("school_data.json")
    except Exception as e:
        print("load error:", e)

    refresh_all_dropdowns()
    refresh_students_table()
    refresh_instructors_table()
    refresh_courses_table()

    root.mainloop()
