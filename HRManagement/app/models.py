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
        db_index=True
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
        return f"{self.job_title} - {self.dept.dept_name}"


class Employee(models.Model):
    """Core employee information"""
    emp_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emp_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    hire_date = models.DateField()
    resignation_date = models.DateField(null=True, blank=True)
    emp_education = models.CharField(null=True,blank=False)
    job = models.ForeignKey(Job,on_delete=models.CASCADE,null=True,blank=True)
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
        """Validate employee data"""
        errors = {}
        
        # Validate resignation date
        if self.resignation_date and self.resignation_date < self.hire_date:
            errors['resignation_date'] = "Resignation date cannot be before hire date"
        
        # Validate hire date is not in future
        if self.hire_date > timezone.now().date():
            errors['hire_date'] = "Hire date cannot be in the future"
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_current_status(self):
        """Get employee's current job status"""
        return self.statuses.filter(
            start_date__lte=timezone.now().date(),
            end_date__isnull=True,
            is_current=True
        ).first()

    def get_current_manager(self):
        """Get employee's current manager"""
        current_status = self.get_current_status()
        return current_status.manager if current_status else None

    def get_current_job(self):
        """Get employee's current job"""
        current_status = self.get_current_status()
        return current_status.job if current_status else None

    def get_current_salary(self):
        """Get employee's current salary"""
        current_status = self.get_current_status()
        return current_status.salary if current_status else None

    def get_leave_balance(self, leave_type, year=None):
        """Calculate current leave balance for a specific leave type and year"""
        if year is None:
            year = timezone.now().year

        try:
            # Try to get from LeaveBalance model first
            balance_record = self.leave_balances.get(leave_type=leave_type, year=year)
            return balance_record.available_days
        except LeaveBalance.DoesNotExist:
            # Fallback to calculation from leave type allocation
            total_allocation = leave_type.annual_allocation
            used_leaves = self.leaves.filter(
                leave_type=leave_type,
                status='APPROVED',
                start_date__year=year
            ).aggregate(
                total_days=Sum('days_requested')
            )['total_days'] or 0
            
            return max(0, total_allocation - used_leaves)

    def can_apply_leave(self, start_date, end_date, leave_type):
        """
        Comprehensive validation for leave application
        Returns: (can_apply: bool, errors: list)
        """
        errors = []

        # Basic employee status checks
        if not self.is_active:
            errors.append("Inactive employee cannot apply for leave")

        # Date validations
        if start_date < self.hire_date:
            errors.append("Cannot apply for leave before joining date")

        if self.resignation_date and start_date > self.resignation_date:
            errors.append("Cannot apply for leave after resignation date")

        if end_date < start_date:
            errors.append("End date cannot be before start date")

        if start_date < timezone.now().date():
            errors.append("Cannot apply for leave for past dates")

        # Calculate requested days
        days_requested = (end_date - start_date).days + 1

        # Leave type validations
        if not leave_type.is_active:
            errors.append("This leave type is not active")

        # Balance check
        current_balance = self.get_leave_balance(leave_type, start_date.year)
        if days_requested > current_balance:
            errors.append(
                f"Insufficient leave balance. Available: {current_balance} days, "
                f"Requested: {days_requested} days"
            )

        # Policy checks
        if days_requested > leave_type.max_consecutive_days:
            errors.append(
                f"Cannot apply for more than {leave_type.max_consecutive_days} consecutive days "
                f"for {leave_type.name}"
            )

        # Notice period check
        notice_days = (start_date - timezone.now().date()).days
        if notice_days < leave_type.min_notice_days:
            errors.append(
                f"Minimum {leave_type.min_notice_days} days notice required for {leave_type.name}"
            )

        # Overlapping leaves check
        overlapping = self.leaves.filter(
            Q(status='PENDING') | Q(status='APPROVED'),
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        if overlapping.exists():
            overlapping_leave = overlapping.first()
            errors.append(
                f"Leave dates overlap with existing {overlapping_leave.status.lower()} leave "
                f"({overlapping_leave.start_date} to {overlapping_leave.end_date})"
            )

        return len(errors) == 0, errors

    def get_subordinates(self):
        """Get all employees reporting to this employee"""
        return Employee.objects.filter(
            statuses__manager=self,
            statuses__is_current=True,
            is_active=True
        ).distinct()

    def is_manager_of(self, employee):
        """Check if this employee is manager of another employee"""
        return employee.get_current_manager() == self


class EmployeeStatus(models.Model):
    """Track employee job assignments, salary, and reporting structure over time"""
    st_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="statuses")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="employee_statuses")
    manager = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="subordinates"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    address = models.TextField(null = True,blank=True)
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
        """Validate employee status data"""
        errors = {}

        # Date validations
        if self.end_date and self.end_date < self.start_date:
            errors['end_date'] = "End date cannot be before start date"

        if self.start_date < self.employee.hire_date:
            errors['start_date'] = "Job start date cannot be before employee hire date"

        # Manager validations
        if self.manager == self.employee:
            errors['manager'] = "Employee cannot be their own manager"

        if self.manager and not self.manager.is_active:
            errors['manager'] = "Manager must be an active employee"

        # Salary validation
        if self.salary <= 0:
            errors['salary'] = "Salary must be greater than zero"

        # Department consistency check

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # If this is current status, set others to not current
        if self.is_current:
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
        unique=True,
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
        ordering = ["year", "employee"]  # ✅ only direct fields

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
    days_requested = models.IntegerField(editable=False)  # Auto-calculated
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    applied_on = models.DateTimeField(auto_now_add=True)
    incharge = models.ForeignKey(  #incharge of handling that employees leave
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="incharge"
    )
    validated_on = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'leave_management'
        verbose_name = 'Leave Application'
        verbose_name_plural = 'Leave Applications'
        ordering = ['-applied_on']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.employee.emp_name} - {self.leave_type.name} ({self.start_date} to {self.end_date}) - {self.status}"

    def clean(self):
        """Validate leave application"""
        # Calculate days requested
        if self.start_date and self.end_date:
            self.days_requested = (self.end_date - self.start_date).days + 1

        # Run comprehensive validation only for new/pending applications
        if self.employee and self.start_date and self.end_date and self.leave_type:
            # Skip validation for approved/rejected leaves to allow admin corrections
            if self.status == 'PENDING' or not self.pk:
                can_apply, errors = self.employee.can_apply_leave(
                    self.start_date, 
                    self.end_date, 
                    self.leave_type
                )
                if not can_apply:
                    raise ValidationError({"__all__": errors})

    def save(self, *args, **kwargs):
        # Always calculate days requested
        if self.start_date and self.end_date:
            self.days_requested = (self.end_date - self.start_date).days + 1
        
        # Validate only for new applications or status changes to pending
        if self.status == 'PENDING' or not self.pk:
            self.full_clean()
        
        # Set approval timestamp
        if self.status == 'APPROVED' and not self.approved_on:
            self.approved_on = timezone.now()
        
        super().save(*args, **kwargs)

    def approve(self, approved_by, comments=None):
        """Approve the leave application"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending leaves can be approved")
        
        # Verify approver has authority
        if not self.employee.is_manager_of(self.employee) and approved_by != self.employee.get_current_manager():
            raise ValidationError("Only the employee's manager can approve leave")
        
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_on = timezone.now()
        if comments:
            self.comments = comments
        self.save(update_fields=['status', 'approved_by', 'approved_on', 'comments'])

    def reject(self, rejected_by, rejection_reason):
        """Reject the leave application"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending leaves can be rejected")
        
        if not rejection_reason.strip():
            raise ValidationError("Rejection reason is required")
        
        self.status = 'REJECTED'
        self.approved_by = rejected_by
        self.approved_on = timezone.now()
        self.rejection_reason = rejection_reason
        self.save(update_fields=['status', 'approved_by', 'approved_on', 'rejection_reason'])

    def cancel(self, cancelled_by=None):
        """Cancel the leave application"""
        if self.status not in ['PENDING', 'APPROVED']:
            raise ValidationError("Only pending or approved leaves can be cancelled")
        
        if self.status == 'APPROVED' and self.start_date <= timezone.now().date():
            raise ValidationError("Cannot cancel leave that has already started")
        
        self.status = 'CANCELLED'
        if cancelled_by:
            self.comments = f"Cancelled by {cancelled_by.emp_name} on {timezone.now().date()}"
        self.save(update_fields=['status', 'comments'])

    def can_be_cancelled(self):
        """Check if leave can be cancelled"""
        if self.status in ['REJECTED', 'CANCELLED']:
            return False
        
        if self.status == 'APPROVED' and self.start_date <= timezone.now().date():
            return False
        
        return True

    def get_approver(self):
        """Get the person who should approve this leave"""
        return self.employee.get_current_manager()

    @property
    def is_active(self):
        """Check if leave is currently active (employee is on leave)"""
        today = timezone.now().date()
        return (self.status == 'APPROVED' and 
                self.start_date <= today <= self.end_date)

