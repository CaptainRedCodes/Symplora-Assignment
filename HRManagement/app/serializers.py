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
        return value.lower()


class JobSerializer(serializers.ModelSerializer):
    dept = EmployeeDeptSerializer(read_only=True)
    dept_id = serializers.UUIDField(write_only=True)  

    class Meta:
        model = Job
        fields = [
            'job_id', 
            'job_title', 
            'dept',        
            'dept_id',     
            'job_description', 
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['job_id', 'created_at', 'updated_at']

    def validate_department_id(self, value):
        """Validate that the department exists"""
        try:
            dept = EmployeeDepartment.objects.get(pk=value)
            return dept  # Return the UUID value, not the object
        except EmployeeDepartment.DoesNotExist:
            raise serializers.ValidationError("Department with this ID does not exist.")

    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        # Remove department_id from the response as it's only for input
        representation.pop('department_id', None)
        return representation


class JobListSerializer(serializers.ModelSerializer):
    dept_name = serializers.CharField(source='department.dept_name', read_only=True)
    dept_id = serializers.UUIDField(source='department', write_only=True)

    class Meta:
        model = Job
        fields = ['job_id', 'job_title', 'dept_name', 'dept_id', 'is_active']


class EmployeeStatusSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    manager_name = serializers.CharField(source='manager.emp_name', read_only=True)
    manager_email = serializers.CharField(source='manager.email', read_only=True)
    employee_name = serializers.CharField(source='employee.emp_name', read_only=True)
    
    class Meta:
        model = EmployeeStatus
        fields = [
            'st_id', 'employee_name', 'job', 'manager_name', 'manager_email',
            'start_date', 'end_date', 'address', 'salary', 'is_current'
        ]


class EmployeeStatusCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeStatus
        fields = [
            'employee', 'job', 'manager', 'start_date', 'end_date', 
            'address', 'salary', 'is_current'
        ]
    
    def validate(self, attrs):
        # Custom validation for employee status
        employee = self.context.get('employee')
        
        if attrs.get('manager') == employee:
            raise serializers.ValidationError("Employee cannot be their own manager")
        
        if employee and attrs.get('start_date') and employee.hire_date:
            if attrs.get('start_date') < employee.hire_date:
                raise serializers.ValidationError("Job start date cannot be before hire date")
        
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
    """Lightweight serializer for employee lists"""
    current_job = serializers.SerializerMethodField()
    current_manager = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date',
             'emp_education', 'current_job', 'current_manager',
            'is_active'
        ]
    
    def get_current_job(self, obj):
        try:
            current_status = obj.get_current_status()
            return current_status.job.job_title if current_status and current_status.job else None
        except (AttributeError, Exception):
            return None
    
    def get_current_manager(self, obj):
        try:
            manager = obj.get_current_manager()
            return manager.emp_name if manager else None
        except (AttributeError, Exception):
            return None
    

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single employee view"""
    dept = EmployeeDeptSerializer(read_only=True)
    current_status = serializers.SerializerMethodField()
    job_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date', 
            'resignation_date', 'emp_education', 'is_active',
            'dept', 'current_status', 'job_history',
            'created_at', 'updated_at'
        ]
    
    def get_current_status(self, obj):
        try:
            current_status = obj.get_current_status()
            return EmployeeStatusSerializer(current_status).data if current_status else None
        except (AttributeError, Exception):
            return None
    
    def get_job_history(self, obj):
        try:
            statuses = obj.statuses.all().order_by('-start_date')[:5]  # Last 5 job changes
            return EmployeeStatusSerializer(statuses, many=True).data
        except (AttributeError, Exception):
            return []
    

class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    dept_id = serializers.UUIDField(source='dept', write_only=True, required=False)

    resignation_date = serializers.DateField(
        input_formats=['%Y-%m-%d'],
        required=False,  
        allow_null=True  
    )
    
    class Meta:
        model = Employee
        fields = [
            'emp_id', 'emp_name', 'email', 'phone', 'hire_date',
            'resignation_date', 'emp_education', 'is_active', 'dept_id'
        ]
    
    def validate_email(self, value):
        # Check email uniqueness (exclude current instance for updates)
        queryset = Employee.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(emp_id=self.instance.emp_id)
        
        if queryset.exists():
            raise serializers.ValidationError("Employee with this email already exists")
        return value.lower()
    
    def validate_phone(self, value):
        # Check for numeric characters only and proper validation
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
            if self.instance:
                hire_date = hire_date or self.instance.hire_date
                
            if hire_date and value < hire_date:
                raise serializers.ValidationError("Resignation date cannot be before hire date")
        return value



class ManagerAssignmentSerializer(serializers.Serializer):
    """Serializer for manager assignments"""
    manager_id = serializers.UUIDField()
    effective_date = serializers.DateField(default=timezone.now().date)
    
    def validate_manager_id(self, value):
        try:
            manager = Employee.objects.get(emp_id=value, is_active=True)
            return manager
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Manager not found or inactive")
    
    def validate(self, attrs):
        employee = self.context.get('employee')
        manager = attrs.get('manager_id')
        
        if manager == employee:
            raise serializers.ValidationError("Employee cannot be their own manager")
        
        # Check for circular reporting
        if employee and hasattr(manager, 'get_subordinates'):
            try:
                subordinates = manager.get_subordinates()
                if employee in subordinates:
                    raise serializers.ValidationError("This would create a circular reporting structure")
            except (AttributeError, Exception):
                pass  # Skip circular check if method doesn't exist or fails
        
        return attrs


class LeaveTypeSerializer(serializers.ModelSerializer):
    """Leave type serializer"""
    class Meta:
        model = LeaveType
        fields = ['leave_type_id', 'leave_name', 'max_consecutive_days', 'annual_allocation', 'carry_forward', 'min_notice_days', 'is_active']
        read_only_fields = ['leave_type_id']


class LeaveManagementSerializer(serializers.ModelSerializer):
    """Complete serializer for Leave Management with validation"""
    
    # Nested serializers for read operations
    employee_details = serializers.SerializerMethodField()
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)
    incharge_by_details = serializers.SerializerMethodField()
    
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
            'days_requested', 'reason', 'status', 'validated_on',
            'applied_on',
            
            # Management fields
            'incharge_by_details', 'comments',
            
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
        """Get employee details without circular dependency"""
        try:
            return {
                'emp_id': str(obj.employee.emp_id),
                'emp_name': obj.employee.emp_name,
                'email': obj.employee.email,
            }
        except (AttributeError, Exception):
            return None

    def get_incharge_by_details(self, obj):
        """Get details of who handled the leave (approved/rejected/cancelled)"""
        handler = None
        
        # Check for different types of handlers based on status
        if obj.status == 'APPROVED' and hasattr(obj, 'approved_by'):
            handler = obj.approved_by
        elif obj.status == 'REJECTED' and hasattr(obj, 'rejected_by'):
            handler = obj.rejected_by
        elif obj.status == 'CANCELLED' and hasattr(obj, 'cancelled_by'):
            handler = obj.cancelled_by
        
        if handler:
            return {
                'emp_id': str(handler.emp_id),
                'emp_name': handler.emp_name,
                'email': handler.email
            }
        return None

    def get_total_days(self, obj):
        """Calculate total days between start and end date"""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return 0

    def get_days_elapsed(self, obj):
        """Calculate days elapsed since start date"""
        if obj.start_date and obj.status == 'APPROVED':
            today = timezone.now().date()
            if today >= obj.start_date:
                return min((today - obj.start_date).days + 1, self.get_total_days(obj))
        return 0

    def get_can_cancel(self, obj):
        """Check if leave can be cancelled"""
        try:
            if hasattr(obj, 'can_be_cancelled'):
                return obj.can_be_cancelled()
        except (AttributeError, Exception):
            pass
        
        # Default logic
        return obj.status in ['PENDING', 'APPROVED']

    def get_can_edit(self, obj):
        """Check if leave can be edited"""
        return obj.status == 'PENDING'

    def validate(self, data):
        """Comprehensive validation for leave application"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type = data.get('leave_type')
        days_requested = data.get('days_requested')
        
        # Date validation
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after or equal to start date.'
                })
            
            # Check if start date is not in the past (for new applications)
            if not self.instance and start_date < timezone.now().date():
                raise serializers.ValidationError({
                    'start_date': 'Start date cannot be in the past.'
                })
        
        # Days validation
        if start_date and end_date and days_requested:
            calculated_days = (end_date - start_date).days + 1
            
            # Allow some flexibility for half days
            if abs(calculated_days - days_requested) > 0.5:
                raise serializers.ValidationError({
                    'days_requested': f'Days requested ({days_requested}) does not match the date range ({calculated_days} days).'
                })
        
        # Leave type validation
        if leave_type and days_requested:
            # Fixed: Use proper attribute name and safe access
            max_consecutive_days = getattr(leave_type, 'max_consecutive_days', None)
            if max_consecutive_days and days_requested > max_consecutive_days:
                leave_name = getattr(leave_type, 'leave_name', 'this leave type')
                raise serializers.ValidationError({
                    'days_requested': f'Cannot request more than {max_consecutive_days} days for {leave_name}.'
                })
        
        # Check for overlapping leaves
        employee = self.context.get('employee') or (self.instance.employee if self.instance else None)
        if employee and start_date and end_date:
            overlapping_query = LeaveManagement.objects.filter(
                employee=employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Exclude current instance when updating
            if self.instance:
                overlapping_query = overlapping_query.exclude(pk=self.instance.pk)
            
            if overlapping_query.exists():
                overlapping_leave = overlapping_query.first()
                raise serializers.ValidationError({
                    'non_field_errors': f'Leave dates overlap with existing leave application '
                                      f'(ID: {overlapping_leave.leave_id}) from '
                                      f'{overlapping_leave.start_date} to {overlapping_leave.end_date}.'
                })
        
        return data

    def validate_reason(self, value):
        """Validate reason field"""
        if not value or not value.strip():
            raise serializers.ValidationError('Reason cannot be empty.')
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Please provide a more detailed reason (minimum 10 characters).')
        
        return value.strip()

    def validate_days_requested(self, value):
        """Validate days requested"""
        if value <= 0:
            raise serializers.ValidationError('Days requested must be greater than 0.')
        
        # Allow half days
        if value % 0.5 != 0:
            raise serializers.ValidationError('Days can only be in increments of 0.5 (half days).')
        
        return value

    def to_representation(self, instance):
        """Customize the output representation"""
        data = super().to_representation(instance)
        
        # Format dates with proper error handling
        try:
            if data.get('start_date'):
                if isinstance(data['start_date'], str):
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
                    data['start_date_formatted'] = start_date.strftime('%d %b %Y')
                elif hasattr(data['start_date'], 'strftime'):
                    data['start_date_formatted'] = data['start_date'].strftime('%d %b %Y')
        except (ValueError, TypeError, AttributeError):
            pass  # Skip formatting if parsing fails
        
        try:
            if data.get('end_date'):
                if isinstance(data['end_date'], str):
                    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
                    data['end_date_formatted'] = end_date.strftime('%d %b %Y')
                elif hasattr(data['end_date'], 'strftime'):
                    data['end_date_formatted'] = data['end_date'].strftime('%d %b %Y')
        except (ValueError, TypeError, AttributeError):
            pass
        
        try:
            if data.get('applied_on'):
                applied_on = data['applied_on']
                if isinstance(applied_on, str):
                    # Handle ISO format with timezone
                    applied_date = applied_on.replace('Z', '+00:00')
                    if '+' not in applied_date and 'T' in applied_date:
                        applied_date = applied_date + '+00:00'
                    applied_date = datetime.fromisoformat(applied_date)
                elif hasattr(applied_on, 'strftime'):
                    applied_date = applied_on
                else:
                    applied_date = None
                
                if applied_date:
                    data['applied_on_formatted'] = applied_date.strftime('%d %b %Y at %I:%M %p')
        except (ValueError, TypeError, AttributeError):
            pass  # Skip formatting if datetime parsing fails
        
        # Add status color coding
        status_colors = {
            'PENDING': '#FFA500',
            'APPROVED': '#28A745',
            'REJECTED': '#DC3545',
            'CANCELLED': '#6C757D'
        }
        data['status_color'] = status_colors.get(data.get('status'), '#6C757D')
        
        return data


class LeaveManagementCreateSerializer(LeaveManagementSerializer):
    """Simplified serializer for creating leave applications"""
    class Meta(LeaveManagementSerializer.Meta):
        fields = [
            'employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'reason'
        ]


class LeaveManagementUpdateSerializer(LeaveManagementSerializer):
    """Serializer for updating pending leave applications"""
    class Meta(LeaveManagementSerializer.Meta):
        fields = [
            'leave_type', 'start_date', 'end_date', 'days_requested', 'reason'
        ]
    
    def validate(self, data):
        """Additional validation for updates"""
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
    """Summary of all leave balances for an employee"""
    DEFAULT_ANNUAL_ALLOCATION = 20
    
    employee = EmployeeListSerializer(read_only=True)
    year = serializers.IntegerField()
    balances = serializers.SerializerMethodField()
    
    def get_balances(self, obj):
        employee = obj['employee']
        year = obj['year']
        
        balances = []
        
        try:
            leave_types = LeaveType.objects.filter(is_active=True)
        except Exception:
            leave_types = []
        
        for leave_type in leave_types:
            try:
                # Get leave balance with safe method access
                if hasattr(employee, 'get_leave_balance'):
                    balance = employee.get_leave_balance(leave_type, year)
                else:
                    balance = 0
                
                # Calculate used leaves with proper aggregation
                used_leaves_query = employee.leaves.filter(
                    leave_type=leave_type,
                    status='APPROVED',
                    start_date__year=year
                )
                
                used_leaves_total = used_leaves_query.aggregate(
                    total=Sum('days_requested')
                )['total']
                used_leaves = used_leaves_total if used_leaves_total is not None else 0
                
                # Use model allocation or default
                allocated_days = getattr(leave_type, 'annual_allocation', None) or self.DEFAULT_ANNUAL_ALLOCATION
                
                balances.append({
                    'leave_type_id': str(leave_type.pk),  # Convert to string for consistency
                    'leave_type_name': getattr(leave_type, 'leave_name', 'Unknown'),
                    'allocated_days': allocated_days,
                    'used_days': float(used_leaves),  # Ensure it's a number
                    'available_days': max(0, allocated_days - used_leaves)  # Ensure non-negative
                })
                
            except Exception as e:
                # Log error and continue with next leave type
                continue
        
        return balances