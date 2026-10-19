-- The five fictional students, five courses, and ten enrollments are course fixtures.
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
    major TEXT, gpa REAL, enrollment_date TEXT
);
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT, course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL, credits INTEGER, instructor TEXT
);
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id), grade TEXT, semester TEXT
);
INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES ('Alice Johnson','alice@sdsu.edu','Computer Science',3.8,'2024-08-20');
INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES ('Bob Smith','bob@sdsu.edu','Mathematics',3.5,'2024-08-20');
INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES ('Carol Davis','carol@sdsu.edu','Computer Science',3.9,'2024-08-20');
INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES ('David Wilson','david@sdsu.edu','Engineering',3.7,'2024-08-20');
INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES ('Eve Martinez','eve@sdsu.edu','Mathematics',3.6,'2024-08-20');
INSERT INTO courses(course_code,course_name,credits,instructor) VALUES ('COMPE475','Microprocessors',3,'Prof. Núñez');
INSERT INTO courses(course_code,course_name,credits,instructor) VALUES ('CS101','Introduction to Programming',4,'Prof. Smith');
INSERT INTO courses(course_code,course_name,credits,instructor) VALUES ('MATH150','Calculus I',4,'Prof. Johnson');
INSERT INTO courses(course_code,course_name,credits,instructor) VALUES ('CS201','Data Structures',3,'Prof. Davis');
INSERT INTO courses(course_code,course_name,credits,instructor) VALUES ('MATH210','Linear Algebra',3,'Prof. Wilson');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='alice@sdsu.edu'),(SELECT id FROM courses WHERE course_code='COMPE475'),'A','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='alice@sdsu.edu'),(SELECT id FROM courses WHERE course_code='CS101'),'A-','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='bob@sdsu.edu'),(SELECT id FROM courses WHERE course_code='COMPE475'),'B+','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='bob@sdsu.edu'),(SELECT id FROM courses WHERE course_code='MATH150'),'A','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='carol@sdsu.edu'),(SELECT id FROM courses WHERE course_code='COMPE475'),'A','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='carol@sdsu.edu'),(SELECT id FROM courses WHERE course_code='CS201'),'A','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='david@sdsu.edu'),(SELECT id FROM courses WHERE course_code='CS101'),'B','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='david@sdsu.edu'),(SELECT id FROM courses WHERE course_code='MATH210'),'B+','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='eve@sdsu.edu'),(SELECT id FROM courses WHERE course_code='MATH150'),'A-','Spring 2026');
INSERT INTO enrollments(student_id,course_id,grade,semester) VALUES ((SELECT id FROM students WHERE email='eve@sdsu.edu'),(SELECT id FROM courses WHERE course_code='MATH210'),'A','Spring 2026');
