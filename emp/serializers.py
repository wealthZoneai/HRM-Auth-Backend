# emp/serializers.py
from rest_framework import serializers
from .models import (
    EmployeeProfile, Notification, Shift, Attendance, CalendarEvent,
    SalaryStructure, EmployeeSalary, Payslip,
    LeaveType, LeaveBalance, LeaveRequest, Policy
)
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()


# Profile

class EmployeeCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=80)
    last_name = serializers.CharField(required=True, max_length=80)
    role = serializers.ChoiceField(choices=[('employee', 'Employee'), ('intern', 'Intern'), (
        'tl', 'Team Leader'), ('hr', 'HR'), ('management', 'Management')], default='employee')
    emp_id = serializers.CharField(
        required=False, allow_blank=True, max_length=50)
    work_email = serializers.EmailField(required=False, allow_blank=True)

    def validate_work_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists.")
        return value

    def create(self, validated_data):
        first_name = validated_data.get('first_name', '').strip()
        last_name = validated_data.get('last_name', '').strip()
        role = validated_data.get('role', 'employee')
        email = (validated_data.get('work_email') or '').strip() or None
        base_username = f"{first_name.lower()}.{last_name.lower()}" if first_name or last_name else "user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        # create user safely
        user = User.objects.create_user(
            username=username, password=None, first_name=first_name, last_name=last_name, email=email, role=role)
        user.set_unusable_password()
        user.save()
        # EmployeeProfile created by signals - ensure it exists
        prof, created = EmployeeProfile.objects.get_or_create(user=user, defaults={
            'emp_id': validated_data.get('emp_id') or '',
            'work_email': email or '',
            'first_name': first_name or '',
            'last_name': last_name or '',
            'role': role
        })
        if validated_data.get('emp_id'):
            prof.emp_id = validated_data.get('emp_id')
            prof.save(update_fields=['emp_id'])
        return user, prof

    def save(self, **kwargs):
        return self.create(self.validated_data)


class EmployeeProfileReadSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        exclude = ('id', 'created_at', 'updated_at', 'username')

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "email": obj.user.email,
            "role": obj.user.role,
        }


class EmployeeContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('personal_email', 'phone_number', 'profile_photo')


class EmployeeIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('aadhaar', 'pan', 'id_card_number',
                  'aadhaar_image', 'pan_image', 'id_card_image')


# Notifications


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'body', 'notif_type',
                  'is_read', 'created_at', 'extra')


# Attendance / Shift


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class AttendanceReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('id', 'date', 'shift', 'clock_in', 'clock_out', 'duration_seconds', 'status',
                  'is_remote', 'late_by_seconds', 'overtime_seconds', 'note', 'manual_entry')


# Calendar


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'

# Payroll


class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'


class EmployeeSalarySerializer(serializers.ModelSerializer):
    structure = SalaryStructureSerializer(read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = '__all__'


class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = '__all__'

# Leave


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ('id', 'leave_type', 'total_allocated', 'used', 'available')

    def get_available(self, obj):
        return float(obj.total_allocated) - float(obj.used)


class LeaveRequestSerializer(serializers.ModelSerializer):
    profile = EmployeeProfileReadSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ('id', 'profile', 'leave_type', 'start_date', 'end_date', 'days',
                  'reason', 'applied_at', 'status', 'tl', 'hr', 'tl_remarks', 'hr_remarks')


class LeaveApplySerializer(serializers.Serializer):
    leave_type_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = serializers.DecimalField(max_digits=5, decimal_places=2)
    reason = serializers.CharField(allow_blank=True, required=False)

    def validate(self, data):
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError(
                "End date cannot be before start date.")
        return data

# Policies


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'
