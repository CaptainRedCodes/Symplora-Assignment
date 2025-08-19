from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.db.models import Sum
import datetime
from .models import (
    Employee, EmployeeDepartment, 
    Job, EmployeeStatus, LeaveType, LeaveBalance, LeaveManagement
)

class EmployeeDeptSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDepartment
        fields = ['dept_id', 'dept_name', 'created_at', 'updated_at']
        read_only_fields = ['dept_id', 'created_at', 'updated_at']

    def validate_dept_name(self, value):
        queryset = EmployeeDepartment.objects.filter(dept_name__iexact=value)

        if self.instance:
            queryset = queryset.exclude(dept_id=self.instance.dept_id)

        if queryset.exists():
            raise serializers.ValidationError("Department already exists")
        return value

class JobSerializer(serializers.ModelSerializer):
    # Nested read-only serializer for displaying department info
    dept = EmployeeDeptSerializer(read_only=True)
    # Write-only field for creating/updating department by ID
    department_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = Job
        fields = [
            'job_id',
            'job_title',
            'dept',            # read-only nested
            'department_id',   # write-only for input
            'job_description',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['job_id', 'created_at', 'updated_at']

    def validate_department_id(self, value):
        """Ensure the department exists"""
        if not EmployeeDepartment.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Department with this ID does not exist.")
        return value

    def create(self, validated_data):
        dept_id = validated_data.pop('department_id')
        validated_data['dept'] = EmployeeDepartment.objects.get(pk=dept_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        dept_id = validated_data.pop('department_id', None)
        if dept_id:
            instance.dept = EmployeeDepartment.objects.get(pk=dept_id)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Customize output to hide write-only field"""
        representation = super().to_representation(instance)
        representation.pop('department_id', None)
        return representation


class JobListSerializer(serializers.ModelSerializer):
    dept = EmployeeDeptSerializer(read_only = True)

    class Meta:
        model = Job
        fields = ['job_id', 'job_title', 'dept','is_active']

class EmployeeStatusSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    employee_name = serializers.CharField(source='employee.emp_name', read_only=True)

    class Meta:
        model = EmployeeStatus
        fields = [
            'st_id', 'employee_name', 'job',
            'start_date', 'end_date', 'salary', 'is_current'
        ]


class EmployeeStatusCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeStatus
        fields = [
            'employee', 'job', 'start_date', 'end_date', 'salary', 'is_current'
        ]

    def validate(self, attrs):
        employee = self.context.get('employee') or attrs.get('employee')
        if employee and attrs.get('start_date') and employee.hire_date:
            if attrs.get('start_date') < employee.hire_date:
                raise serializers.ValidationError("Job start date cannot be before hire date")
        if attrs.get('salary') <= 0:
            raise serializers.ValidationError("Salary must be greater than zero")
        return attrs


class AssignJobSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    start_date = serializers.DateField(required=False)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_start_date(self, value):
        """Ensure start_date is not in the future"""
        if value and value > datetime.date.today():
            raise serializers.ValidationError("Start date cannot be in the future.")
        return value


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for employee lists with current job"""
    current_job = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date',
            'emp_education', 'current_job', 'is_active'
        ]

    def get_current_job(self, obj):
        current_status = obj.get_current_status()
        return current_status.job.job_title if current_status and current_status.job else None


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single employee view"""
    current_status = serializers.SerializerMethodField()
    job_history = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date', 
            'resignation_date', 'emp_education', 'is_active',
            'current_status', 'job_history',
            'created_at', 'updated_at'
        ]

    def get_current_status(self, obj):
        current_status = obj.get_current_status()
        return EmployeeStatusSerializer(current_status).data if current_status else None

    def get_job_history(self, obj):
        statuses = obj.statuses.all().order_by('-start_date')
        return EmployeeStatusSerializer(statuses, many=True).data


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    resignation_date = serializers.DateField(
        input_formats=['%Y-%m-%d'],
        required=False,  
        allow_null=True  
    )

    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date',
            'resignation_date', 'emp_education', 'is_active'
        ]

    def validate_email(self, value):
        queryset = Employee.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(emp_id=self.instance.emp_id)
        if queryset.exists():
            raise serializers.ValidationError("Employee with this email already exists")
        return value.lower()

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number should only contain digits")
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
        queryset = Employee.objects.filter(phone=value)
        if self.instance:
            queryset = queryset.exclude(emp_id=self.instance.emp_id)
        if queryset.exists():
            raise serializers.ValidationError("Employee with this phone number already exists")
        return value

    def validate_hire_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Hire date cannot be in the future")
        return value

    def validate_resignation_date(self, value):
        if value is not None:
            hire_date = self.initial_data.get('hire_date')
            if isinstance(hire_date, str):
                hire_date = datetime.date.fromisoformat(hire_date)
            if self.instance:
                hire_date = hire_date or self.instance.hire_date
            if hire_date and value < hire_date:
                raise serializers.ValidationError("Resignation date cannot be before hire date")
        return value



class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ('leave_type_id', 'created_at', 'updated_at')

    def validate_leave_name(self, value):
        # Check for duplicate active leave names
        instance = getattr(self, 'instance', None)
        queryset = LeaveType.objects.filter(leave_name__iexact=value, is_active=True)
        
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("An active leave type with this name already exists.")
        
        return value



class LeaveManagementSerializer(serializers.ModelSerializer):
    """Serializer for Leave Management with validation"""

    # Nested serializers for read operations
    employee_details = serializers.SerializerMethodField()
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)

    # Computed fields
    total_days = serializers.SerializerMethodField()
    days_elapsed = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = LeaveManagement
        fields = [
            # Primary fields
            'leave_id', 'employee', 'leave_type', 'start_date', 'end_date',
            'days_requested', 'reason', 'status', 'validated_on', 'applied_on',

            # Management fields
            'comments',

            # Nested objects
            'employee_details', 'leave_type_details',

            # Computed fields
            'total_days', 'days_elapsed', 'can_cancel', 'can_edit',
        ]

        read_only_fields = [
            'leave_id', 'applied_on', 'validated_on', 'status'
        ]

        extra_kwargs = {
            'start_date': {'required': True},
            'end_date': {'required': True},
            'leave_type': {'required': True},
            'reason': {'required': True, 'allow_blank': False},
            'days_requested': {'required': True, 'min_value': 0.5},
        }

    def get_employee_details(self, obj):
        """Get employee details (basic info)"""
        try:
            return {
                'emp_id': str(obj.employee.emp_id),
                'emp_name': obj.employee.emp_name,
                'email': obj.employee.email,
            }
        except AttributeError:
            return None

    def get_total_days(self, obj):
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return 0

    def get_days_elapsed(self, obj):
        if obj.start_date and obj.status == 'APPROVED':
            today = timezone.now().date()
            if today >= obj.start_date:
                return min((today - obj.start_date).days + 1, self.get_total_days(obj))
        return 0

    def get_can_cancel(self, obj):
        if hasattr(obj, 'can_be_cancelled'):
            return obj.can_be_cancelled()
        return obj.status in ['PENDING', 'APPROVED']

    def get_can_edit(self, obj):
        return obj.status == 'PENDING'

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type = data.get('leave_type')
        days_requested = data.get('days_requested')
        employee = data.get('employee') or (self.instance.employee if self.instance else None)

        # Dates
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({'end_date': 'End date must be after or equal to start date.'})

            if not self.instance and start_date < timezone.now().date():
                raise serializers.ValidationError({'start_date': 'Start date cannot be in the past.'})

        # Days match
        if start_date and end_date and days_requested:
            calculated_days = (end_date - start_date).days + 1
            if abs(calculated_days - days_requested) > 0.5:
                raise serializers.ValidationError({
                    'days_requested': f'Days requested ({days_requested}) does not match the date range ({calculated_days} days).'
                })

        # Max days per leave type
        if leave_type and days_requested:
            max_days = getattr(leave_type, 'max_consecutive_days', None)
            if max_days and days_requested > max_days:
                leave_name = getattr(leave_type, 'leave_name', 'this leave type')
                raise serializers.ValidationError({
                    'days_requested': f'Cannot request more than {max_days} days for {leave_name}.'
                })

        # Overlap check (for same employee)
        if employee and start_date and end_date:
            overlapping = LeaveManagement.objects.filter(
                employee=employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                overlap = overlapping.first()
                raise serializers.ValidationError({
                    'non_field_errors': f'Leave overlaps with existing (ID: {overlap.leave_id}) '
                                        f'from {overlap.start_date} to {overlap.end_date}.'
                })

        return data

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Reason cannot be empty.')
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Please provide a more detailed reason (min 10 chars).')
        return value.strip()

    def validate_days_requested(self, value):
        if value <= 0:
            raise serializers.ValidationError('Days requested must be greater than 0.')
        if value % 0.5 != 0:
            raise serializers.ValidationError('Days must be in increments of 0.5.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Format dates
        for field in ['start_date', 'end_date']:
            try:
                if data.get(field):
                    if isinstance(data[field], str):
                        parsed = datetime.datetime.strptime(data[field], '%Y-%m-%d')
                    else:
                        parsed = data[field]
                    data[f'{field}_formatted'] = parsed.strftime('%d %b %Y')
            except Exception:
                pass

        # Applied on
        try:
            applied = data.get('applied_on')
            if applied:
                if isinstance(applied, str):
                    applied_date = datetime.datetime.fromisoformat(applied.replace('Z', '+00:00'))
                else:
                    applied_date = applied
                data['applied_on_formatted'] = applied_date.strftime('%d %b %Y at %I:%M %p')
        except Exception:
            pass

        # Status colors
        data['status_color'] = {
            'PENDING': '#FFA500',
            'APPROVED': '#28A745',
            'REJECTED': '#DC3545',
            'CANCELLED': '#6C757D'
        }.get(data.get('status', 'PENDING'), '#6C757D')

        return data


class LeaveManagementCreateSerializer(LeaveManagementSerializer):
    """Serializer for creating leave applications"""
    class Meta(LeaveManagementSerializer.Meta):
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'reason']


class LeaveManagementUpdateSerializer(LeaveManagementSerializer):
    """Serializer for updating pending leave applications"""
    class Meta(LeaveManagementSerializer.Meta):
        fields = ['leave_type', 'start_date', 'end_date', 'days_requested', 'reason']

    def validate(self, data):
        if self.instance and self.instance.status != 'PENDING':
            raise serializers.ValidationError('Only pending leaves can be updated.')
        return super().validate(data)


class LeaveApprovalSerializer(serializers.Serializer):
    """Serializer for leave approval"""
    comments = serializers.CharField(max_length=500, required=False, allow_blank=True)


class LeaveRejectionSerializer(serializers.Serializer):
    """Serializer for leave rejection"""
    rejection_reason = serializers.CharField(max_length=500, required=True)
    
    def validate_rejection_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Rejection reason is required.')
        return value.strip()


class EmployeeLeaveBalanceSummarySerializer(serializers.Serializer):
    """Summary of leave balances per employee per year"""
    
    DEFAULT_ANNUAL_ALLOCATION = 20

    employee = serializers.SerializerMethodField()
    year = serializers.IntegerField()
    balances = serializers.SerializerMethodField()

    def get_employee(self, obj):
        emp = obj['employee']
        return {
            'emp_id': str(emp.emp_id),
            'emp_name': emp.emp_name,
            'email': emp.email
        }

    def get_balances(self, obj):
        employee = obj['employee']
        year = obj['year']
        balances = []

        leave_types = LeaveType.objects.filter(is_active=True)
        for leave_type in leave_types:
            allocated_days = getattr(leave_type, 'annual_allocation', self.DEFAULT_ANNUAL_ALLOCATION)

            used_leaves = employee.leaves.filter(
                leave_type=leave_type,
                status='APPROVED',
                start_date__year=year
            ).aggregate(total=Sum('days_requested'))['total'] or 0

            balances.append({
                'leave_type_id': str(leave_type.pk),
                'leave_type_name': getattr(leave_type, 'leave_name', 'Unknown'),
                'allocated_days': allocated_days,
                'used_days': float(used_leaves),
                'available_days': max(0, allocated_days - used_leaves)
            })

        return balances