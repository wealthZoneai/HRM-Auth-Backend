# hr/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Employee management
    path('employees/', views.HRListEmployeesAPIView.as_view(),
         name='hr-employees-list'),
    path('employees/<int:pk>/', views.HRRetrieveEmployeeAPIView.as_view(),
         name='hr-employee-detail'),
    path('employees/<int:pk>/jobbank/',
         views.HRUpdateJobBankAPIView.as_view(), name='hr-employee-jobbank'),

    # Attendance admin
    path('attendance/', views.HRAttendanceListAPIView.as_view(),
         name='hr-attendance-list'),
    path('attendance/<int:pk>/', views.HRAttendanceRetrieveAPIView.as_view(),
         name='hr-attendance-detail'),
    path('attendance/<int:attendance_id>/correct/',
         views.HRAttendanceCorrectAPIView.as_view(), name='hr-attendance-correct'),

    # Shift
    path('shifts/', views.ShiftListCreateAPIView.as_view(), name='hr-shifts'),
    path('shifts/<int:pk>/', views.ShiftRetrieveUpdateAPIView.as_view(),
         name='hr-shift-detail'),

    # Calendar / announcements
    path('calendar/create/', views.HRCalendarCreateAPIView.as_view(),
         name='hr-calendar-create'),

    # Salary & payslip
    path('salary-structures/', views.SalaryStructureListCreateAPIView.as_view(),
         name='hr-salary-structures'),
    path('employees/<int:profile_id>/assign-salary/',
         views.EmployeeSalaryAssignAPIView.as_view(), name='hr-assign-salary'),
    path('employees/<int:profile_id>/generate-payslip/',
         views.HRGeneratePayslipAPIView.as_view(), name='hr-generate-payslip'),

    # Leave management
    path('leaves/', views.HRLeaveListAPIView.as_view(), name='hr-leave-list'),
    path('leaves/<int:pk>/', views.HRLeaveDetailAPIView.as_view(),
         name='hr-leave-detail'),
    path('leaves/<int:leave_id>/action/',
         views.HRLeaveActionAPIView.as_view(), name='hr-leave-action'),
]
