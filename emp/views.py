# emp/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count
import calendar
from .serializers import EmployeeCreateSerializer, EmployeeProfileReadSerializer
from . import models, serializers
from .permissions import IsHROrManagement, IsTLorHRorOwner
from django.contrib.auth import get_user_model

User = get_user_model()

# --- Profile ---


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        return Response(serializers.EmployeeProfileReadSerializer(prof).data)


class UpdateContactView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeContactUpdateSerializer(
            prof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UpdateIdentificationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        prof = request.user.employeeprofile
        serializer = serializers.EmployeeIdentificationSerializer(
            prof, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# --- Notifications ---


class MyNotificationsList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationSerializer

    def get_queryset(self):
        q = models.Notification.objects.filter(to_user=self.request.user)
        if self.request.query_params.get('unread') in ('true', '1', 'True'):
            q = q.filter(is_read=False)
        return q


class MarkNotificationsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        models.Notification.objects.filter(
            id__in=ids, to_user=request.user).update(is_read=True)
        return Response({"marked": len(ids)})

# --- Dashboard ---


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        att = models.Attendance.objects.filter(user=user, date=today).first()
        att_ser = serializers.AttendanceReadSerializer(
            att).data if att else None

        month_q = request.query_params.get('month')
        if month_q:
            y, m = map(int, month_q.split('-'))
        else:
            d = timezone.localdate()
            y, m = d.year, d.month

        qs = models.Attendance.objects.filter(
            user=user, date__year=y, date__month=m, status='completed')
        days_present = qs.count()
        total_seconds = qs.aggregate(total=Sum('duration_seconds'))[
            'total'] or 0
        monthly_summary = {'year': y, 'month': m, 'days_present': days_present, 'hours': round(
            total_seconds/3600, 2)}

        project_status = []  # placeholder for React; they will fetch separate API if exists

        announcements = models.Notification.objects.filter(
            to_user=user).order_by('-created_at')[:5]
        ann_ser = serializers.NotificationSerializer(
            announcements, many=True).data

        leave_counts = models.LeaveRequest.objects.filter(
            profile=user.employeeprofile).values('status').annotate(c=Count('id'))
        leave_summary = {row['status']: row['c'] for row in leave_counts}

        upcoming = models.CalendarEvent.objects.filter(
            event_type='holiday', date__gte=today).order_by('date')[:10]
        up_ser = serializers.CalendarEventSerializer(upcoming, many=True).data

        return Response({
            'attendance_today': att_ser,
            'monthly_summary': monthly_summary,
            'project_status': project_status,
            'announcements': ann_ser,
            'leave_summary': leave_summary,
            'upcoming_holidays': up_ser,
        })

# --- Attendance ---


class ClockInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()
        if models.Attendance.objects.filter(user=user, date=today).exists():
            return Response({"detail": "Attendance for today already exists."}, status=400)
        shift_id = request.data.get('shift')
        shift = None
        if shift_id:
            shift = get_object_or_404(models.Shift, id=shift_id)
        att = models.Attendance.objects.create(user=user, date=today, shift=shift, clock_in=timezone.now(
        ), status='in_progress', note=request.data.get('note', ''))
        return Response(serializers.AttendanceReadSerializer(att).data, status=201)


class ClockOutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.localdate()
        att = models.Attendance.objects.filter(user=user, date=today).first()
        if not att:
            return Response({"detail": "No clock-in found for today."}, status=400)
        if att.clock_out:
            return Response({"detail": "Already clocked out."}, status=400)
        att.clock_out = timezone.now()
        att.status = 'completed'
        att.compute_duration_and_overtime()
        att.save()
        return Response(serializers.AttendanceReadSerializer(att).data)


class MyAttendanceDaysAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.AttendanceReadSerializer

    def get_queryset(self):
        user = self.request.user
        month = self.request.query_params.get('month')
        if month:
            y, m = map(int, month.split('-'))
            return models.Attendance.objects.filter(user=user, date__year=y, date__month=m).order_by('-date')
        else:
            return models.Attendance.objects.filter(user=user).order_by('-date')[:30]

# --- Calendar ---


class CalendarEventsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CalendarEventSerializer

    def get_queryset(self):
        year = int(self.request.query_params.get(
            'year', timezone.localdate().year))
        month = int(self.request.query_params.get(
            'month', timezone.localdate().month))
        q = models.CalendarEvent.objects.filter(
            date__year=year, date__month=month)
        return q

# --- Payroll ---


class MySalaryDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        try:
            es = prof.salary
            ser = serializers.EmployeeSalarySerializer(es).data
        except models.EmployeeSalary.DoesNotExist:
            ser = None
        return Response({'salary': ser})


class MyPayslipsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PayslipSerializer

    def get_queryset(self):
        prof = self.request.user.employeeprofile
        return models.Payslip.objects.filter(profile=prof).order_by('-year', '-month')


class PayslipDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year, month):
        prof = request.user.employeeprofile
        payslip = get_object_or_404(
            models.Payslip, profile=prof, year=year, month=month)
        # TODO: implement PDF generation (ReportLab or WeasyPrint)
        return Response({'download_url': f'/media/payslips/{prof.emp_id}-{year}-{month}.pdf', 'payslip': serializers.PayslipSerializer(payslip).data})

# --- Leave ---


class MyLeaveBalancesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prof = request.user.employeeprofile
        balances = models.LeaveBalance.objects.filter(profile=prof)
        return Response(serializers.LeaveBalanceSerializer(balances, many=True).data)


class MyLeaveRequestsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LeaveRequestSerializer

    def get_queryset(self):
        return models.LeaveRequest.objects.filter(profile=self.request.user.employeeprofile)


class LeaveApplyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = serializers.LeaveApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prof = request.user.employeeprofile
        lt = get_object_or_404(
            models.LeaveType, id=ser.validated_data['leave_type_id'])
        tl_user = prof.manager
        lr = models.LeaveRequest.objects.create(
            profile=prof,
            leave_type=lt,
            start_date=ser.validated_data['start_date'],
            end_date=ser.validated_data['end_date'],
            days=ser.validated_data['days'],
            reason=ser.validated_data.get('reason', ''),
            tl=tl_user
        )
        if tl_user:
            models.Notification.objects.create(
                to_user=tl_user, title=f"Leave request from {prof.full_name()}", body=f"{prof.full_name()} applied for {lt.name} from {lr.start_date} to {lr.end_date}.", notif_type='leave', extra={'leave_request_id': lr.id})
        return Response(serializers.LeaveRequestSerializer(lr).data, status=201)

# --- HR support endpoints ---


class HRCreateEmployeeAPIView(APIView):
    permission_classes = [IsAuthenticated, IsHROrManagement]

    def post(self, request):
        serializer = EmployeeCreateSerializer(
            data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user, profile = serializer.save()
        return Response(EmployeeProfileReadSerializer(profile).data, status=status.HTTP_201_CREATED)


class HRTLActionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTLorHRorOwner]

    def post(self, request, leave_id):
        action = request.data.get('action')  # 'approve' or 'reject'
        remarks = request.data.get('remarks', '')
        lr = get_object_or_404(models.LeaveRequest, id=leave_id)
        user = request.user
        # If user is TL (manager), apply tl action
        if getattr(user, 'role', None) == 'tl':
            if lr.profile.user.employeeprofile.manager != user:
                return Response({'detail': 'Forbidden'}, status=403)
            if action == 'approve':
                lr.apply_tl_approval(user, approve=True, remarks=remarks)
                # notify HR (simple approach: create notifications for all HR users)
                for hr_user in User.objects.filter(role__in=['hr', 'management']):
                    models.Notification.objects.create(
                        to_user=hr_user, title=f"TL approved leave: {lr.profile.full_name()}", body=f"Leave {lr.id} needs HR action.", notif_type='leave', extra={'leave_request_id': lr.id})
                return Response({'detail': 'tl_approved'})
            else:
                lr.apply_tl_approval(user, approve=False, remarks=remarks)
                models.Notification.objects.create(to_user=lr.profile.user, title='Leave rejected by TL',
                                                   body=remarks or 'Your leave was rejected by TL', notif_type='leave', extra={'leave_request_id': lr.id})
                return Response({'detail': 'tl_rejected'})
        # If user is HR
        if getattr(user, 'role', None) in ('hr', 'management'):
            if action == 'approve':
                lr.apply_hr_approval(user, approve=True, remarks=remarks)
                # deduct balance if exists
                try:
                    lb = models.LeaveBalance.objects.get(
                        profile=lr.profile, leave_type=lr.leave_type)
                    lb.used = lb.used + lr.days
                    lb.save()
                except models.LeaveBalance.DoesNotExist:
                    pass
                models.Notification.objects.create(to_user=lr.profile.user, title='Leave approved',
                                                   body=remarks or 'Your leave has been approved', notif_type='leave', extra={'leave_request_id': lr.id})
                return Response({'detail': 'hr_approved'})
            else:
                lr.apply_hr_approval(user, approve=False, remarks=remarks)
                models.Notification.objects.create(to_user=lr.profile.user, title='Leave rejected by HR',
                                                   body=remarks or 'Your leave was rejected by HR', notif_type='leave', extra={'leave_request_id': lr.id})
                return Response({'detail': 'hr_rejected'})
        return Response({'detail': 'Not allowed'}, status=403)
