# emp/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import calendar
from .validators import validate_file_size, validate_image_extension

User = settings.AUTH_USER_MODEL

# -----------------------
# Core / Profile
# -----------------------


class Department(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name


class EmployeeProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='employeeprofile')

    # System fields
    emp_id = models.CharField(max_length=20, unique=True)
    work_email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, null=True, blank=True)

    # Contact Info (employee editable)
    personal_email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True,
                                      blank=True, validators=[validate_file_size, validate_image_extension])

    # Identity
    aadhaar = models.CharField(max_length=20, null=True, blank=True)
    pan = models.CharField(max_length=20, null=True, blank=True)
    id_card_number = models.CharField(max_length=50, null=True, blank=True)
    aadhaar_image = models.ImageField(upload_to='ids/aadhaar/', null=True,
                                      blank=True, validators=[validate_file_size, validate_image_extension])
    pan_image = models.ImageField(upload_to='ids/pan/', null=True, blank=True,
                                  validators=[validate_file_size, validate_image_extension])
    id_card_image = models.ImageField(upload_to='ids/idcard/', null=True,
                                      blank=True, validators=[validate_file_size, validate_image_extension])

    # Job Info (HR editable)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)

    job_title = models.CharField(max_length=150, null=True, blank=True)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                blank=True, on_delete=models.SET_NULL, related_name='team_members')
    employment_type = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=150, null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)

    # Bank Details (HR editable)
    bank_name = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=64, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    branch = models.CharField(max_length=150, null=True, blank=True)

    # Role / flags
    # 'hr','management','tl','employee','intern'
    role = models.CharField(max_length=30, default='employee')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name()} ({self.emp_id})"

    class Meta:
        ordering = ['-created_at']


# -----------------------
# Notifications
# -----------------------
class Notification(models.Model):
    NOTIF_TYPES = [
        ('announcement', 'Announcement'),
        ('meeting', 'Meeting'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('leave', 'Leave'),
        ('payroll', 'Payroll'),
    ]
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=250)
    body = models.TextField()
    notif_type = models.CharField(
        max_length=50, choices=NOTIF_TYPES, default='announcement')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


# -----------------------
# Shift & Attendance
# -----------------------
class Shift(models.Model):
    name = models.CharField(max_length=120)
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_hours = models.DecimalField(
        max_digits=4, decimal_places=2, default=8.00)
    grace_minutes = models.PositiveIntegerField(default=5)
    late_threshold = models.PositiveIntegerField(default=15)  # minutes

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('manual', 'Manual'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    shift = models.ForeignKey(
        Shift, null=True, blank=True, on_delete=models.SET_NULL)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress')
    is_remote = models.BooleanField(default=False)
    late_by_seconds = models.PositiveIntegerField(null=True, blank=True)
    overtime_seconds = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    manual_entry = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def compute_duration_and_overtime(self, standard_seconds=9*3600):
        """
        Calculate duration_seconds and overtime_seconds automatically.
        Default standard_seconds = 9 hours.
        """
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            self.duration_seconds = int(delta.total_seconds())
            if self.duration_seconds > standard_seconds:
                self.overtime_seconds = self.duration_seconds - standard_seconds
            else:
                self.overtime_seconds = 0
            # compute late_by_seconds if shift is set
            if self.shift and self.shift.start_time:
                # convert shift start_time to timezone-aware datetime for this date
                dt_shift_start = timezone.make_aware(timezone.datetime.combine(
                    self.date, self.shift.start_time), timezone.get_current_timezone())
                clk_in_local = timezone.localtime(self.clock_in)
                if clk_in_local > dt_shift_start:
                    self.late_by_seconds = int(
                        (clk_in_local - dt_shift_start).total_seconds())
                else:
                    self.late_by_seconds = 0
            self.save(update_fields=['duration_seconds',
                      'overtime_seconds', 'late_by_seconds'])
            return self.duration_seconds
        return None


# -----------------------
# Calendar Events
# -----------------------
class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('announcement', 'Announcement'),
        ('holiday', 'Holiday'),
    ]
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    event_type = models.CharField(
        max_length=50, choices=EVENT_TYPES, default='announcement')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    visible_to_tl_hr = models.BooleanField(default=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-date']


# -----------------------
# Payroll (Option B - Advanced Payslip)
# -----------------------
class SalaryStructure(models.Model):
    name = models.CharField(max_length=150)
    monthly_ctc = models.DecimalField(max_digits=12, decimal_places=2)
    basic_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.0)
    hra_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.0)
    other_allowances = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.0)
    overtime_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.25)

    def basic_amount(self):
        return (self.monthly_ctc * (self.basic_percent / 100))

    def __str__(self):
        return f"{self.name} ({self.monthly_ctc})"


class EmployeeSalary(models.Model):
    profile = models.OneToOneField(
        EmployeeProfile, on_delete=models.CASCADE, related_name='salary')
    structure = models.ForeignKey(SalaryStructure, on_delete=models.PROTECT)
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    def hourly_rate(self, working_days_in_month=22, hours_per_day=8):
        basic = float(self.structure.monthly_ctc) * \
            (float(self.structure.basic_percent) / 100.0)
        denom = working_days_in_month * hours_per_day
        if denom == 0:
            return 0.0
        return basic / denom


class Payslip(models.Model):
    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='payslips')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    overtime_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.JSONField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    finalized = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'year', 'month')
        ordering = ['-year', '-month']


# -----------------------
# Leave (employee essentials)
# -----------------------
class LeaveType(models.Model):
    name = models.CharField(max_length=120)  # Casual, Sick, Paid, Unpaid, etc.
    code = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    total_allocated = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.0)
    used = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    def available(self):
        return float(self.total_allocated) - float(self.used)

    def __str__(self):
        return f"{self.profile.emp_id} - {self.leave_type.name} : {self.available()}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('tl_approved', 'TL Approved'),
        ('tl_rejected', 'TL Rejected'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='applied')
    tl = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                           on_delete=models.SET_NULL, related_name='tl_for_leave')
    hr = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                           on_delete=models.SET_NULL, related_name='hr_for_leave')
    tl_remarks = models.TextField(null=True, blank=True)
    hr_remarks = models.TextField(null=True, blank=True)
    last_action_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                       blank=True, on_delete=models.SET_NULL, related_name='leave_actions')
    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def apply_tl_approval(self, approver_user, approve: bool, remarks: str = None):
        self.tl = approver_user
        self.tl_remarks = remarks or ''
        self.last_action_by = approver_user
        self.last_action_at = timezone.now()
        if approve:
            self.status = 'tl_approved'
        else:
            self.status = 'tl_rejected'
        self.save()

    def apply_hr_approval(self, approver_user, approve: bool, remarks: str = None):
        self.hr = approver_user
        self.hr_remarks = remarks or ''
        self.last_action_by = approver_user
        self.last_action_at = timezone.now()
        if approve:
            self.status = 'hr_approved'
        else:
            self.status = 'hr_rejected'
        self.save()


# -----------------------
# Policies (static documents)
# -----------------------
class Policy(models.Model):
    POLICY_TYPES = [
        ('policy', 'Policy'),
        ('terms', 'Terms'),
        ('resignation', 'Resignation'),
        ('termination', 'Termination'),
    ]
    title = models.CharField(max_length=250)
    policy_type = models.CharField(
        max_length=50, choices=POLICY_TYPES, default='policy')
    content = models.TextField()
    file = models.FileField(upload_to='policies/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
