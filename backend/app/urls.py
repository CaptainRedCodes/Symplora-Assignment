# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employees')
router.register(r'leave-applications', views.LeaveManagementViewSet, basename='leaveapplications')
router.register(r'Departments',views.DepartmentListView,basename = 'department')
router.register(r'Jobs',views.JobViewSet,basename='job')
router.register(r'leave-types', views.LeaveTypeViewSet, basename='leavetype')
router.register(r'employee-status',views.EmployeeStatusViewSet,basename='emp_status')
router.register(r'leave-balances', views.EmployeeLeaveBalanceViewSet, basename='leave-balances')


urlpatterns = [
    path('api/', include(router.urls)),
]