from django.utils import timezone
from jsonschema import ValidationError
from rest_framework import generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django_filters import FilterSet, CharFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import (
    Employee, EmployeeDepartment, 
    Job, EmployeeStatus, LeaveType, LeaveBalance, LeaveManagement
)

from .serializers import (
    AssignJobSerializer, EmployeeCreateUpdateSerializer,EmployeeDeptSerializer,EmployeeDetailSerializer,
    EmployeeLeaveBalanceSummarySerializer,EmployeeListSerializer,EmployeeStatusCreateSerializer,EmployeeStatusSerializer,
    EmployeeDeptSerializer,LeaveManagementSerializer,LeaveTypeSerializer,
    JobSerializer,JobListSerializer
)

# Employee Management: Create, read, update employee records
# Leave Application: Apply for leave, view applications
# Leave Approval: Approve/reject leave requests
# Leave Balance: Check current balances

class EmployeeViewSet(ModelViewSet):
    """Employee CRUD operations"""
    queryset = Employee.objects.all()
    lookup_field = 'emp_id'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job__job_title', 'is_active']
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
        employee = self.get_object()
        serializer = AssignJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_id = serializer.validated_data['job_id']
        start_date = serializer.validated_data.get('start_date', timezone.now().date())
        salary = serializer.validated_data['salary']

        job = get_object_or_404(Job, pk=job_id)

        with transaction.atomic():
            current_status = employee.get_current_status()
            if current_status:
                current_status.end_date = start_date
                current_status.save()

            new_status = EmployeeStatus.objects.create(
                employee=employee,
                job=job,
                start_date=start_date,
                salary=salary,
                manager=None  
            )

        return Response(
            EmployeeStatusSerializer(new_status).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def transfer(self, request, *args, **kwargs):
        employee = self.get_object()
        current_status = employee.get_current_status()
        
        if not current_status:
            return Response(
                {'error': 'Employee has no current job assignment'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # validate inputs
        effective_date_str = request.data.get('effective_date')
        effective_date = (
            datetime.date.fromisoformat(effective_date_str)
            if effective_date_str else timezone.now().date()
        )

        manager = None
        manager_id = request.data.get('manager_id')
        if manager_id:
            manager = get_object_or_404(Employee, pk=manager_id)

        with transaction.atomic():
            current_status.end_date = effective_date
            current_status.save()

            new_status = EmployeeStatus.objects.create(
                employee=employee,
                job=current_status.job,
                manager=manager,
                start_date=effective_date,
                salary=current_status.salary
            )

        return Response(
            EmployeeStatusSerializer(new_status).data, 
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def job_history(self, request, *args, **kwargs):
        employee = self.get_object()
        statuses = employee.statuses.all().order_by('-start_date')
        serializer = EmployeeStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminate(self, request, *args, **kwargs):
        employee = self.get_object()
        current_status = employee.get_current_status()
        
        if not current_status:
            return Response(
                {'error': 'Employee has no current job assignment'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        end_date_str = request.data.get('end_date')
        end_date = (
            datetime.date.fromisoformat(end_date_str)
            if end_date_str else timezone.now().date()
        )
        
        with transaction.atomic():
            current_status.end_date = end_date
            current_status.save()
            
            if request.data.get('set_inactive', False):
                employee.is_active = False
                employee.resignation_date = end_date
                employee.save()

        return Response(
            {'message': 'Employee assignment terminated successfully'}, 
            status=status.HTTP_200_OK
        )

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
            #'dept': ['exact'],
            'is_active': ['exact'],
        }


class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related('job').prefetch_related('employee_statuses')
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


class EmployeeStatusViewSet(ModelViewSet):
    """
    ViewSet for managing employee status records (job assignments)
    """
    queryset = EmployeeStatus.objects.select_related('employee', 'job', 'manager')
    serializer_class = EmployeeStatusSerializer
    #permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'job', 'manager', 'end_date']
    search_fields = ['employee__emp_name', 'job__job_title']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter for current assignments
        if self.request.query_params.get('current_only') == 'true':
            queryset = queryset.filter(end_date__isnull=True)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
            
        return queryset


    def perform_create(self, serializer):
        """Override to handle business logic when creating new status"""
        employee = serializer.validated_data['employee']
        start_date = serializer.validated_data.get('start_date', timezone.now().date())
        
        # End current status if exists
        current_status = employee.get_current_status()
        if current_status:
            current_status.end_date = start_date
            current_status.save()
        
        serializer.save()

    def perform_update(self, serializer):
        """Override to handle business logic when updating status"""
        # Add any business logic for updates
        serializer.save()


class LeaveTypeViewSet(ModelViewSet):
    """Complete CRUD operations for Leave Types"""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    #permission_classes = [IsAuthenticated]
    lookup_field = 'leave_type_id'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'carry_forward']
    search_fields = ['leave_name']
    ordering_fields = ['leave_name', 'annual_allocation', 'created_at']
    ordering = ['leave_name']
    
    def get_queryset(self):
        """Show only active leave types by default"""
        queryset = super().get_queryset()
        if self.action == 'list':
            show_inactive = self.request.query_params.get('show_inactive', 'false')
            if show_inactive.lower() != 'true':
                queryset = queryset.filter(is_active=True)
        return queryset
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.is_active = False
        instance.save()
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Leave type deactivated successfully"}, 
            status=status.HTTP_200_OK
        )


class LeaveManagementViewSet(ModelViewSet):
    """Complete CRUD operations for Leave Applications"""
    queryset = LeaveManagement.objects.all()
    serializer_class = LeaveManagementSerializer
    #permission_classes = [IsAuthenticated]
    lookup_field = 'leave_id'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'leave_type', 'employee']
    search_fields = ['employee__emp_name', 'reason', 'leave_type__name']
    ordering_fields = ['applied_on', 'start_date', 'end_date', 'days_requested']
    ordering = ['-applied_on']

    def get_queryset(self):
        """Filter based on user permissions and action"""
        queryset = super().get_queryset()
        user_employee = getattr(self.request.user, 'employee_profile', None)
        
        if not user_employee:
            return queryset.none()

        if self.action in ['update', 'partial_update']:
            # Only allow updates to own pending leaves
            return queryset.filter(employee=user_employee, status='PENDING')
        elif self.action == 'destroy':
            # Only allow cancellation of own leaves
            return queryset.filter(employee=user_employee)
        else:
            # Show own leaves + subordinate leaves
            return queryset.filter(
                Q(employee=user_employee) |
                Q(employee__in=user_employee.get_subordinates())
            )

    def perform_create(self, serializer):
        """Auto-set employee for leave application"""
        user_employee = getattr(self.request.user, 'employee_profile', None)
        if user_employee:
            serializer.save(employee=user_employee)
        else:
            raise ValidationError("Employee profile not found for user")

    def perform_destroy(self, instance):
        """Cancel leave instead of deleting"""
        if instance.can_be_cancelled():
            instance.cancel(cancelled_by=getattr(self.request.user, 'employee_profile', None))
        else:
            raise ValidationError("This leave cannot be cancelled")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Leave application cancelled successfully"}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, leave_id=None):
        """Approve a leave application"""
        leave = self.get_object()
        user_employee = getattr(request.user, 'employee_profile', None)
        
        if not user_employee:
            return Response(
                {"error": "Employee profile not found"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            comments = request.data.get('comments', '')
            leave.approve(approved_by=user_employee, comments=comments)
            return Response(
                {"message": "Leave approved successfully"},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, leave_id=None):
        """Reject a leave application"""
        leave = self.get_object()
        user_employee = getattr(request.user, 'employee_profile', None)
        
        if not user_employee:
            return Response(
                {"error": "Employee profile not found"},
                status=status.HTTP_403_FORBIDDEN
            )

        rejection_reason = request.data.get('rejection_reason', '')
        if not rejection_reason.strip():
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            leave.reject(rejected_by=user_employee, rejection_reason=rejection_reason)
            return Response(
                {"message": "Leave rejected successfully"},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending leave applications for approval"""
        user_employee = getattr(request.user, 'employee_profile', None)
        if not user_employee:
            return Response(
                {"error": "Employee profile not found"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get pending leaves from subordinates
        pending_leaves = self.get_queryset().filter(
            employee__in=user_employee.get_subordinates(),
            status='PENDING'
        )
        
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_leaves(self, request):
        """Get current user's leave applications"""
        user_employee = getattr(request.user, 'employee_profile', None)
        if not user_employee:
            return Response(
                {"error": "Employee profile not found"},
                status=status.HTTP_403_FORBIDDEN
            )

        my_leaves = self.get_queryset().filter(employee=user_employee)
        serializer = self.get_serializer(my_leaves, many=True)
        return Response(serializer.data)
    
# class MyLeaveBalanceView(generics.RetrieveAPIView):
#     """Get current user's leave balance"""
    
#     def get(self, request, year=None):
#         if year is None:
#             year = timezone.now().year
        
#         employee = request.user.employee  # Adjust based on your user model
        
#         data = {
#             'employee': employee,
#             'year': year
#         }
        
#         serializer = EmployeeLeaveBalanceSummarySerializer(data)
#         return Response(serializer.data)
