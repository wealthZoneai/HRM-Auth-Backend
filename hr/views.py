# hr/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from emp.models import EmployeeProfile, Shift, Attendance, CalendarEvent, SalaryStructure, EmployeeSalary, Payslip, LeaveRequest, LeaveType, LeaveBalance
from . import serializers
from .permissions import IsHR, IsTL
from django.db.models import Sum, Count
from django.utils import timezone
import calendar
from django.contrib.auth import get_user_model
from . import models

User = get_user_model()

# --- Employee listing & detail (HR) ---


class HRListEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeListSerializer
    queryset = EmployeeProfile.objects.all().select_related('user', 'department')


class HRRetrieveEmployeeAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeDetailSerializer
    queryset = EmployeeProfile.objects.all()


class HRUpdateJobBankAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.EmployeeJobBankUpdateSerializer
    queryset = EmployeeProfile.objects.all()
    lookup_field = 'pk'

# --- Attendance admin endpoints ---


class HRAttendanceListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.AttendanceAdminSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        month = self.request.query_params.get('month')
        qs = Attendance.objects.all().select_related('user', 'shift')
        if user_id:
            qs = qs.filter(user__id=user_id)
        if month:
            y, m = map(int, month.split('-'))
            qs = qs.filter(date__year=y, date__month=m)
        return qs.order_by('-date')


class HRAttendanceRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    queryset = Attendance.objects.all()
    serializer_class = serializers.AttendanceAdminSerializer


class HRAttendanceCorrectAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, attendance_id):
        att = get_object_or_404(Attendance, id=attendance_id)
        new_ci = request.data.get('clock_in')
        new_co = request.data.get('clock_out')
        note = request.data.get('note', 'Corrected by HR')
        if new_ci:
            att.clock_in = new_ci
        if new_co:
            att.clock_out = new_co
        att.note = (att.note or '') + f"\nHR correction: {note}"
        att.manual_entry = True
        att.status = 'completed' if att.clock_out else att.status
        att.compute_duration_and_overtime()
        att.save()
        return Response(serializers.AttendanceAdminSerializer(att).data)

# --- Shift management ---


class ShiftListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()


class ShiftRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.ShiftSerializer
    queryset = Shift.objects.all()

# --- Calendar & announcements (HR create) ---


class HRCalendarCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.CalendarEventSerializer
    queryset = CalendarEvent.objects.all()

# --- Salary / Payslip admin ---


class SalaryStructureListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.SalaryStructureSerializer
    queryset = SalaryStructure.objects.all()


class EmployeeSalaryAssignAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, profile_id):
        prof = get_object_or_404(EmployeeProfile, id=profile_id)
        struct_id = request.data.get('structure_id')
        eff_from = request.data.get('effective_from')
        struct = get_object_or_404(SalaryStructure, id=struct_id)
        es, created = EmployeeSalary.objects.update_or_create(
            profile=prof, defaults={'structure': struct, 'effective_from': eff_from})
        return Response(serializers.EmployeeSalaryAdminSerializer(es).data)


class HRGeneratePayslipAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, profile_id):
        # body: year, month, force (bool)
        profile = get_object_or_404(EmployeeProfile, id=profile_id)
        year = int(request.data.get('year', timezone.localdate().year))
        month = int(request.data.get('month', timezone.localdate().month))
        force = bool(request.data.get('force', False))

        # validate salary assigned
        try:
            es = profile.salary
        except EmployeeSalary.DoesNotExist:
            return Response({"detail": "No salary assigned"}, status=400)

        # working days (Mon-Fri)
        cal = calendar.Calendar()
        working_days = sum(1 for d in cal.itermonthdays2(
            year, month) if d[0] != 0 and d[1] < 5)

        attend_qs = Attendance.objects.filter(
            user=profile.user, date__year=year, date__month=month, status='completed')
        days_present = attend_qs.count()
        total_seconds = attend_qs.aggregate(
            total=Sum('duration_seconds'))['total'] or 0
        overtime_seconds = attend_qs.aggregate(
            total=Sum('overtime_seconds'))['total'] or 0

        gross = float(es.structure.monthly_ctc)
        prorata = gross * \
            (days_present / working_days) if working_days else 0.0

        hourly_rate = es.hourly_rate(working_days_in_month=working_days)
        overtime_amt = (overtime_seconds / 3600.0) * \
            hourly_rate * float(es.structure.overtime_multiplier)

        # HR can pass extra deductions
        deductions = float(request.data.get('deductions', 0.0))
        net = prorata + overtime_amt - deductions

        payslip, created = Payslip.objects.update_or_create(
            profile=profile, year=year, month=month,
            defaults={
                'working_days': working_days,
                'days_present': days_present,
                'gross_amount': round(prorata, 2),
                'overtime_amount': round(overtime_amt, 2),
                'deductions': round(deductions, 2),
                'net_amount': round(net, 2),
                'details': {
                    'monthly_ctc': es.structure.monthly_ctc,
                    'prorata': round(prorata, 2),
                    'overtime_amt': round(overtime_amt, 2),
                    'deductions': round(deductions, 2)
                },
                'generated_by': request.user
            }
        )
        return Response(serializers.PayslipAdminSerializer(payslip).data, status=201 if created else 200)

# --- Leave admin actions and listings ---


class HRLeaveListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.LeaveRequestAdminSerializer

    def get_queryset(self):
        q = LeaveRequest.objects.all().select_related('profile', 'leave_type')
        status = self.request.query_params.get('status')
        if status:
            q = q.filter(status=status)
        return q


class HRLeaveDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsHR]
    serializer_class = serializers.LeaveRequestAdminSerializer
    queryset = LeaveRequest.objects.all()


class HRLeaveActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, leave_id):
        action = request.data.get('action')  # 'approve' or 'reject'
        remarks = request.data.get('remarks', '')
        lr = get_object_or_404(LeaveRequest, id=leave_id)
        if action == 'approve':
            lr.apply_hr_approval(request.user, approve=True, remarks=remarks)
            # deduct balance
            try:
                lb = LeaveBalance.objects.get(
                    profile=lr.profile, leave_type=lr.leave_type)
                lb.used = lb.used + lr.days
                lb.save()
            except LeaveBalance.DoesNotExist:
                pass
            # notify employee
            # create notification
            models.Notification.objects.create(to_user=lr.profile.user, title='Leave approved',
                                               body=remarks or 'Your leave approved by HR', notif_type='leave', extra={'leave_id': lr.id})
            return Response({'detail': 'approved'})
        else:
            lr.apply_hr_approval(request.user, approve=False, remarks=remarks)
            models.Notification.objects.create(to_user=lr.profile.user, title='Leave rejected',
                                               body=remarks or 'Your leave rejected by HR', notif_type='leave', extra={'leave_id': lr.id})
            return Response({'detail': 'rejected'})
