from django.utils import timezone
from jsonschema import ValidationError
from rest_framework import generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django_filters import FilterSet, CharFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import (
    Employee, EmployeeDepartment, 
    Job, EmployeeStatus, LeaveType, LeaveBalance, LeaveManagement
)
import datetime
from .serializers import (
    AssignJobSerializer, EmployeeCreateUpdateSerializer,EmployeeDeptSerializer,EmployeeDetailSerializer, EmployeeLeaveBalanceSummarySerializer,
    EmployeeListSerializer,EmployeeStatusSerializer,
    EmployeeDeptSerializer,LeaveManagementSerializer,LeaveTypeSerializer,
    JobSerializer,JobListSerializer
)
from .filters import EmployeeFilter

class EmployeeViewSet(ModelViewSet):
    """Employee CRUD operations"""
    queryset = Employee.objects.all()
    lookup_field = 'emp_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['emp_name', 'email', 'phone']
    ordering_fields = ['emp_name', 'hire_date']
    ordering = ['emp_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        elif self.action == 'assign_job':
            return AssignJobSerializer  
        else:
            return EmployeeDetailSerializer

    @action(detail=True, methods=['post'])
    def assign_job(self, request, *args, **kwargs):
        """Assign a new job to an employee"""
        employee = self.get_object()
        serializer = AssignJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(Job, pk=serializer.validated_data['job_id'])

        # Check if the job is active
        if not job.is_active:
            return Response(
                {'error': f"The job '{job.job_title}' is not active and cannot be assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = serializer.validated_data.get('start_date', timezone.now().date())
        salary = serializer.validated_data['salary']

        if not employee.is_active:
            return Response({
                'error': f"The employee '{employee.emp_name}' is not active and cannot be assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if employee already has a current job
        current_status = employee.get_current_status()
        if current_status:
            return Response(
                {'error': f"Employee already has a current job '{current_status.job.job_title}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            new_status = EmployeeStatus.objects.create(
                employee=employee,
                job=job,
                start_date=start_date,
                salary=salary,
                is_current=True
            )

        return Response(EmployeeStatusSerializer(new_status).data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['get'])
    def job_history(self, request, *args, **kwargs):
        """Return full job history for employee"""
        employee = self.get_object()
        statuses = employee.statuses.all().order_by('-start_date')
        serializer = EmployeeStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminate(self, request, *args, **kwargs):
        """Terminate employee's current job assignment"""
        employee = self.get_object()
        current_status = employee.get_current_status()
        
        if not current_status:
            return Response({'error': 'Employee has no current job assignment'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        end_date_str = request.data.get('end_date')
        end_date = datetime.date.fromisoformat(end_date_str) if end_date_str else timezone.now().date()
        
        with transaction.atomic():
            current_status.end_date = end_date
            current_status.is_current = False
            current_status.save()

            if request.data.get('set_inactive', False):
                employee.is_active = False
                employee.resignation_date = end_date
                employee.save()

        return Response({'message': 'Employee assignment terminated successfully'}, status=status.HTTP_200_OK)
    
class EmployeeStatusViewSet(ModelViewSet):
    """Manage employee job assignment records"""
    queryset = EmployeeStatus.objects.select_related('employee', 'job')
    serializer_class = EmployeeStatusSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'job', 'end_date']
    search_fields = ['employee__emp_name', 'job__job_title']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('current_only') == 'true':
            queryset = queryset.filter(is_current=True)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
        return queryset

    def perform_create(self, serializer):
        """End previous current status if exists"""
        employee = serializer.validated_data['employee']
        start_date = serializer.validated_data.get('start_date', timezone.now().date())
        current_status = employee.get_current_status()
        if current_status:
            current_status.end_date = start_date
            current_status.is_current = False
            current_status.save()
        serializer.save(is_current=True)


class DepartmentListView(ModelViewSet):
    """List all departments"""
    queryset = EmployeeDepartment.objects.all()
    serializer_class = EmployeeDeptSerializer
    lookup_field = 'dept_id'
    search_fields = ['dept_name']
    ordering = ['dept_name']

    def get_serializer_class(self):
        return EmployeeDeptSerializer


class JobFilter(FilterSet):
    """Custom filter for Job model"""
    job_name = CharFilter(field_name='job_title', lookup_expr='icontains')
    dept_name = CharFilter(field_name='dept__dept_name', lookup_expr='icontains')
    
    class Meta:
        model = Job
        fields = {
            'job_title': ['exact', 'icontains'],
            'dept': ['exact'],
            'is_active': ['exact'],
        }


class JobViewSet(ModelViewSet):
    """Custom filter for Job View"""
    queryset = Job.objects.select_related('dept').prefetch_related('employee_statuses')
    lookup_field = 'job_id'
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['job_title', 'dept__dept_name']
    ordering_fields = ['job_title', 'created_at', 'updated_at']
    ordering = ['job_title']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return JobListSerializer
        return JobSerializer

    @action(detail=True, methods=['get'])
    def current_employees(self, request, job_id=None):
        """Get all employees currently assigned to this job"""
        job = self.get_object()
        current_statuses = EmployeeStatus.objects.filter(
            job=job, 
            end_date__isnull=True
        ).select_related('employee')
        
        employees = [status.employee for status in current_statuses]
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def assignment_history(self, request, job_id=None):
        """Get assignment history for this job"""
        job = self.get_object()
        statuses = job.employee_statuses.all().order_by('-start_date')
        serializer = EmployeeStatusSerializer(statuses, many=True)
        return Response(serializer.data)



class LeaveTypeViewSet(ModelViewSet):
    """Complete CRUD operations for Leave Types"""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    lookup_field = 'leave_type_id'
    
    # Filtering, searching, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'carry_forward']
    search_fields = ['leave_name']
    ordering_fields = ['leave_name', 'annual_allocation', 'created_at']
    ordering = ['leave_name']

    def get_queryset(self):
        """Show all leave types by default, filter only if requested"""
        queryset = super().get_queryset()
        if self.action == 'list':
            show_active_only = self.request.query_params.get('active_only', 'false')
            if show_active_only.lower() == 'true':
                queryset = queryset.filter(is_active=True)
        return queryset


class LeaveManagementViewSet(ModelViewSet):
    """View Set of Leaveme Mgmt"""
    queryset = LeaveManagement.objects.all()
    serializer_class = LeaveManagementSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a leave request"""
        leave = self.get_object()
        comments = request.data.get("comments", "")

        try:
            leave.approve(comments=comments)
            return Response({"message": "Leave approved successfully"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": e.message_dict if hasattr(e, "message_dict") else e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a leave request"""
        leave = self.get_object()
        rejection_reason = request.data.get("rejection_reason", "")

        try:
            leave.reject(rejection_reason=rejection_reason)
            return Response({"message": "Leave rejected successfully"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": e.message_dict if hasattr(e, "message_dict") else e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a leave request"""
        leave = self.get_object()
        cancelled_by = getattr(request.user, "employee", None)  # if user is linked to Employee

        try:
            leave.cancel(cancelled_by=cancelled_by)
            return Response({"message": "Leave cancelled successfully"}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": e.message_dict if hasattr(e, "message_dict") else e.messages}, status=status.HTTP_400_BAD_REQUEST)
        

class EmployeeLeaveBalanceViewSet(viewsets.ViewSet):
    """
    Return leave balances per employee, optionally filtered by year.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter('year', OpenApiTypes.INT, description='Year to filter leave balances')
        ]
    )
    def retrieve(self, request, pk=None):
        try:
            emp = Employee.objects.get(emp_id=pk)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        year = request.query_params.get('year', None)
        leave_types = LeaveType.objects.filter(is_active=True)

        if year:
            leave_usages = LeaveManagement.objects.filter(
                employee=emp,
                status='APPROVED',
                start_date__year=year
            ).values('leave_type').annotate(total_used=Sum('days_requested'))
        else:
            leave_usages = LeaveManagement.objects.filter(
                employee=emp,
                status='APPROVED'
            ).values('leave_type').annotate(total_used=Sum('days_requested'))

        usage_dict = {entry['leave_type']: float(entry['total_used']) for entry in leave_usages}

        balances = [
            {
                'leave_type_id': str(lt.leave_type_id),
                'leave_type_name': lt.leave_name,
                'allocated_days': lt.annual_allocation,
                'used_days': usage_dict.get(lt.leave_type_id, 0),
                'available_days': max(0, lt.annual_allocation - usage_dict.get(lt.leave_type_id, 0))
            }
            for lt in leave_types
        ]

        result = {
            'employee': {
                'emp_id': str(emp.emp_id),
                'emp_name': emp.emp_name,
                'email': emp.email
            },
            'year': year if year else 'All Years',
            'balances': balances
        }

        return Response(result, status=status.HTTP_200_OK)