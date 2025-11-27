# hr/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from django.contrib.auth import get_user_model

User = get_user_model()

# User-light serializer (for HR lists)
class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name','email','role')

# Employee list / detail
class EmployeeListSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = EmployeeProfile
        fields = ('id','emp_id','user','first_name','last_name','work_email','job_title','department','role','start_date','location','profile_photo')

class EmployeeDetailSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    class Meta:
        model = EmployeeProfile
        fields = '__all__'
        read_only_fields = ('emp_id','work_email','username','created_at','user')

class EmployeeJobBankUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ('job_title','department','manager','employment_type','start_date','location','job_description',
                  'bank_name','account_number','ifsc_code','branch')

# Shift & Attendance serializers (HR)
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AttendanceAdminSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(source='user', read_only=True)
    class Meta:
        model = Attendance
        fields = ('id','user','date','shift','clock_in','clock_out','duration_seconds','status','is_remote','late_by_seconds','overtime_seconds','note','manual_entry')

# Calendar event (HR create)
class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = '__all__'

# Salary and payslip admin serializers
class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'

class EmployeeSalaryAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)
    class Meta:
        model = EmployeeSalary
        fields = '__all__'

class PayslipAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)
    class Meta:
        model = Payslip
        fields = '__all__'

# Leave admin serializers
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class LeaveBalanceSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)
    class Meta:
        model = LeaveBalance
        fields = '__all__'

class LeaveRequestAdminSerializer(serializers.ModelSerializer):
    profile = EmployeeListSerializer(read_only=True)
    class Meta:
        model = LeaveRequest
        fields = '__all__'
