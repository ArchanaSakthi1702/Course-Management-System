# Python & Django imports
from datetime import date
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers


# DRF imports
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied

# JWT for authentication
from rest_framework_simplejwt.tokens import RefreshToken

# App models
from api.models import (
    Course, Student, Progress, Enrollment,
    Announcement, Assignment, CourseFile, Teacher
)

# App serializers
from api.serializers import (
    ProgressSerializer, AnnouncementSerializer,
    AssignmentSerializer, CourseFileSerializer, CourseSerializer,
    UserSerializer, TeacherSerializer, StudentSerializer, RegisterSerializer,
    EnrolledCourseSerializer, TeacherCourseSerializer,
    CourseDetailSerializer, BasicCourseSerializer
)

User = get_user_model()

# Register API
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# Login API (JWT Token)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=400)

# Retrieve User Profile
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserSerializer(user).data

        # Check if the user is a teacher
        try:
            teacher = Teacher.objects.get(user=user)
            user_data['role'] = "Teacher"
            user_data['teacher_details'] = TeacherSerializer(teacher).data
        except Teacher.DoesNotExist:
            pass

        # Check if the user is a student
        try:
            student = Student.objects.get(user=user)
            user_data['role'] = "Student"
            user_data['student_details'] = StudentSerializer(student).data
        except Student.DoesNotExist:
            pass

        print(user_data)
        return Response(user_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only logged-in users can access
def upload_course(request):
    try:
        user = request.user

        # Check if the user is a teacher
        if not hasattr(user, 'teacher'):
            return Response({"error": "Only teachers can upload courses."}, status=status.HTTP_403_FORBIDDEN)

        teacher = user.teacher  # Get the teacher instance

        # ✅ Use `request.FILES` for file uploads
        data = request.data.copy()
        data['teacher'] = teacher.id  
        print("Received Data:", data)  # ✅ Debug request data
        print("Received Files:", request.FILES)

        # ✅ Pass both `data` and `FILES` to serializer
        serializer = CourseSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            course = serializer.save(thumbnail=request.FILES.get('thumbnail'))  # ✅ Store file

            # ✅ Print stored course data after saving
            print("Stored Course Data:", serializer.data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class EnrollCourseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        # Check if user is a student
        try:
            student = user.student_profile  
        except Student.DoesNotExist:
            return Response({"error": "Only students can enroll in courses."}, status=403)

        course_id = request.data.get("course")
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found."}, status=404)

        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)

        if not created:
            return Response({"message": "Already enrolled in this course."}, status=400)

        return Response({"message": "Successfully enrolled!"}, status=201)


class UploadCourseFileView(generics.CreateAPIView):
    queryset = CourseFile.objects.all()
    serializer_class = CourseFileSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user

        # Ensure only teachers can upload files
        if not hasattr(user, 'teacher'):
            return Response({"error": "Only teachers can upload course files."}, status=status.HTTP_403_FORBIDDEN)

        course_id = request.data.get('course')

        # Ensure the teacher owns the course
        try:
            course = Course.objects.get(id=course_id, teacher=user.teacher)
        except Course.DoesNotExist:
            return Response({"error": "You can only upload files to your own courses."}, status=status.HTTP_403_FORBIDDEN)

        # Serialize and save the file
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

class EditCourseView(generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Ensure only the teacher who owns the course can edit it."""
        user = self.request.user
        if hasattr(user, 'teacher'):
            return Course.objects.filter(teacher=user.teacher)
        return Course.objects.none()  # Prevent access for non-teachers

    def update(self, request, *args, **kwargs):
        """Custom update method to return JSON response."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Course updated successfully!", "course": serializer.data}, status=status.HTTP_200_OK)

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class DeleteCourseFileView(generics.DestroyAPIView):
    queryset = CourseFile.objects.all()
    serializer_class = CourseFileSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        file_id = kwargs.get('pk')  # Get file ID from URL
        try:
            course_file = CourseFile.objects.get(id=file_id)
            course = course_file.course

            # Ensure only the teacher who owns the course can delete the file
            if course.teacher == user.teacher:
                course_file.delete()
                return Response({"message": "Course file deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You can only delete files from your own courses."}, status=status.HTTP_403_FORBIDDEN)

        except CourseFile.DoesNotExist:
            return Response({"error": "Course file not found."}, status=status.HTTP_404_NOT_FOUND)


class DeleteCourseView(generics.DestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        course_id = kwargs.get('pk')  # Get course ID from URL
        try:
            course = Course.objects.get(id=course_id)

            # Ensure only the teacher who owns the course can delete it
            if course.teacher == user.teacher:
                course.delete()
                return Response({"message": "Course deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You can only delete your own courses."}, status=status.HTTP_403_FORBIDDEN)

        except Course.DoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        
class AssignmentCreateView(generics.CreateAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        print("Request Data:", self.request.data)  # ✅ Debugging Output

        # Check if user is a teacher
        if not hasattr(user, 'teacher'):
            raise serializers.ValidationError({"error": "Only teachers can create assignments."})

        course_id = self.request.data.get('course_id')
        if not course_id:
            raise serializers.ValidationError({"error": "course_id is required."})

        try:
            course = Course.objects.get(id=course_id, teacher=user.teacher)
        except Course.DoesNotExist:
            raise serializers.ValidationError({"error": "You can only create assignments for your own courses."})

        # ✅ Let serializer handle the course_id
        serializer.save()

class AssignmentEditDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = self.request.user
        assignment = self.get_object()

        # Only allow the course owner to update
        if hasattr(user, 'teacher') and assignment.course.teacher == user.teacher:
            serializer = self.get_serializer(assignment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Assignment updated successfully."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "You can only edit assignments for your own courses."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        assignment = self.get_object()

        # Only allow the course owner to delete
        if hasattr(user, 'teacher') and assignment.course.teacher == user.teacher:
            assignment.delete()
            return Response({"message": "Assignment deleted successfully."}, status=status.HTTP_200_OK)

        return Response({"error": "You can only delete assignments for your own courses."}, status=status.HTTP_403_FORBIDDEN)




class AnnouncementCreateView(generics.CreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        course_id = self.request.data.get('course')

        if hasattr(user, 'teacher'):  # Ensure user is a teacher
            try:
                course = Course.objects.get(id=course_id, teacher=user.teacher)
                serializer.save(course=course)
                return Response({"message": "Announcement created successfully."}, status=status.HTTP_201_CREATED)
            except Course.DoesNotExist:
                return Response({"error": "You can only create announcements for your own courses."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"error": "Only teachers can create announcements."}, status=status.HTTP_403_FORBIDDEN)


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        announcement = self.get_object()

        if hasattr(user, 'teacher') and announcement.course.teacher == user.teacher:
            serializer.save()
            return Response({"message": "Announcement updated successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "You can only edit your own announcements."}, status=status.HTTP_403_FORBIDDEN)

    def perform_destroy(self, instance):
        user = self.request.user

        if hasattr(user, 'teacher') and instance.course.teacher == user.teacher:
            instance.delete()
            return Response({"message": "Announcement deleted successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "You can only delete your own announcements."}, status=status.HTTP_403_FORBIDDEN)


class IsCourseTeacher(permissions.BasePermission):
    """Custom permission to allow only the course teacher to manage progress."""
    def has_permission(self, request, view):
        progress = get_object_or_404(Progress, pk=view.kwargs['pk'])
        return request.user == progress.course.teacher.user

class ProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacher]

class EnrolledCoursesView(generics.ListAPIView):
    serializer_class = EnrolledCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user.student_profile)



class MyCoursesView(generics.ListAPIView):
    serializer_class = TeacherCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(teacher__user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request}) 
        return Response(serializer.data)

class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only logged-in users can access

    def get(self, request, course_id):
        user = request.user
        course = Course.objects.filter(id=course_id).first()

        if not course:
            return Response({"error": "Course not found"}, status=404)

        # If user is a student, check enrollment
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            is_enrolled = Enrollment.objects.filter(student=student, course=course).exists()

            if is_enrolled:
                serializer = CourseDetailSerializer(course)
                print(serializer.data)  # Full details
                return Response({**serializer.data, "edit": False, "is_enrolled": True})  # No edit access
            else:
                serializer = BasicCourseSerializer(course) 
                print(serializer.data)   # Basic details
                return Response({**serializer.data, "edit": False, "is_enrolled": False})  # No edit access

        # If user is a teacher, check if they are the course owner
        if hasattr(user, 'teacher'):
            is_teacher = course.teacher == user.teacher  # Check if the logged-in user is the course teacher
            if is_teacher:
                serializer = CourseDetailSerializer(course) 
                print(serializer.data)  # Use full details
            else:
                serializer = BasicCourseSerializer(course)  
                print(serializer.data) # Use basic details if not their course

            return Response({**serializer.data, "edit": is_teacher, "is_enrolled": True})  

        # If neither student nor teacher, return error
        return Response({"error": "Access denied"}, status=403)


class IsTeacherOwner(permissions.BasePermission):
    """
    Custom permission to allow only the teacher who owns the course to modify it.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and hasattr(request.user, 'teacher') and obj.course.teacher == request.user.teacher

class AnnouncementCreateView(generics.CreateAPIView):
    """
    Create an announcement (only for the teacher who owns the course).
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'teacher'):
            raise PermissionDenied("Only teachers can create announcements.")
        
        course_id = self.request.data.get('course')  # Get course ID from request
        course = Course.objects.filter(id=course_id, teacher=user.teacher).first()

        if not course:
            raise PermissionDenied("You can only create announcements for your own courses.")
        
        serializer.save(course=course)  # Save with the correct course

class AnnouncementUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete announcements (only for the teacher who owns the course).
    """
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsTeacherOwner]

@api_view(['GET'])
@permission_classes([AllowAny])  # ✅ Allow all users (students & teachers) to see courses
def get_all_courses(request):
    courses = Course.objects.all()
    serializer = CourseSerializer(courses, many=True, context={"request": request})
    return Response(serializer.data)
