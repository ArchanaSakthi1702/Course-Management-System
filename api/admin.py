from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Teacher, Student,Course,Certificate,Enrollment,Assignment,Progress,Announcement,CourseFile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['id', 'username', 'email', 'mobile_number', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'mobile_number']
    ordering = ['id']

class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience', 'qualifications', 'subjects_taught', 'joining_date']
    search_fields = ['user__username', 'qualifications', 'subjects_taught']
    
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'enrollment_year', 'grade', 'section', 'parent_contact']
    search_fields = ['user__username', 'grade', 'section']
    

# Course Admin
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'start_date', 'end_date','total_lessons')
    search_fields = ('title', 'teacher__user__username')

# Enrollment Admin
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date')
    search_fields = ('student__user__username', 'course__title')

# Assignment Admin
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date')
    search_fields = ('title', 'course__title')

# Announcement Admin
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    search_fields = ('title', 'course__title')

# CourseFile Admin
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_at')
    search_fields = ('title', 'course__title')

# Progress Admin
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'completed_lessons', 'total_lessons', 'is_completed', 'completion_date')
    search_fields = ('student__user__username', 'course__title')

# Certificate Admin
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date_issued')
    search_fields = ('student__user__username', 'course__title')

# Register models


# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)

admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Announcement, AnnouncementAdmin)

admin.site.register(CourseFile, CourseFileAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(Certificate, CertificateAdmin)
