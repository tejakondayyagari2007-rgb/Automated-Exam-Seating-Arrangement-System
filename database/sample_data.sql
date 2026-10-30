-- Sample data for Automated Exam Seating Arrangement System.
-- Safe to re-run: records are matched by their existing unique natural keys.
-- This script does not create login users or overwrite existing rows.

START TRANSACTION;

-- Departments and sections
INSERT INTO departments (name)
SELECT 'Computer Science' WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE name = 'Computer Science'
);
INSERT INTO departments (name)
SELECT 'Electronics' WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE name = 'Electronics'
);
INSERT INTO departments (name)
SELECT 'Mathematics' WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE name = 'Mathematics'
);

INSERT INTO sections (name)
SELECT 'A' WHERE NOT EXISTS (SELECT 1 FROM sections WHERE name = 'A');
INSERT INTO sections (name)
SELECT 'B' WHERE NOT EXISTS (SELECT 1 FROM sections WHERE name = 'B');
INSERT INTO sections (name)
SELECT 'C' WHERE NOT EXISTS (SELECT 1 FROM sections WHERE name = 'C');

SELECT id INTO @dept_cs FROM departments WHERE name = 'Computer Science';
SELECT id INTO @dept_ece FROM departments WHERE name = 'Electronics';
SELECT id INTO @dept_math FROM departments WHERE name = 'Mathematics';
SELECT id INTO @section_a FROM sections WHERE name = 'A';
SELECT id INTO @section_b FROM sections WHERE name = 'B';
SELECT id INTO @section_c FROM sections WHERE name = 'C';

-- Students. These are academic records, not login accounts.
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'CS26-001', 'Aarav Mehta', 'aarav.mehta@example.edu', '9000001001', @dept_cs, @section_a, 2, 'Male', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'CS26-001');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'CS26-002', 'Diya Nair', 'diya.nair@example.edu', '9000001002', @dept_cs, @section_a, 2, 'Female', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'CS26-002');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'CS26-003', 'Rohan Singh', 'rohan.singh@example.edu', '9000001003', @dept_cs, @section_b, 2, 'Male', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'CS26-003');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'CS26-004', 'Ananya Das', 'ananya.das@example.edu', '9000001004', @dept_cs, @section_b, 2, 'Female', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'CS26-004');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'EC26-001', 'Nisha Rao', 'nisha.rao@example.edu', '9000001005', @dept_ece, @section_a, 2, 'Female', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'EC26-001');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'EC26-002', 'Karthik Menon', 'karthik.menon@example.edu', '9000001006', @dept_ece, @section_a, 2, 'Male', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'EC26-002');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'MA26-001', 'Meera Iyer', 'meera.iyer@example.edu', '9000001007', @dept_math, @section_c, 1, 'Female', 'Yes', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'MA26-001');
INSERT INTO students
    (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status)
SELECT 'MA26-002', 'Vikram Shah', 'vikram.shah@example.edu', '9000001008', @dept_math, @section_c, 1, 'Male', 'No', 'active'
WHERE NOT EXISTS (SELECT 1 FROM students WHERE roll_no = 'MA26-002');

-- Teachers
INSERT INTO teachers
    (employee_id, name, email, phone, department_id, designation, availability)
SELECT 'EMP26-001', 'Dr. Kavya Rao', 'kavya.rao@example.edu', '9000002001', @dept_cs, 'Associate Professor', 'available'
WHERE NOT EXISTS (SELECT 1 FROM teachers WHERE employee_id = 'EMP26-001');
INSERT INTO teachers
    (employee_id, name, email, phone, department_id, designation, availability)
SELECT 'EMP26-002', 'Prof. Arjun Nair', 'arjun.nair@example.edu', '9000002002', @dept_ece, 'Professor', 'available'
WHERE NOT EXISTS (SELECT 1 FROM teachers WHERE employee_id = 'EMP26-002');
INSERT INTO teachers
    (employee_id, name, email, phone, department_id, designation, availability)
SELECT 'EMP26-003', 'Dr. Sana Iyer', 'sana.iyer@example.edu', '9000002003', @dept_math, 'Assistant Professor', 'available'
WHERE NOT EXISTS (SELECT 1 FROM teachers WHERE employee_id = 'EMP26-003');

-- Subjects
INSERT INTO subjects (name, code, credits)
SELECT 'Database Systems', 'DBS2601', 4
WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE code = 'DBS2601');
INSERT INTO subjects (name, code, credits)
SELECT 'Digital Circuits', 'DGC2602', 3
WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE code = 'DGC2602');
INSERT INTO subjects (name, code, credits)
SELECT 'Applied Mathematics', 'MAT2603', 4
WHERE NOT EXISTS (SELECT 1 FROM subjects WHERE code = 'MAT2603');

-- Rooms: one active 3x4 room holds all eight active sample students.
-- Other rooms are available to test listing and status handling.
INSERT INTO rooms
    (room_number, building, floor, `rows`, `columns`, capacity, facilities, status)
SELECT 'LAB-101', 'Main Academic Block', 1, 3, 4, 12, 'Projector, Accessible seating', 'active'
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE room_number = 'LAB-101');
INSERT INTO rooms
    (room_number, building, floor, `rows`, `columns`, capacity, facilities, status)
SELECT 'HALL-202', 'East Block', 2, 2, 3, 6, 'Whiteboard', 'inactive'
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE room_number = 'HALL-202');
INSERT INTO rooms
    (room_number, building, floor, `rows`, `columns`, capacity, facilities, status)
SELECT 'ROOM-303', 'Science Block', 3, 2, 3, 6, 'Projector', 'inactive'
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE room_number = 'ROOM-303');

SELECT id INTO @room_main FROM rooms WHERE room_number = 'LAB-101';
SELECT id INTO @room_east FROM rooms WHERE room_number = 'HALL-202';
SELECT id INTO @room_science FROM rooms WHERE room_number = 'ROOM-303';

-- Physical seat records. Keep labels consistent with the seating service format.
INSERT INTO room_seats (room_id, seat_number, row_no, column_no, status)
SELECT @room_main, seats.seat_number, seats.row_no, seats.column_no, seats.status
FROM (
    SELECT 'A01' AS seat_number, 1 AS row_no, 1 AS column_no, 'available' AS status
    UNION ALL SELECT 'A02', 1, 2, 'available'
    UNION ALL SELECT 'A03', 1, 3, 'available'
    UNION ALL SELECT 'A04', 1, 4, 'available'
    UNION ALL SELECT 'B01', 2, 1, 'available'
    UNION ALL SELECT 'B02', 2, 2, 'available'
    UNION ALL SELECT 'B03', 2, 3, 'available'
    UNION ALL SELECT 'B04', 2, 4, 'available'
    UNION ALL SELECT 'C01', 3, 1, 'available'
    UNION ALL SELECT 'C02', 3, 2, 'reserved'
    UNION ALL SELECT 'C03', 3, 3, 'available'
    UNION ALL SELECT 'C04', 3, 4, 'blocked'
) AS seats
WHERE NOT EXISTS (
    SELECT 1 FROM room_seats existing
    WHERE existing.room_id = @room_main AND existing.seat_number = seats.seat_number
);

INSERT INTO room_seats (room_id, seat_number, row_no, column_no, status)
SELECT @room_east, seats.seat_number, seats.row_no, seats.column_no, seats.status
FROM (
    SELECT 'A01' AS seat_number, 1 AS row_no, 1 AS column_no, 'available' AS status
    UNION ALL SELECT 'A02', 1, 2, 'available'
    UNION ALL SELECT 'A03', 1, 3, 'blocked'
    UNION ALL SELECT 'B01', 2, 1, 'available'
    UNION ALL SELECT 'B02', 2, 2, 'available'
    UNION ALL SELECT 'B03', 2, 3, 'reserved'
) AS seats
WHERE NOT EXISTS (
    SELECT 1 FROM room_seats existing
    WHERE existing.room_id = @room_east AND existing.seat_number = seats.seat_number
);

INSERT INTO room_seats (room_id, seat_number, row_no, column_no, status)
SELECT @room_science, seats.seat_number, seats.row_no, seats.column_no, seats.status
FROM (
    SELECT 'A01' AS seat_number, 1 AS row_no, 1 AS column_no, 'available' AS status
    UNION ALL SELECT 'A02', 1, 2, 'available'
    UNION ALL SELECT 'A03', 1, 3, 'available'
    UNION ALL SELECT 'B01', 2, 1, 'available'
    UNION ALL SELECT 'B02', 2, 2, 'available'
    UNION ALL SELECT 'B03', 2, 3, 'available'
) AS seats
WHERE NOT EXISTS (
    SELECT 1 FROM room_seats existing
    WHERE existing.room_id = @room_science AND existing.seat_number = seats.seat_number
);

-- Exams, scheduled in the future relative to the project date.
INSERT INTO exams
    (name, exam_code, subject_id, date_value, start_time, end_time, duration_minutes, student_count, status)
SELECT 'Database Systems Midterm', 'EX-DBS-2601',
       (SELECT id FROM subjects WHERE code = 'DBS2601'),
       '2026-11-12', '09:00:00', '10:30:00', 90, 8, 'Upcoming'
WHERE NOT EXISTS (SELECT 1 FROM exams WHERE exam_code = 'EX-DBS-2601');
INSERT INTO exams
    (name, exam_code, subject_id, date_value, start_time, end_time, duration_minutes, student_count, status)
SELECT 'Digital Circuits Quiz', 'EX-DGC-2602',
       (SELECT id FROM subjects WHERE code = 'DGC2602'),
       '2026-11-14', '11:00:00', '12:00:00', 60, 4, 'Upcoming'
WHERE NOT EXISTS (SELECT 1 FROM exams WHERE exam_code = 'EX-DGC-2602');
INSERT INTO exams
    (name, exam_code, subject_id, date_value, start_time, end_time, duration_minutes, student_count, status)
SELECT 'Applied Mathematics Test', 'EX-MAT-2603',
       (SELECT id FROM subjects WHERE code = 'MAT2603'),
       '2026-11-16', '14:00:00', '16:00:00', 120, 4, 'Upcoming'
WHERE NOT EXISTS (SELECT 1 FROM exams WHERE exam_code = 'EX-MAT-2603');

SELECT id INTO @exam_db FROM exams WHERE exam_code = 'EX-DBS-2601';
SELECT id INTO @exam_dgc FROM exams WHERE exam_code = 'EX-DGC-2602';
SELECT id INTO @exam_mat FROM exams WHERE exam_code = 'EX-MAT-2603';
SELECT id INTO @teacher_cs FROM teachers WHERE employee_id = 'EMP26-001';
SELECT id INTO @teacher_ece FROM teachers WHERE employee_id = 'EMP26-002';
SELECT id INTO @teacher_math FROM teachers WHERE employee_id = 'EMP26-003';

-- Exam registrations. Exam 1 includes all eight students; other exams include four.
INSERT INTO exam_students (exam_id, student_id)
SELECT @exam_db, s.id FROM students s
WHERE s.roll_no IN ('CS26-001', 'CS26-002', 'CS26-003', 'CS26-004', 'EC26-001', 'EC26-002', 'MA26-001', 'MA26-002')
AND NOT EXISTS (
    SELECT 1 FROM exam_students es WHERE es.exam_id = @exam_db AND es.student_id = s.id
);
INSERT INTO exam_students (exam_id, student_id)
SELECT @exam_dgc, s.id FROM students s
WHERE s.roll_no IN ('CS26-001', 'CS26-002', 'EC26-001', 'EC26-002')
AND NOT EXISTS (
    SELECT 1 FROM exam_students es WHERE es.exam_id = @exam_dgc AND es.student_id = s.id
);
INSERT INTO exam_students (exam_id, student_id)
SELECT @exam_mat, s.id FROM students s
WHERE s.roll_no IN ('CS26-003', 'CS26-004', 'MA26-001', 'MA26-002')
AND NOT EXISTS (
    SELECT 1 FROM exam_students es WHERE es.exam_id = @exam_mat AND es.student_id = s.id
);

-- Timetable entries and invigilator assignments.
INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time)
SELECT @exam_db, @room_main, @teacher_cs, '2026-11-12', '09:00:00', '10:30:00'
WHERE NOT EXISTS (
    SELECT 1 FROM timetable
    WHERE exam_id = @exam_db AND room_id = @room_main
      AND exam_date = '2026-11-12' AND start_time = '09:00:00'
);
INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time)
SELECT @exam_dgc, @room_main, @teacher_ece, '2026-11-14', '11:00:00', '12:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM timetable
    WHERE exam_id = @exam_dgc AND room_id = @room_main
      AND exam_date = '2026-11-14' AND start_time = '11:00:00'
);
INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time)
SELECT @exam_mat, @room_main, @teacher_math, '2026-11-16', '14:00:00', '16:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM timetable
    WHERE exam_id = @exam_mat AND room_id = @room_main
      AND exam_date = '2026-11-16' AND start_time = '14:00:00'
);

INSERT INTO invigilators (exam_id, teacher_id)
SELECT @exam_db, @teacher_cs
WHERE NOT EXISTS (SELECT 1 FROM invigilators WHERE exam_id = @exam_db AND teacher_id = @teacher_cs);
INSERT INTO invigilators (exam_id, teacher_id)
SELECT @exam_dgc, @teacher_ece
WHERE NOT EXISTS (SELECT 1 FROM invigilators WHERE exam_id = @exam_dgc AND teacher_id = @teacher_ece);
INSERT INTO invigilators (exam_id, teacher_id)
SELECT @exam_mat, @teacher_math
WHERE NOT EXISTS (SELECT 1 FROM invigilators WHERE exam_id = @exam_mat AND teacher_id = @teacher_math);

-- A published sample arrangement for reports. All seats are in one room, and
-- seat numbers are unique within the arrangement as required by the schema.
INSERT INTO seating_arrangements (exam_id, status, quality_score, published_at)
SELECT @exam_db, 'PUBLISHED', 96.00, '2026-11-01 09:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM seating_arrangements
    WHERE exam_id = @exam_db AND status = 'PUBLISHED'
      AND quality_score = 96.00 AND published_at = '2026-11-01 09:00:00'
);
SELECT id INTO @sample_arrangement
FROM seating_arrangements
WHERE exam_id = @exam_db AND status = 'PUBLISHED'
  AND quality_score = 96.00 AND published_at = '2026-11-01 09:00:00'
ORDER BY id
LIMIT 1;

INSERT INTO seat_assignments
    (arrangement_id, student_id, room_id, row_no, column_no, seat_number, status)
SELECT @sample_arrangement, s.id, @room_main, seats.row_no, seats.column_no, seats.seat_number, 'assigned'
FROM (
    SELECT 'CS26-001' AS roll_no, 1 AS row_no, 1 AS column_no, 'A01' AS seat_number
    UNION ALL SELECT 'CS26-002', 1, 2, 'A02'
    UNION ALL SELECT 'CS26-003', 1, 3, 'A03'
    UNION ALL SELECT 'CS26-004', 1, 4, 'A04'
    UNION ALL SELECT 'EC26-001', 2, 1, 'B01'
    UNION ALL SELECT 'EC26-002', 2, 2, 'B02'
    UNION ALL SELECT 'MA26-001', 2, 3, 'B03'
    UNION ALL SELECT 'MA26-002', 2, 4, 'B04'
) AS seats
JOIN students s ON s.roll_no = seats.roll_no
WHERE NOT EXISTS (
    SELECT 1 FROM seat_assignments existing
    WHERE existing.arrangement_id = @sample_arrangement
      AND (existing.student_id = s.id OR existing.seat_number = seats.seat_number)
);

-- Attendance sample for the first exam (both present and absent examples).
INSERT INTO attendance (student_id, exam_id, present_status, remarks)
SELECT s.id, @exam_db, attendance_data.present_status, attendance_data.remarks
FROM (
    SELECT 'CS26-001' AS roll_no, 1 AS present_status, 'Present' AS remarks
    UNION ALL SELECT 'CS26-002', 1, 'Present'
    UNION ALL SELECT 'CS26-003', 1, 'Present'
    UNION ALL SELECT 'CS26-004', 0, 'Absent'
    UNION ALL SELECT 'EC26-001', 1, 'Present'
    UNION ALL SELECT 'EC26-002', 0, 'Absent'
    UNION ALL SELECT 'MA26-001', 1, 'Present'
    UNION ALL SELECT 'MA26-002', 1, 'Present'
) AS attendance_data
JOIN students s ON s.roll_no = attendance_data.roll_no
WHERE NOT EXISTS (
    SELECT 1 FROM attendance existing
    WHERE existing.student_id = s.id AND existing.exam_id = @exam_db
);

-- Notifications are global (user_id NULL) because no login accounts are seeded.
INSERT INTO notifications (user_id, title, message, status)
SELECT NULL, 'Exam timetable published', 'The November sample exam timetable is available.', 'unread'
WHERE NOT EXISTS (
    SELECT 1 FROM notifications
    WHERE user_id IS NULL AND title = 'Exam timetable published'
      AND message = 'The November sample exam timetable is available.'
);
INSERT INTO notifications (user_id, title, message, status)
SELECT NULL, 'Seating arrangement ready', 'A sample seating arrangement is available for Database Systems Midterm.', 'unread'
WHERE NOT EXISTS (
    SELECT 1 FROM notifications
    WHERE user_id IS NULL AND title = 'Seating arrangement ready'
      AND message = 'A sample seating arrangement is available for Database Systems Midterm.'
);

-- Audit rows have no linked user because this seed does not create credentials.
INSERT INTO audit_logs (user_id, action, description)
SELECT NULL, 'Sample data loaded', 'Sample academic and exam records were added.'
WHERE NOT EXISTS (
    SELECT 1 FROM audit_logs
    WHERE user_id IS NULL AND action = 'Sample data loaded'
      AND description = 'Sample academic and exam records were added.'
);

-- Use sample-specific setting keys so existing application settings are untouched.
INSERT INTO system_settings (key_name, value)
SELECT 'sample_seating_mode', 'auto'
WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key_name = 'sample_seating_mode');
INSERT INTO system_settings (key_name, value)
SELECT 'sample_attendance_threshold', '75'
WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key_name = 'sample_attendance_threshold');

COMMIT;

-- Verification queries (select and run separately after the seed completes):
-- SELECT 'departments' AS table_name, COUNT(*) AS sample_rows FROM departments WHERE name IN ('Computer Science', 'Electronics', 'Mathematics')
-- UNION ALL SELECT 'sections', COUNT(*) FROM sections WHERE name IN ('A', 'B', 'C')
-- UNION ALL SELECT 'students', COUNT(*) FROM students WHERE roll_no LIKE 'CS26-%' OR roll_no LIKE 'EC26-%' OR roll_no LIKE 'MA26-%'
-- UNION ALL SELECT 'teachers', COUNT(*) FROM teachers WHERE employee_id LIKE 'EMP26-%'
-- UNION ALL SELECT 'subjects', COUNT(*) FROM subjects WHERE code IN ('DBS2601', 'DGC2602', 'MAT2603')
-- UNION ALL SELECT 'rooms', COUNT(*) FROM rooms WHERE room_number IN ('LAB-101', 'HALL-202', 'ROOM-303')
-- UNION ALL SELECT 'exams', COUNT(*) FROM exams WHERE exam_code IN ('EX-DBS-2601', 'EX-DGC-2602', 'EX-MAT-2603');
