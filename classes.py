"""Domain Models for School Management System

This module contains all the main classes for the school management system.
Basically the core objects that represent students, instructors, and courses.

Classes:
- Person: Base class with common attributes like name, age, email
- Student: Inherits from Person, adds student-specific stuff
- Instructor: Inherits from Person, adds instructor-specific stuff  
- Course: Represents a course with instructor and enrolled students

All classes have validation methods to make sure the data is correct.
"""

import re
from typing import Dict, Any

class Person:
    """Base class for all people in the system - the parent class basically
    
    This is the base class that both Student and Instructor inherit from.
    It has all the common stuff like name, age, and email with validation.
    
    :param name: Person's full name
    :type name: str
    :param age: Person's age (must be non-negative)
    :type age: int
    :param email: Person's email address (must be valid format)
    :type email: str
    """
    
    def __init__(self, name: str, age: int, email: str):
        """Constructor method - sets up a new person with validation"""
        self.name = self.valid_name(name)
        self.age = self.valid_age(age)
        self.__email = self.valid_email(email)
    
    def valid_name(self, name: str) -> str:
        """Check that the name is valid - makes sure it's not empty
        
        :param name: The name to validate
        :type name: str
        :return: The cleaned name (stripped of whitespace)
        :rtype: str
        :raises ValueError: If name is empty or not a string
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Name must be a non-empty string")
        return name.strip()
    
    def valid_age(self, age: int) -> int:
        """Check that the age is valid - makes sure it's not negative
        
        :param age: The age to validate
        :type age: int
        :return: The validated age
        :rtype: int
        :raises ValueError: If age is negative or not an integer
        """
        if not isinstance(age, int) or age < 0:
            raise ValueError("Age must be a non-negative integer")
        return age
    
    def valid_email(self, email: str) -> str:
        """Check that the email is valid - uses regex to validate email format
        
        :param email: The email to validate
        :type email: str
        :return: The validated email
        :rtype: str
        :raises ValueError: If email format is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not isinstance(email, str) or not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email
    
    def introduce(self):
        """Introduce the person - prints basic info about the person
        
        Just prints out the person's name and age. Pretty simple.
        """
        print(f"My name is {self.name}, I'm {self.age} years old.")
    
    @property
    def email(self):
        return self.__email
    
    @email.setter
    def email(self, new_email: str):
        self.__email = self.valid_email(new_email)
    

    def person_to_dict(self) -> Dict[str, Any]:
        """Convert person to dictionary - for saving to database
        
        :return: Dictionary with person's data
        :rtype: Dict[str, Any]
        """
        return {
            'name': self.name,
            'age': self.age,
            'email': self.__email
        }
    
    def dict_to_person(cls, data: Dict[str, Any]) -> 'Person':
        return cls(data['name'], data['age'], data['email'])


class Student(Person):
    """Student class - inherits from Person, adds student-specific stuff
    
    This is for students in the school. It has everything from Person plus
    a student ID and a list of courses they're registered for.
    
    :param name: Student's full name
    :type name: str
    :param age: Student's age (must be non-negative)
    :type age: int
    :param email: Student's email address (must be valid format)
    :type email: str
    :param student_id: Unique student identifier
    :type student_id: str
    """
    
    def __init__(self, name: str, age: int, email: str, student_id: str):
        """Constructor method - sets up a new student with validation"""
        super().__init__(name, age, email)
        self.student_id = self.valid_student_id(student_id)
        self.registered_courses = [] 

    def valid_student_id(self, student_id: str) -> str:
        """Check that the student ID is valid - makes sure it's not empty
        
        :param student_id: The student ID to validate
        :type student_id: str
        :return: The cleaned student ID (stripped of whitespace)
        :rtype: str
        :raises ValueError: If student ID is empty or not a string
        """
        if not isinstance(student_id, str) or not student_id.strip():
            raise ValueError("Student ID must be a non-empty string")
        return student_id.strip()
    

    def introduce(self):
        """Introduce the student - prints student info including ID
        
        Overrides the parent introduce method to include student-specific info.
        """
        print(f"My name is {self.name}, I'm {self.age} years old. I'm a student and my ID is: {self.student_id}")


    def register_course(self, course):
        """Register for a course - adds the course to student's list
        
        :param course: The course to register for
        :type course: Course
        
        Makes sure the student doesn't register for the same course twice.
        Also adds the student to the course's enrolled students list.
        """
        if course not in self.registered_courses:
            self.registered_courses.append(course)
            # i have also to add the student to the course's enrolled students
            course.enrolled_students.append(self)
            print(f"{self.student_id} successfully registered for {course}")
        else:
            print(f"Already registered for {course}")
    
    def unregister_course(self, course):
        """Unregister from a course - removes the course from student's list
        
        :param course: The course to unregister from
        :type course: Course
        
        Removes the course from the student's registered courses and also
        removes the student from the course's enrolled students list.
        """
        if course in self.registered_courses:
            self.registered_courses.remove(course)
            # i have also to remove the student from the course's enrolled students
            course.enrolled_students.remove(self)
            print(f"{self.student_id} successfully unregistered from {course}")
        else:
            print(f"Not registered for {course}")
    
    
    def list_courses(self):
        """List all courses the student is registered for
        
        Prints out all the courses this student is taking. If they're not
        registered for any courses, it says so.
        """
        if self.registered_courses:
            print(f"Registered courses for {self.name}:")
            for course in self.registered_courses:
                print(f"  - {course}")
        else:
            print(f"{self.name} is not registered for any courses yet.")
    

    def student_to_dict(self) -> Dict[str, Any]:
        """Convert student to dictionary - for saving to database
        
        :return: Dictionary with student's data including registered courses
        :rtype: Dict[str, Any]
        
        This is used by the database manager to save student data.
        """
        base_dict = super().person_to_dict()
        base_dict.update({
            'student_id': self.student_id,
            'registered_courses': [course.course_id for course in self.registered_courses]
        })
        return base_dict
    
    def dict_to_student(cls, data: Dict[str, Any]) -> 'Student':
        """Create a Student from dictionary data - for loading from database
        
        :param data: Dictionary containing student data
        :type data: Dict[str, Any]
        :return: New Student instance
        :rtype: Student
        
        This is used by the database manager to load student data.
        """
        return cls(data['name'], data['age'], data['email'], data['student_id'])
    
    def get(self, key, default=None):
        """Get attribute value with default - like dict.get() but for objects
        
        :param key: Attribute name to get
        :type key: str
        :param default: Default value if attribute doesn't exist
        :return: Attribute value or default
        
        This is useful for database operations where you need to handle
        missing attributes gracefully.
        """
        return getattr(self, key, default)


class Instructor(Person):
    """Instructor class - inherits from Person, adds instructor-specific stuff
    
    This is for instructors/teachers in the school. It has everything from Person plus
    an instructor ID and a list of courses they're assigned to teach.
    
    :param name: Instructor's full name
    :type name: str
    :param age: Instructor's age (must be non-negative)
    :type age: int
    :param email: Instructor's email address (must be valid format)
    :type email: str
    :param instructor_id: Unique instructor identifier
    :type instructor_id: str
    """
    
    def __init__(self, name: str, age: int, email: str, instructor_id: str):
        """Constructor method - sets up a new instructor with validation"""
        super().__init__(name, age, email)
        self.instructor_id = self.valid_instructor_id(instructor_id)
        self.assigned_courses = [] 
    
    def valid_instructor_id(self, instructor_id: str) -> str:
        """Check that the instructor ID is valid - makes sure it's not empty
        
        :param instructor_id: The instructor ID to validate
        :type instructor_id: str
        :return: The cleaned instructor ID (stripped of whitespace)
        :rtype: str
        :raises ValueError: If instructor ID is empty or not a string
        """
        if not isinstance(instructor_id, str) or not instructor_id.strip():
            raise ValueError("Instructor ID must be a non-empty string")
        return instructor_id.strip()
    
    def introduce(self):
        """Introduce the instructor - prints instructor info including ID
        
        Overrides the parent introduce method to include instructor-specific info.
        """
        print(f"My name is {self.name}, I'm {self.age} years old. I'm an instructor and my ID is: {self.instructor_id}")


    def assign_course(self, course):
        """Assign a course to this instructor - adds course to instructor's list
        
        :param course: The course to assign
        :type course: Course
        
        Makes sure the course isn't already assigned to someone else and that
        this instructor isn't already assigned to this course.
        """
        if course.instructor is not None:
            print(f"{course} is already assigned to {course.instructor.name}")
            return
        if course not in self.assigned_courses:
            self.assigned_courses.append(course)
            course.instructor = self  
            print(f"Successfully assigned {course} to {self.name}")
        else:
            print(f"{course} is already assigned to {self.name}")
    
    def unassign_course(self, course):
        """Unassign a course from this instructor - removes course from instructor's list
        
        :param course: The course to unassign
        :type course: Course
        
        Removes the course from the instructor's assigned courses and sets
        the course's instructor to None.
        """
        if course in self.assigned_courses:
            self.assigned_courses.remove(course)
            course.instructor = None
            print(f"Successfully unassigned {course} from {self.name}")
        else:
            print(f"{course} is not assigned to {self.name}")
    
    
    def list_assigned_courses(self):
        """List all courses assigned to this instructor
        
        Prints out all the courses this instructor is teaching. If they're not
        assigned to any courses, it says so.
        """
        if self.assigned_courses:
            print(f"Assigned courses for {self.name}:")
            for course in self.assigned_courses:
                print(f"  - {course}")
        else:
            print(f"{self.name} is not assigned to any courses yet.")
    

    def instructor_to_dict(self) -> Dict[str, Any]:
        """Convert instructor to dictionary - for saving to database
        
        :return: Dictionary with instructor's data including assigned courses
        :rtype: Dict[str, Any]
        
        This is used by the database manager to save instructor data.
        """
        base_dict = super().person_to_dict()
        base_dict.update({
            'instructor_id': self.instructor_id,
            'assigned_courses': [course.course_id for course in self.assigned_courses]
        })
        return base_dict
    
    def from_dict(cls, data: Dict[str, Any]) -> 'Instructor':
        """Create an Instructor from dictionary data - for loading from database
        
        :param data: Dictionary containing instructor data
        :type data: Dict[str, Any]
        :return: New Instructor instance
        :rtype: Instructor
        
        This is used by the database manager to load instructor data.
        """
        return cls(data['name'], data['age'], data['email'], data['instructor_id'])
    
    def get(self, key, default=None):
        """Get attribute value with default - like dict.get() but for objects
        
        :param key: Attribute name to get
        :type key: str
        :param default: Default value if attribute doesn't exist
        :return: Attribute value or default
        
        This is useful for database operations where you need to handle
        missing attributes gracefully.
        """
        return getattr(self, key, default)


class Course:
    """Course class - represents a course with instructor and enrolled students
    
    This represents a course in the school. It has a course ID, name, an instructor
    (optional), and a list of enrolled students.
    
    :param course_id: Unique course identifier
    :type course_id: str
    :param course_name: Name of the course
    :type course_name: str
    :param instructor: The instructor teaching this course (optional)
    :type instructor: Instructor, optional
    """
    
    def __init__(self, course_id: str, course_name: str, instructor: Instructor = None):
        """Constructor method - sets up a new course with validation"""
        self.course_id = self.valid_course_id(course_id)
        self.course_name = self.valid_course_name(course_name)
        self.instructor = self.valid_instructor(instructor)
        self.enrolled_students = [] 
    
    def valid_course_id(self, course_id: str) -> str:
        """Check that the course ID is valid - makes sure it's not empty
        
        :param course_id: The course ID to validate
        :type course_id: str
        :return: The cleaned course ID (stripped of whitespace)
        :rtype: str
        :raises ValueError: If course ID is empty or not a string
        """
        if not isinstance(course_id, str) or not course_id.strip():
            raise ValueError("Course ID must be a non-empty string")
        return course_id.strip()
    
    def valid_course_name(self, course_name: str) -> str:
        """Check that the course name is valid - makes sure it's not empty
        
        :param course_name: The course name to validate
        :type course_name: str
        :return: The cleaned course name (stripped of whitespace)
        :rtype: str
        :raises ValueError: If course name is empty or not a string
        """
        if not isinstance(course_name, str) or not course_name.strip():
            raise ValueError("Course name must be a non-empty string")
        return course_name.strip()
    
    def valid_instructor(self, instructor) -> Instructor:
        """Check that the instructor is valid - makes sure it's an Instructor object or None
        
        :param instructor: The instructor to validate
        :type instructor: Instructor or None
        :return: The validated instructor
        :rtype: Instructor or None
        :raises ValueError: If instructor is not an Instructor object or None
        """
        if instructor is not None and not isinstance(instructor, Instructor):
            raise ValueError("Instructor must be an Instructor object or None")
        return instructor
    
    def add_student(self, student):
        """Add a student to this course - enrolls a student in the course
        
        :param student: The student to enroll
        :type student: Student
        :raises ValueError: If student is not a Student object
        
        Makes sure the student isn't already enrolled in this course.
        """
        if not isinstance(student, Student):
            raise ValueError("Student must be a Student object")
        
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)
            print(f"Successfully enrolled {student.name} in {self.course_name}")
        else:
            print(f"{student.name} is already enrolled in {self.course_name}")
        
    
    def course_to_dict(self) -> Dict[str, Any]:
        """Convert course to dictionary - for saving to database
        
        :return: Dictionary with course's data including instructor and enrolled students
        :rtype: Dict[str, Any]
        
        This is used by the database manager to save course data.
        """
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'instructor_id': self.instructor.instructor_id if self.instructor else None,
            'enrolled_students': [student.student_id for student in self.enrolled_students]
        }
    
    def dict_to_course(cls, data: Dict[str, Any], instructor: Instructor = None) -> 'Course':
        """Create a Course from dictionary data - for loading from database
        
        :param data: Dictionary containing course data
        :type data: Dict[str, Any]
        :param instructor: The instructor for this course (optional)
        :type instructor: Instructor, optional
        :return: New Course instance
        :rtype: Course
        
        This is used by the database manager to load course data.
        """
        return cls(data['course_id'], data['course_name'], instructor)
    
    def get(self, key, default=None):
        """Get attribute value with default - like dict.get() but for objects
        
        :param key: Attribute name to get
        :type key: str
        :param default: Default value if attribute doesn't exist
        :return: Attribute value or default
        
        This is useful for database operations where you need to handle
        missing attributes gracefully.
        """
        return getattr(self, key, default)



