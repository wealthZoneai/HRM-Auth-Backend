# tl/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from django.utils import timezone

from emp.models import EmployeeProfile, LeaveRequest, Attendance, CalendarEvent
from emp.serializers import LeaveRequestSerializer, AttendanceReadSerializer, CalendarEventSerializer
from .serializers import TeamMemberSerializer
from .permissions import IsTL

# ------------------------------
# TL: Team Members List
# ------------------------------


class TLTeamMembersAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = TeamMemberSerializer

    def get_queryset(self):
        # TL can see ONLY team members whose manager = TL
        return EmployeeProfile.objects.filter(manager=self.request.user)


# ------------------------------
# TL: Pending Leave Requests
# ------------------------------
class TLPendingLeaveAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        return LeaveRequest.objects.filter(
            tl=self.request.user,
            status="applied"
        ).select_related("profile", "leave_type")


# ------------------------------
# TL: Approve/Reject Leave
# ------------------------------
class TLApproveRejectLeaveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def post(self, request, leave_id):
        leave = get_object_or_404(LeaveRequest, id=leave_id)

        if leave.tl != request.user:
            return Response({"detail": "Not your team member"}, status=403)

        action = request.data.get("action")  # approve / reject
        remarks = request.data.get("remarks", "")

        if action == "approve":
            leave.apply_tl_approval(
                request.user, approve=True, remarks=remarks)
            return Response({"detail": "TL approved leave."})

        leave.apply_tl_approval(request.user, approve=False, remarks=remarks)
        return Response({"detail": "TL rejected leave."})


# ------------------------------
# TL: Team Attendance List
# ------------------------------
class TLTeamAttendanceAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTL]
    serializer_class = AttendanceReadSerializer

    def get_queryset(self):
        month = self.request.query_params.get("month")
        team = EmployeeProfile.objects.filter(
            manager=self.request.user).values_list("user", flat=True)

        qs = Attendance.objects.filter(user__in=team)

        if month:
            y, m = map(int, month.split("-"))
            qs = qs.filter(date__year=y, date__month=m)

        return qs.order_by("-date")


# ------------------------------
# TL: Create Calendar Event (Team Meeting)
# ------------------------------
class TLCreateEventAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def post(self, request):
        title = request.data.get("title")
        description = request.data.get("description", "")
        date = request.data.get("date")
        start_time = request.data.get("start_time")
        end_time = request.data.get("end_time")

        event = CalendarEvent.objects.create(
            title=title,
            description=description,
            event_type="meeting",
            date=date,
            start_time=start_time,
            end_time=end_time,
            created_by=request.user,
            visible_to_tl_hr=True,
        )

        return Response(CalendarEventSerializer(event).data, status=201)


# ------------------------------
# TL Dashboard Summary
# ------------------------------
class TLDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTL]

    def get(self, request):
        user = request.user

        team_members = EmployeeProfile.objects.filter(manager=user)

        # Team count
        team_count = team_members.count()

        # Pending leaves
        pending_leaves = LeaveRequest.objects.filter(
            tl=user,
            status="applied"
        ).count()

        # Attendance summary (current month)
        today = timezone.localdate()
        y, m = today.year, today.month
        attendance_qs = Attendance.objects.filter(
            user__in=team_members.values_list("user", flat=True),
            date__year=y,
            date__month=m
        )

        total_present = attendance_qs.count()
        total_hours = attendance_qs.aggregate(
            total=Sum("duration_seconds"))["total"] or 0

        # Upcoming meetings
        meetings = CalendarEvent.objects.filter(
            event_type="meeting",
            created_by=user
        ).order_by("-date")[:5]

        from emp.serializers import CalendarEventSerializer
        meeting_data = CalendarEventSerializer(meetings, many=True).data

        return Response({
            "team_count": team_count,
            "pending_leave_requests": pending_leaves,
            "attendance_summary": {
                "present_days": total_present,
                "total_hours": round(total_hours / 3600, 2)
            },
            "recent_meetings": meeting_data
        })
