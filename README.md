HRMS Portal - Complete API Reference (HR & Employee)

HR APIs
1) HR Login (JWT) - POST /api/login/
Body:
{
"username": "hr_user",
"password": "Password123!"
}

3) Create Employee (Auto username, mail, emp_id) - POST /api/create-employee/
Body:
{
"first_name": "John",
"last_name": "Doe",
"role": "employee",
"department": "IT",
"job_title": "Developer",
"employment_type": "full-time",
"start_date": "2025-11-01",
"location": "Hyderabad"
}

4) Employee List - GET /api/employee-list/
Headers: Authorization: Bearer 

5) Employee Full Details - GET /api/employees/id/
Headers: Authorization: Bearer 

6) HR Update Employee - PATCH /api/employees/id/
Body example:
{
"department": "Tech",
"job_title": "Senior Developer"
}

7) HR View Employee Attendance Monthly - GET /api/attendance/hr/employee/id/?month=2025-11

8) HR All Employees Attendance Summary - GET /api/attendance/hr/monthly-report/?month=2025-11

Employee APIs

1) Employee Login (JWT) - POST /api/login/
Body:
{
"username": "john.doe",
"password": "Employee@123"
}

2) Forgot Password (Send OTP) - POST /api/forgot-password/
Body:
{
"email": "john.doe@wealthzonegroupai.com"
}

3) Verify OTP - POST /api/verify-otp/
Body:
{
"email": "john.doe@wealthzonegroupai.com",
"otp": "1234"
}

4) Reset Password - POST /api/reset-password/
Body:
{
"email": "john.doe@wealthzonegroupai.com",
"new_password": "Employee@123",
"confirm_password": "Employee@123"
}

5) My Profile (View) - GET /api/my-profile/
Headers: Authorization: Bearer

7) Update My Profile - PATCH /api/my-profile/
Body (multipart/form-data):
personal_email: "john.personal@gmail.com"
phone_number: "9999999999"
profile_photo: 

8) Clock-in - POST /api/attendance/clock-in/
Headers: Authorization: Bearer 

9) Clock-out - POST /api/attendance/clock-out/
Headers: Authorization: Bearer 

10) Today's Attendance Status - GET /api/attendance/my-today/
Headers: Authorization: Bearer 

11) Monthly Attendance Summary - GET /api/attendance/my-monthly/?month=2025-11
Headers: Authorization: Bearer 

Notes for Frontend Team

Authentication
All authenticated API calls must include: Authorization: Bearer 

Auto-generated values
Employee username, work email, and employee ID are auto-generated.

Initial login
Employee cannot login until they reset password via OTP workflow (Forgot Password).

Permissions
HR can view and modify all employee records. Employees can only modify personal info fields.

Attendance rules
Only one clock-in per day; clock-out required before next clock-in.
