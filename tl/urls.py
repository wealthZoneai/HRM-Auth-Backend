# tl/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("team/members/", views.TLTeamMembersAPIView.as_view()),
    path("team/attendance/", views.TLTeamAttendanceAPIView.as_view()),
    path("team/dashboard/", views.TLDashboardAPIView.as_view()),

    # Leave management
    path("leave/pending/", views.TLPendingLeaveAPIView.as_view()),
    path("leave/<int:leave_id>/action/",
         views.TLApproveRejectLeaveAPIView.as_view()),

    # Calendar
    path("calendar/create/", views.TLCreateEventAPIView.as_view()),
]
