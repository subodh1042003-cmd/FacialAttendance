from django.contrib import admin
from .models import Student, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'roll_number',
        'course',
        'semester',
        'registered_at'
    )
    search_fields = ('name', 'roll_number', 'email')
    list_filter = ('course', 'semester')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'date',
        'time',
        'status'
    )
    search_fields = (
        'student__name',
        'student__roll_number'
    )
    list_filter = (
        'date',
        'status'
    )
