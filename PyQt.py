"""School Management System (PyQt5 GUI)

This is basically a complete school management app built with PyQt5.
It handles students, instructors, and courses with a proper database backend.

What it does:
- Full CRUD operations for students, instructors, and courses
- Search/filter functionality in all tables - you can find anything
- CSV/JSON import/export - save your data or load it back
- Student enrollment system - register students in courses
- Instructor assignment - assign instructors to courses

The UI is organized into three tabs and a main window with menu/toolbar.

Notes
-----
* This module only defines classes/functions; the QApplication is created
  under the usual ``if __name__ == "__main__":`` guard, so importing it for
  Sphinx autodoc is safe.
* The GUI depends on :mod:`classes` (domain models) and :mod:`database`
  (data access). 
"""

import sys
from typing import Optional
import json
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QMessageBox,
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QGroupBox, QComboBox, QSplitter, QMenuBar, QMenu,
    QAction, QFileDialog, QToolBar
)

from classes import Student, Instructor, Course
from database_pyqt import DatabaseManager


# i am defining these functions just to avoid repetition in my code
def ask_yes_no(parent: QWidget, title: str, text: str) -> bool:
    """Ask a Yes/No question - basically pops up a dialog asking the user yes or no
    
    :param parent: Parent widget used for modality/centering, defaults to None
    :type parent: QWidget
    :param title: Dialog window title - what shows up in the title bar
    :type title: str
    :param text: Question text - the actual question to ask
    :type text: str
    :return: True if the user clicked Yes, otherwise False
    :rtype: bool
    """
    return QMessageBox.question(parent, title, text, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes


def info(parent: QWidget, text: str):
    """Show an information message box - just shows a simple info popup
    
    :param parent: Parent widget - the main widget
    :type parent: QWidget
    :param text: Message text to display - what message to show
    :type text: str
    """
    QMessageBox.information(parent, "Info", text)


def err(parent: QWidget, text: str):
    """Show a critical/error message box - shows an error popup when something goes wrong
    
    :param parent: Parent widget - the main widget
    :type parent: QWidget
    :param text: Error text to display - what error message to show
    :type text: str
    """
    QMessageBox.critical(parent, "Error", text)


# here i start the code for the gui by defining the main window
class MainWindow(QMainWindow):
    """Top-level application window that hosts the three management tabs - the main window basically
    
    This is where everything happens. It's got all the tabs for students, instructors,
    and courses. Also handles all the menu/toolbar stuff for saving/loading data and
    making sure everything stays in sync.
    
    :param db: Database manager instance for data access
    :type db: DatabaseManager
    """
    def __init__(self):
        """Initialize the window, tabs, menus, toolbar, and database - sets everything up
        
        This is where I set up the main window with all its components. Database connection,
        tabs, menu bar, toolbar - basically everything you need to get started.
        """
        super().__init__()
        self.setWindowTitle("School Management System")
        self.resize(1100, 650)

        self.db = DatabaseManager()  #: Data access layer instance

        # i make sure database exists and tables are created
        try:
            self.db.init_database()
        except Exception as e:
            err(self, f"DB init failed: {e}")

        tabs = QTabWidget()
        self.students_tab = StudentsTab(self.db)
        self.instructors_tab = InstructorsTab(self.db)
        self.courses_tab = CoursesTab(self.db)

        tabs.addTab(self.students_tab, "Students")
        tabs.addTab(self.instructors_tab, "Instructors")
        tabs.addTab(self.courses_tab, "Courses • Enroll • Assign")

        # when i update instructors, courses tab should see it 
        self.students_tab.on_any_change = self.refresh_all
        self.instructors_tab.on_any_change = self.refresh_all
        self.courses_tab.on_any_change = self.refresh_all

        self.create_menu_bar()
        self.create_toolbar()

        self.setCentralWidget(tabs)
        self.refresh_all()

    def refresh_all(self):
        """Refresh all tabs (tables, comboboxes, counts) - updates everything
        
        When you make changes in one tab, this makes sure all the other tabs
        get updated too. Keeps everything in sync.
        """
        self.students_tab.refresh()
        self.instructors_tab.refresh()
        self.courses_tab.refresh()
    
    def create_menu_bar(self):
        """Create the **File** menu with Save/Load and CSV export commands."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')

        save_action = QAction('Save Data', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        load_action = QAction('Load Data', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_data)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        export_students_action = QAction('Export Students to CSV', self)
        export_students_action.triggered.connect(self.export_students_csv)
        file_menu.addAction(export_students_action)
        
        export_instructors_action = QAction('Export Instructors to CSV', self)
        export_instructors_action.triggered.connect(self.export_instructors_csv)
        file_menu.addAction(export_instructors_action)
        
        export_courses_action = QAction('Export Courses to CSV', self)
        export_courses_action.triggered.connect(self.export_courses_csv)
        file_menu.addAction(export_courses_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_toolbar(self):
        """Create a simple toolbar mirroring the Save/Load/Export actions."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_data)
        toolbar.addAction(save_action)
        
        load_action = QAction('Load', self)
        load_action.triggered.connect(self.load_data)
        toolbar.addAction(load_action)
        
        toolbar.addSeparator()
        
        export_action = QAction('Export CSV', self)
        export_action.triggered.connect(self.show_export_menu)
        toolbar.addAction(export_action)
    
    def save_data(self):
        """Export the whole DB to JSON via a file dialog - saves all your data
        
        This lets you save everything to a JSON file. Students, instructors, courses -
        the whole database basically. It handles both object and dict formats so it's pretty flexible.
        """
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Data", 
                "school_data.json", 
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # i have to first get all data from database
                students = self.db.all_students()
                instructors = self.db.all_instructors()
                courses = self.db.all_courses()
                
                # then onvert to serializable format
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'students': [],
                    'instructors': [],
                    'courses': []
                }
                
                # let's convert students
                for s in students:
                    data['students'].append({
                        'student_id': getattr(s, 'student_id', None) or s.get('student_id'),
                        'name': getattr(s, 'name', None) or s.get('name'),
                        'age': getattr(s, 'age', None) or s.get('age'),
                        'email': getattr(s, '_Person__email', None) or getattr(s, 'email', None) or s.get('email')
                    })
                
                # and now convert instructors
                for i in instructors:
                    data['instructors'].append({
                        'instructor_id': getattr(i, 'instructor_id', None) or i.get('instructor_id'),
                        'name': getattr(i, 'name', None) or i.get('name'),
                        'age': getattr(i, 'age', None) or i.get('age'),
                        'email': getattr(i, '_Person__email', None) or getattr(i, 'email', None) or i.get('email')
                    })
                
                # and now convert courses
                for c in courses:
                    inst = getattr(c, 'instructor', None) or c.get('instructor')
                    instructor_id = None
                    if inst is not None:
                        instructor_id = getattr(inst, 'instructor_id', None) or inst.get('instructor_id')
                    
                    data['courses'].append({
                        'course_id': getattr(c, 'course_id', None) or c.get('course_id'),
                        'course_name': getattr(c, 'course_name', None) or c.get('course_name'),
                        'instructor_id': instructor_id
                    })
                
                # save to file
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                info(self, f"Data saved successfully to {file_path}")
                
        except Exception as e:
            err(self, f"Error saving data: {e}")
    
    def load_data(self):
        """Import JSON into the DB via a file dialog, then refresh all tabs - loads your saved data
        
        Loads data from a JSON file back into the database. Clears everything first
        then loads the new data and refreshes all tabs to show it.
        """
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Load Data", 
                "", 
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                import json
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # clear existing data
                self.db.clear_database()
                
                # first, load students
                for student_data in data.get('students', []):
                    try:
                        student = Student(
                            name=student_data['name'],
                            age=student_data['age'],
                            email=student_data['email'],
                            student_id=student_data['student_id']
                        )
                        self.db.add_student(student)
                    except Exception as e:
                        print(f"Error loading student {student_data}: {e}")
                
                # secpnd, load instructors
                for instructor_data in data.get('instructors', []):
                    try:
                        instructor = Instructor(
                            name=instructor_data['name'],
                            age=instructor_data['age'],
                            email=instructor_data['email'],
                            instructor_id=instructor_data['instructor_id']
                        )
                        self.db.add_instructor(instructor)
                    except Exception as e:
                        print(f"Error loading instructor {instructor_data}: {e}")
                
                # third, oad courses
                for course_data in data.get('courses', []):
                    try:
                        instructor = None
                        if course_data.get('instructor_id'):
                            instructor = self.db.get_instructor(course_data['instructor_id'])
                        
                        course = Course(
                            course_id=course_data['course_id'],
                            course_name=course_data['course_name'],
                            instructor=instructor
                        )
                        self.db.add_course(course)
                    except Exception as e:
                        print(f"Error loading course {course_data}: {e}")
                
                # refresh all tabs for successful loading
                self.refresh_all()
                info(self, f"Data loaded successfully from {file_path}")
                
        except Exception as e:
            err(self, f"Error loading data: {e}")
    
    def show_export_menu(self):
        """Pop up a small menu with per-entity and 'Export All' CSV actions."""
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        students_action = menu.addAction("Export Students")
        students_action.triggered.connect(self.export_students_csv)
        
        instructors_action = menu.addAction("Export Instructors")
        instructors_action.triggered.connect(self.export_instructors_csv)
        
        courses_action = menu.addAction("Export Courses")
        courses_action.triggered.connect(self.export_courses_csv)
        
        menu.addSeparator()
        
        all_action = menu.addAction("Export All Data")
        all_action.triggered.connect(self.export_all_csv)
        
        # show menu at cursor position
        menu.exec_(self.mapToGlobal(self.cursor().pos()))
    
    # these functions are to export data into csv files (i will create 2 different files: students, instructors, and courses)
    def export_students_csv(self):
        """Export the Students table to a CSV file (via dialog)."""
        self.export_to_csv('students', 'Students')
    
    def export_instructors_csv(self):
        """Export the Instructors table to a CSV file (via dialog)."""
        self.export_to_csv('instructors', 'Instructors')
    
    def export_courses_csv(self):
        """Export the Courses table to a CSV file (via dialog)."""
        self.export_to_csv('courses', 'Courses')
    
    def export_all_csv(self):
        """Run the three CSV exports (students, instructors, courses)."""
        self.export_students_csv()
        self.export_instructors_csv()
        self.export_courses_csv()
    
    def export_to_csv(self, data_type, display_name):
        """Export a single entity set (students/instructors/courses) to CSV.

        Args:
            data_type (str): One of ``'students'``, ``'instructors'``, ``'courses'``.
            display_name (str): Human-readable name used in dialog titles.
        """
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                f"Export {display_name} to CSV", 
                f"{data_type}.csv", 
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                import csv
                
                if data_type == 'students':
                    data = self.db.all_students()
                    headers = ['Student ID', 'Name', 'Age', 'Email']
                    rows = []
                    for s in data:
                        rows.append([
                            getattr(s, 'student_id', None) or s.get('student_id'),
                            getattr(s, 'name', None) or s.get('name'),
                            getattr(s, 'age', None) or s.get('age'),
                            getattr(s, '_Person__email', None) or getattr(s, 'email', None) or s.get('email')
                        ])
                
                elif data_type == 'instructors':
                    data = self.db.all_instructors()
                    headers = ['Instructor ID', 'Name', 'Age', 'Email']
                    rows = []
                    for i in data:
                        rows.append([
                            getattr(i, 'instructor_id', None) or i.get('instructor_id'),
                            getattr(i, 'name', None) or i.get('name'),
                            getattr(i, 'age', None) or i.get('age'),
                            getattr(i, '_Person__email', None) or getattr(i, 'email', None) or i.get('email')
                        ])
                
                elif data_type == 'courses':
                    data = self.db.all_courses()
                    headers = ['Course ID', 'Course Name', 'Instructor Name', 'Students Enrolled']
                    rows = []
                    for c in data:
                        inst = getattr(c, 'instructor', None) or c.get('instructor')
                        instructor_name = "No instructor"
                        if inst is not None:
                            instructor_name = getattr(inst, 'name', None) or inst.get('name', 'Unknown')
                        
                        enrolled_students = getattr(c, 'enrolled_students', None) or c.get('enrolled_students', [])
                        student_count = len(enrolled_students) if isinstance(enrolled_students, list) else 0
                        
                        rows.append([
                            getattr(c, 'course_id', None) or c.get('course_id'),
                            getattr(c, 'course_name', None) or c.get('course_name'),
                            instructor_name,
                            student_count
                        ])
                
                # write data to csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)
                
                info(self, f"{display_name} data exported successfully to {file_path}")
                
        except Exception as e:
            err(self, f"Error exporting {display_name} data: {e}")


class BaseTab(QWidget):
    """Common base for the three tabs, holding the DB handle and helpers - the base class for all tabs
    
    Pretty much the parent class for all the tabs. It's got the database connection
    and some helper methods that all tabs need, like filling up tables with data.
    
    :param db: Database manager instance for data access
    :type db: DatabaseManager
    """
    def __init__(self, db: DatabaseManager):
        """Store the DB handle and an ``on_any_change`` callback."""
        super().__init__()
        self.db = db
        self.on_any_change = lambda: None  # type: ignore

    # this is atiny helper to fill QTableWidget (i keep the headers matching object fields)
    def _fill_table(self, table: QTableWidget, rows: list[dict], headers: list[str]):
        """Populate a QTableWidget with dict rows - fills up a table with data
        
        :param table: The table to fill - which table widget to populate
        :type table: QTableWidget
        :param rows: A list of dict rows - the data to put in the table
        :type rows: list[dict]
        :param headers: Column keys and header labels (same order) - what goes in the header
        :type headers: list[str]
        """
        table.clear()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, h in enumerate(headers):
                item = QTableWidgetItem(str(row.get(h, "")))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                table.setItem(r, c, item)
        table.resizeColumnsToContents()


class StudentsTab(BaseTab):
    """Students management tab: CRUD, table, and search filter - handles all student stuff
    
    This is where you manage students. Add new ones, edit existing ones, delete them,
    and search through the list. Pretty straightforward.
    
    :param db: Database manager instance for data access
    :type db: DatabaseManager
    """
    def __init__(self, db: DatabaseManager):
        """Build the student form and table UI and wire signals."""
        super().__init__(db)

        # left = form, right = table 
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)

        form_box = QGroupBox("Student form")
        form = QFormLayout()
        self.s_id = QLineEdit()
        self.s_name = QLineEdit()
        self.s_age = QLineEdit()
        self.s_email = QLineEdit()
        form.addRow("ID:", self.s_id)
        form.addRow("Name:", self.s_name)
        form.addRow("Age:", self.s_age)
        form.addRow("Email:", self.s_email)

        btn_row = QHBoxLayout()
        self.btn_s_add = QPushButton("Create")
        self.btn_s_update = QPushButton("Update")
        self.btn_s_del = QPushButton("Delete")
        self.btn_s_clear = QPushButton("Clear")
        self.btn_s_reload = QPushButton("Load")
        for b in (self.btn_s_add, self.btn_s_update, self.btn_s_del, self.btn_s_clear, self.btn_s_reload):
            btn_row.addWidget(b)
        form.addRow(btn_row)
        form_box.setLayout(form)

        table_box = QGroupBox("Students")
        v = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, name, or email...")
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        v.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        v.addWidget(self.table)
        table_box.setLayout(v)

        splitter.addWidget(form_box)
        splitter.addWidget(table_box)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.table.cellClicked.connect(self._on_row_clicked)
        self.btn_s_add.clicked.connect(self._create)
        self.btn_s_update.clicked.connect(self._update)
        self.btn_s_del.clicked.connect(self._delete)
        self.btn_s_clear.clicked.connect(self._clear)
        self.btn_s_reload.clicked.connect(self.refresh)
        
        # store original data for filtering
        self.original_data = []

    def refresh(self):
        """Reload students from DB and update table (with current filter) - updates the student list
        
        Reloads all students from the database and updates the table. If you're
        searching for something, it keeps that filter active.
        """
        # database.py returns Student objects so I normalize to dict for table
        try:
            students = self.db.all_students()
            rows = []
            for s in students:
                # i wnat to support both object or dict return shapes to be safe
                sid = getattr(s, 'student_id', None) or s.get('student_id')
                name = getattr(s, 'name', None) or s.get('name')
                age = getattr(s, 'age', None) or s.get('age')
                email = getattr(s, '_Person__email', None) or getattr(s, 'email', None) or s.get('email')
                rows.append({
                    'student_id': sid,
                    'name': name,
                    'age': age,
                    'email': email,
                })
            self.original_data = rows  
            self._filter_table() 
        except Exception as e:
            err(self, f"Load students failed: {e}")
    
    def _filter_table(self):
        """Filter the table by ID/name/email based on the search box."""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            # show all data if search is empty
            filtered_data = self.original_data
        else:
            # filter data based on search 
            filtered_data = []
            for row in self.original_data:
                # search in student_id, name, and email
                if (search_text in str(row.get('student_id', '')).lower() or
                    search_text in str(row.get('name', '')).lower() or
                    search_text in str(row.get('email', '')).lower()):
                    filtered_data.append(row)
        
        self._fill_table(self.table, filtered_data, ["student_id", "name", "age", "email"])

    def _create(self):
        """Create a student from the form values and insert into DB - adds a new student
        
        Takes whatever you typed in the form fields and creates a new student
        with that info. Adds it to the database if everything looks good.
        """
        try:
            s = Student(
                name=self.s_name.text().strip(),
                age=int(self.s_age.text()),
                email=self.s_email.text().strip(),
                student_id=self.s_id.text().strip(),
            )
            if self.db.add_student(s):
                info(self, "Student created")
                self.on_any_change()
            else:
                err(self, "Could not create student (DB said False)")
        except Exception as e:
            err(self, f"Create failed: {e}")

    def _update(self):
        """Update a student in DB using current form values - updates an existing student
        
        Updates the student that's currently selected using whatever you have
        in the form fields. Pretty straightforward.
        """
        try:
            s = Student(
                name=self.s_name.text().strip(),
                age=int(self.s_age.text()),
                email=self.s_email.text().strip(),
                student_id=self.s_id.text().strip(),
            )
            if self.db.edit_student(s):
                info(self, "Student updated ✓")
                self.on_any_change()
            else:
                err(self, "Update failed (DB said False)")
        except Exception as e:
            err(self, f"Update failed: {e}")

    def _delete(self):
        """Delete the selected/typed student by ID - removes a student
        
        Deletes the student that's either selected in the table or has their ID
        in the form. Asks for confirmation first because deleting is permanent.
        """
        sid = self.s_id.text().strip()
        if not sid:
            err(self, "Please select a student or enter an ID")
            return
        if not ask_yes_no(self, "Confirm", f"Delete student {sid}?"):
            return
        try:
            if self.db.delete_student(sid):
                info(self, "Deleted")
                self.on_any_change()
            else:
                err(self, "Delete failed (DB said False)")
        except Exception as e:
            err(self, f"Delete failed: {e}")

    def _clear(self):
        """Clear the form and selection."""
        self.s_id.clear(); self.s_name.clear(); self.s_age.clear(); self.s_email.clear()
        self.table.clearSelection()

    def _on_row_clicked(self, r: int, c: int):
        """Load the clicked row into the form."""
        # populate form from table
        self.s_id.setText(self.table.item(r, 0).text())
        self.s_name.setText(self.table.item(r, 1).text())
        self.s_age.setText(self.table.item(r, 2).text())
        self.s_email.setText(self.table.item(r, 3).text())


class InstructorsTab(BaseTab):
    """Instructors management tab: CRUD, table, and search filter - handles all instructor stuff
    
    Same as students tab but for instructors. Add, edit, delete, search through
    the instructor list. Nothing fancy here.
    
    :param db: Database manager instance for data access
    :type db: DatabaseManager
    """
    def __init__(self, db: DatabaseManager):
        """Build the instructor form and table UI and wire signals."""
        super().__init__(db)

        splitter = QSplitter(Qt.Horizontal)

        # form
        form_box = QGroupBox("Instructor form")
        form = QFormLayout()
        self.i_id = QLineEdit()
        self.i_name = QLineEdit()
        self.i_age = QLineEdit()
        self.i_email = QLineEdit()
        form.addRow("ID:", self.i_id)
        form.addRow("Name:", self.i_name)
        form.addRow("Age:", self.i_age)
        form.addRow("Email:", self.i_email)

        btn_row = QHBoxLayout()
        self.btn_i_add = QPushButton("Create")
        self.btn_i_update = QPushButton("Update")
        self.btn_i_del = QPushButton("Delete")
        self.btn_i_clear = QPushButton("Clear")
        self.btn_i_reload = QPushButton("Load")
        for b in (self.btn_i_add, self.btn_i_update, self.btn_i_del, self.btn_i_clear, self.btn_i_reload):
            btn_row.addWidget(b)
        form.addRow(btn_row)
        form_box.setLayout(form)

        table_box = QGroupBox("Instructors")
        v = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, name, or email...")
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        v.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        v.addWidget(self.table)
        table_box.setLayout(v)

        splitter.addWidget(form_box)
        splitter.addWidget(table_box)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.table.cellClicked.connect(self._on_row_clicked)
        self.btn_i_add.clicked.connect(self._create)
        self.btn_i_update.clicked.connect(self._update)
        self.btn_i_del.clicked.connect(self._delete)
        self.btn_i_clear.clicked.connect(self._clear)
        self.btn_i_reload.clicked.connect(self.refresh)
        
        # store original data for filtering
        self.original_data = []

    def refresh(self):
        """Reload instructors from DB and update table (with current filter)."""
        try:
            instructors = self.db.all_instructors()
            rows = []
            for i in instructors:
                iid = getattr(i, 'instructor_id', None) or i.get('instructor_id')
                name = getattr(i, 'name', None) or i.get('name')
                age = getattr(i, 'age', None) or i.get('age')
                email = getattr(i, '_Person__email', None) or getattr(i, 'email', None) or i.get('email')
                rows.append({'instructor_id': iid, 'name': name, 'age': age, 'email': email})
            self.original_data = rows  
            self._filter_table()
        except Exception as e:
            err(self, f"Load instructors failed: {e}")
    
    def _filter_table(self):
        """Filter by instructor ID, name, or email based on the search box."""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            filtered_data = self.original_data
        else:
            filtered_data = []
            for row in self.original_data:
                if (search_text in str(row.get('instructor_id', '')).lower() or
                    search_text in str(row.get('name', '')).lower() or
                    search_text in str(row.get('email', '')).lower()):
                    filtered_data.append(row)
        
        self._fill_table(self.table, filtered_data, ["instructor_id", "name", "age", "email"])

    def _create(self):
        """Create an instructor from the form values and insert into DB."""
        try:
            i = Instructor(
                name=self.i_name.text().strip(),
                age=int(self.i_age.text()),
                email=self.i_email.text().strip(),
                instructor_id=self.i_id.text().strip(),
            )
            if self.db.add_instructor(i):
                info(self, "Instructor created")
                self.on_any_change()
            else:
                err(self, "Create failed (DB said False)")
        except Exception as e:
            err(self, f"Create failed: {e}")

    def _update(self):
        """Update an instructor in DB using current form values."""
        try:
            i = Instructor(
                name=self.i_name.text().strip(),
                age=int(self.i_age.text()),
                email=self.i_email.text().strip(),
                instructor_id=self.i_id.text().strip(),
            )
            if self.db.edit_instructor(i):
                info(self, "Instructor updated ✓")
                self.on_any_change()
            else:
                err(self, "Update failed (DB said False)")
        except Exception as e:
            err(self, f"Update failed: {e}")

    def _delete(self):
        """Delete the selected/typed instructor by ID."""
        iid = self.i_id.text().strip()
        if not iid:
            err(self, "Please select an instructor or enter an ID")
            return
        if not ask_yes_no(self, "Confirm", f"Delete instructor {iid}?"):
            return
        try:
            if self.db.delete_instructor(iid):
                info(self, "Deleted")
                self.on_any_change()
            else:
                err(self, "Delete failed (DB said False)")
        except Exception as e:
            err(self, f"Delete failed: {e}")

    def _clear(self):
        """Clear the form and selection."""
        self.i_id.clear(); self.i_name.clear(); self.i_age.clear(); self.i_email.clear()
        self.table.clearSelection()

    def _on_row_clicked(self, r: int, c: int):
        """Load the clicked row into the form."""
        self.i_id.setText(self.table.item(r, 0).text())
        self.i_name.setText(self.table.item(r, 1).text())
        self.i_age.setText(self.table.item(r, 2).text())
        self.i_email.setText(self.table.item(r, 3).text())


class CoursesTab(BaseTab):
    """Courses management tab: CRUD, search, enroll, and assign workflows - the most complex tab
    
    This one's a bit more complicated. You manage courses here, but also handle
    enrolling students in courses and assigning instructors. It's got the most features.
    
    :param db: Database manager instance for data access
    :type db: DatabaseManager
    """
    def __init__(self, db: DatabaseManager):
        """Build the course form, tables, actions, and relationship widgets."""
        super().__init__(db)

        root = QSplitter(Qt.Horizontal)

        # left: course CRUD
        left_box = QGroupBox("Course form")
        form = QFormLayout()
        self.c_id = QLineEdit()
        self.c_name = QLineEdit()
        self.c_instructor = QComboBox() 
        form.addRow("Course ID:", self.c_id)
        form.addRow("Course name:", self.c_name)
        form.addRow("Instructor:", self.c_instructor)

        btn_row = QHBoxLayout()
        self.btn_c_add = QPushButton("Create")
        self.btn_c_update = QPushButton("Update")
        self.btn_c_del = QPushButton("Delete")
        self.btn_c_clear = QPushButton("Clear")
        self.btn_c_reload = QPushButton("Load")
        for b in (self.btn_c_add, self.btn_c_update, self.btn_c_del, self.btn_c_clear, self.btn_c_reload):
            btn_row.addWidget(b)
        form.addRow(btn_row)
        left_box.setLayout(form)

        # right top: courses table
        right = QWidget()
        right_v = QVBoxLayout(right)
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by course ID, name, instructor, or students...")
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        right_v.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        right_v.addWidget(self.table)

        # right bottom: relationships (enroll + assign) 
        rel_box = QGroupBox("Quick actions: enroll students / assign instructors")
        rel_layout = QFormLayout()

        self.enroll_student_combo = QComboBox()
        self.enroll_course_combo = QComboBox()
        self.btn_enroll = QPushButton("Enroll student → course")
        self.btn_unenroll = QPushButton("Unenroll student ← course")

        self.assign_instructor_combo = QComboBox()
        self.assign_course_combo = QComboBox()
        self.btn_assign = QPushButton("Assign instructor → course")
        self.btn_unassign = QPushButton("Unassign instructor ← course")

        rel_layout.addRow(QLabel("Student:"), self.enroll_student_combo)
        rel_layout.addRow(QLabel("Course:"), self.enroll_course_combo)
        rel_layout.addRow(self.btn_enroll, self.btn_unenroll)
        rel_layout.addRow(QLabel("Instructor:"), self.assign_instructor_combo)
        rel_layout.addRow(QLabel("Course:"), self.assign_course_combo)
        rel_layout.addRow(self.btn_assign, self.btn_unassign)
        rel_box.setLayout(rel_layout)
        right_v.addWidget(rel_box)

        root.addWidget(left_box)
        root.addWidget(right)
        root.setStretchFactor(1, 1)

        layout = QVBoxLayout()
        layout.addWidget(root)
        self.setLayout(layout)

        self.table.cellClicked.connect(self._on_row_clicked)
        self.btn_c_add.clicked.connect(self._create)
        self.btn_c_update.clicked.connect(self._update)
        self.btn_c_del.clicked.connect(self._delete)
        self.btn_c_clear.clicked.connect(self._clear)
        self.btn_c_reload.clicked.connect(self.refresh)

        self.btn_enroll.clicked.connect(self._enroll)
        self.btn_unenroll.clicked.connect(self._unenroll)
        self.btn_assign.clicked.connect(self._assign)
        self.btn_unassign.clicked.connect(self._unassign)
        
        # store original data for filtering
        self.original_data = []

    def refresh(self):
        """Reload courses, update table, and refresh relationship combos."""
        # refresh courses table
        try:
            courses = self.db.all_courses()
            rows = []
            for c in courses:
                cid = getattr(c, 'course_id', None) or c.get('course_id')
                cname = getattr(c, 'course_name', None) or c.get('course_name')
                
                # get instructor name
                instructor_name = "No instructor"
                inst = getattr(c, 'instructor', None) or c.get('instructor')
                if inst is not None:
                    instructor_name = getattr(inst, 'name', None) or inst.get('name', 'Unknown')
                
                # get number of enrolled students
                enrolled_students = getattr(c, 'enrolled_students', None) or c.get('enrolled_students', [])
                if enrolled_students is None:
                    enrolled_students = []
                student_count = len(enrolled_students) if isinstance(enrolled_students, list) else 0
                
                rows.append({
                    'course_id': cid, 
                    'course_name': cname, 
                    'instructor_name': instructor_name,
                    'students_enrolled': student_count
                })
            self.original_data = rows  
            self._filter_table() 
        except Exception as e:
            err(self, f"Load courses failed: {e}")
    
    def _filter_table(self):
        """Filter by course ID/name/instructor/num-students using search box."""
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            # show all data if search is empty
            filtered_data = self.original_data
        else:
            # filter data based on search text
            filtered_data = []
            for row in self.original_data:
                # search in course_id, course_name, instructor_name, and students_enrolled
                if (search_text in str(row.get('course_id', '')).lower() or
                    search_text in str(row.get('course_name', '')).lower() or
                    search_text in str(row.get('instructor_name', '')).lower() or
                    search_text in str(row.get('students_enrolled', '')).lower()):
                    filtered_data.append(row)
        
        self._fill_table(self.table, filtered_data, ["course_id", "course_name", "instructor_name", "students_enrolled"])

        # refresh combo sources (students / instructors / courses)
        try:
            self._fill_students_combo()
            self._fill_instructors_combo()
            self._fill_courses_combo()
        except Exception as e:
            err(self, f"Refresh combos failed: {e}")

    def _fill_students_combo(self):
        """Reload the *enroll student* combobox with current students."""
        self.enroll_student_combo.clear()
        students = self.db.all_students()
        self.enroll_student_combo.addItem("— choose —", None)
        for s in students:
            sid = getattr(s, 'student_id', None) or s.get('student_id')
            name = getattr(s, 'name', None) or s.get('name')
            self.enroll_student_combo.addItem(f"{name} ({sid})", sid)

    def _fill_instructors_combo(self):
        """Reload instructor combos and preserve current instructor selection."""
        current = self.c_instructor.currentData()
        self.c_instructor.clear()
        self.c_instructor.addItem("— none —", None)
        instructors = self.db.all_instructors()
        for i in instructors:
            iid = getattr(i, 'instructor_id', None) or i.get('instructor_id')
            name = getattr(i, 'name', None) or i.get('name')
            self.c_instructor.addItem(f"{name} ({iid})", iid)

        self.assign_instructor_combo.clear()
        self.assign_instructor_combo.addItem("— choose —", None)
        for i in instructors:
            iid = getattr(i, 'instructor_id', None) or i.get('instructor_id')
            name = getattr(i, 'name', None) or i.get('name')
            self.assign_instructor_combo.addItem(f"{name} ({iid})", iid)

        if current is not None:
            idx = self.c_instructor.findData(current)
            if idx >= 0:
                self.c_instructor.setCurrentIndex(idx)

    def _fill_courses_combo(self):
        """Reload the course combos used for enroll/assign actions."""
        self.enroll_course_combo.clear()
        self.assign_course_combo.clear()
        self.enroll_course_combo.addItem("— choose —", None)
        self.assign_course_combo.addItem("— choose —", None)
        for c in self.db.all_courses():
            cid = getattr(c, 'course_id', None) or c.get('course_id')
            cname = getattr(c, 'course_name', None) or c.get('course_name')
            self.enroll_course_combo.addItem(f"{cname} ({cid})", cid)
            self.assign_course_combo.addItem(f"{cname} ({cid})", cid)

    def _create(self):
        """Create a course from form values (with optional instructor)."""
        try:
            cid = self.c_id.text().strip()
            cname = self.c_name.text().strip()
            iid = self.c_instructor.currentData()
            
            # first i have to check if instructor is already assigned to another course
            if iid:
                courses = self.db.all_courses()
                for course in courses:
                    inst = getattr(course, 'instructor', None) or course.get('instructor')
                    if inst is not None:
                        inst_id = getattr(inst, 'instructor_id', None) or inst.get('instructor_id')
                        if inst_id == iid:
                            course_id = getattr(course, 'course_id', None) or course.get('course_id')
                            err(self, f"This instructor is already assigned to course {course_id}")
                            return
            
            instructor_obj: Optional[Instructor] = None
            if iid:
                #  if database has a get_instructor, i use it else fallback to list
                try:
                    inst = self.db.get_instructor(iid)
                except Exception:
                    inst = None
                if inst is None:
                    for i in self.db.all_instructors():
                        if (getattr(i, 'instructor_id', None) or i.get('instructor_id')) == iid:
                            inst = i; break

                # normalize to instructor instance
                if inst and not isinstance(inst, Instructor):
                    inst = Instructor(
                        name=getattr(inst, 'name', None) or inst.get('name'),
                        age=int(getattr(inst, 'age', None) or inst.get('age')),
                        email=(getattr(inst, 'email', None) or inst.get('email') or getattr(inst, '_Person__email', None)),
                        instructor_id=iid,
                    )
                instructor_obj = inst
            course = Course(course_id=cid, course_name=cname, instructor=instructor_obj)
            if self.db.add_course(course):
                info(self, "Course created")
                self.on_any_change()
            else:
                err(self, "Create failed (DB said False)")
        except Exception as e:
            err(self, f"Create failed: {e}")

    def _update(self):
        """Update a course in DB using current form values (with checks)."""
        try:
            cid = self.c_id.text().strip()
            cname = self.c_name.text().strip()
            iid = self.c_instructor.currentData()
            
            # first i have to check if instructor is already assigned to another course
            if iid:
                courses = self.db.all_courses()
                for course in courses:
                    course_id = getattr(course, 'course_id', None) or course.get('course_id')
                    if course_id != cid:  # Skip the current course being updated
                        inst = getattr(course, 'instructor', None) or course.get('instructor')
                        if inst is not None:
                            inst_id = getattr(inst, 'instructor_id', None) or inst.get('instructor_id')
                            if inst_id == iid:
                                err(self, f"This instructor is already assigned to course {course_id}")
                                return
            
            inst_obj = None
            if iid:
                inst = self.db.get_instructor(iid)
                if inst and not isinstance(inst, Instructor):
                    inst = Instructor(
                        name=getattr(inst, 'name', None) or inst.get('name'),
                        age=int(getattr(inst, 'age', None) or inst.get('age')),
                        email=(getattr(inst, 'email', None) or inst.get('email') or getattr(inst, '_Person__email', None)),
                        instructor_id=iid,
                    )
                inst_obj = inst
            course = Course(course_id=cid, course_name=cname, instructor=inst_obj)
            if self.db.edit_course(course):
                info(self, "Course updated ✓")
                self.on_any_change()
            else:
                err(self, "Update failed (DB said False)")
        except Exception as e:
            err(self, f"Update failed: {e}")

    def _delete(self):
        """Delete the selected/typed course by ID."""
        cid = self.c_id.text().strip()
        if not cid:
            err(self, "Please select a course or enter an ID")
            return
        if not ask_yes_no(self, "Confirm", f"Delete course {cid}?"):
            return
        try:
            if self.db.delete_course(cid):
                info(self, "Deleted")
                self.on_any_change()
            else:
                err(self, "Delete failed (DB said False)")
        except Exception as e:
            err(self, f"Delete failed: {e}")

    def _clear(self):
        """Clear the course form and selection."""
        self.c_id.clear(); self.c_name.clear(); self.c_instructor.setCurrentIndex(0)
        self.table.clearSelection()

    def _on_row_clicked(self, r: int, c: int):
        """Load the clicked row into the course form and set instructor."""
        self.c_id.setText(self.table.item(r, 0).text())
        self.c_name.setText(self.table.item(r, 1).text())
        
        # find instructor by name (column 2 is now instructor_name)
        instructor_name = self.table.item(r, 2).text() if self.table.item(r, 2) else ""
        if instructor_name and instructor_name != "No instructor":
            # find the instructor ID by name
            iid = None
            for i in range(self.c_instructor.count()):
                if self.c_instructor.itemText(i).startswith(instructor_name):
                    iid = self.c_instructor.itemData(i)
                    break
            idx = self.c_instructor.findData(iid) if iid else 0
        else:
            idx = 0
        self.c_instructor.setCurrentIndex(idx if idx >= 0 else 0)

    def _enroll(self):
        """Enroll a student into a course (combobox selections) - registers a student in a course
        
        Takes the student and course you selected from the dropdowns and
        enrolls the student in that course. Updates everything automatically.
        """
        sid = self.enroll_student_combo.currentData()
        cid = self.enroll_course_combo.currentData()
        if not sid or not cid:
            err(self, "Pick both student and course")
            return
        try:
            if self.db.register_student_in_course(sid, cid):
                info(self, "Enrolled ✓")
                self.on_any_change()  # refresh all tabs to update counts
            else:
                err(self, "Enroll failed (DB said False)")
        except Exception as e:
            err(self, f"Enroll failed: {e}")

    def _unenroll(self):
        """Unenroll a student from a course."""
        sid = self.enroll_student_combo.currentData()
        cid = self.enroll_course_combo.currentData()
        if not sid or not cid:
            err(self, "Pick both student and course")
            return
        try:
            if self.db.unregister_student_from_course(sid, cid):
                info(self, "Unenrolled")
                self.on_any_change()  # refresh all tabs to update counts
            else:
                err(self, "Unenroll failed (DB said False)")
        except Exception as e:
            err(self, f"Unenroll failed: {e}")

    def _assign(self):
        """Assign an instructor to a course (with safety checks)."""
        iid = self.assign_instructor_combo.currentData()
        cid = self.assign_course_combo.currentData()
        if not iid or not cid:
            err(self, "Pick both instructor and course")
            return
        
        # first i have to check if instructor is already assigned to another course
        try:
            courses = self.db.all_courses()
            for course in courses:
                inst = getattr(course, 'instructor', None) or course.get('instructor')
                if inst is not None:
                    inst_id = getattr(inst, 'instructor_id', None) or inst.get('instructor_id')
                    if inst_id == iid:
                        course_id = getattr(course, 'course_id', None) or course.get('course_id')
                        if course_id != cid:
                            err(self, f"This instructor is already assigned to course {course_id}")
                            return
        except Exception as e:
            err(self, f"Error checking instructor assignments: {e}")
            return
        
        # first i have toheck if course already has an instructor
        try:
            courses = self.db.all_courses()
            for course in courses:
                course_id = getattr(course, 'course_id', None) or course.get('course_id')
                if course_id == cid:
                    inst = getattr(course, 'instructor', None) or course.get('instructor')
                    if inst is not None:
                        inst_name = getattr(inst, 'name', None) or inst.get('name', 'Unknown')
                        err(self, f"This course already has instructor: {inst_name}")
                        return
                    break
        except Exception as e:
            err(self, f"Error checking course assignments: {e}")
            return
        
        try:
            if self.db.assign_instructor_to_course(iid, cid):
                info(self, "Assigned")
                self.on_any_change()
            else:
                err(self, "Assign failed (DB said False)")
        except Exception as e:
            err(self, f"Assign failed: {e}")

    def _unassign(self):
        """Unassign an instructor from a course."""
        iid = self.assign_instructor_combo.currentData()
        cid = self.assign_course_combo.currentData()
        if not iid or not cid:
            err(self, "Pick both instructor and course")
            return
        try:
            if self.db.unassign_instructor_from_course(cid):
                # i assume database unassigns by course 
                info(self, "Unassigned")
                self.on_any_change()
            else:
                err(self, "Unassign failed (DB said False)")
        except Exception as e:
            # if database requires both ids, fallback to a 2 arg call 
            try:
                ok = self.db.unassign_instructor_from_course(iid, cid)  
                if ok:
                    info(self, "Unassigned")
                    self.on_any_change()
                else:
                    err(self, "Unassign failed (DB said False)")
            except Exception as e2:
                err(self, f"Unassign failed: {e}\n{e2}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
