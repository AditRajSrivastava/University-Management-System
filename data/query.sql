-- DROP existing database and tables if they exist
DROP DATABASE IF EXISTS student_management_system_new;

-- Create database
CREATE DATABASE student_management_system_new;
USE student_management_system_new;

-- Disable foreign key checks temporarily to avoid issues during table creation
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Person superclass
CREATE TABLE Person (
    person_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    contact_number VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    person_type ENUM('Student', 'Faculty', 'Staff') NOT NULL
);

-- 2. Student subclass
CREATE TABLE Student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT UNIQUE NOT NULL,
    enrollment_date DATE NOT NULL,
    graduation_date DATE,
    status ENUM('Active', 'Inactive', 'Graduated', 'Suspended') DEFAULT 'Active',
    dept_id INT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
);

-- 3. Faculty subclass
CREATE TABLE Faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT UNIQUE NOT NULL,
    hire_date DATE NOT NULL,
    faculty_rank VARCHAR(50),
    specialization VARCHAR(100),
    dept_id INT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
);

-- 4. Staff subclass
CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT UNIQUE NOT NULL,
    position VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE
);

-- 5. Department
CREATE TABLE Department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    building VARCHAR(50),
    budget DECIMAL(15,2),
    head_faculty_id INT,
    FOREIGN KEY (head_faculty_id) REFERENCES Faculty(faculty_id)
);

-- Now add the foreign keys that were previously missing due to creation order
ALTER TABLE Student ADD CONSTRAINT fk_student_dept 
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id);

ALTER TABLE Faculty ADD CONSTRAINT fk_faculty_dept 
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id);

-- 6. Course
CREATE TABLE Course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    description TEXT,
    dept_id INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
);

-- 7. Section
CREATE TABLE Section (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester ENUM('Fall', 'Spring', 'Summer') NOT NULL,
    year YEAR NOT NULL,
    room_number VARCHAR(20),
    faculty_id INT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (faculty_id) REFERENCES Faculty(faculty_id)
);

-- 8. Prerequisite
CREATE TABLE Prerequisite (
    course_id INT NOT NULL,
    prereq_course_id INT NOT NULL,
    PRIMARY KEY (course_id, prereq_course_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (prereq_course_id) REFERENCES Course(course_id),
    CHECK (course_id != prereq_course_id)
);

-- 9. Schedule
CREATE TABLE Schedule (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (section_id) REFERENCES Section(section_id) ON DELETE CASCADE
);

-- 10. Grade
CREATE TABLE Grade (
    grade_id INT AUTO_INCREMENT PRIMARY KEY,
    letter_grade VARCHAR(2) NOT NULL,
    points DECIMAL(3,2) NOT NULL,
    date_recorded DATE NOT NULL,
    section_id INT NOT NULL,
    FOREIGN KEY (section_id) REFERENCES Section(section_id)
);

-- 11. Student_Record
CREATE TABLE Student_Record (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT UNIQUE NOT NULL,
    gpa DECIMAL(3,2),
    total_credits INT DEFAULT 0,
    standing ENUM('Freshman', 'Sophomore', 'Junior', 'Senior') DEFAULT 'Freshman',
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
);

-- 12. Transcript
CREATE TABLE Transcript (
    transcript_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    issue_date DATE NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
);

-- Bridge table for Transcript-Grade
CREATE TABLE Transcript_Grade (
    transcript_id INT NOT NULL,
    grade_id INT NOT NULL,
    PRIMARY KEY (transcript_id, grade_id),
    FOREIGN KEY (transcript_id) REFERENCES Transcript(transcript_id) ON DELETE CASCADE,
    FOREIGN KEY (grade_id) REFERENCES Grade(grade_id) ON DELETE CASCADE
);

-- 13. Degree_Program
CREATE TABLE Degree_Program (
    program_id INT AUTO_INCREMENT PRIMARY KEY,
    program_name VARCHAR(100) NOT NULL,
    total_credits_required INT NOT NULL,
    dept_id INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id)
);

-- 14. Requirement
CREATE TABLE Requirement (
    req_id INT AUTO_INCREMENT PRIMARY KEY,
    program_id INT NOT NULL,
    req_type ENUM('Core', 'Elective', 'General') NOT NULL,
    credits_required INT NOT NULL,
    description TEXT,
    FOREIGN KEY (program_id) REFERENCES Degree_Program(program_id) ON DELETE CASCADE
);

-- 15. Building
CREATE TABLE Building (
    building_id INT AUTO_INCREMENT PRIMARY KEY,
    building_name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    floors INT
);

-- 16. Room
CREATE TABLE Room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    capacity INT,
    room_type ENUM('Classroom', 'Lab', 'Office', 'Auditorium') NOT NULL,
    FOREIGN KEY (building_id) REFERENCES Building(building_id),
    UNIQUE (building_id, room_number)
);

-- 17. Facility
CREATE TABLE Facility (
    facility_id INT AUTO_INCREMENT PRIMARY KEY,
    facility_type ENUM('Library', 'Gym', 'Lab', 'Cafeteria') NOT NULL,
    location VARCHAR(255) NOT NULL,
    manager_staff_id INT,
    FOREIGN KEY (manager_staff_id) REFERENCES Staff(staff_id)
);

-- 18. Library_Book
CREATE TABLE Library_Book (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    status ENUM('Available', 'Checked Out', 'Lost') DEFAULT 'Available',
    facility_id INT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES Facility(facility_id)
);

-- 19. Checkout_Record
CREATE TABLE Checkout_Record (
    checkout_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    student_id INT NOT NULL,
    checkout_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    FOREIGN KEY (book_id) REFERENCES Library_Book(book_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
);

-- 20. Student_Tuition
CREATE TABLE Student_Tuition (
    tuition_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('Paid', 'Unpaid', 'Partial') DEFAULT 'Unpaid',
    semester ENUM('Fall', 'Spring', 'Summer') NOT NULL,
    year YEAR NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
);

-- 21. Scholarship
CREATE TABLE Scholarship (
    scholarship_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    criteria TEXT,
    donor VARCHAR(100)
);

-- 22. Payment
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATETIME NOT NULL,
    method ENUM('Credit Card', 'Debit Card', 'Bank Transfer', 'Cash', 'Check') NOT NULL,
    tuition_id INT,
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (tuition_id) REFERENCES Student_Tuition(tuition_id)
);

-- 23. Financial_Aid
CREATE TABLE Financial_Aid (
    aid_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    aid_type ENUM('Loan', 'Grant', 'Work Study') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    terms TEXT,
    application_date DATE NOT NULL,
    status ENUM('Pending', 'Approved', 'Denied') DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
);

-- 24. Club
CREATE TABLE Club (
    club_id INT AUTO_INCREMENT PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    meeting_schedule VARCHAR(255),
    faculty_advisor_id INT,
    FOREIGN KEY (faculty_advisor_id) REFERENCES Faculty(faculty_id)
);

-- 25. Event
CREATE TABLE Event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT,
    organizer_type ENUM('Club', 'Department') NOT NULL,
    organizer_club_id INT,
    organizer_dept_id INT,
    FOREIGN KEY (organizer_club_id) REFERENCES Club(club_id),
    FOREIGN KEY (organizer_dept_id) REFERENCES Department(dept_id),
    CHECK (
        (organizer_type = 'Club' AND organizer_club_id IS NOT NULL AND organizer_dept_id IS NULL) OR
        (organizer_type = 'Department' AND organizer_dept_id IS NOT NULL AND organizer_club_id IS NULL)
    )
);

-- Many-to-many relationships

-- Student-Course Enrollment
CREATE TABLE Enrollment (
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    grade_id INT,
    PRIMARY KEY (student_id, section_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (section_id) REFERENCES Section(section_id),
    FOREIGN KEY (grade_id) REFERENCES Grade(grade_id)
);

-- Student-Degree Program
CREATE TABLE Program_Enrollment (
    student_id INT NOT NULL,
    program_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    expected_graduation DATE,
    PRIMARY KEY (student_id, program_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (program_id) REFERENCES Degree_Program(program_id)
);

-- Student-Club Membership
CREATE TABLE Club_Membership (
    student_id INT NOT NULL,
    club_id INT NOT NULL,
    join_date DATE NOT NULL,
    role ENUM('Member', 'Officer', 'President') DEFAULT 'Member',
    PRIMARY KEY (student_id, club_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (club_id) REFERENCES Club(club_id)
);

-- Student-Scholarship
CREATE TABLE Student_Scholarship (
    student_id INT NOT NULL,
    scholarship_id INT NOT NULL,
    award_date DATE NOT NULL,
    amount_awarded DECIMAL(10,2) NOT NULL,
    semester ENUM('Fall', 'Spring', 'Summer') NOT NULL,
    year YEAR NOT NULL,
    PRIMARY KEY (student_id, scholarship_id, semester, year),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (scholarship_id) REFERENCES Scholarship(scholarship_id)
);

-- Insert sample data for University Management System

-- Insert Departments
INSERT INTO Department (dept_name, building, budget) VALUES
('Computer Science', 'Engineering Building', 500000.00),
('Mathematics', 'Science Building', 350000.00),
('Physics', 'Science Building', 400000.00),
('Biology', 'Life Sciences Building', 450000.00),
('Business Administration', 'Business Building', 600000.00);

-- Insert Persons (Students, Faculty, Staff)
INSERT INTO Person (first_name, last_name, date_of_birth, gender, contact_number, email, person_type) VALUES
-- Students
('John', 'Smith', '2000-05-15', 'Male', '555-0101', 'john.smith@university.edu', 'Student'),
('Emily', 'Johnson', '2001-02-20', 'Female', '555-0102', 'emily.johnson@university.edu', 'Student'),
('Michael', 'Williams', '1999-11-10', 'Male', '555-0103', 'michael.williams@university.edu', 'Student'),
('Sarah', 'Brown', '2000-08-25', 'Female', '555-0104', 'sarah.brown@university.edu', 'Student'),
('David', 'Jones', '2001-03-30', 'Male', '555-0105', 'david.jones@university.edu', 'Student'),
-- Faculty
('Robert', 'Davis', '1975-06-18', 'Male', '555-0201', 'robert.davis@university.edu', 'Faculty'),
('Jennifer', 'Miller', '1980-09-22', 'Female', '555-0202', 'jennifer.miller@university.edu', 'Faculty'),
('Thomas', 'Wilson', '1972-12-05', 'Male', '555-0203', 'thomas.wilson@university.edu', 'Faculty'),
('Lisa', 'Moore', '1978-04-15', 'Female', '555-0204', 'lisa.moore@university.edu', 'Faculty'),
('James', 'Taylor', '1965-07-30', 'Male', '555-0205', 'james.taylor@university.edu', 'Faculty'),
-- Staff
('Patricia', 'Anderson', '1985-01-10', 'Female', '555-0301', 'patricia.anderson@university.edu', 'Staff'),
('Christopher', 'Thomas', '1990-10-12', 'Male', '555-0302', 'christopher.thomas@university.edu', 'Staff'),
('Nancy', 'Jackson', '1988-03-25', 'Female', '555-0303', 'nancy.jackson@university.edu', 'Staff'),
('Daniel', 'White', '1982-11-18', 'Male', '555-0304', 'daniel.white@university.edu', 'Staff'),
('Karen', 'Harris', '1979-08-05', 'Female', '555-0305', 'karen.harris@university.edu', 'Staff');

-- Insert Students
INSERT INTO Student (person_id, enrollment_date, graduation_date, status, dept_id) VALUES
(1, '2019-09-01', NULL, 'Active', 1),
(2, '2020-01-15', NULL, 'Active', 2),
(3, '2018-09-01', '2022-05-15', 'Graduated', 1),
(4, '2020-09-01', NULL, 'Active', 3),
(5, '2021-01-15', NULL, 'Active', 4);

-- Insert Faculty
INSERT INTO Faculty (person_id, hire_date, faculty_rank, specialization, dept_id) VALUES
(6, '2010-08-15', 'Professor', 'Artificial Intelligence', 1),
(7, '2015-01-10', 'Associate Professor', 'Data Structures', 1),
(8, '2005-09-01', 'Professor', 'Quantum Mechanics', 3),
(9, '2018-03-15', 'Assistant Professor', 'Cell Biology', 4),
(10, '2000-06-01', 'Professor', 'Financial Management', 5);

-- Insert Staff
INSERT INTO Staff (person_id, position, department) VALUES
(11, 'Administrative Assistant', 'Registrar Office'),
(12, 'IT Support Specialist', 'Information Technology'),
(13, 'Lab Technician', 'Biology Department'),
(14, 'Financial Officer', 'Finance Department'),
(15, 'Librarian', 'University Library');

-- Set department heads
UPDATE Department SET head_faculty_id = 6 WHERE dept_id = 1;
UPDATE Department SET head_faculty_id = 7 WHERE dept_id = 2;
UPDATE Department SET head_faculty_id = 8 WHERE dept_id = 3;
UPDATE Department SET head_faculty_id = 9 WHERE dept_id = 4;
UPDATE Department SET head_faculty_id = 10 WHERE dept_id = 5;

-- Insert Courses
INSERT INTO Course (title, credits, description, dept_id) VALUES
('Introduction to Programming', 4, 'Basic programming concepts using Python', 1),
('Data Structures', 4, 'Fundamental data structures and algorithms', 1),
('Calculus I', 4, 'Limits, derivatives, and integrals', 2),
('Linear Algebra', 3, 'Vector spaces and linear transformations', 2),
('Quantum Physics', 4, 'Introduction to quantum mechanics', 3),
('Genetics', 4, 'Principles of genetic inheritance', 4),
('Financial Accounting', 3, 'Fundamentals of financial accounting', 5),
('Database Systems', 4, 'Design and implementation of databases', 1),
('Operating Systems', 4, 'Principles of operating system design', 1),
('Discrete Mathematics', 3, 'Mathematical structures for computer science', 2);

-- Insert Prerequisites
INSERT INTO Prerequisite (course_id, prereq_course_id) VALUES
(2, 1),  -- Data Structures requires Intro to Programming
(5, 3),  -- Quantum Physics requires Calculus I
(8, 1),  -- Database Systems requires Intro to Programming
(9, 2),  -- Operating Systems requires Data Structures
(10, 3); -- Discrete Math requires Calculus I

-- Insert Sections
INSERT INTO Section (course_id, semester, year, room_number, faculty_id) VALUES
(1, 'Fall', 2023, 'ENG-101', 6),
(2, 'Fall', 2023, 'ENG-205', 7),
(3, 'Fall', 2023, 'SCI-102', 7),
(4, 'Spring', 2023, 'SCI-104', 7),
(5, 'Fall', 2023, 'SCI-201', 8),
(6, 'Spring', 2023, 'LIF-301', 9),
(7, 'Fall', 2023, 'BUS-101', 10),
(8, 'Spring', 2023, 'ENG-103', 6),
(9, 'Fall', 2023, 'ENG-207', 7),
(10, 'Spring', 2023, 'SCI-105', 7);

-- Insert Schedule
INSERT INTO Schedule (section_id, day_of_week, start_time, end_time) VALUES
(1, 'Monday', '09:00:00', '10:30:00'),
(1, 'Wednesday', '09:00:00', '10:30:00'),
(2, 'Tuesday', '13:00:00', '14:30:00'),
(2, 'Thursday', '13:00:00', '14:30:00'),
(3, 'Monday', '10:00:00', '11:30:00'),
(3, 'Wednesday', '10:00:00', '11:30:00'),
(4, 'Tuesday', '11:00:00', '12:30:00'),
(4, 'Thursday', '11:00:00', '12:30:00'),
(5, 'Friday', '14:00:00', '17:00:00');

-- Insert Grades
INSERT INTO Grade (letter_grade, points, date_recorded, section_id) VALUES
('A', 4.0, '2023-05-15', 1),
('B+', 3.3, '2023-05-15', 1),
('A-', 3.7, '2023-05-15', 2),
('B', 3.0, '2023-05-15', 3),
('C+', 2.3, '2023-05-15', 4),
('A', 4.0, '2023-05-15', 5),
('B-', 2.7, '2023-05-15', 6),
('A', 4.0, '2023-05-15', 7),
('B+', 3.3, '2023-05-15', 8),
('A-', 3.7, '2023-05-15', 9);

-- Insert Student Records
INSERT INTO Student_Record (student_id, gpa, total_credits, standing) VALUES
(1, 3.8, 45, 'Junior'),
(2, 3.5, 30, 'Sophomore'),
(3, 3.2, 120, 'Senior'),
(4, 3.9, 60, 'Junior'),
(5, 3.0, 15, 'Freshman');

-- Insert Enrollments
INSERT INTO Enrollment (student_id, section_id, enrollment_date, grade_id) VALUES
(1, 1, '2023-08-20', 1),
(2, 1, '2023-08-21', 2),
(3, 2, '2023-08-20', 3),
(4, 3, '2023-08-22', 4),
(5, 4, '2023-08-23', 5),
(1, 5, '2023-08-20', 6),
(2, 6, '2023-08-21', 7),
(3, 7, '2023-08-22', 8),
(4, 8, '2023-08-23', 9),
(5, 9, '2023-08-20', 10);

-- Insert Degree Programs
INSERT INTO Degree_Program (program_name, total_credits_required, dept_id) VALUES
('Bachelor of Science in Computer Science', 120, 1),
('Bachelor of Arts in Mathematics', 110, 2),
('Bachelor of Science in Physics', 125, 3),
('Bachelor of Science in Biology', 130, 4),
('Bachelor of Business Administration', 115, 5);

-- Insert Program Enrollments
INSERT INTO Program_Enrollment (student_id, program_id, enrollment_date, expected_graduation) VALUES
(1, 1, '2019-09-01', '2023-05-15'),
(2, 2, '2020-01-15', '2024-05-15'),
(3, 1, '2018-09-01', '2022-05-15'),
(4, 3, '2020-09-01', '2024-05-15'),
(5, 4, '2021-01-15', '2025-05-15');

-- Insert Buildings
INSERT INTO Building (building_name, location, floors) VALUES
('Engineering Building', 'North Campus', 5),
('Science Building', 'Central Campus', 4),
('Life Sciences Building', 'East Campus', 3),
('Business Building', 'West Campus', 4),
('Library', 'Central Campus', 3);

-- Insert Rooms
INSERT INTO Room (building_id, room_number, capacity, room_type) VALUES
(1, '101', 30, 'Classroom'),
(1, '205', 25, 'Classroom'),
(2, '102', 40, 'Classroom'),
(2, '104', 35, 'Classroom'),
(2, '201', 20, 'Lab'),
(3, '301', 15, 'Lab'),
(4, '101', 50, 'Classroom'),
(1, '103', 30, 'Classroom'),
(1, '207', 20, 'Lab'),
(2, '105', 30, 'Classroom');

-- Insert Facilities
INSERT INTO Facility (facility_type, location, manager_staff_id) VALUES
('Library', 'Central Campus', 15),
('Gym', 'East Campus', 14),
('Lab', 'Engineering Building', 13),
('Cafeteria', 'Central Campus', 11);

-- Insert Library Books
INSERT INTO Library_Book (title, author, isbn, status, facility_id) VALUES
('Introduction to Algorithms', 'Thomas Cormen', '9780262033848', 'Available', 1),
('Clean Code', 'Robert Martin', '9780132350884', 'Checked Out', 1),
('The Pragmatic Programmer', 'Andrew Hunt', '9780201616224', 'Available', 1),
('Design Patterns', 'Erich Gamma', '9780201633610', 'Available', 1),
('Database System Concepts', 'Abraham Silberschatz', '9780078022159', 'Checked Out', 1);

-- Insert Checkout Records
INSERT INTO Checkout_Record (book_id, student_id, checkout_date, due_date) VALUES
(2, 1, '2023-09-10', '2023-10-10'),
(5, 3, '2023-09-15', '2023-10-15');

-- Insert Tuition
INSERT INTO Student_Tuition (student_id, amount, due_date, status, semester, year) VALUES
(1, 5000.00, '2023-09-30', 'Paid', 'Fall', 2023),
(2, 5000.00, '2023-09-30', 'Unpaid', 'Fall', 2023),
(3, 5000.00, '2023-09-30', 'Partial', 'Fall', 2023),
(4, 5000.00, '2023-09-30', 'Paid', 'Fall', 2023),
(5, 5000.00, '2023-09-30', 'Unpaid', 'Fall', 2023);

-- Insert Scholarships
INSERT INTO Scholarship (name, amount, criteria, donor) VALUES
('Presidential Scholarship', 10000.00, 'GPA 3.8+', 'University Endowment'),
('STEM Excellence Award', 5000.00, 'STEM majors with GPA 3.5+', 'Tech Corporation'),
('Need-Based Grant', 3000.00, 'Demonstrated financial need', 'Alumni Association'),
('Athletic Scholarship', 8000.00, 'Varsity team members', 'Athletic Department'),
('Research Fellowship', 6000.00, 'Undergraduate researchers', 'Science Foundation');

-- Insert Student Scholarships
INSERT INTO Student_Scholarship (student_id, scholarship_id, award_date, amount_awarded, semester, year) VALUES
(1, 1, '2023-08-15', 5000.00, 'Fall', 2023),
(2, 3, '2023-08-15', 3000.00, 'Fall', 2023),
(4, 2, '2023-08-15', 5000.00, 'Fall', 2023);

-- Insert Payments
INSERT INTO Payment (student_id, amount, payment_date, method, tuition_id) VALUES
(1, 5000.00, '2023-09-01 10:30:00', 'Bank Transfer', 1),
(3, 3000.00, '2023-09-05 14:15:00', 'Credit Card', 3),
(4, 5000.00, '2023-09-02 11:45:00', 'Debit Card', 4);

-- Insert Financial Aid
INSERT INTO Financial_Aid (student_id, aid_type, amount, terms, application_date, status) VALUES
(2, 'Loan', 10000.00, '5 year repayment', '2023-07-15', 'Approved'),
(5, 'Grant', 4000.00, 'Need-based', '2023-07-20', 'Approved'),
(1, 'Work Study', 2000.00, '10 hours/week', '2023-07-10', 'Approved');

-- Insert Clubs
INSERT INTO Club (club_name, description, meeting_schedule, faculty_advisor_id) VALUES
('Computer Science Club', 'For students interested in programming and technology', 'Every Tuesday 6pm', 6),
('Math Society', 'Mathematics enthusiasts and problem solvers', 'Every Wednesday 5pm', 7),
('Physics Club', 'Exploring the wonders of the physical world', 'Every Thursday 4pm', 8),
('Biology Students Association', 'For biology majors and enthusiasts', 'Every Monday 5pm', 9),
('Business Leaders Forum', 'Developing future business leaders', 'Every Friday 3pm', 10);

-- Insert Club Memberships
INSERT INTO Club_Membership (student_id, club_id, join_date, role) VALUES
(1, 1, '2022-09-15', 'President'),
(2, 2, '2022-09-20', 'Member'),
(3, 1, '2022-09-16', 'Officer'),
(4, 3, '2022-09-18', 'Member'),
(5, 4, '2022-09-22', 'Member');

-- Insert Events
INSERT INTO Event (event_name, event_date, location, description, organizer_type, organizer_club_id, organizer_dept_id) VALUES
('Hackathon 2023', '2023-10-15', 'Engineering Building', 'Annual programming competition', 'Club', 1, NULL),
('Math Olympiad', '2023-11-05', 'Science Building', 'Mathematics competition', 'Club', 2, NULL),
('Career Fair', '2023-09-28', 'Business Building', 'Meet potential employers', 'Department', NULL, 5),
('Science Symposium', '2023-11-15', 'Life Sciences Building', 'Student research presentations', 'Department', NULL, 3),
('Welcome Party', '2023-09-10', 'Cafeteria', 'Welcome new students', 'Department', NULL, 1);
-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;