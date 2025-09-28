"""Database Management for School Management System

This module handles all the database operations for the school management system.
Basically it's the data access layer that talks to SQLite and manages all the
CRUD operations for students, instructors, and courses.

Features:
- SQLite database with proper table structure
- Full CRUD operations for all entities
- Student-course enrollment management
- Instructor-course assignment management
- Database statistics and backup functionality

All methods return proper objects from the classes module and handle errors gracefully.
"""

import sqlite3
from typing import List, Dict, Optional
from classes import Student, Instructor, Course


class DatabaseManager:
    """Database manager class - handles all database operations
    
    This is the main class that manages the SQLite database for the school
    management system. It creates tables, handles CRUD operations, and manages
    relationships between students, instructors, and courses.
    
    :param db_path: Path to the SQLite database file, defaults to "school_management.db"
    :type db_path: str, optional
    """
    
    def __init__(self, db_path: str = "school_management.db"):
        """Constructor method - sets up the database connection and initializes tables"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database - creates all the tables if they don't exist
        
        This method creates the database structure with all the necessary tables:
        students, instructors, courses, and student_courses junction table.
        It's safe to call multiple times since it uses CREATE TABLE IF NOT EXISTS.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create instructors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS instructors (
                    instructor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create courses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    course_id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    instructor_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instructor_id) REFERENCES instructors (instructor_id)
                )
            ''')
            
            # Create student_courses junction table 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_courses (
                    student_id TEXT,
                    course_id TEXT,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (student_id, course_id),
                    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses (course_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection - creates a new connection to the database
        
        :return: SQLite connection object
        :rtype: sqlite3.Connection
        
        This is used internally by other methods to get database connections.
        """
        return sqlite3.connect(self.db_path)
    
    def add_student(self, student: Student) -> bool:
        """Add a new student to the database
        
        :param student: Student object to add
        :type student: Student
        :return: True if successful, False otherwise
        :rtype: bool
        
        Adds a new student to the students table. Returns False if there's an error
        (like duplicate student_id or email).
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO students (student_id, name, age, email)
                    VALUES (?, ?, ?, ?)
                ''', (student.student_id, student.name, student.age, student.email))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_student(self, student_id: str) -> Optional[Student]:
        """Get a student by their ID
        
        :param student_id: The student ID to look up
        :type student_id: str
        :return: Student object if found, None otherwise
        :rtype: Optional[Student]
        
        Retrieves a student from the database and also loads their registered courses.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, name, age, email FROM students
                    WHERE student_id = ?
                ''', (student_id,))
                row = cursor.fetchone()
                
                if row:
                    student = Student(row[1], row[2], row[3], row[0])
                    # Load registered courses
                    student.registered_courses = self.get_student_courses(student_id)
                    return student
                return None
        except sqlite3.Error as e:
            print(f"Error getting student: {e}")
            return None
    
    def all_students(self) -> List[Student]:
        """Get all students from the database
        
        :return: List of all Student objects
        :rtype: List[Student]
        
        Retrieves all students from the database, ordered by name. Each student
        also has their registered courses loaded.
        """
        students = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, name, age, email FROM students
                    ORDER BY name
                ''')
                rows = cursor.fetchall()
                
                for row in rows:
                    student = Student(row[1], row[2], row[3], row[0])
                    student.registered_courses = self.get_student_courses(row[0])
                    students.append(student)
        except sqlite3.Error as e:
            print(f"Error getting all students: {e}")
        
        return students
    
    def edit_student(self, student: Student) -> bool:
        """Update an existing student in the database
        
        :param student: Student object with updated information
        :type student: Student
        :return: True if successful, False otherwise
        :rtype: bool
        
        Updates a student's information in the database. The student_id is used
        to identify which student to update.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE students 
                    SET name = ?, age = ?, email = ?
                    WHERE student_id = ?
                ''', (student.name, student.age, student.email, student.student_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating student: {e}")
            return False
    
    def delete_student(self, student_id: str) -> bool:
        """Delete a student from the database
        
        :param student_id: The student ID to delete
        :type student_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Deletes a student and also removes them from all courses they were
        enrolled in. This is a cascading delete operation.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # First remove from student_courses table
                cursor.execute('DELETE FROM student_courses WHERE student_id = ?', (student_id,))
                # Then delete the student
                cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting student: {e}")
            return False
    
   
    def add_instructor(self, instructor: Instructor) -> bool:
        """Add a new instructor to the database
        
        :param instructor: Instructor object to add
        :type instructor: Instructor
        :return: True if successful, False otherwise
        :rtype: bool
        
        Adds a new instructor to the instructors table. Returns False if there's an error
        (like duplicate instructor_id or email).
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO instructors (instructor_id, name, age, email)
                    VALUES (?, ?, ?, ?)
                ''', (instructor.instructor_id, instructor.name, instructor.age, instructor.email))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding instructor: {e}")
            return False
    
    def get_instructor(self, instructor_id: str) -> Optional[Instructor]:
        """Get an instructor by their ID
        
        :param instructor_id: The instructor ID to look up
        :type instructor_id: str
        :return: Instructor object if found, None otherwise
        :rtype: Optional[Instructor]
        
        Retrieves an instructor from the database and also loads their assigned courses.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT instructor_id, name, age, email FROM instructors
                    WHERE instructor_id = ?
                ''', (instructor_id,))
                row = cursor.fetchone()
                
                if row:
                    instructor = Instructor(row[1], row[2], row[3], row[0])
                    # Load assigned courses
                    instructor.assigned_courses = self.get_instructor_courses(instructor_id)
                    return instructor
                return None
        except sqlite3.Error as e:
            print(f"Error getting instructor: {e}")
            return None
    
    def all_instructors(self) -> List[Instructor]:
        """Get all instructors from the database
        
        :return: List of all Instructor objects
        :rtype: List[Instructor]
        
        Retrieves all instructors from the database, ordered by name. Each instructor
        also has their assigned courses loaded.
        """
        instructors = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT instructor_id, name, age, email FROM instructors
                    ORDER BY name
                ''')
                rows = cursor.fetchall()
                
                for row in rows:
                    instructor = Instructor(row[1], row[2], row[3], row[0])
                    instructor.assigned_courses = self.get_instructor_courses(row[0])
                    instructors.append(instructor)
        except sqlite3.Error as e:
            print(f"Error getting all instructors: {e}")
        
        return instructors
    
    def edit_instructor(self, instructor: Instructor) -> bool:
        """Update an existing instructor in the database
        
        :param instructor: Instructor object with updated information
        :type instructor: Instructor
        :return: True if successful, False otherwise
        :rtype: bool
        
        Updates an instructor's information in the database. The instructor_id is used
        to identify which instructor to update.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE instructors 
                    SET name = ?, age = ?, email = ?
                    WHERE instructor_id = ?
                ''', (instructor.name, instructor.age, instructor.email, instructor.instructor_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating instructor: {e}")
            return False
    
    def delete_instructor(self, instructor_id: str) -> bool:
        """Delete an instructor from the database
        
        :param instructor_id: The instructor ID to delete
        :type instructor_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Deletes an instructor and also unassigns them from all courses they were
        teaching. This prevents orphaned course assignments.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # First unassign all courses from this instructor
                cursor.execute('''
                    UPDATE courses SET instructor_id = NULL 
                    WHERE instructor_id = ?
                ''', (instructor_id,))
                # Then delete the instructor
                cursor.execute('DELETE FROM instructors WHERE instructor_id = ?', (instructor_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting instructor: {e}")
            return False
    
    def add_course(self, course: Course) -> bool:
        """Add a new course to the database
        
        :param course: Course object to add
        :type course: Course
        :return: True if successful, False otherwise
        :rtype: bool
        
        Adds a new course to the courses table. The instructor is optional - if provided,
        it gets linked to the course.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                instructor_id = course.instructor.instructor_id if course.instructor else None
                cursor.execute('''
                    INSERT INTO courses (course_id, course_name, instructor_id)
                    VALUES (?, ?, ?)
                ''', (course.course_id, course.course_name, instructor_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding course: {e}")
            return False
    
    def get_course(self, course_id: str) -> Optional[Course]:
        """Get a course by its ID
        
        :param course_id: The course ID to look up
        :type course_id: str
        :return: Course object if found, None otherwise
        :rtype: Optional[Course]
        
        Retrieves a course from the database with its instructor (if any) and
        all enrolled students loaded.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.course_id, c.course_name, c.instructor_id,
                           i.name, i.age, i.email, i.instructor_id
                    FROM courses c
                    LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
                    WHERE c.course_id = ?
                ''', (course_id,))
                row = cursor.fetchone()
                
                if row:
                    instructor = None
                    if row[2]:  # if instructor_id is not None
                        instructor = Instructor(row[3], row[4], row[5], row[6])
                    
                    course = Course(row[0], row[1], instructor)
                    # Load enrolled students
                    course.enrolled_students = self.get_course_students(course_id)
                    return course
                return None
        except sqlite3.Error as e:
            print(f"Error getting course: {e}")
            return None
    
    def all_courses(self) -> List[Course]:
        """Get all courses from the database
        
        :return: List of all Course objects
        :rtype: List[Course]
        
        Retrieves all courses from the database, ordered by course name. Each course
        has its instructor (if any) and enrolled students loaded.
        """
        courses = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.course_id, c.course_name, c.instructor_id,
                           i.name, i.age, i.email, i.instructor_id
                    FROM courses c
                    LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
                    ORDER BY c.course_name
                ''')
                rows = cursor.fetchall()
                
                for row in rows:
                    instructor = None
                    if row[2]:  # if instructor_id is not None
                        instructor = Instructor(row[3], row[4], row[5], row[6])
                    
                    course = Course(row[0], row[1], instructor)
                    course.enrolled_students = self.get_course_students(row[0])
                    courses.append(course)
        except sqlite3.Error as e:
            print(f"Error getting all courses: {e}")
        
        return courses
    
    def edit_course(self, course: Course) -> bool:
        """Update an existing course in the database
        
        :param course: Course object with updated information
        :type course: Course
        :return: True if successful, False otherwise
        :rtype: bool
        
        Updates a course's information in the database. The course_id is used
        to identify which course to update.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                instructor_id = course.instructor.instructor_id if course.instructor else None
                cursor.execute('''
                    UPDATE courses 
                    SET course_name = ?, instructor_id = ?
                    WHERE course_id = ?
                ''', (course.course_name, instructor_id, course.course_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating course: {e}")
            return False
    
    def delete_course(self, course_id: str) -> bool:
        """Delete a course from the database
        
        :param course_id: The course ID to delete
        :type course_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Deletes a course and also removes all student enrollments for that course.
        This is a cascading delete operation.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # First remove from student_courses table
                cursor.execute('DELETE FROM student_courses WHERE course_id = ?', (course_id,))
                # Then delete the course
                cursor.execute('DELETE FROM courses WHERE course_id = ?', (course_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting course: {e}")
            return False
    
    def register_student_in_course(self, student_id: str, course_id: str) -> bool:
        """Register a student in a course
        
        :param student_id: The student ID to enroll
        :type student_id: str
        :param course_id: The course ID to enroll in
        :type course_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Enrolls a student in a course. Uses INSERT OR IGNORE so it won't fail
        if the student is already enrolled.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO student_courses (student_id, course_id)
                    VALUES (?, ?)
                ''', (student_id, course_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error enrolling student in course: {e}")
            return False
    
    def unregister_student_from_course(self, student_id: str, course_id: str) -> bool:
        """Unregister a student from a course
        
        :param student_id: The student ID to unenroll
        :type student_id: str
        :param course_id: The course ID to unenroll from
        :type course_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Removes a student's enrollment from a course.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM student_courses 
                    WHERE student_id = ? AND course_id = ?
                ''', (student_id, course_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error unenrolling student from course: {e}")
            return False
    
    def assign_instructor_to_course(self, instructor_id: str, course_id: str) -> bool:
        """Assign an instructor to a course
        
        :param instructor_id: The instructor ID to assign
        :type instructor_id: str
        :param course_id: The course ID to assign to
        :type course_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Assigns an instructor to teach a course. Includes validation to make sure
        the instructor isn't already teaching another course and the course doesn't
        already have an instructor.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if instructor is already assigned to another course
                cursor.execute('''
                    SELECT course_id FROM courses 
                    WHERE instructor_id = ? AND course_id != ?
                ''', (instructor_id, course_id))
                existing_course = cursor.fetchone()
                if existing_course:
                    print(f"Instructor {instructor_id} is already assigned to course {existing_course[0]}")
                    return False
                
                # Check if course already has an instructor
                cursor.execute('''
                    SELECT instructor_id FROM courses 
                    WHERE course_id = ? AND instructor_id IS NOT NULL
                ''', (course_id,))
                existing_instructor = cursor.fetchone()
                if existing_instructor:
                    print(f"Course {course_id} already has instructor {existing_instructor[0]}")
                    return False
                
                # If both checks pass, assign the instructor
                cursor.execute('''
                    UPDATE courses 
                    SET instructor_id = ?
                    WHERE course_id = ?
                ''', (instructor_id, course_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error assigning instructor to course: {e}")
            return False
    
    def unassign_instructor_from_course(self, course_id: str) -> bool:
        """Unassign an instructor from a course
        
        :param course_id: The course ID to unassign instructor from
        :type course_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Removes the instructor assignment from a course, setting it to NULL.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE courses 
                    SET instructor_id = NULL
                    WHERE course_id = ?
                ''', (course_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error unassigning instructor from course: {e}")
            return False
    
   
    def get_student_courses(self, student_id: str) -> List[Course]:
        """Get all courses a student is enrolled in
        
        :param student_id: The student ID to look up
        :type student_id: str
        :return: List of Course objects the student is enrolled in
        :rtype: List[Course]
        
        Helper method that retrieves all courses a specific student is enrolled in.
        Used internally when loading student objects.
        """
        courses = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.course_id, c.course_name, c.instructor_id,
                           i.name, i.age, i.email, i.instructor_id
                    FROM courses c
                    LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
                    JOIN student_courses sc ON c.course_id = sc.course_id
                    WHERE sc.student_id = ?
                ''', (student_id,))
                rows = cursor.fetchall()
                
                for row in rows:
                    instructor = None
                    if row[2]:  # if instructor_id is not None
                        instructor = Instructor(row[3], row[4], row[5], row[6])
                    
                    course = Course(row[0], row[1], instructor)
                    courses.append(course)
        except sqlite3.Error as e:
            print(f"Error getting student courses: {e}")
        
        return courses
    
    def get_instructor_courses(self, instructor_id: str) -> List[Course]:
        """Get all courses an instructor is assigned to
        
        :param instructor_id: The instructor ID to look up
        :type instructor_id: str
        :return: List of Course objects the instructor is assigned to
        :rtype: List[Course]
        
        Helper method that retrieves all courses a specific instructor is teaching.
        Used internally when loading instructor objects.
        """
        courses = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT course_id, course_name, instructor_id
                    FROM courses
                    WHERE instructor_id = ?
                ''', (instructor_id,))
                rows = cursor.fetchall()
                
                for row in rows:
                    # Create course without instructor 
                    # The instructor will be set when the course is loaded 
                    course = Course(row[0], row[1], None)
                    courses.append(course)
        except sqlite3.Error as e:
            print(f"Error getting instructor courses: {e}")
        
        return courses
    
    def get_course_students(self, course_id: str) -> List[Student]:
        """Get all students enrolled in a course
        
        :param course_id: The course ID to look up
        :type course_id: str
        :return: List of Student objects enrolled in the course
        :rtype: List[Student]
        
        Helper method that retrieves all students enrolled in a specific course.
        Used internally when loading course objects.
        """
        students = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.student_id, s.name, s.age, s.email
                    FROM students s
                    JOIN student_courses sc ON s.student_id = sc.student_id
                    WHERE sc.course_id = ?
                ''', (course_id,))
                rows = cursor.fetchall()
                
                for row in rows:
                    student = Student(row[1], row[2], row[3], row[0])
                    students.append(student)
        except sqlite3.Error as e:
            print(f"Error getting course students: {e}")
        
        return students
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics - counts of all entities
        
        :return: Dictionary with counts of students, instructors, courses, and enrollments
        :rtype: Dict[str, int]
        
        Returns a dictionary with the total count of students, instructors, courses,
        and student enrollments. Useful for displaying summary information.
        """
        stats = {}
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM students')
                stats['students'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM instructors')
                stats['instructors'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM courses')
                stats['courses'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM student_courses')
                stats['enrollments'] = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting database stats: {e}")
            stats = {'students': 0, 'instructors': 0, 'courses': 0, 'enrollments': 0}
        
        return stats
    
    def clear_database(self) -> bool:
        """Clear all data from the database - deletes everything
        
        :return: True if successful, False otherwise
        :rtype: bool
        
        WARNING: This deletes ALL data from the database! Use with caution.
        Deletes in the correct order to respect foreign key constraints.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM student_courses')
                cursor.execute('DELETE FROM courses')
                cursor.execute('DELETE FROM instructors')
                cursor.execute('DELETE FROM students')
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error clearing database: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database file
        
        :param backup_path: Path where to save the backup file
        :type backup_path: str
        :return: True if successful, False otherwise
        :rtype: bool
        
        Creates a copy of the database file to the specified backup location.
        Useful for creating backups before major operations.
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False



