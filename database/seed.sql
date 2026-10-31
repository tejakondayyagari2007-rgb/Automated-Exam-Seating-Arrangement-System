INSERT INTO departments (name) VALUES ('CSE'), ('ECE'), ('EEE'), ('MECH'), ('CIVIL');
INSERT INTO sections (name) VALUES ('A'), ('B'), ('C');

INSERT INTO users (name, username, email, password_hash, role) VALUES
('System Admin', 'admin', 'admin@college.edu', 'scrypt:32768:8:1$6Ri7SG0MhOJ5Sv7I$d529525348b019b6f626b7a35c227c8b25a3d411e0856346da76f3a47f75684907a70374a103436f5b1f6848646488e9505250a80a03151d81208fd84adcb481', 'ADMIN'),
('Dr. Anita Rao', 'teacher1', 'anita.rao@college.edu', 'scrypt:32768:8:1$xG6XlXixABLoAtGO$7ef498ce3dd7171dc104f8cca8769c78cf74435b7e4d7c226b3d46bdda543f05c623440afed85eca8a02700d849b7df76ce75fa43f65a80d9827149089fb0114', 'TEACHER'),
('Student Demo', 'student1', 'aarav.mehta@college.edu', 'scrypt:32768:8:1$iZnJxb1K9rBv7jwa$ac9c980b463b7096e21dd095c5e5affd3e4905015b03564bef4d5bd95915507e7e435c97557d1a329eedca2770dc34103049d9a7528e9a47383211c50e85b84b', 'STUDENT');

INSERT INTO subjects (name, code, credits) VALUES
('Data Structures', 'CSE201', 4),
('Database Management', 'CSE205', 4),
('Operating Systems', 'CSE303', 3),
('Digital Electronics', 'ECE205', 3),
('Power Systems', 'EEE302', 3);

INSERT INTO teachers (employee_id, name, email, phone, department_id, designation, availability) VALUES
('EMP001', 'Dr. Anita Rao', 'anita.rao@college.edu', '9876500011', 1, 'Professor', 'available'),
('EMP002', 'Dr. Manoj Sharma', 'manoj.sharma@college.edu', '9876500012', 2, 'Associate Professor', 'available'),
('EMP003', 'Dr. Riya Sen', 'riya.sen@college.edu', '9876500013', 3, 'Assistant Professor', 'available'),
('EMP004', 'Mr. Nikhil Verma', 'nikhil.verma@college.edu', '9876500014', 4, 'Lecturer', 'available'),
('EMP005', 'Dr. Swati Jain', 'swati.jain@college.edu', '9876500015', 5, 'Professor', 'available');

INSERT INTO rooms (room_number, building, floor, `rows`, `columns`, capacity, facilities, status) VALUES
('101', 'Main Block', 1, 5, 6, 30, 'Projector, Wi-Fi', 'active'),
('102', 'Main Block', 1, 5, 6, 30, 'Projector, Wi-Fi', 'active'),
('201', 'Academic Block', 2, 5, 6, 30, 'Projector, Whiteboard', 'active'),
('202', 'Academic Block', 2, 5, 6, 30, 'Projector, Whiteboard', 'active'),
('301', 'Innovation Hall', 3, 5, 6, 30, 'AC, Projector', 'active');

INSERT INTO room_seats (room_id, seat_number, row_no, column_no, status) VALUES
(1, 'A01', 1, 1, 'available'), (1, 'A02', 1, 2, 'available'), (1, 'A03', 1, 3, 'blocked'), (1, 'A04', 1, 4, 'available'),
(1, 'A05', 1, 5, 'available'), (1, 'A06', 1, 6, 'reserved'),
(2, 'A01', 1, 1, 'available'), (2, 'A02', 1, 2, 'available'), (2, 'A03', 1, 3, 'available'), (2, 'A04', 1, 4, 'blocked'),
(2, 'A05', 1, 5, 'reserved'), (2, 'A06', 1, 6, 'available');

INSERT INTO students (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status) VALUES
('CS-21-101', 'Aarav Mehta', 'aarav.mehta@college.edu', '9000000001', 1, 1, 2, 'Male', 'No', 'active'),
('CS-21-102', 'Diya Nair', 'diya.nair@college.edu', '9000000002', 1, 1, 2, 'Female', 'No', 'active'),
('CS-21-103', 'Rohan Singh', 'rohan.singh@college.edu', '9000000003', 1, 2, 2, 'Male', 'No', 'active'),
('CS-21-104', 'Ananya Das', 'ananya.das@college.edu', '9000000004', 1, 2, 2, 'Female', 'No', 'active'),
('CS-21-105', 'Rahul Iyer', 'rahul.iyer@college.edu', '9000000005', 1, 3, 2, 'Male', 'No', 'active'),
('EC-21-201', 'Nisha Rao', 'nisha.rao@college.edu', '9000000006', 2, 1, 2, 'Female', 'No', 'active'),
('EC-21-202', 'Karthik Menon', 'karthik.menon@college.edu', '9000000007', 2, 1, 2, 'Male', 'No', 'active'),
('EC-21-203', 'Sana Khan', 'sana.khan@college.edu', '9000000008', 2, 2, 2, 'Female', 'No', 'active'),
('EC-21-204', 'Varun Joshi', 'varun.joshi@college.edu', '9000000009', 2, 2, 2, 'Male', 'No', 'active'),
('EC-21-205', 'Meera Pillai', 'meera.pillai@college.edu', '9000000010', 2, 3, 2, 'Female', 'Yes', 'active'),
('EE-21-301', 'Harsh Patil', 'harsh.patil@college.edu', '9000000011', 3, 1, 2, 'Male', 'No', 'active'),
('EE-21-302', 'Aditi Rao', 'aditi.rao@college.edu', '9000000012', 3, 1, 2, 'Female', 'No', 'active'),
('EE-21-303', 'Vivek Shah', 'vivek.shah@college.edu', '9000000013', 3, 2, 2, 'Male', 'No', 'active'),
('EE-21-304', 'Ishita Sen', 'ishita.sen@college.edu', '9000000014', 3, 2, 2, 'Female', 'No', 'active'),
('EE-21-305', 'Aditya Roy', 'aditya.roy@college.edu', '9000000015', 3, 3, 2, 'Male', 'No', 'active'),
('ME-21-401', 'Ritika Jain', 'ritika.jain@college.edu', '9000000016', 4, 1, 2, 'Female', 'No', 'active'),
('ME-21-402', 'Shivam Gupta', 'shivam.gupta@college.edu', '9000000017', 4, 1, 2, 'Male', 'No', 'active'),
('ME-21-403', 'Pooja Mishra', 'pooja.mishra@college.edu', '9000000018', 4, 2, 2, 'Female', 'No', 'active'),
('ME-21-404', 'Kunal Shah', 'kunal.shah@college.edu', '9000000019', 4, 2, 2, 'Male', 'No', 'active'),
('ME-21-405', 'Yash Verma', 'yash.verma@college.edu', '9000000020', 4, 3, 2, 'Male', 'No', 'active');

INSERT INTO exams (name, exam_code, subject_id, date_value, start_time, end_time, duration_minutes, student_count, status) VALUES
('Data Structures Midterm', 'DS-101', 1, '2026-10-18', '09:00:00', '10:30:00', 90, 20, 'Upcoming'),
('Database Management Quiz', 'DB-202', 2, '2026-10-20', '11:00:00', '12:00:00', 60, 20, 'Upcoming'),
('Operating Systems Final', 'OS-303', 3, '2026-10-22', '14:00:00', '16:00:00', 120, 20, 'Upcoming');

INSERT INTO exam_students (exam_id, student_id) SELECT 1, id FROM students LIMIT 20;
INSERT INTO exam_students (exam_id, student_id) SELECT 2, id FROM students LIMIT 20;
INSERT INTO exam_students (exam_id, student_id) SELECT 3, id FROM students LIMIT 20;

INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time) VALUES
(1, 1, 1, '2026-10-18', '09:00:00', '10:30:00'),
(2, 2, 2, '2026-10-20', '11:00:00', '12:00:00'),
(3, 3, 3, '2026-10-22', '14:00:00', '16:00:00');

INSERT INTO system_settings (key_name, value) VALUES
('dark_mode', 'enabled'),
('attendance_threshold', '75'),
('seating_mode', 'auto');
