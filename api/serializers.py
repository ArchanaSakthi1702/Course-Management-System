from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import (
    Teacher, Student, Course, Enrollment,
    Assignment, Announcement, CourseFile,
    Progress, Certificate
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'mobile_number', 'profile_pic', 'bio']

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['experience', 'qualifications', 'subjects_taught', 'joining_date']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['enrollment_year', 'grade', 'section', 'parent_contact']

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=['teacher', 'student'], write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    profile_pic = serializers.ImageField(required=False, allow_null=True)  # ✅ Add profile_pic field

    # Fields for teacher
    experience = serializers.IntegerField(required=False)
    qualifications = serializers.CharField(required=False, allow_blank=True)
    subjects_taught = serializers.CharField(required=False, allow_blank=True)
    joining_date = serializers.DateField(required=False)

    # Fields for student
    enrollment_year = serializers.IntegerField(required=False)
    grade = serializers.CharField(required=False, allow_blank=True)
    section = serializers.CharField(required=False, allow_blank=True)
    parent_contact = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'mobile_number', 'profile_pic', 'role',
                  'experience', 'qualifications', 'subjects_taught', 'joining_date', 
                  'enrollment_year', 'grade', 'section', 'parent_contact']

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        profile_pic = validated_data.pop('profile_pic', None)  # ✅ Extract profile pic

        # Extract Teacher & Student specific data
        teacher_data = {
            'experience': validated_data.pop('experience', None),
            'qualifications': validated_data.pop('qualifications', None),
            'subjects_taught': validated_data.pop('subjects_taught', None),
            'joining_date': validated_data.pop('joining_date', None),
        }

        student_data = {
            'enrollment_year': validated_data.pop('enrollment_year', None),
            'grade': validated_data.pop('grade', None),
            'section': validated_data.pop('section', None),
            'parent_contact': validated_data.pop('parent_contact', None),
        }

        # Create the User
        user = User.objects.create_user(password=password, **validated_data)

        # ✅ Assign profile pic if uploaded
        if profile_pic:
            user.profile_pic = profile_pic
            user.save()

        # Create the Teacher or Student profile
        if role == 'teacher':
            Teacher.objects.create(user=user, **teacher_data)
        elif role == 'student':
            Student.objects.create(user=user, **student_data)

        return user


class CourseSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())  # Accept teacher ID
    thumbnail = serializers.ImageField(required=False)  # ✅ Allow file uploads

    class Meta:
        model = Course
        fields = ['id', 'teacher', 'title', 'description', 'start_date', 'end_date', 'total_lessons', 'thumbnail']

    def to_representation(self, instance):
        """ Modify representation to include absolute URL for thumbnail """
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if instance.thumbnail and request is not None:
            representation['thumbnail'] = request.build_absolute_uri(instance.thumbnail.url)
        return representation


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'enrollment_date']

    def validate_student(self, value):
        """Ensure the user is a student."""
        if not Student.objects.filter(user=value.user).exists():
            raise serializers.ValidationError("Only students can enroll in courses.")
        return value

class ProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'student', 'student_name', 'course', 'course_title', 
                  'completed_lessons', 'total_lessons', 'is_completed', 'completion_date']
        read_only_fields = ['is_completed', 'completion_date']


class AssignmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'title', 'description', 'due_date']

class AnnouncementSerializer(serializers.ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = Announcement
        fields = ['id', 'course', 'title', 'message', 'created_at']


class CourseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFile
        fields = ['id', 'course', 'title', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']
        


class CertificateSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    course = CourseSerializer()

    class Meta:
        model = Certificate
        fields = ['id', 'student', 'course', 'date_issued', 'certificate_file']
        

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'course', 'title', 'message', 'created_at']

class AssignmentSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(write_only=True)  # ✅ Add this

    class Meta:
        model = Assignment
        fields = ['id', 'course_id', 'title', 'description', 'due_date']
        read_only_fields = ['id']

    def create(self, validated_data):
        course_id = validated_data.pop('course_id')
        course = Course.objects.get(id=course_id)  # ✅ Get course from `course_id`
        return Assignment.objects.create(course=course, **validated_data)


# ✅ Serializer for basic course details
class BasicCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'total_lessons', 'thumbnail']

# ✅ Serializer for full course details (if enrolled)
class CourseDetailSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    announcements = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'total_lessons', 'thumbnail', 'files', 'assignments', 'announcements']

    def get_files(self, obj):
        request = self.context.get('request')
        return [{"id": file.id, "title": file.title, "file": request.build_absolute_uri(file.file.url)} for file in obj.files.all()]

    def get_assignments(self, obj):
        return [{"id": assignment.id, "title": assignment.title, "description": assignment.description, "due_date": assignment.due_date} for assignment in obj.assignments.all()]

    def get_announcements(self, obj):
        return [{"id": announcement.id, "title": announcement.title, "message": announcement.message, "created_at": announcement.created_at} for announcement in obj.announcements.all()]

class CourseSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()  # ✅ Ensure full image URL

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'total_lessons', 'thumbnail', 'teacher']

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            return request.build_absolute_uri(obj.thumbnail.url)  # ✅ Return full URL
        return None
    
class TeacherCourseSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    course_id = serializers.ReadOnlyField(source='id')  

    class Meta:
        model = Course
        fields = ['course_id', 'title', 'description', 'start_date', 'end_date', 'total_lessons', 'thumbnail']

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')  # ✅ Ensure request is passed
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)  # ✅ Build full URL
            return obj.thumbnail.url  # ✅ Fallback to relative URL
        return None  # ✅ Return None if no thumbnail

class EnrolledCourseSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id', read_only=True)  # Returns course ID
    course_title = serializers.CharField(source='course.title', read_only=True)  # Returns course title

    class Meta:
        model = Enrollment
        fields = [ 'course_id', 'course_title', 'enrollment_date']
