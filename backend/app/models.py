# models.py
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class EmployeeDepartment(models.Model):
    """Department lookup table for organizing employees"""
    dept_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dept_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_department'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['dept_name']

    def __str__(self):
        return self.dept_name


class Job(models.Model):
    """Job positions within departments"""
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=100, unique=True, db_index=True)
    dept = models.ForeignKey(
        EmployeeDepartment, 
        on_delete=models.CASCADE, 
        related_name='jobs',
        db_index=True,
        null=True,
        blank=True
    )
    job_description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['job_title']
        indexes = [
            models.Index(fields=['job_title', 'is_active']),
            models.Index(fields=['dept', 'is_active']),
        ]

    def __str__(self):
        return self.job_title


class Employee(models.Model):
    """Core employee information"""
    emp_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emp_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    hire_date = models.DateField()
    resignation_date = models.DateField(null=True, blank=True)
    emp_education = models.CharField(null=True, blank=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['emp_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['hire_date']),
        ]

    def __str__(self):
        return f"{self.emp_name} ({self.email})"

    def clean(self):
        errors = {}
        if self.resignation_date and self.resignation_date < self.hire_date:
            errors['resignation_date'] = "Resignation date cannot be before hire date"
        if self.hire_date > timezone.now().date():
            errors['hire_date'] = "Hire date cannot be in the future"
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_current_status(self):
        """Get employee's current job status"""
        return self.statuses.filter(is_current=True).first()

    def get_current_job(self):
        """Get employee's current job"""
        status = self.get_current_status()
        return status.job if status else None

    def get_job_history(self):
        return self.statuses.all().order_by('-start_date')
    
    def can_apply_leave(self, start_date, end_date, leave_type):
        """
        Check if employee can apply for leave based on available balance
        Returns (can_apply: bool, errors: list)
        """
        errors = []
        
        # Calculate requested days
        requested_days = (end_date - start_date).days + 1
        year = start_date.year
        
        # Get or create leave balance for this year and leave type
        try:
            leave_balance = self.leave_balances.get(
                leave_type=leave_type, 
                year=year
            )
            available_balance = leave_balance.balance
        except LeaveBalance.DoesNotExist:
            # If no balance exists, create one with max_allocation from leave_type
            available_balance = leave_type.annual_allocation
            LeaveBalance.objects.create(
                employee=self,
                leave_type=leave_type,
                year=year,
                balance=available_balance
            )
        
        # Calculate already consumed leave for this year and type
        consumed_days = self.leaves.filter(
            leave_type=leave_type,
            year=year,
            status='APPROVED'
        ).aggregate(
            total=models.Sum('days_requested')
        )['total'] or 0
        
        # Calculate remaining balance
        remaining_balance = available_balance - consumed_days
        
        # Validate if enough balance is available
        if requested_days > remaining_balance:
            errors.append(
                f"Insufficient leave balance. Requested: {requested_days} days, "
                f"Available: {remaining_balance} days for {leave_type.name} in {year}"
            )
        
        # Additional validations
        if requested_days <= 0:
            errors.append("Leave duration must be at least 1 day")
        
        if start_date < timezone.now().date():
            errors.append("Cannot apply for leave in the past")
        
        if end_date < start_date:
            errors.append("End date cannot be before start date")
        
        # Check for overlapping approved leaves
        overlapping_leaves = self.leaves.filter(
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='APPROVED'
        ).exclude(pk=getattr(self, 'pk', None))  # Exclude current leave if updating
        
        if overlapping_leaves.exists():
            errors.append("Leave dates overlap with existing approved leave")
        
        return len(errors) == 0, errors
    
    def get_leave_balance(self, leave_type, year=None):
        """Get current leave balance for a specific leave type and year"""
        if year is None:
            year = timezone.now().year
        
        try:
            leave_balance = self.leave_balances.get(
                leave_type=leave_type,
                year=year
            )
            available_balance = leave_balance.balance
        except LeaveBalance.DoesNotExist:
            available_balance = leave_type.annual_allocation
        
        # Calculate consumed leave
        consumed_days = self.leaves.filter(
            leave_type=leave_type,
            year=year,
            status='APPROVED'
        ).aggregate(
            total=models.Sum('days_requested')
        )['total'] or 0
        
        return {
            'total_allocation': available_balance,
            'consumed': consumed_days,
            'remaining': available_balance - consumed_days
        }


class EmployeeStatus(models.Model):
    """Track employee job assignments and salary history"""
    st_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="statuses")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="employee_statuses")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_status'
        verbose_name = 'Employee Status'
        verbose_name_plural = 'Employee Statuses'
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['employee'],
                condition=models.Q(is_current=True),
                name='unique_current_status_per_employee'
            )
        ]
        indexes = [
            models.Index(fields=['employee', 'is_current']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return f"{self.employee.emp_name} - {self.job.job_title} ({self.start_date})"

    def clean(self):
        errors = {}
        if self.end_date and self.end_date < self.start_date:
            errors['end_date'] = "End date cannot be before start date"
        if self.start_date < self.employee.hire_date:
            errors['start_date'] = "Job start date cannot be before employee hire date"
        if self.salary <= 0:
            errors['salary'] = "Salary must be greater than zero"
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_current:
            # Mark other current statuses as not current
            EmployeeStatus.objects.filter(
                employee=self.employee,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False, end_date=timezone.now().date())
        super().save(*args, **kwargs)



class LeaveType(models.Model):
    """Define different types of leaves with their policies"""
    leave_type_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    leave_name = models.CharField(
        max_length=50,
        help_text="e.g., Annual Leave, Sick Leave, Personal Leave",
    )
    annual_allocation = models.IntegerField(
        default=20, help_text="Default annual allocation in days"
    )
    carry_forward = models.BooleanField(
        default=False, help_text="Can unused leaves be carried to next year"
    )
    max_consecutive_days = models.IntegerField(
        default=7, help_text="Maximum consecutive days allowed"
    )
    min_notice_days = models.IntegerField(
        default=1, help_text="Minimum notice required in days"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leave_type"
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"
        ordering = ["leave_name"] 

    def __str__(self):
        return f"{self.leave_name} ({self.annual_allocation} days)"

    def clean(self):
        if self.annual_allocation < 0:
            raise ValidationError("Annual allocation cannot be negative")
        if self.max_consecutive_days < 1:
            raise ValidationError("Maximum consecutive days must be at least 1")
        if self.min_notice_days < 0:
            raise ValidationError("Minimum notice days cannot be negative")


class LeaveBalance(models.Model):
    """Track yearly leave balances for each employee and leave type"""
    balance_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    employee = models.ForeignKey(
        "Employee", on_delete=models.CASCADE, related_name="leave_balances"
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.CASCADE, related_name="leave_balances"
    )
    year = models.PositiveIntegerField()
    balance = models.IntegerField(default=0)

    class Meta:
        db_table = "leave_balance"
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "leave_type", "year"],
                name="unique_leave_balance_per_year",
            )
        ]
        ordering = ["year", "employee"]  

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.year}): {self.balance} days"
    
class LeaveManagement(models.Model):
    """Leave application and approval workflow"""
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    leave_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="leave_applications")
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.IntegerField(editable=False)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    applied_on = models.DateTimeField(auto_now_add=True)
    validated_on = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    year = models.IntegerField(editable=False, db_index=True, null=False, blank=False)

    class Meta:
        db_table = 'leave_management'
        verbose_name = 'Leave Application'
        verbose_name_plural = 'Leave Applications'
        ordering = ['-applied_on']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'year']),
        ]

    def __str__(self):
        return f"{self.employee.emp_name} - {self.leave_type.name} ({self.start_date} to {self.end_date}) - {self.status}"

    def clean(self):
        """Validate leave application"""
        if self.start_date and self.end_date:
            self.days_requested = (self.end_date - self.start_date).days + 1
            self.year = self.start_date.year

        if self.days_requested <= 0:
            raise ValidationError("End date must be after start date")
    
        # Only validate balance for new applications or pending status
        if self.employee and self.start_date and self.end_date and self.leave_type:
            if self.status == 'PENDING' or not self.pk:
                can_apply, errors = self.employee.can_apply_leave(
                    self.start_date, self.end_date, self.leave_type
                )
                if not can_apply:
                    raise ValidationError({"__all__": errors})

    def save(self, *args, **kwargs):
        # Always calculate days and year
        if self.start_date and self.end_date:
            self.days_requested = (self.end_date - self.start_date).days + 1
            self.year = self.start_date.year

        # Only validate for new applications or pending status
        if self.status == 'PENDING' or not self.pk:
            self.full_clean()

        super().save(*args, **kwargs)

    def approve(self, comments=None):
        """Approve the leave application and update leave balance"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending leaves can be approved")

        # Double-check balance before approval
        can_apply, errors = self.employee.can_apply_leave(
            self.start_date, self.end_date, self.leave_type
        )
        if not can_apply:
            raise ValidationError(f"Cannot approve: {', '.join(errors)}")

        self.status = 'APPROVED'
        self.validated_on = timezone.now()
        if comments:
            self.comments = comments
        
        # Deduct from leave balance
        self._update_leave_balance(-self.days_requested)
        
        self.save(update_fields=['status', 'comments', 'validated_on'])

    def reject(self, rejection_reason):
        """Reject the leave application"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending leaves can be rejected")

        if not rejection_reason.strip():
            raise ValidationError("Rejection reason is required")

        self.status = 'REJECTED'
        self.rejection_reason = rejection_reason
        self.validated_on = timezone.now()
        self.save(update_fields=['status', 'rejection_reason', 'validated_on'])

    def cancel(self, cancelled_by=None):
        """Cancel the leave application"""
        if self.status not in ['PENDING', 'APPROVED']:
            raise ValidationError("Only pending or approved leaves can be cancelled")

        if self.status == 'APPROVED' and self.start_date <= timezone.now().date():
            raise ValidationError("Cannot cancel leave that has already started")

        old_status = self.status
        self.status = 'CANCELLED'
        
        if cancelled_by:
            self.comments = f"Cancelled by {cancelled_by.emp_name} on {timezone.now().date()}"
        
        # If was approved, restore the leave balance
        if old_status == 'APPROVED':
            self._update_leave_balance(self.days_requested)
        
        self.save(update_fields=['status', 'comments'])

    def _update_leave_balance(self, days_change):
        """Update leave balance - positive to add, negative to subtract"""
        leave_balance, created = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=self.year,
            defaults={'balance': self.leave_type.annual_allocation}
        )
        
        leave_balance.balance += days_change
        leave_balance.save(update_fields=['balance'])

    def can_be_cancelled(self):
        """Check if leave can be cancelled"""
        if self.status in ['REJECTED', 'CANCELLED']:
            return False

        if self.status == 'APPROVED' and self.start_date <= timezone.now().date():
            return False

        return True

    @property
    def is_active(self):
        """Check if leave is currently active (employee is on leave)"""
        today = timezone.now().date()
        return (self.status == 'APPROVED' and self.start_date <= today <= self.end_date)