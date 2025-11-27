# tl/serializers.py
from rest_framework import serializers
from emp.models import EmployeeProfile, LeaveRequest, Attendance
from emp.serializers import LeaveRequestSerializer, AttendanceReadSerializer


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = ("id", "emp_id", "first_name", "last_name",
                  "work_email", "job_title", "profile_photo")
