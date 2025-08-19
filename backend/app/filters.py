# filters.py
import django_filters
from .models import Employee

class EmployeeFilter(django_filters.FilterSet):
    job_title = django_filters.CharFilter(field_name='job__job_title', lookup_expr='icontains')

    class Meta:
        model = Employee
        fields = ['job_title', 'is_active']
